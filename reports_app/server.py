import base64
import json
import os
import threading
import time
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .config import DB_PATH, STATIC_DIR, WORKSPACE_USER
from .db import connect, create_project, init_db, row_to_dict
from .github import check_repo, refresh_repo
from .markdown import render_markdown
from .materials import material_is_editable, store_manual_material, store_material, update_manual_material
from .reports import changed_since_last_success, generate_report
from .risks import evaluate_risks, progress_status
from .timeutil import current_week_key, iso_now
from .timeutil import get_zone, parse_iso
from .validation import (
    ValidationError,
    require_project_name,
    validate_provider,
    validate_repo,
    validate_schedule_item,
    validate_timezone,
)


def run(host="127.0.0.1", port=8000, db_path=DB_PATH):
    init_db(db_path)
    stop = threading.Event()
    scheduler = threading.Thread(target=scheduler_loop, args=(stop, db_path), daemon=True)
    scheduler.start()
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.db_path = db_path
    try:
        print(f"Weekly reports workspace running at http://{host}:{port}")
        httpd.serve_forever()
    finally:
        stop.set()


def scheduler_loop(stop, db_path):
    while not stop.wait(60):
        try:
            with connect(db_path) as conn:
                for row in conn.execute("SELECT id FROM projects WHERE status != 'archived'"):
                    evaluate_schedules(conn, row["id"])
                conn.commit()
        except Exception:
            pass


def evaluate_schedules(conn, project_id):
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    week_key = current_week_key(project["timezone"])
    due = False
    for schedule in conn.execute("SELECT * FROM update_schedules WHERE project_id = ?", (project_id,)):
        if schedule_due(schedule):
            due = True
            conn.execute("UPDATE update_schedules SET last_checked_at = ? WHERE id = ?", (iso_now(), schedule["id"]))
    if due and changed_since_last_success(conn, project_id, week_key):
        generate_report(conn, project_id, "scheduled", force=False)
    evaluate_risks(conn, project_id)


def schedule_due(schedule, now=None):
    zone = get_zone(schedule["timezone"])
    local_now = (now or datetime.now(zone)).astimezone(zone)
    if local_now.isoweekday() != int(schedule["weekday"]):
        return False
    hour, minute = [int(part) for part in schedule["local_time"].split(":", 1)]
    due_at = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if local_now < due_at:
        return False
    last = parse_iso(schedule["last_checked_at"])
    if not last:
        return True
    return last.astimezone(zone) < due_at


class Handler(BaseHTTPRequestHandler):
    server_version = "WeeklyReports/0.1"
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            if parsed.path.startswith("/api/"):
                self.handle_api("GET", parsed.path, parse_qs(parsed.query))
            else:
                self.serve_static(parsed.path)
        except Exception as exc:
            self.error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_POST(self):
        self.handle_write("POST")

    def do_PUT(self):
        self.handle_write("PUT")

    def handle_write(self, method):
        try:
            parsed = urlparse(self.path)
            self.handle_api(method, parsed.path, parse_qs(parsed.query))
        except ValidationError as exc:
            self.error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:
            self.error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def body_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def handle_api(self, method, path, query):
        parts = [p for p in path.split("/") if p]
        with connect(self.server.db_path) as conn:
            if path == "/api/state" and method == "GET":
                projects = [dict(row) for row in conn.execute("SELECT * FROM projects ORDER BY updated_at DESC")]
                self.json({"projects": projects, "workspace_user": WORKSPACE_USER})
                return
            if path == "/api/projects" and method == "POST":
                payload = self.body_json()
                require_project_name(payload)
                validate_timezone(payload.get("timezone") or "Asia/Shanghai")
                validate_provider(payload.get("report_provider") or "codex")
                project_id = create_project(conn, payload)
                conn.commit()
                self.json({"id": project_id}, HTTPStatus.CREATED)
                return
            if len(parts) >= 3 and parts[0] == "api" and parts[1] == "projects":
                project_id = int(parts[2])
                if len(parts) == 4 and parts[3] == "workspace" and method == "GET":
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 4 and parts[3] == "settings" and method == "PUT":
                    update_settings(conn, project_id, self.body_json())
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 4 and parts[3] == "materials" and method == "POST":
                    payload = self.body_json()
                    if payload.get("source_type") == "manual":
                        material_id = store_manual_material(conn, project_id, payload)
                    else:
                        material_id = store_material(conn, project_id, payload)
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json({"id": material_id}, HTTPStatus.CREATED)
                    return
                if len(parts) == 5 and parts[3] == "materials" and method == "PUT":
                    update_manual_material(conn, project_id, int(parts[4]), self.body_json())
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 4 and parts[3] == "repos" and method == "POST":
                    repo_id = add_repo(conn, project_id, self.body_json())
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json({"id": repo_id}, HTTPStatus.CREATED)
                    return
                if len(parts) == 5 and parts[3] == "repos" and method == "PUT":
                    update_repo_notes(conn, project_id, int(parts[4]), self.body_json())
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 6 and parts[3] == "repos" and parts[5] == "refresh" and method == "POST":
                    refresh_repo(conn, int(parts[4]))
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 4 and parts[3] == "plan" and method == "PUT":
                    save_plan(conn, project_id, self.body_json())
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 4 and parts[3] == "weekly-outcomes" and method == "PUT":
                    save_outcomes(conn, project_id, self.body_json())
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 4 and parts[3] == "weekly-update" and method == "PUT":
                    save_weekly_update(conn, project_id, self.body_json())
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 4 and parts[3] == "generate" and method == "POST":
                    generate_report(conn, project_id, "manual", force=True)
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 4 and parts[3] == "schedule-check" and method == "POST":
                    evaluate_schedules(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
            if len(parts) == 4 and parts[:2] == ["api", "risks"] and method == "POST":
                status = parts[3]
                if status not in {"dismissed", "resolved"}:
                    raise ValidationError("invalid risk status")
                conn.execute("UPDATE risk_warnings SET status = ?, updated_at = ? WHERE id = ?", (status, iso_now(), int(parts[2])))
                conn.commit()
                self.json({"ok": True})
                return
        self.error(HTTPStatus.NOT_FOUND, "not found")

    def serve_static(self, path):
        if path in {"", "/"}:
            file_path = STATIC_DIR / "index.html"
        else:
            file_path = STATIC_DIR / path.lstrip("/")
        if not file_path.exists() or not file_path.is_file():
            self.error(HTTPStatus.NOT_FOUND, "not found")
            return
        content_type = "text/html"
        if file_path.suffix == ".js":
            content_type = "application/javascript"
        elif file_path.suffix == ".css":
            content_type = "text/css"
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "keep-alive")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def json(self, payload, status=HTTPStatus.OK):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "keep-alive")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def error(self, status, message):
        self.json({"error": message}, status)

    def log_message(self, fmt, *args):
        return


def workspace(conn, project_id):
    evaluate_risks(conn, project_id)
    project = dict(conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())
    week_key = current_week_key(project["timezone"])
    report = conn.execute("SELECT * FROM weekly_reports WHERE project_id = ? AND week_key = ?", (project_id, week_key)).fetchone()
    report_dict = dict(report) if report else None
    if report_dict:
        report_dict["content_html"] = render_markdown(report_dict["content_md"])
    report_history = []
    for row in conn.execute(
        """
        SELECT id, week_key, content_md, latest_job_id, created_at, updated_at
        FROM weekly_reports
        WHERE project_id = ?
        ORDER BY week_key DESC, updated_at DESC
        """,
        (project_id,),
    ):
        item = dict(row)
        item["is_current_week"] = item["week_key"] == week_key
        item["content_html"] = render_markdown(item["content_md"])
        report_history.append(item)
    return {
        "project": project,
        "week_key": week_key,
        "schedules": [dict(row) for row in conn.execute("SELECT * FROM update_schedules WHERE project_id = ? ORDER BY weekday, local_time", (project_id,))],
        "materials": material_rows(conn, project_id, project["timezone"]),
        "repos": [dict(row) for row in conn.execute("SELECT * FROM github_repos WHERE project_id = ? ORDER BY id", (project_id,))],
        "plan": plan_dict(conn, project_id),
        "outcomes": [dict(row) for row in conn.execute("SELECT * FROM weekly_outcomes WHERE project_id = ? AND week_key = ? ORDER BY id", (project_id, week_key))],
        "weekly_update": row_to_dict(conn.execute("SELECT * FROM weekly_updates WHERE project_id = ? AND week_key = ?", (project_id, week_key)).fetchone()),
        "report": report_dict,
        "report_history": report_history,
        "jobs": [dict(row) for row in conn.execute("SELECT id, week_key, trigger_type, provider, status, input_snapshot_hash, input_summary, failure_reason, started_at, completed_at FROM generation_jobs WHERE project_id = ? AND week_key = ? ORDER BY id DESC", (project_id, week_key))],
        "risks": [dict(row) for row in conn.execute("SELECT * FROM risk_warnings WHERE project_id = ? AND week_key = ? AND rule IN ('missing_update', 'overdue_milestone', 'blocked_outcome') ORDER BY status, severity DESC, updated_at DESC", (project_id, week_key))],
        "source_diagnostics": source_diagnostics(conn, project_id, week_key),
        "progress_status": progress_status(conn, project_id),
    }


def source_diagnostics(conn, project_id, week_key):
    items = []
    latest_job = conn.execute(
        """
        SELECT id, provider, status, failure_reason, started_at, completed_at
        FROM generation_jobs
        WHERE project_id = ? AND week_key = ?
        ORDER BY started_at DESC, id DESC LIMIT 1
        """,
        (project_id, week_key),
    ).fetchone()
    if latest_job and latest_job["status"] == "failed":
        items.append(
            {
                "kind": "generation",
                "severity": "error",
                "title": "Report generation failed",
                "details": latest_job["failure_reason"],
                "source_ref": str(latest_job["id"]),
                "updated_at": latest_job["completed_at"] or latest_job["started_at"],
            }
        )
    for row in conn.execute(
        """
        SELECT id, repo, status, status_message, updated_at
        FROM github_repos
        WHERE project_id = ? AND status IN ('disconnected', 'unauthenticated', 'inaccessible')
        ORDER BY updated_at DESC, id DESC
        """,
        (project_id,),
    ):
        items.append(
            {
                "kind": "github",
                "severity": "warning",
                "title": "GitHub source unavailable",
                "details": f"{row['repo']}: {row['status_message']}",
                "source_ref": str(row["id"]),
                "updated_at": row["updated_at"],
            }
        )
    for row in conn.execute(
        """
        SELECT id, filename, extraction_error, updated_at
        FROM materials
        WHERE project_id = ? AND extraction_status = 'failed'
        ORDER BY updated_at DESC, id DESC
        """,
        (project_id,),
    ):
        items.append(
            {
                "kind": "material",
                "severity": "warning",
                "title": "Material text extraction failed",
                "details": f"{row['filename']}: {row['extraction_error']}",
                "source_ref": str(row["id"]),
                "updated_at": row["updated_at"],
            }
        )
    return items


def plan_dict(conn, project_id):
    row = conn.execute("SELECT * FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    if not row:
        return {"objectives": "", "milestones": [], "deliverables": [], "version": 1}
    return {
        "objectives": row["objectives"],
        "milestones": json.loads(row["milestones_json"] or "[]"),
        "deliverables": json.loads(row["deliverables_json"] or "[]"),
        "version": row["version"],
        "updated_at": row["updated_at"],
    }


def material_rows(conn, project_id, timezone):
    rows = []
    for row in conn.execute(
        """
        SELECT id, filename, source_type, content_type, size_bytes, extraction_status,
               extraction_error, extracted_text, created_at, updated_at
        FROM materials WHERE project_id = ? ORDER BY id DESC
        """,
        (project_id,),
    ):
        item = dict(row)
        item["editable"] = material_is_editable(row, timezone)
        if item["source_type"] == "manual":
            item["content"] = item.pop("extracted_text") or ""
        else:
            item.pop("extracted_text", None)
        rows.append(item)
    return rows


def update_settings(conn, project_id, payload):
    validate_timezone(payload.get("timezone") or "Asia/Shanghai")
    validate_provider(payload.get("report_provider") or "codex")
    for item in payload.get("schedules") or []:
        validate_schedule_item(item)
    now = iso_now()
    conn.execute(
        """
        UPDATE projects
        SET name = ?, description = ?, start_date = ?, end_date = ?, status = ?, timezone = ?,
            report_provider = ?, system_prompt = ?, report_template = ?, manual_background = ?,
            manual_objectives = ?, manual_constraints = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            payload["name"].strip(),
            payload.get("description", ""),
            payload["start_date"],
            payload.get("end_date") or None,
            payload.get("status") or "active",
            payload.get("timezone") or "Asia/Shanghai",
            payload.get("report_provider") or "codex",
            payload.get("system_prompt") or "",
            payload.get("report_template") or "",
            payload.get("manual_background") or "",
            payload.get("manual_objectives") or "",
            payload.get("manual_constraints") or "",
            now,
            project_id,
        ),
    )
    conn.execute("DELETE FROM update_schedules WHERE project_id = ?", (project_id,))
    for item in payload.get("schedules") or []:
        conn.execute(
            "INSERT INTO update_schedules (project_id, weekday, local_time, timezone, created_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, int(item["weekday"]), item["local_time"], item.get("timezone") or payload.get("timezone"), now),
        )


def add_repo(conn, project_id, payload):
    repo = validate_repo(payload.get("repo"))
    notes = payload.get("notes") or ""
    existing = conn.execute(
        "SELECT id FROM github_repos WHERE project_id = ? AND repo = ?",
        (project_id, repo),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE github_repos SET notes = ?, updated_at = ? WHERE id = ?",
            (notes, iso_now(), existing["id"]),
        )
        return existing["id"]
    result = check_repo(repo)
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO github_repos
        (project_id, repo, notes, status, status_message, last_checked_at, last_activity_at, activity_summary, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            repo,
            notes,
            result["status"],
            result["status_message"],
            now,
            result["last_activity_at"],
            result["activity_summary"],
            now,
            now,
        ),
    )
    return cur.lastrowid


def update_repo_notes(conn, project_id, repo_id, payload):
    now = iso_now()
    conn.execute(
        "UPDATE github_repos SET notes = ?, updated_at = ? WHERE id = ? AND project_id = ?",
        (payload.get("notes") or "", now, repo_id, project_id),
    )


def save_plan(conn, project_id, payload):
    now = iso_now()
    current = conn.execute("SELECT version FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    version = (current["version"] if current else 0) + 1
    milestones = payload.get("milestones") or []
    deliverables = payload.get("deliverables") or []
    snapshot = {"objectives": payload.get("objectives") or "", "milestones": milestones, "deliverables": deliverables}
    conn.execute(
        """
        INSERT INTO project_plans (project_id, objectives, milestones_json, deliverables_json, version, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET objectives = excluded.objectives,
            milestones_json = excluded.milestones_json, deliverables_json = excluded.deliverables_json,
            version = excluded.version, updated_at = excluded.updated_at
        """,
        (project_id, snapshot["objectives"], json.dumps(milestones), json.dumps(deliverables), version, now),
    )
    conn.execute(
        "INSERT INTO plan_versions (project_id, version, snapshot_json, created_at) VALUES (?, ?, ?, ?)",
        (project_id, version, json.dumps(snapshot), now),
    )


def save_outcomes(conn, project_id, payload):
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    week_key = payload.get("week_key") or current_week_key(project["timezone"])
    now = iso_now()
    conn.execute("DELETE FROM weekly_outcomes WHERE project_id = ? AND week_key = ?", (project_id, week_key))
    for item in payload.get("outcomes") or []:
        if not (item.get("title") or "").strip():
            continue
        conn.execute(
            """
            INSERT INTO weekly_outcomes (project_id, week_key, title, details, status, owner_label, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                week_key,
                item["title"].strip(),
                item.get("details") or "",
                item.get("status") or "planned",
                item.get("owner_label") or "",
                now,
                now,
            ),
        )


def save_weekly_update(conn, project_id, payload):
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    week_key = payload.get("week_key") or current_week_key(project["timezone"])
    now = iso_now()
    conn.execute(
        """
        INSERT INTO weekly_updates
        (project_id, week_key, completed, in_progress, blockers, risks, next_steps, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id, week_key) DO UPDATE SET completed = excluded.completed,
            in_progress = excluded.in_progress, blockers = excluded.blockers, risks = excluded.risks,
            next_steps = excluded.next_steps, updated_at = excluded.updated_at
        """,
        (
            project_id,
            week_key,
            payload.get("completed") or "",
            payload.get("in_progress") or "",
            payload.get("blockers") or "",
            payload.get("risks") or "",
            payload.get("next_steps") or "",
            now,
            now,
        ),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    run(port=port)
