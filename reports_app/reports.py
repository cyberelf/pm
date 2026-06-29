import hashlib
import json
import os
import shlex
import subprocess
import tempfile
import time
from pathlib import Path

from .config import DEFAULT_REPORT_TEMPLATE, DEFAULT_SYSTEM_PROMPT, ROOT_DIR
from .github import weekly_commits
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
        SELECT filename, source_type, extraction_status, extracted_text,
               extraction_error, created_at, updated_at
        FROM materials WHERE project_id = ? ORDER BY id DESC
        """,
        (project_id,),
    ).fetchall()
    repos = conn.execute(
        "SELECT repo, notes, status, status_message, last_checked_at, last_activity_at, activity_summary FROM github_repos WHERE project_id = ? ORDER BY id",
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
                "excerpt": (row["extracted_text"] or "")[:8000],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in materials
            if parse_iso(row["created_at"]) and week_key_for(parse_iso(row["created_at"]), project["timezone"]) == week_key
        ],
        "github_activity": [dict(row) for row in repos],
        "git_commits_this_week": [
            repo_commit_context(row, week_start, week_end)
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


def repo_commit_context(repo_row, week_start, week_end):
    result = weekly_commits(repo_row["repo"], week_start, week_end)
    result["notes"] = repo_row["notes"]
    return result


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


def generate_report(conn, project_id, trigger_type="manual", force=False, timeout=300):
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    week_key = current_week_key(project["timezone"])
    if trigger_type == "scheduled" and not force and not changed_since_last_success(conn, project_id, week_key):
        return None
    context, snapshot_hash = assemble_context(conn, project_id, week_key)
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO generation_jobs
        (project_id, week_key, trigger_type, provider, status, input_snapshot_hash, input_summary, started_at)
        VALUES (?, ?, ?, ?, 'running', ?, ?, ?)
        """,
        (project_id, week_key, trigger_type, project["report_provider"], snapshot_hash, input_summary(context), now),
    )
    job_id = cur.lastrowid
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


def invoke_provider(provider, context, timeout=300):
    with tempfile.TemporaryDirectory(prefix="weekly-report-") as tmp:
        tmp_path = Path(tmp)
        output_path = (tmp_path / "report.md").resolve()
        if fake_provider_enabled():
            output_path.write_text(fake_report(context), encoding="utf-8")
        else:
            if provider == "claude" and not os.environ.get("REPORTS_CLAUDE_CMD"):
                prompt = build_claude_evidence_prompt(context)
                command = provider_command(provider, "", tmp_path, output_path)
                result = run_provider_command(command, tmp, timeout, input_text=prompt)
                output_path.write_text(result.stdout, encoding="utf-8")
            else:
                prompt = build_tool_prompt(context, provider)
                command = provider_command(provider, prompt, tmp_path, output_path)
                run_provider_command(command, tmp, timeout)
        if not output_path.exists() or not output_path.read_text(encoding="utf-8").strip():
            raise RuntimeError("expected Markdown output file was missing or empty")
        return output_path.read_text(encoding="utf-8")


def provider_command(provider, prompt, cwd, output_path):
    if provider == "codex":
        custom = os.environ.get("REPORTS_CODEX_CMD")
        if custom:
            return shlex.split(custom) + [prompt]
        return ["codex", "exec", "--skip-git-repo-check", "-C", os.fspath(cwd), "-o", os.fspath(output_path), prompt]
    if provider == "claude":
        custom = os.environ.get("REPORTS_CLAUDE_CMD")
        if custom:
            return shlex.split(custom) + [prompt]
        command = ["claude", "--print", "--permission-mode", "dontAsk", "--no-session-persistence"]
        if prompt:
            command.append(prompt)
        return command
    raise ValueError("unsupported report provider")


def run_provider_command(command, cwd, timeout, attempts=2, input_text=None):
    last_error = None
    per_attempt_timeout = min(timeout, 120)
    for attempt in range(1, attempts + 1):
        try:
            return subprocess.run(
                command,
                cwd=cwd,
                input=input_text,
                text=True,
                capture_output=True,
                timeout=per_attempt_timeout,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            last_error = provider_error(command, exc)
            if attempt < attempts and transient_provider_error(last_error):
                time.sleep(5 * attempt)
                continue
            raise RuntimeError(last_error) from exc
        except subprocess.TimeoutExpired as exc:
            last_error = provider_timeout_error(command, per_attempt_timeout, exc)
            if attempt < attempts:
                time.sleep(5 * attempt)
                continue
            raise RuntimeError(last_error) from exc
    raise RuntimeError(last_error or "provider command failed")


def provider_error(command, exc):
    details = [
        f"Command exited with status {exc.returncode}",
        f"command={shlex.join(command)}",
    ]
    if exc.stdout:
        details.append(f"stdout:\n{exc.stdout[-4000:]}")
    if exc.stderr:
        details.append(f"stderr:\n{exc.stderr[-4000:]}")
    return "\n".join(details)


def provider_timeout_error(command, timeout, exc):
    details = [
        f"Command timed out after {timeout} seconds",
        f"command={shlex.join(command)}",
    ]
    if exc.stdout:
        details.append(f"stdout:\n{str(exc.stdout)[-4000:]}")
    if exc.stderr:
        details.append(f"stderr:\n{str(exc.stderr)[-4000:]}")
    return "\n".join(details)


def transient_provider_error(message):
    lowered = message.lower()
    return any(
        marker in lowered
        for marker in (
            "api error: 529",
            "overloaded",
            "temporarily unavailable",
            "try again",
            "rate limit",
            "访问量过大",
            "稍后再试",
        )
    )


def fake_provider_enabled():
    value = os.environ.get("REPORTS_FAKE_PROVIDER", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_tool_prompt(context, provider):
    tool = agent_tool_command(context)
    output_instruction = "Return Markdown only as your final response."
    if provider == "codex":
        output_instruction = "Return Markdown only as your final response; the runner will save that response as the report."
    return (
        f"{context['system_prompt']}\n\n"
        "You are generating a weekly project report. "
        f"{output_instruction} Do not describe your process.\n\n"
        "You MUST get all project/platform information through this read-only platform CLI. "
        "Do not read application files, uploaded files, SQLite databases, or GitHub directly. "
        "Do not run `gh`; GitHub activity and commits must come from the platform CLI.\n\n"
        f"Platform CLI base command:\n`{tool}`\n\n"
        "Start with:\n"
        f"`{tool} overview`\n\n"
        "Then call only the subcommands you need, for example:\n"
        f"- `{tool} project`\n"
        f"- `{tool} plan`\n"
        f"- `{tool} weekly-update`\n"
        f"- `{tool} materials`\n"
        f"- `{tool} material --id <material_id>`\n"
        f"- `{tool} repos`\n"
        f"- `{tool} commits`\n"
        f"- `{tool} commits --repo <owner/name>`\n"
        f"- `{tool} history`\n"
        f"- `{tool} report --week-key <YYYY-Www>`\n"
        f"- `{tool} template`\n\n"
        "Use project profile and plan to understand description, background, objectives, constraints, milestones, and deliverables. "
        "Evaluate this week's progress against plan and weekly planned outcomes. "
        "Use repository notes to interpret what each repo means in this project. "
        "Use current-week manually entered or uploaded materials and current-week Git commits as primary evidence for this week's changes. "
        "If you need full material content, fetch it with `material --id`; do not infer from filenames alone. "
        "For every connected repository, include a short per-repo section. "
        "If a repository has commits, cite representative commit messages and dates; if it has none, say so explicitly. "
        "If there are no new materials, say so explicitly. "
        "The risk section must include deterministic risks from the context plus your forecast from the evidence, "
        "and must mention any risk caused by missing or stale project profile, objectives, constraints, plan, or weekly outcomes.\n\n"
        "Required Markdown structure:\n\n"
        f"{context['report_template']}"
    )


def build_claude_evidence_prompt(context):
    evidence = compact_evidence(context)
    return (
        f"{context['system_prompt']}\n\n"
        "You are generating a weekly project report. Return Markdown only. Do not describe your process.\n\n"
        "Claude Code CLI tool execution is disabled for this provider path. "
        "The application has retrieved the following bounded evidence through its read-only platform context CLI. "
        "Use only this evidence. Do not read application files, uploaded files, SQLite databases, or GitHub directly. Do not run `gh`.\n\n"
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


def agent_tool_command(context):
    script = ROOT_DIR / "scripts" / "report_context.py"
    project_id = int(context["project"]["id"])
    week_key = context["week_key"]
    return f"python3 {shlex.quote(os.fspath(script))} --project-id {project_id} --week-key {shlex.quote(week_key)}"


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
Review overdue milestones, blocked planned outcomes, source availability, and generation failures.

## Next Week Plan
{(context.get('weekly_update') or {}).get('next_steps', '') or 'No next steps recorded.'}

## GitHub Activity Summary
{sum(len(repo.get('commits', [])) for repo in context.get('git_commits_this_week', []))} commit(s) this week across {len(context['github_activity'])} repository source(s).

## Source/Input References
{len(context.get('new_materials_this_week', []))} new material file(s) this week, {len(context['weekly_planned_outcomes'])} planned outcome(s).
"""
