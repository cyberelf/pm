import argparse
import json
import sys
from pathlib import Path

from .config import DB_PATH
from .db import connect
from .github import weekly_commits
from .markdown import render_markdown
from .reports import get_effective_template
from .timeutil import current_week_key, parse_iso, week_bounds, week_key_for


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="reports-agent-context",
        description="Read-only project context tool for report generation agents.",
    )
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite database path")
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--week-key", default="")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("overview")
    sub.add_parser("project")
    sub.add_parser("plan")
    sub.add_parser("weekly-update")
    sub.add_parser("materials")
    material = sub.add_parser("material")
    material.add_argument("--id", type=int, required=True)
    sub.add_parser("repos")
    commits = sub.add_parser("commits")
    commits.add_argument("--repo", default="")
    sub.add_parser("history")
    report = sub.add_parser("report")
    report.add_argument("--week-key", required=True)
    sub.add_parser("template")

    args = parser.parse_args(argv)
    with connect(args.db) as conn:
        payload = dispatch(conn, args)
    if args.format == "text":
        print_text(payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def dispatch(conn, args):
    project = require_project(conn, args.project_id)
    week_key = args.week_key or current_week_key(project["timezone"])
    if args.command == "overview":
        return overview(conn, project, week_key)
    if args.command == "project":
        return {"project": project_profile(project)}
    if args.command == "plan":
        return {"plan": plan(conn, project["id"])}
    if args.command == "weekly-update":
        return {"weekly_update": weekly_update(conn, project["id"], week_key), "week_key": week_key}
    if args.command == "materials":
        return {"week_key": week_key, "materials": materials(conn, project, week_key, include_excerpt=False)}
    if args.command == "material":
        return {"material": material(conn, project, args.id)}
    if args.command == "repos":
        return {"repos": repos(conn, project["id"])}
    if args.command == "commits":
        return {"week_key": week_key, "commits": commits(conn, project, week_key, args.repo)}
    if args.command == "history":
        return {"reports": report_history(conn, project["id"])}
    if args.command == "report":
        return {"report": report(conn, project["id"], args.week_key)}
    if args.command == "template":
        return {"report_template": get_effective_template(project)}
    raise SystemExit(f"unsupported command: {args.command}")


def require_project(conn, project_id):
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise SystemExit(f"project not found: {project_id}")
    return dict(row)


def overview(conn, project, week_key):
    material_rows = materials(conn, project, week_key, include_excerpt=False)
    repo_rows = repos(conn, project["id"])
    return {
        "project": project_profile(project),
        "week_key": week_key,
        "project_week": project_week(project, week_key),
        "plan_summary": plan_summary(plan(conn, project["id"])),
        "weekly_update_present": weekly_update(conn, project["id"], week_key) is not None,
        "current_week_material_count": len([m for m in material_rows if m["is_current_week"]]),
        "material_count": len(material_rows),
        "repo_count": len(repo_rows),
        "repos": [
            {
                "repo": row["repo"],
                "notes": row["notes"],
                "status": row["status"],
                "last_activity_at": row["last_activity_at"],
            }
            for row in repo_rows
        ],
        "historical_report_weeks": [item["week_key"] for item in report_history(conn, project["id"])],
        "available_commands": available_commands(project["id"], week_key),
    }


def project_profile(project):
    return {
        "id": project["id"],
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
    }


def project_week(project, week_key):
    start, end = week_bounds(project["timezone"])
    return {
        "week_key": week_key,
        "timezone": project["timezone"],
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
    }


def plan(conn, project_id):
    row = conn.execute("SELECT * FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    if not row:
        return {"objectives": "", "version": 1, "milestones": [], "deliverables": [], "updated_at": None}
    return {
        "objectives": row["objectives"],
        "version": row["version"],
        "milestones": json.loads(row["milestones_json"] or "[]"),
        "deliverables": json.loads(row["deliverables_json"] or "[]"),
        "updated_at": row["updated_at"],
    }


def plan_summary(plan_data):
    return {
        "has_objectives": bool(plan_data.get("objectives")),
        "milestones": len(plan_data.get("milestones") or []),
        "deliverables": len(plan_data.get("deliverables") or []),
        "version": plan_data.get("version"),
        "updated_at": plan_data.get("updated_at"),
    }


def weekly_update(conn, project_id, week_key):
    row = conn.execute(
        "SELECT completed, in_progress, blockers, risks, next_steps, created_at, updated_at FROM weekly_updates WHERE project_id = ? AND week_key = ?",
        (project_id, week_key),
    ).fetchone()
    return dict(row) if row else None


def materials(conn, project, week_key, include_excerpt=True):
    result = []
    for row in conn.execute(
        """
        SELECT id, filename, source_type, content_type, size_bytes, extraction_status,
               extraction_error, extracted_text, created_at, updated_at
        FROM materials WHERE project_id = ? ORDER BY id DESC
        """,
        (project["id"],),
    ):
        created = parse_iso(row["created_at"])
        item = {
            "id": row["id"],
            "filename": row["filename"],
            "source_type": row["source_type"],
            "content_type": row["content_type"],
            "size_bytes": row["size_bytes"],
            "extraction_status": row["extraction_status"],
            "extraction_error": row["extraction_error"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "is_current_week": bool(created and week_key_for(created, project["timezone"]) == week_key),
        }
        if include_excerpt:
            item["excerpt"] = (row["extracted_text"] or "")[:2000]
        result.append(item)
    return result


def material(conn, project, material_id):
    row = conn.execute(
        """
        SELECT id, filename, source_type, content_type, size_bytes, extraction_status,
               extraction_error, extracted_text, created_at, updated_at
        FROM materials WHERE project_id = ? AND id = ?
        """,
        (project["id"], material_id),
    ).fetchone()
    if not row:
        raise SystemExit(f"material not found: {material_id}")
    return dict(row)


def repos(conn, project_id):
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT id, repo, notes, status, status_message, last_checked_at,
                   last_activity_at, activity_summary, created_at, updated_at
            FROM github_repos WHERE project_id = ? ORDER BY id
            """,
            (project_id,),
        )
    ]


def commits(conn, project, week_key, repo_name=""):
    start, end = week_bounds(project["timezone"])
    result = []
    for row in repos(conn, project["id"]):
        if row["status"] != "connected":
            continue
        if repo_name and row["repo"] != repo_name:
            continue
        item = weekly_commits(row["repo"], start, end)
        item["notes"] = row["notes"]
        result.append(item)
    if repo_name and not result:
        raise SystemExit(f"connected repo not found for project week {week_key}: {repo_name}")
    return result


def report_history(conn, project_id):
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT id, week_key, latest_job_id, created_at, updated_at
            FROM weekly_reports WHERE project_id = ?
            ORDER BY week_key DESC, updated_at DESC
            """,
            (project_id,),
        )
    ]


def report(conn, project_id, week_key):
    row = conn.execute(
        """
        SELECT id, week_key, content_md, latest_job_id, created_at, updated_at
        FROM weekly_reports WHERE project_id = ? AND week_key = ?
        """,
        (project_id, week_key),
    ).fetchone()
    if not row:
        raise SystemExit(f"report not found for week: {week_key}")
    item = dict(row)
    item["content_html"] = render_markdown(item["content_md"])
    return item


def available_commands(project_id, week_key):
    script = Path(__file__).resolve().parents[1] / "scripts" / "report_context.py"
    base = f"python3 {script} --project-id {project_id} --week-key {week_key}"
    return [
        f"{base} overview",
        f"{base} project",
        f"{base} plan",
        f"{base} weekly-update",
        f"{base} materials",
        f"{base} material --id <material_id>",
        f"{base} repos",
        f"{base} commits",
        f"{base} commits --repo <owner/name>",
        f"{base} history",
        f"{base} report --week-key <YYYY-Www>",
        f"{base} template",
    ]


def print_text(payload):
    if isinstance(payload, dict):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(payload)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
