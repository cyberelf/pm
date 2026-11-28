"""Internal-agent work for 工作线: weekly snapshot extraction, batch
classification of unassigned materials, follow-up TODO suggestions and
the queued 「AI 整理」 job, which also syncs this week's PR / issue activity
(workstream_git.py) and uses it as snapshot evidence.

Past weeks are locked. The first 「AI 整理」 of a project initialises history
once (classify every unassigned material, fill missing snapshots from past
reports); every later run is incremental and only touches the current week.

The agent only sees bounded evidence assembled here (workstream names and
goals, report Markdown, material filenames and summaries) and answers JSON;
every write goes through workstreams.py, which never overwrites manual
links or manual snapshots. REPORTS_FAKE_PROVIDER keeps tests offline with a
deterministic stand-in.
"""

import json
import re

from .db import connect
from .timeutil import current_week_key, iso_now, parse_iso, week_key_for
from .workstreams import (
    MATRIX_WEEKS,
    SNAPSHOT_STATUSES,
    add_agent_todos,
    auto_link_material,
    close_agent_todos,
    list_workstreams,
    open_todos_for_prompt,
    recent_week_keys,
    upsert_snapshot,
    week_materials_by_workstream,
    workstreams_for_prompt,
)

CLASSIFY_BATCH = 40
PARENT_MATERIALS = 25
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
        "带 parent 的是该父工作线下的子工作线：资料明确属于某条子工作线时归到子工作线，只与整条线总体相关时归到父工作线；"
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


def classify_unassigned(conn, project_id, timeout=120, week_key=None):
    """Link materials without any workstream to the agent's choice; with
    week_key only materials created that week. Returns how many were linked."""
    workstreams = workstreams_for_prompt(conn, project_id)
    if not workstreams:
        return 0
    tz_name = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()["timezone"]
    rows = [
        r
        for r in conn.execute(
            """
            SELECT m.id, m.filename, m.summary, m.extracted_text, m.source_type, m.created_at FROM materials m
            WHERE m.project_id = ? AND NOT EXISTS (SELECT 1 FROM material_workstreams mw WHERE mw.material_id = m.id)
            ORDER BY m.id DESC
            """,
            (project_id,),
        ).fetchall()
        if week_key is None or (parse_iso(r["created_at"]) and week_key_for(parse_iso(r["created_at"]), tz_name) == week_key)
    ]
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


def build_snapshot_prompt(week_key, workstreams, report_md, with_items=False):
    items_rule = (
        "open_items 是该工作线尚未关闭的 TODO。new_items 写证据中明确提到、需要后续跟进且不在 open_items 里的事项，"
        "每条不超过40个汉字，最多3条，没有就给空数组；done_item_ids 写证据明确表明已完成的 open_items 的 id，没有就给空数组。"
        if with_items else ""
    )
    shape = (
        '{"id": 工作线ID, "status": "...", "summary": "...", "next_step": "...", "new_items": ["..."], "done_item_ids": [ID]}'
        if with_items else '{"id": 工作线ID, "status": "...", "summary": "...", "next_step": "..."}'
    )
    return (
        f"根据 {week_key} 的项目周报和各工作线本周关联资料，为每条工作线写一条本周快照。"
        "只依据给出的证据，不要编造。status 取值：advanced（本周有实质进展）、steady（无明显进展或没有证据）、"
        "blocked（明确受阻或等待外部）。summary 用一句话写本周进展，不超过60个汉字；没有证据时写“本周无进展”。"
        "next_step 写证据中提到的下一步，不超过60个汉字，没有则留空。不要写风险预测。"
        "pull_requests_and_issues 是本周更新过的代码仓库 PR / Issue（state：merged 已合并、closed 已关闭、open 进行中、draft 草稿），"
        "合并的 PR 和关闭的 Issue 算实质进展，长期 open 或明确卡住的算受阻证据；它们也是后续跟进事项的证据来源。"
        "带 parent 的是子工作线，只写它自己的进展；父工作线的资料里含其子工作线的资料（带 sub_workstream 字段），"
        "父工作线的快照概括整条线，new_items 只写属于父工作线本身的事项。"
        f"{items_rule}"
        f"只输出 JSON 数组，每项严格使用 {shape}，不要 Markdown。\n\n"
        f"工作线及本周关联资料：\n{json.dumps(workstreams, ensure_ascii=False, indent=2)}\n\n"
        f"周报：\n{(report_md or '（本周尚未生成周报）')[:REPORT_EXCERPT_CHARS]}"
    )


FAKE_FOLLOW_UP = "待跟进："
FAKE_DONE = "已完成："


def _fake_snapshot(item):
    texts = [m["summary"] or "" for m in item["materials"] if not m.get("sub_workstream")]
    new_items = [re.split(r"[。\n]", t.split(FAKE_FOLLOW_UP, 1)[1])[0].strip() for t in texts if FAKE_FOLLOW_UP in t]
    done = [
        open_item["id"]
        for open_item in item.get("open_items", [])
        if any(FAKE_DONE + open_item["title"] in t for t in texts)
    ]
    code = item.get("pull_requests_and_issues") or []
    if not item["materials"] and code:
        return {
            "status": "advanced", "summary": f"本周 {len(code)} 条 PR/Issue：{code[0]['title']}", "next_step": "",
            "new_items": [], "done_item_ids": [o["id"] for o in item.get("open_items", []) if any(
                c["state"] in ("merged", "closed") and o["title"] in c["title"] for c in code)],
        }
    return {
        "status": "advanced" if item["materials"] else "steady",
        "summary": f"本周 {len(item['materials'])} 份资料：{item['materials'][0]['filename']}" if item["materials"] else "本周无进展",
        "next_step": "",
        "new_items": new_items,
        "done_item_ids": done,
    }


def extract_snapshots(conn, project_id, week_key, report_md, source="generated", timeout=120, only_missing=False):
    """Write one snapshot per active workstream for the week; manual
    snapshots are kept. For the current week the agent also adds follow-ups
    as TODOs linked to the line and closes its own finished, unedited ones; a past week (history
    initialisation) only fills workstreams that have no snapshot yet.
    Returns {"snapshots", "items_added", "items_closed"}."""
    result = {"snapshots": 0, "items_added": 0, "items_closed": 0}
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    rows = [r for r in list_workstreams(conn, project_id) if r["status"] == "active"]
    if not project or not rows:
        return result
    if only_missing:
        have = {
            r["workstream_id"]
            for r in conn.execute(
                f"SELECT workstream_id FROM workstream_weekly WHERE week_key = ? AND workstream_id IN ({','.join('?' for _ in rows)})",
                (week_key, *[r["id"] for r in rows]),
            )
        }
        rows = [r for r in rows if r["id"] not in have]
        if not rows:
            return result
    with_items = week_key == current_week_key(project["timezone"])
    from .workstream_git import week_items_by_workstream

    materials = week_materials_by_workstream(conn, project_id, project["timezone"], week_key)
    git = week_items_by_workstream(conn, project_id, week_key)
    every = list_workstreams(conn, project_id)
    names = {r["id"]: r["name"] for r in every}
    evidence = []
    for r in rows:
        own = [{"filename": m["filename"], "summary": m["summary"]} for m in materials.get(r["id"], [])]
        seen = {m["id"] for m in materials.get(r["id"], [])}
        for child in every:
            if child["parent_id"] != r["id"]:
                continue
            for m in materials.get(child["id"], []):
                if m["id"] not in seen and len(own) < PARENT_MATERIALS:
                    seen.add(m["id"])
                    own.append({"filename": m["filename"], "summary": m["summary"], "sub_workstream": child["name"]})
        code = list(git.get(r["id"], []))
        for child in every:
            if child["parent_id"] == r["id"]:
                code += [{**g, "sub_workstream": child["name"]} for g in git.get(child["id"], [])][:PARENT_MATERIALS - len(code)]
        entry = {
            "id": r["id"],
            "name": r["name"],
            "goal": (r["goal"] or "")[:300],
            "materials": own,
        }
        if code:
            entry["pull_requests_and_issues"] = code
        if r["parent_id"] in names:
            entry["parent"] = names[r["parent_id"]]
        if with_items:
            entry["open_items"] = open_todos_for_prompt(conn, r["id"])
        evidence.append(entry)
    if _fake():
        answers = {item["id"]: _fake_snapshot(item) for item in evidence}
    else:
        answers = {
            entry.get("id"): entry
            for entry in parse_json_array(_chat(conn, build_snapshot_prompt(week_key, evidence, report_md, with_items), timeout))
        }
    for item in evidence:
        answer = answers.get(item["id"])
        if not answer:
            continue
        if str(answer.get("summary") or "").strip():
            status = answer.get("status") if answer.get("status") in SNAPSHOT_STATUSES else "steady"
            if upsert_snapshot(conn, item["id"], week_key, status, answer.get("summary"), answer.get("next_step") or "", source=source):
                result["snapshots"] += 1
        if with_items:
            new_items = answer.get("new_items") if isinstance(answer.get("new_items"), list) else []
            done_ids = answer.get("done_item_ids") if isinstance(answer.get("done_item_ids"), list) else []
            result["items_added"] += add_agent_todos(conn, item["id"], [t for t in new_items if isinstance(t, str)])
            result["items_closed"] += close_agent_todos(conn, item["id"], done_ids)
    return result


def current_report_md(conn, project_id, week_key):
    row = conn.execute(
        "SELECT content_md FROM weekly_reports WHERE project_id = ? AND week_key = ?", (project_id, week_key)
    ).fetchone()
    return row["content_md"] if row else ""


def refresh_after_report(conn, project_id, week_key, report_md, timeout=120, git_extras=None):
    """Called after a successful report; never raises. Only the current week
    is refreshed: past weeks are locked. The PR / issue extras the report
    already fetched are stored and classified first, without new API calls."""
    try:
        project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not project or week_key != current_week_key(project["timezone"]) or not list_workstreams(conn, project_id):
            return 0
        if git_extras:
            from .workstream_git import sync_week

            sync_week(conn, project_id, timeout, extras_list=git_extras)
        written = extract_snapshots(conn, project_id, week_key, report_md, "generated", timeout)["snapshots"]
        conn.commit()
        return written
    except Exception as exc:  # the report itself already succeeded
        conn.rollback()
        print(f"workstream snapshot extraction failed: project={project_id} week={week_key}: {exc}", flush=True)
        return 0


def backfill_snapshots(conn, project_id, timeout=120):
    """History initialisation: snapshots from past reports of the matrix
    weeks, only for active workstreams that have none that week."""
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project or not any(r["status"] == "active" for r in list_workstreams(conn, project_id)):
        return 0
    current = current_week_key(project["timezone"])
    weeks = set(recent_week_keys(project["timezone"], MATRIX_WEEKS)) - {current}
    filled = 0
    for report in conn.execute(
        "SELECT week_key, content_md FROM weekly_reports WHERE project_id = ? ORDER BY week_key DESC", (project_id,)
    ).fetchall():
        if report["week_key"] not in weeks:
            continue
        if extract_snapshots(conn, project_id, report["week_key"], report["content_md"], "backfill", timeout, only_missing=True)["snapshots"]:
            filled += 1
        conn.commit()
    return filled


def project_was_organized(conn, project_id, exclude_job_id=None):
    return bool(conn.execute(
        "SELECT 1 FROM generation_jobs WHERE project_id = ? AND trigger_type = 'workstreams' AND status = 'success' AND id != ?",
        (project_id, exclude_job_id or 0),
    ).fetchone())


# ---------------------------------------------------------------- queued job


def run_workstream_job(db_path, job_id, project_id, timeout=180):
    """Task-queue worker for 「AI 整理」. The project's first run initialises
    history; later runs only touch the current week. Progress lands in
    generation_jobs."""
    with connect(db_path) as conn:
        initial = not project_was_organized(conn, project_id, job_id)
        conn.execute(
            "UPDATE generation_jobs SET status = 'running', input_summary = ?, started_at = ? WHERE id = ?",
            ("workstreams: initial history + current week" if initial else "workstreams: current week", iso_now(), job_id),
        )
        conn.commit()
        try:
            tz_name = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()["timezone"]
            week = current_week_key(tz_name)
            from .workstream_git import sync_week

            git = sync_week(conn, project_id, timeout)
            linked = classify_unassigned(conn, project_id, timeout, week_key=None if initial else week)
            filled = backfill_snapshots(conn, project_id, timeout) if initial else 0
            current = extract_snapshots(conn, project_id, week, current_report_md(conn, project_id, week), "generated", timeout)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            conn.execute(
                "UPDATE generation_jobs SET status = 'failed', failure_reason = ?, completed_at = ? WHERE id = ?",
                (f"工作线整理失败：{exc}"[:2000], iso_now(), job_id),
            )
            conn.commit()
            return
        parts = [f"归类 {linked} 份资料"]
        if initial:
            parts.append(f"补齐 {filled} 周历史快照")
        if git["items"]:
            parts.append(f"同步 {git['items']} 条 PR/Issue（AI 归类 {git['linked']} 条）")
        parts.append(f"更新本周 {current['snapshots']} 条快照")
        if current["items_added"]:
            parts.append(f"新增 {current['items_added']} 条 TODO")
        if current["items_closed"]:
            parts.append(f"关闭 {current['items_closed']} 条")
        summary = ("首次整理：" if initial else "本周：") + "，".join(parts)
        conn.execute(
            "UPDATE generation_jobs SET status = 'success', output_md = ?, completed_at = ? WHERE id = ?",
            (summary, iso_now(), job_id),
        )
        from .risks import evaluate_risks

        evaluate_risks(conn, project_id)
        conn.commit()
