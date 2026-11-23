"""Internal-agent work for 工作线: weekly snapshot extraction, batch
classification of unassigned materials and the queued 「AI 整理」 job.

The agent only sees bounded evidence assembled here (workstream names and
goals, report Markdown, material filenames and summaries) and answers JSON;
every write goes through workstreams.py, which never overwrites manual
links or manual snapshots. REPORTS_FAKE_PROVIDER keeps tests offline with a
deterministic stand-in.
"""

import json
import re

from .db import connect
from .timeutil import iso_now
from .workstreams import (
    MATRIX_WEEKS,
    SNAPSHOT_STATUSES,
    auto_link_material,
    list_workstreams,
    recent_week_keys,
    upsert_snapshot,
    week_materials_by_workstream,
    workstreams_for_prompt,
)

CLASSIFY_BATCH = 40
REPORT_EXCERPT_CHARS = 12000


def _fake():
    from .reports import fake_provider_enabled

    return fake_provider_enabled()


def _chat(conn, prompt, timeout):
    from .internal_agent import internal_chat, resolve_llm_settings

    return internal_chat(prompt, resolve_llm_settings(conn), timeout=timeout, temperature=0)


def parse_json_array(raw):
    value = (raw or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value, flags=re.IGNORECASE)
    start, end = value.find("["), value.rfind("]")
    if start < 0 or end < start:
        raise ValueError("agent output is not a JSON array")
    data = json.loads(value[start:end + 1])
    if not isinstance(data, list):
        raise ValueError("agent output is not a JSON array")
    return [item for item in data if isinstance(item, dict)]


def fake_classify(text, workstreams):
    """Offline stand-in: the first workstream whose name appears in the text."""
    text = text or ""
    return next((item["id"] for item in workstreams if item["name"] and item["name"] in text), None)


# ---------------------------------------------------------------- classification


def build_classify_prompt(workstreams, items):
    return (
        "把每份项目资料归到最相关的一条工作线。只依据文件名和摘要判断；"
        "无法判断或与所有工作线都无关时 workstream_id 填 null，不要勉强归类。"
        "只输出 JSON 数组，每项严格使用 {\"id\": 资料ID, \"workstream_id\": 工作线ID或null}，不要 Markdown。\n\n"
        f"工作线：\n{json.dumps(workstreams, ensure_ascii=False, indent=2)}\n\n"
        f"资料：\n{json.dumps(items, ensure_ascii=False, indent=2)}"
    )


def _material_hint(row):
    """Summary for uploads; manual notes have none, so their text start."""
    text = row["summary"] or ""
    if not text and row["source_type"] == "manual":
        text = row["extracted_text"] or ""
    return text[:400]


def classify_unassigned(conn, project_id, timeout=120):
    """Link materials without any workstream to the agent's choice; returns
    how many were linked."""
    workstreams = workstreams_for_prompt(conn, project_id)
    if not workstreams:
        return 0
    rows = conn.execute(
        """
        SELECT m.id, m.filename, m.summary, m.extracted_text, m.source_type FROM materials m
        WHERE m.project_id = ? AND NOT EXISTS (SELECT 1 FROM material_workstreams mw WHERE mw.material_id = m.id)
        ORDER BY m.id DESC
        """,
        (project_id,),
    ).fetchall()
    linked = 0
    for start in range(0, len(rows), CLASSIFY_BATCH):
        batch = rows[start:start + CLASSIFY_BATCH]
        items = [{"id": r["id"], "filename": r["filename"], "summary": _material_hint(r)} for r in batch]
        if _fake():
            choices = {item["id"]: fake_classify(f"{item['filename']} {item['summary']}", workstreams) for item in items}
        else:
            choices = {
                entry.get("id"): entry.get("workstream_id")
                for entry in parse_json_array(_chat(conn, build_classify_prompt(workstreams, items), timeout))
            }
        for item in items:
            if choices.get(item["id"]) is not None and auto_link_material(conn, project_id, item["id"], choices[item["id"]]):
                linked += 1
        conn.commit()
    return linked


# ---------------------------------------------------------------- snapshots


def build_snapshot_prompt(week_key, workstreams, report_md):
    return (
        f"根据 {week_key} 的项目周报和各工作线本周关联资料，为每条工作线写一条本周快照。"
        "只依据给出的证据，不要编造。status 取值：advanced（本周有实质进展）、steady（无明显进展或没有证据）、"
        "blocked（明确受阻或等待外部）。summary 用一句话写本周进展，不超过60个汉字；没有证据时写“本周无进展”。"
        "next_step 写证据中提到的下一步，不超过60个汉字，没有则留空。不要写风险预测。"
        "只输出 JSON 数组，每项严格使用 {\"id\": 工作线ID, \"status\": \"...\", \"summary\": \"...\", \"next_step\": \"...\"}，不要 Markdown。\n\n"
        f"工作线及本周关联资料：\n{json.dumps(workstreams, ensure_ascii=False, indent=2)}\n\n"
        f"周报：\n{(report_md or '')[:REPORT_EXCERPT_CHARS]}"
    )


def extract_snapshots(conn, project_id, week_key, report_md, source="generated", timeout=120):
    """Write one snapshot per active workstream for the week; manual
    snapshots are kept. Returns how many were written."""
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    rows = [r for r in list_workstreams(conn, project_id) if r["status"] == "active"]
    if not project or not rows:
        return 0
    materials = week_materials_by_workstream(conn, project_id, project["timezone"], week_key)
    evidence = [
        {
            "id": r["id"],
            "name": r["name"],
            "goal": (r["goal"] or "")[:300],
            "materials": [{"filename": m["filename"], "summary": m["summary"]} for m in materials.get(r["id"], [])],
        }
        for r in rows
    ]
    if _fake():
        answers = {
            item["id"]: {
                "status": "advanced" if item["materials"] else "steady",
                "summary": f"本周 {len(item['materials'])} 份资料：{item['materials'][0]['filename']}" if item["materials"] else "本周无进展",
                "next_step": "",
            }
            for item in evidence
        }
    else:
        answers = {
            entry.get("id"): entry
            for entry in parse_json_array(_chat(conn, build_snapshot_prompt(week_key, evidence, report_md), timeout))
        }
    written = 0
    for item in evidence:
        answer = answers.get(item["id"])
        if not answer or not str(answer.get("summary") or "").strip():
            continue
        status = answer.get("status") if answer.get("status") in SNAPSHOT_STATUSES else "steady"
        if upsert_snapshot(conn, item["id"], week_key, status, answer.get("summary"), answer.get("next_step") or "", source=source):
            written += 1
    return written


def refresh_after_report(conn, project_id, week_key, report_md, timeout=120):
    """Called after a successful report; never raises."""
    try:
        if not list_workstreams(conn, project_id):
            return 0
        written = extract_snapshots(conn, project_id, week_key, report_md, "generated", timeout)
        conn.commit()
        return written
    except Exception as exc:  # the report itself already succeeded
        conn.rollback()
        print(f"workstream snapshot extraction failed: project={project_id} week={week_key}: {exc}", flush=True)
        return 0


def backfill_snapshots(conn, project_id, timeout=120):
    """Snapshots for recent report weeks where an active workstream has none."""
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    active = [r["id"] for r in list_workstreams(conn, project_id) if r["status"] == "active"]
    if not project or not active:
        return 0
    weeks = set(recent_week_keys(project["timezone"], MATRIX_WEEKS))
    filled = 0
    for report in conn.execute(
        "SELECT week_key, content_md FROM weekly_reports WHERE project_id = ? ORDER BY week_key DESC", (project_id,)
    ).fetchall():
        if report["week_key"] not in weeks:
            continue
        have = {
            r["workstream_id"]
            for r in conn.execute(
                f"SELECT workstream_id FROM workstream_weekly WHERE week_key = ? AND workstream_id IN ({','.join('?' for _ in active)})",
                (report["week_key"], *active),
            )
        }
        if have >= set(active):
            continue
        if extract_snapshots(conn, project_id, report["week_key"], report["content_md"], "backfill", timeout):
            filled += 1
        conn.commit()
    return filled


# ---------------------------------------------------------------- queued job


def run_workstream_job(db_path, job_id, project_id, timeout=180):
    """Task-queue worker for 「AI 整理」: classify unassigned materials, then
    backfill missing snapshots. Progress lands in generation_jobs."""
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE generation_jobs SET status = 'running', input_summary = ?, started_at = ? WHERE id = ?",
            ("workstreams: classify + backfill", iso_now(), job_id),
        )
        conn.commit()
        try:
            linked = classify_unassigned(conn, project_id, timeout)
            filled = backfill_snapshots(conn, project_id, timeout)
        except Exception as exc:
            conn.rollback()
            conn.execute(
                "UPDATE generation_jobs SET status = 'failed', failure_reason = ?, completed_at = ? WHERE id = ?",
                (f"工作线整理失败：{exc}"[:2000], iso_now(), job_id),
            )
            conn.commit()
            return
        conn.execute(
            "UPDATE generation_jobs SET status = 'success', output_md = ?, completed_at = ? WHERE id = ?",
            (f"归类 {linked} 份资料，补齐 {filled} 周快照", iso_now(), job_id),
        )
        from .risks import evaluate_risks

        evaluate_risks(conn, project_id)
        conn.commit()
