import hashlib
import json
import os

from .config import DEFAULT_REPORT_TEMPLATE, DEFAULT_SYSTEM_PROMPT
from .db import connect
from .git_sources import git_auth_for_user, weekly_commits
from .risks import evaluate_risks
from .timeutil import current_week_key, iso_now, parse_iso, week_bounds, week_key_for


def get_effective_template(project):
    return project["report_template"] or DEFAULT_REPORT_TEMPLATE


def get_effective_prompt(project):
    return project["system_prompt"] or DEFAULT_SYSTEM_PROMPT


def assemble_context(conn, project_id, week_key=None):
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    week_key = week_key or current_week_key(project["timezone"])
    week_start, week_end = week_bounds(project["timezone"])
    plan = conn.execute("SELECT * FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    outcomes = conn.execute(
        "SELECT title, details, status, owner_label FROM weekly_outcomes WHERE project_id = ? AND week_key = ? ORDER BY id",
        (project_id, week_key),
    ).fetchall()
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
        SELECT repo, git_mode, gitlab_server, notes, tracked_branches_json, status, status_message,
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
            "background": project["manual_background"],
            "objectives": project["manual_objectives"],
            "constraints": project["manual_constraints"],
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
        "weekly_planned_outcomes": [dict(row) for row in outcomes],
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
    has_profile = any(profile.get(key) for key in ("description", "background", "objectives", "constraints"))
    has_plan = bool(plan.get("objectives") or plan.get("milestones") or plan.get("deliverables"))
    return (
        f"week={context['week_key']}; "
        f"profile={'yes' if has_profile else 'no'}; "
        f"plan={'yes' if has_plan else 'no'}; "
        f"new_materials={len(context.get('new_materials_this_week', []))}; "
        f"commits={commits}; "
        f"repos={len(context['github_activity'])}; "
        f"outcomes={len(context['weekly_planned_outcomes'])}"
    )


def repo_commit_context(repo_row, week_start, week_end, auth_info):
    branches = json.loads(repo_row["tracked_branches_json"] or '["main"]')
    result = weekly_commits(
        repo_row["repo"],
        week_start,
        week_end,
        branches,
        git_mode=repo_row["git_mode"],
        gitlab_server=repo_row["gitlab_server"],
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
    row = conn.execute(
        "SELECT MAX(updated_at) AS ts FROM weekly_outcomes WHERE project_id = ? AND week_key = ?",
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
                "UPDATE weekly_reports SET content_md = ?, latest_job_id = ?, updated_at = ? WHERE id = ?",
                (output_md, job_id, completed, existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO weekly_reports (project_id, week_key, content_md, latest_job_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (project_id, week_key, output_md, job_id, completed, completed),
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
        "Use project profile and plan to understand description, background, objectives, constraints, milestones, and deliverables. "
        "Evaluate this week's progress against plan and weekly planned outcomes. "
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
        "weekly_planned_outcomes": context.get("weekly_planned_outcomes"),
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


def fake_report(context):
    project = context["project"]
    return f"""# Weekly Report - {project['name']}

## This Week's Summary
Generated for {context['week_key']} from local workspace context.

## Completed Work
{(context.get('weekly_update') or {}).get('completed', '') or 'No completed work recorded.'}

## In Progress
{(context.get('weekly_update') or {}).get('in_progress', '') or 'No in-progress work recorded.'}

## Blockers and Risks
{(context.get('weekly_update') or {}).get('blockers', '') or 'No blockers recorded.'}

## Risk Forecast
Review overdue milestones, blocked planned outcomes, source availability, missing project inputs, and stale project evidence.

## Next Week Plan
{(context.get('weekly_update') or {}).get('next_steps', '') or 'No next steps recorded.'}

## GitHub Activity Summary
{sum(len(repo.get('commits', [])) for repo in context.get('git_commits_this_week', []))} commit(s) this week across {len(context['github_activity'])} repository source(s).

## Source/Input References
{len(context.get('new_materials_this_week', []))} new material file(s) this week, {len(context['weekly_planned_outcomes'])} planned outcome(s).
"""
