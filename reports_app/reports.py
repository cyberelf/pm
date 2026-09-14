import hashlib
import json
import os
import re

from .config import DEFAULT_REPORT_TEMPLATE, DEFAULT_SYSTEM_PROMPT
from .db import connect
from .git_sources import git_auth_for_user, weekly_commits
from .risks import evaluate_risks
from .timeutil import current_week_key, iso_now, parse_iso, week_bounds, week_key_for
from .validation import ValidationError


def get_effective_template(project):
    return project["report_template"] or DEFAULT_REPORT_TEMPLATE


def get_effective_prompt(project):
    # the system prompt is fixed platform-wide; per-project values stay frozen
    # in legacy rows but are never used
    return DEFAULT_SYSTEM_PROMPT


def assemble_context(conn, project_id, week_key=None):
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    week_key = week_key or current_week_key(project["timezone"])
    week_start, week_end = week_bounds(project["timezone"])
    plan = conn.execute("SELECT * FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    update = conn.execute(
        "SELECT * FROM weekly_updates WHERE project_id = ? AND week_key = ?", (project_id, week_key)
    ).fetchone()
    materials = conn.execute(
        """
        SELECT filename, source_type, extraction_status, extracted_text, summary,
               extraction_error, created_at, updated_at
        FROM materials WHERE project_id = ? ORDER BY id DESC
        """,
        (project_id,),
    ).fetchall()
    repos = conn.execute(
        """
        SELECT repo, git_mode, notes, tracked_branches_json, status, status_message,
               last_checked_at, last_activity_at, activity_summary
        FROM github_repos WHERE project_id = ? AND enabled = 1 ORDER BY id
        """,
        (project_id,),
    ).fetchall()
    previous = conn.execute(
        "SELECT content_md, updated_at FROM weekly_reports WHERE project_id = ? AND week_key = ?",
        (project_id, week_key),
    ).fetchone()
    context = {
        "project": dict(project),
        "project_profile": {
            "name": project["name"],
            "description": project["description"],
            "status": project["status"],
            "owner": project["owner"],
            "start_date": project["start_date"],
            "end_date": project["end_date"],
            "timezone": project["timezone"],
        },
        "week_key": week_key,
        "project_week": {
            "timezone": project["timezone"],
            "start_utc": week_start.isoformat(),
            "end_utc": week_end.isoformat(),
        },
        "plan": {
            "objectives": plan["objectives"] if plan else "",
            "version": plan["version"] if plan else 1,
            "milestones": json.loads(plan["milestones_json"] if plan else "[]"),
            "deliverables": json.loads(plan["deliverables_json"] if plan else "[]"),
        },
        "weekly_update": dict(update) if update else None,
        "materials": [
            {
                "filename": row["filename"],
                "source_type": row["source_type"],
                "extraction_status": row["extraction_status"],
                "extraction_error": row["extraction_error"],
                "summary": row["summary"],
                "excerpt": (row["extracted_text"] or "")[:8000],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in materials
        ],
        "new_materials_this_week": [
            {
                "filename": row["filename"],
                "source_type": row["source_type"],
                "extraction_status": row["extraction_status"],
                "extraction_error": row["extraction_error"],
                "summary": row["summary"],
                "excerpt": (row["extracted_text"] or "")[:8000],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in materials
            if parse_iso(row["created_at"]) and week_key_for(parse_iso(row["created_at"]), project["timezone"]) == week_key
        ],
        "github_activity": [repo_activity_context(row) for row in repos],
        "git_commits_this_week": [
            repo_commit_context(row, week_start, week_end, git_auth_for_user(conn, project["user_id"]))
            for row in repos
            if row["status"] == "connected"
        ],
        "previous_current_week_report": dict(previous) if previous else None,
        "system_prompt": get_effective_prompt(project),
        "report_template": get_effective_template(project),
    }
    encoded = json.dumps(context, sort_keys=True, ensure_ascii=False)
    return context, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def input_summary(context):
    commits = sum(len(repo.get("commits", [])) for repo in context.get("git_commits_this_week", []))
    profile = context.get("project_profile") or {}
    plan = context.get("plan") or {}
    has_profile = bool(profile.get("description"))
    has_plan = bool(plan.get("objectives") or plan.get("milestones") or plan.get("deliverables"))
    return (
        f"week={context['week_key']}; "
        f"profile={'yes' if has_profile else 'no'}; "
        f"plan={'yes' if has_plan else 'no'}; "
        f"new_materials={len(context.get('new_materials_this_week', []))}; "
        f"commits={commits}; "
        f"repos={len(context['github_activity'])}"
    )


def repo_commit_context(repo_row, week_start, week_end, auth_info):
    branches = json.loads(repo_row["tracked_branches_json"] or '["main"]')
    result = weekly_commits(
        repo_row["repo"],
        week_start,
        week_end,
        branches,
        git_mode=repo_row["git_mode"],
        auth_info=auth_info,
    )
    result["notes"] = repo_row["notes"]
    return result


def repo_activity_context(repo_row):
    item = dict(repo_row)
    item["tracked_branches"] = json.loads(item.pop("tracked_branches_json") or '["main"]')
    return item


def latest_success(conn, project_id, week_key):
    return conn.execute(
        """
        SELECT * FROM generation_jobs
        WHERE project_id = ? AND week_key = ? AND status = 'success'
        ORDER BY completed_at DESC, id DESC LIMIT 1
        """,
        (project_id, week_key),
    ).fetchone()


def changed_since_last_success(conn, project_id, week_key):
    last = latest_success(conn, project_id, week_key)
    if not last:
        return True
    last_at = parse_iso(last["completed_at"])
    checks = []
    row = conn.execute("SELECT updated_at FROM projects WHERE id = ?", (project_id,)).fetchone()
    checks.append(row["updated_at"])
    row = conn.execute("SELECT updated_at FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    if row:
        checks.append(row["updated_at"])
    for table in ("materials", "github_repos"):
        row = conn.execute(f"SELECT MAX(updated_at) AS ts FROM {table} WHERE project_id = ?", (project_id,)).fetchone()
        checks.append(row["ts"])
    row = conn.execute(
        "SELECT MAX(updated_at) AS ts FROM weekly_updates WHERE project_id = ? AND week_key = ?",
        (project_id, week_key),
    ).fetchone()
    checks.append(row["ts"])
    return any(parse_iso(ts) and parse_iso(ts) > last_at for ts in checks if ts)


def generate_report(conn, project_id, trigger_type="manual", force=False, timeout=300, job_id=None):
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    week_key = current_week_key(project["timezone"])
    if trigger_type == "scheduled" and not force and not changed_since_last_success(conn, project_id, week_key):
        if job_id is not None:
            # the queued row was created before the change check could run;
            # retire it instead of leaving a ghost job in the queue
            conn.execute(
                "UPDATE generation_jobs SET status = 'skipped', failure_reason = ?, completed_at = ? WHERE id = ?",
                ("scheduled trigger fired but no input changed since last successful report", iso_now(), job_id),
            )
            conn.commit()
        return None
    context, snapshot_hash = assemble_context(conn, project_id, week_key)
    supplement = context.get("weekly_update")
    supplement_json = json.dumps(supplement, ensure_ascii=False) if supplement else ""
    now = iso_now()
    if job_id is None:
        cur = conn.execute(
            """
            INSERT INTO generation_jobs
            (project_id, week_key, trigger_type, provider, status, input_snapshot_hash, input_summary, started_at)
            VALUES (?, ?, ?, ?, 'running', ?, ?, ?)
            """,
            (project_id, week_key, trigger_type, project["report_provider"], snapshot_hash, input_summary(context), now),
        )
        job_id = cur.lastrowid
    else:
        conn.execute(
            "UPDATE generation_jobs SET status = 'running', input_snapshot_hash = ?, input_summary = ?, started_at = ? WHERE id = ?",
            (snapshot_hash, input_summary(context), now, job_id),
        )
    conn.commit()
    try:
        output_md = invoke_provider(project["report_provider"], context, timeout)
        if not output_md.strip():
            raise RuntimeError("expected Markdown output file was missing or empty")
        completed = iso_now()
        conn.execute(
            "UPDATE generation_jobs SET status = 'success', output_md = ?, completed_at = ? WHERE id = ?",
            (output_md, completed, job_id),
        )
        existing = conn.execute(
            "SELECT id FROM weekly_reports WHERE project_id = ? AND week_key = ?", (project_id, week_key)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE weekly_reports SET content_md = ?, supplement_json = ?, latest_job_id = ?, updated_at = ? WHERE id = ?",
                (output_md, supplement_json, job_id, completed, existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO weekly_reports (project_id, week_key, content_md, supplement_json, latest_job_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, week_key, output_md, supplement_json, job_id, completed, completed),
            )
        conn.commit()
        return job_id
    except Exception as exc:
        completed = iso_now()
        conn.execute(
            "UPDATE generation_jobs SET status = 'failed', failure_reason = ?, completed_at = ? WHERE id = ?",
            (str(exc), completed, job_id),
        )
        conn.commit()
        return job_id


def run_report_job(db_path, job_id, project_id, trigger_type, force=False, timeout=300):
    """Task-queue worker for a previously queued generation job. Opens its own
    database connection and refreshes deterministic risks once the report
    lands, mirroring what the old synchronous endpoint did."""
    with connect(db_path) as conn:
        generate_report(conn, project_id, trigger_type, force=force, timeout=timeout, job_id=job_id)
        evaluate_risks(conn, project_id)
        conn.commit()


def fail_stale_generation_jobs(db_path):
    """Jobs left queued or running by a previous process can never finish;
    mark them failed at startup so they stop consuming queue capacity."""
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE generation_jobs SET status = 'failed', failure_reason = 'interrupted by service restart', completed_at = ? WHERE status IN ('queued', 'running')",
            (iso_now(),),
        )
        conn.commit()


def invoke_provider(provider, context, timeout=300):
    """Report generation now always runs through the in-process internal
    agent; REPORTS_FAKE_PROVIDER keeps tests and dry runs offline."""
    if fake_provider_enabled():
        return fake_report(context)
    from .internal_agent import generate_internal_report

    return generate_internal_report(context, timeout=timeout)


def fake_provider_enabled():
    value = os.environ.get("REPORTS_FAKE_PROVIDER", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_internal_evidence_prompt(context):
    evidence = compact_evidence(context)
    return (
        f"{context['system_prompt']}\n\n"
        "You are generating a weekly project report. Return Markdown only. Do not describe your process.\n\n"
        "This report is generated in-process without tool execution. "
        "The application has retrieved the following bounded evidence from the local workspace. "
        "Use only this evidence. Do not invent facts.\n\n"
        "Use project profile and plan to understand description, milestones, and deliverables. "
        "Evaluate this week's progress against the plan and the weekly supplement. "
        "Use repository notes to interpret what each repo means in this project. "
        "Use current-week manually entered or uploaded materials and current-week Git commits as primary evidence for this week's changes. "
        "For every connected repository, include a short per-repo section. "
        "If a repository has commits, cite representative commit messages and dates; if it has none, say so explicitly. "
        "If there are no new materials, say so explicitly. "
        "The risk section must include observed risks plus your forecast from the evidence.\n\n"
        "Required Markdown structure:\n\n"
        f"{context['report_template']}\n\n"
        "Evidence JSON:\n\n"
        f"```json\n{json.dumps(evidence, ensure_ascii=False, indent=2)}\n```"
    )


def compact_evidence(context):
    return {
        "project_profile": context.get("project_profile"),
        "week_key": context.get("week_key"),
        "project_week": context.get("project_week"),
        "plan": context.get("plan"),
        "weekly_update": context.get("weekly_update"),
        "new_materials_this_week": [
            {**item, "excerpt": (item.get("excerpt") or "")[:2500]}
            for item in context.get("new_materials_this_week", [])
        ],
        "github_activity": context.get("github_activity"),
        "git_commits_this_week": context.get("git_commits_this_week"),
        "historical_report_weeks": historical_report_weeks(context),
        "previous_current_week_report": compact_previous_report(context.get("previous_current_week_report")),
    }


def historical_report_weeks(context):
    previous = context.get("previous_current_week_report")
    return [context["week_key"]] if previous else []


def compact_previous_report(report):
    if not report:
        return None
    return {
        "available": True,
        "updated_at": report.get("updated_at"),
    }


FAKE_SUGGESTED_TEMPLATE = """# 周报（建议模板）

## 本周总结

## 已完成工作

## 进行中

## 阻塞与风险

## 风险预测

## 下周计划

## Git 活动摘要

## 资料来源与依据
"""


def collect_template_sources(conn, project_id):
    """Bounded, network-free snapshot of the data sources a report template
    can draw on: profile, plan, materials and repositories registrations,
    weekly-input presence, and past report weeks."""
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        raise LookupError("project not found")
    plan = conn.execute(
        "SELECT objectives, milestones_json, deliverables_json FROM project_plans WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    materials = conn.execute(
        """
        SELECT filename, summary FROM materials
        WHERE project_id = ? AND extraction_status != 'failed'
        ORDER BY id DESC LIMIT 20
        """,
        (project_id,),
    ).fetchall()
    material_count = conn.execute(
        "SELECT COUNT(*) AS n FROM materials WHERE project_id = ? AND extraction_status != 'failed'",
        (project_id,),
    ).fetchone()["n"]
    repos = conn.execute(
        "SELECT repo, git_mode, notes FROM github_repos WHERE project_id = ? AND enabled = 1 ORDER BY id",
        (project_id,),
    ).fetchall()
    week_key = current_week_key(project["timezone"])
    update = conn.execute(
        "SELECT id FROM weekly_updates WHERE project_id = ? AND week_key = ?", (project_id, week_key)
    ).fetchone()
    history = conn.execute(
        "SELECT week_key FROM weekly_reports WHERE project_id = ? ORDER BY week_key DESC LIMIT 5", (project_id,)
    ).fetchall()
    return {
        "project_profile": {
            "name": project["name"],
            "description": project["description"],
            "status": project["status"],
        },
        "plan": {
            "objectives": plan["objectives"] if plan else "",
            "milestones": json.loads(plan["milestones_json"]) if plan else [],
            "deliverables": json.loads(plan["deliverables_json"]) if plan else [],
        },
        "material_count": material_count,
        "materials": [{"filename": row["filename"], "summary": row["summary"]} for row in materials],
        "repositories": [{"repo": row["repo"], "git_mode": row["git_mode"], "notes": row["notes"]} for row in repos],
        "weekly_update_present": bool(update),
        "report_history_weeks": [row["week_key"] for row in history],
    }


def latest_report_markdown(conn, project_id):
    """Most recent generated report regardless of week; week_key values sort
    chronologically as YYYY-Www strings."""
    row = conn.execute(
        "SELECT content_md FROM weekly_reports WHERE project_id = ? ORDER BY week_key DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    return (row["content_md"] or "").strip() if row else ""


def build_template_suggestion_prompt(requirements, sources, last_report_md):
    return (
        "你是周报模板设计助手。请根据用户要求、项目可用的数据来源和最近一期周报，"
        "设计一份新的项目周报 Markdown 模板。\n"
        "要求：\n"
        "- 只输出模板本身的 Markdown，不要任何解释，不要代码块围栏。\n"
        "- 用标题和空小节表达结构，每个小节内可以用 <!-- ... --> 注释写明该节应包含的内容。\n"
        "- 结合可用数据来源设计章节：数据来源里有的内容才设计对应章节，没有的不要凭空增加。\n"
        "- 参考最近一期周报的整体结构与语言风格，但不要照抄其中的正文内容。\n"
        "- 用户要求与其他输入冲突时，以用户要求为准。\n\n"
        "用户要求（来自模板输入框当前内容）：\n"
        f"{requirements or '（未填写，请按数据来源自行设计）'}\n\n"
        "可用数据来源（JSON）：\n\n"
        f"```json\n{json.dumps(sources, ensure_ascii=False, indent=2)}\n```\n\n"
        "最近一期周报（结构与风格参考）：\n\n"
        f"{last_report_md or '（该项目还没有已生成的周报）'}"
    )


def strip_template_fences(raw):
    value = (raw or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:markdown|md)?\s*|\s*```$", "", value, flags=re.IGNORECASE)
    return value.strip()


def generate_report_template(conn, project_id, requirements, timeout=300, job_id=None):
    """Design a fresh report template with the internal agent and save it to
    the project automatically. Template design runs as a queued background
    task: with a job_id the generation_jobs row is driven through the
    queued/running/success|failed lifecycle and failures are recorded in
    failure_reason. Direct calls without a job_id skip the bookkeeping and
    raise ValidationError on failure. REPORTS_FAKE_PROVIDER keeps tests and
    dry runs offline."""
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        raise LookupError("project not found")
    requirements = (requirements or "").strip()[:8000]
    now = iso_now()
    if job_id is not None:
        conn.execute(
            "UPDATE generation_jobs SET status = 'running', input_summary = ?, started_at = ? WHERE id = ?",
            (f"template design; requirements {len(requirements)} chars", now, job_id),
        )
        conn.commit()

    def _fail(message):
        if job_id is None:
            raise ValidationError(message)
        conn.execute(
            "UPDATE generation_jobs SET status = 'failed', failure_reason = ?, completed_at = ? WHERE id = ?",
            (message[:2000], iso_now(), job_id),
        )
        conn.commit()
        return None

    sources = collect_template_sources(conn, project_id)
    last_report = latest_report_markdown(conn, project_id)[:6000]
    prompt = build_template_suggestion_prompt(requirements, sources, last_report)
    if fake_provider_enabled():
        template = FAKE_SUGGESTED_TEMPLATE.strip()
    else:
        from .internal_agent import internal_chat, resolve_llm_settings

        try:
            raw = internal_chat(prompt, resolve_llm_settings(conn), timeout=timeout, max_tokens=4096, temperature=0)
        except RuntimeError as exc:
            return _fail(f"模板生成失败：{exc}")
        template = strip_template_fences(raw)
    if not template:
        return _fail("模板生成结果为空，请重试")
    conn.execute(
        "UPDATE projects SET report_template = ?, updated_at = ? WHERE id = ?",
        (template, iso_now(), project_id),
    )
    if job_id is not None:
        conn.execute(
            "UPDATE generation_jobs SET status = 'success', output_md = ?, completed_at = ? WHERE id = ?",
            (template, iso_now(), job_id),
        )
    conn.commit()
    return template


def run_template_job(db_path, job_id, project_id, requirements, timeout=300):
    """Task-queue worker for a queued template design job. Opens its own
    database connection; the generated template is saved by
    generate_report_template itself."""
    with connect(db_path) as conn:
        generate_report_template(conn, project_id, requirements, timeout=timeout, job_id=job_id)
        conn.commit()


def fake_report(context):
    project = context["project"]
    return f"""# 周报 - {project['name']}

## 本周总结
基于 {context['week_key']} 的本地工作区上下文生成。

## 已完成工作
{(context.get('weekly_update') or {}).get('completed', '') or '暂无已完成工作记录。'}

## 进行中
{(context.get('weekly_update') or {}).get('in_progress', '') or '暂无进行中工作记录。'}

## 阻塞与风险
{(context.get('weekly_update') or {}).get('blockers', '') or '暂无阻塞记录。'}

## 风险预测
检查逾期里程碑、资料可用性、缺失的项目输入和过期的项目证据。

## 下周计划
{(context.get('weekly_update') or {}).get('next_steps', '') or '暂无下周计划记录。'}

## Git 活动摘要
本周 {len(context.get('git_commits_this_week', []))} 个仓库来源共 {sum(len(repo.get('commits', [])) for repo in context.get('git_commits_this_week', []))} 次提交。

## 资料来源与依据
本周新增资料 {len(context.get('new_materials_this_week', []))} 份。
"""
