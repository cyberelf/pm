import base64
import gzip
import json
import os
import ssl
import sys
import threading
import time
import traceback
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import auth
from .config import (
    ASR_ENDPOINT_SETTING,
    ASR_LANGUAGE_SETTING,
    ASR_MODEL_SETTING,
    DB_PATH,
    DEFAULT_ASR_ENDPOINT,
    DEFAULT_ASR_LANGUAGE,
    DEFAULT_ASR_MODEL,
    DEFAULT_LLM_BASE_URLS,
    DEFAULT_LLM_PROVIDER,
    LLM_API_KEY_ENV_VARS,
    LLM_API_KEY_SETTING,
    LLM_BASE_URL_SETTING,
    LLM_MODEL_SETTING,
    LLM_PROVIDER_SETTING,
    QUEUE_CAPACITY_SETTING,
    QUEUE_PARALLELISM_SETTING,
    REPORT_PROVIDER,
    STATIC_DIR,
    UI_MODE_SETTING,
    UI_THEME_SETTING,
    UPLOAD_DIR,
)
from .db import (
    connect,
    create_project,
    get_effective_user_setting,
    get_setting,
    get_user_setting,
    init_db,
    row_to_dict,
    set_setting,
    set_user_setting,
)
from .config import (
    GITHUB_ENABLED_SETTING,
    GITHUB_TOKEN_SETTING,
    GITHUB_TOKENS_SETTING,
    GITLAB_ENABLED_SETTING,
    GITLAB_TOKEN_SETTING,
    GITLAB_URL_SETTING,
)
from .git_sources import check_repo, git_auth_for_user, list_branches, load_github_tokens, refresh_repo
from .markdown import render_markdown
from .materials import (
    delete_material,
    material_is_editable,
    material_is_unlocked,
    remove_material_file,
    store_manual_material,
    store_material,
    summarize_uploaded_materials,
    update_manual_material,
    update_material_summary,
)
from .pdf_export import pdf_filename, report_pdf_bytes
from .reports import changed_since_last_success, fail_stale_generation_jobs, generate_report
from .risks import evaluate_risks, progress_status
from .task_queue import (
    QueueFullError,
    enqueue_report_generation,
    enqueue_voice_job,
    queue_capacity,
    queue_parallelism,
    task_queue_state,
)
from .timeutil import current_week_key, iso_now
from .timeutil import get_zone, parse_iso
from .todos import close_todo, create_todo, delete_todo, todo_rows, update_todo
from .asr import normalize_asr_endpoint
from .voice_todos import (
    cancel_voice_job,
    fail_stale_voice_jobs,
    get_active_voice_job,
    get_voice_job,
)
from .validation import (
    ValidationError,
    gitlab_server_from_url,
    require_project_name,
    validate_llm_base_url,
    validate_llm_provider,
    validate_provider,
    validate_branches,
    validate_git_mode,
    validate_gitlab_server,
    validate_repo,
    validate_schedule_item,
    validate_project_status,
    validate_queue_capacity,
    validate_queue_parallelism,
    validate_timezone,
    validate_ui_mode,
    validate_ui_theme,
)


PUBLIC_API_ROUTES = {
    ("GET", "/api/auth/state"),
    ("POST", "/api/auth/login"),
}

ADMIN_ONLY_SETTING_KEYS = {
    "asr_endpoint",
    "asr_model",
    "asr_language",
    "llm_provider",
    "llm_base_url",
    "llm_model",
    "llm_api_key",
    "queue_capacity",
    "queue_parallelism",
    "github_enabled",
    "gitlab_enabled",
}


def update_user(conn, actor, target_id, payload):
    target = conn.execute("SELECT * FROM users WHERE id = ?", (target_id,)).fetchone()
    if not target:
        raise ValidationError("user not found")
    now = iso_now()
    updates = {}
    if "password" in payload and payload.get("password"):
        auth.validate_new_password(payload.get("password"))
        updates["password_hash"] = auth.hash_password(payload.get("password"))
    if "is_admin" in payload:
        updates["is_admin"] = 1 if payload.get("is_admin") else 0
    if "enabled" in payload:
        updates["enabled"] = 1 if payload.get("enabled") else 0
    if not updates:
        return auth.user_public(target)
    if target_id == actor["id"] and (updates.get("is_admin") == 0 or updates.get("enabled") == 0):
        raise ValidationError("you cannot demote or disable your own account")
    becomes_weaker = updates.get("is_admin") == 0 or updates.get("enabled") == 0
    if target["is_admin"] and target["enabled"] and becomes_weaker:
        remaining = conn.execute(
            "SELECT COUNT(*) AS n FROM users WHERE is_admin = 1 AND enabled = 1 AND id != ?",
            (target_id,),
        ).fetchone()["n"]
        if not remaining:
            raise ValidationError("the last enabled administrator cannot be demoted or disabled")
    assignments = ", ".join(f"{name} = ?" for name in updates)
    conn.execute(
        f"UPDATE users SET {assignments}, updated_at = ? WHERE id = ?",
        (*updates.values(), now, target_id),
    )
    if updates.get("enabled") == 0:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (target_id,))
    return auth.user_public(conn.execute("SELECT * FROM users WHERE id = ?", (target_id,)).fetchone())


def delete_user(conn, actor, target_id):
    target = conn.execute("SELECT * FROM users WHERE id = ?", (target_id,)).fetchone()
    if not target:
        raise ValidationError("user not found")
    if target_id == actor["id"]:
        raise ValidationError("you cannot delete your own account")
    if target["is_admin"] and target["enabled"]:
        remaining = conn.execute(
            "SELECT COUNT(*) AS n FROM users WHERE is_admin = 1 AND enabled = 1 AND id != ?",
            (target_id,),
        ).fetchone()["n"]
        if not remaining:
            raise ValidationError("the last enabled administrator cannot be deleted")
    for table in ("projects", "todos", "voice_jobs"):
        count = conn.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE user_id = ?", (target_id,)).fetchone()["n"]
        if count:
            raise ValidationError(
                f"this user still owns {count} record(s) in {table}; reassign or remove their data first"
            )
    conn.execute("DELETE FROM users WHERE id = ?", (target_id,))


def llm_state(conn):
    """LLM provider settings as exposed to the frontend; the API key
    itself never leaves the server, only whether one is configured."""
    provider = get_setting(conn, LLM_PROVIDER_SETTING, DEFAULT_LLM_PROVIDER)
    if provider not in DEFAULT_LLM_BASE_URLS:
        provider = DEFAULT_LLM_PROVIDER
    return {
        "llm_provider": provider,
        "llm_base_url": get_setting(conn, LLM_BASE_URL_SETTING, "") or DEFAULT_LLM_BASE_URLS[provider],
        "llm_model": get_setting(conn, LLM_MODEL_SETTING, ""),
        "llm_api_key_set": bool(get_setting(conn, LLM_API_KEY_SETTING, "")) or bool(os.environ.get(LLM_API_KEY_ENV_VARS[provider], "")),
    }


def settings_state(conn, user):
    """Settings visible to the current user. Appearance and per-user git
    credentials are scoped to the account; LLM, ASR, queue, and integration
    switch configuration is administrative and only included for admins."""
    is_admin = bool(user and user["is_admin"])
    user_id = user["id"] if user else None
    state = {
        "ui_theme": get_effective_user_setting(conn, user_id, UI_THEME_SETTING, ""),
        "ui_mode": get_effective_user_setting(conn, user_id, UI_MODE_SETTING, ""),
        "github_enabled": get_setting(conn, GITHUB_ENABLED_SETTING, "1") != "0",
        "gitlab_enabled": get_setting(conn, GITLAB_ENABLED_SETTING, "1") != "0",
        "github_token_set": bool(load_github_tokens(conn, user_id)),
        "github_tokens": [
            {
                "label": entry["label"],
                "owner": entry["owner"],
                "hint": f"····{entry['token'][-4:]}" if entry["token"] else "",
            }
            for entry in load_github_tokens(conn, user_id)
        ],
        "gitlab_token_set": bool(get_user_setting(conn, user_id, GITLAB_TOKEN_SETTING)),
        "gitlab_url": get_user_setting(conn, user_id, GITLAB_URL_SETTING),
    }
    if is_admin:
        state.update(
            {
                "asr_endpoint": get_setting(conn, ASR_ENDPOINT_SETTING, DEFAULT_ASR_ENDPOINT),
                "asr_model": get_setting(conn, ASR_MODEL_SETTING, DEFAULT_ASR_MODEL),
                "asr_language": get_setting(conn, ASR_LANGUAGE_SETTING, DEFAULT_ASR_LANGUAGE),
                "queue_capacity": queue_capacity(conn),
                "queue_parallelism": queue_parallelism(conn),
            }
        )
        state.update(llm_state(conn))
    return state


def require_admin(user):
    if not user or not user["is_admin"]:
        raise PermissionError("administrator access required")


def run(host="127.0.0.1", port=8000, db_path=DB_PATH, tls_port=None, tls_cert=None, tls_key=None):
    init_db(db_path)
    fail_stale_voice_jobs(db_path)
    fail_stale_generation_jobs(db_path)
    stop = threading.Event()
    scheduler = threading.Thread(target=scheduler_loop, args=(stop, db_path), daemon=True)
    scheduler.start()
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.db_path = db_path
    tls_server = build_tls_server(host, tls_port, db_path, tls_cert, tls_key)
    if tls_server:
        threading.Thread(target=tls_server.serve_forever, daemon=True).start()
    try:
        print(f"Weekly reports workspace running at http://{host}:{port}")
        if tls_server:
            print(f"Weekly reports workspace running at https://{host}:{tls_server.server_port} (self-signed TLS)")
        httpd.serve_forever()
    finally:
        stop.set()
        if tls_server:
            tls_server.shutdown()
            tls_server.server_close()


def build_tls_server(host, tls_port, db_path, tls_cert, tls_key):
    """Builds an HTTPS listener used by devices that need microphone access
    (browsers only expose getUserMedia on secure origins)."""
    if tls_port is None or not (tls_cert and tls_key):
        return None
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(tls_cert, tls_key)
    httpd = ThreadingHTTPServer((host, int(tls_port)), Handler)
    httpd.db_path = db_path
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    return httpd


def scheduler_loop(stop, db_path):
    while not stop.wait(60):
        try:
            with connect(db_path) as conn:
                for row in conn.execute("SELECT id FROM projects WHERE status = 'active'"):
                    evaluate_schedules(conn, row["id"])
                conn.commit()
        except Exception:
            print(f"scheduler loop error: {traceback.format_exc()}", file=sys.stderr, flush=True)


def evaluate_schedules(conn, project_id):
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if project["status"] != "active":
        return
    week_key = current_week_key(project["timezone"])
    due = False
    for schedule in conn.execute("SELECT * FROM update_schedules WHERE project_id = ?", (project_id,)):
        if not schedule["enabled"]:
            continue
        if schedule_due(schedule):
            due = True
            conn.execute("UPDATE update_schedules SET last_checked_at = ? WHERE id = ?", (iso_now(), schedule["id"]))
            print(f"scheduled trigger fired: project={project_id} schedule={schedule['id']} week={week_key}", flush=True)
    if due:
        if changed_since_last_success(conn, project_id, week_key):
            generate_report(conn, project_id, "scheduled", force=False)
        else:
            record_skipped_run(conn, project_id, week_key, project["report_provider"])
            print(f"scheduled update skipped, no source changes since last success: project={project_id} week={week_key}", flush=True)
    evaluate_risks(conn, project_id)


def record_skipped_run(conn, project_id, week_key, provider):
    now = iso_now()
    reason = "scheduled trigger fired but no input changed since last successful report"
    conn.execute(
        """
        INSERT INTO generation_jobs
        (project_id, week_key, trigger_type, provider, status, input_summary, failure_reason, started_at, completed_at)
        VALUES (?, ?, 'scheduled', ?, 'skipped', ?, ?, ?, ?)
        """,
        (project_id, week_key, provider, reason, reason, now, now),
    )


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
        except PermissionError as exc:
            self.error(HTTPStatus.FORBIDDEN, str(exc))
        except Exception as exc:
            self.error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_POST(self):
        self.handle_write("POST")

    def do_PUT(self):
        self.handle_write("PUT")

    def do_DELETE(self):
        self.handle_write("DELETE")

    def wants_gzip(self):
        accept = self.headers.get("Accept-Encoding") or ""
        return "gzip" in (part.strip().lower() for part in accept.split(","))

    def _send_bytes(self, data, content_type, status=HTTPStatus.OK, extra_headers=None):
        # The service answers on a VPN interface (utun, MTU 1420) where bulk
        # transfers dominate request time; compress text payloads on the way
        # out when the client accepts it.
        if (
            len(data) > 1024
            and content_type.split(";")[0].strip() in {"application/json", "application/javascript", "text/css", "text/html"}
            and self.wants_gzip()
        ):
            data = gzip.compress(data, 6)
            gzipped = True
        else:
            gzipped = False
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        if gzipped:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "keep-alive")
        self.send_header("Cache-Control", "no-store")
        for name, value in extra_headers or []:
            self.send_header(name, value)
        self.end_headers()
        try:
            self.wfile.write(data)
        except OSError:
            # a truncated keep-alive response would poison the next request
            # parsed from this connection; close it instead
            self.close_connection = True

    def handle_write(self, method):
        try:
            # Drain the body for every write request, even for handlers that
            # never look at it (e.g. cancel). An unread body would otherwise
            # stick to the keep-alive connection and be parsed as the next
            # request line, surfacing as 501 Unsupported method ('{}POST').
            self.read_body_bytes()
            parsed = urlparse(self.path)
            self.handle_api(method, parsed.path, parse_qs(parsed.query))
        except QueueFullError as exc:
            self.error(HTTPStatus.CONFLICT, str(exc))
        except PermissionError as exc:
            self.error(HTTPStatus.FORBIDDEN, str(exc))
        except ValidationError as exc:
            self.error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:
            self.error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def read_body_bytes(self):
        length = int(self.headers.get("Content-Length") or 0)
        self._raw_body = self.rfile.read(length) if length > 0 else b""

    def body_json(self):
        raw = getattr(self, "_raw_body", b"")
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def current_user(self, conn):
        header = self.headers.get("Cookie") or ""
        return auth.user_for_session(conn, auth.token_from_cookie_header(header))

    def handle_api(self, method, path, query):
        parts = [p for p in path.split("/") if p]
        with connect(self.server.db_path) as conn:
            user = self.current_user(conn)
            if (method, path) not in PUBLIC_API_ROUTES and user is None:
                self.error(HTTPStatus.UNAUTHORIZED, "authentication required")
                return
            user_id = user["id"] if user else None
            is_admin = bool(user and user["is_admin"])
            if path == "/api/auth/state" and method == "GET":
                self.json({"authenticated": bool(user), "current_user": auth.user_public(user)})
                return
            if path == "/api/auth/login" and method == "POST":
                payload = self.body_json()
                row = auth.authenticate(conn, payload.get("username"), payload.get("password"))
                token = auth.create_session(conn, row["id"])
                conn.commit()
                self.json(
                    {"current_user": auth.user_public(row)},
                    extra_headers=[("Set-Cookie", auth.session_cookie_header(token))],
                )
                return
            if path == "/api/auth/logout" and method == "POST":
                token = auth.token_from_cookie_header(self.headers.get("Cookie") or "")
                auth.delete_session(conn, token)
                conn.commit()
                self.json({"ok": True}, extra_headers=[("Set-Cookie", auth.clear_cookie_header())])
                return
            if path == "/api/auth/password" and method == "PUT":
                payload = self.body_json()
                auth.change_password(conn, user_id, payload.get("old_password"), payload.get("new_password"))
                conn.commit()
                self.json({"ok": True})
                return
            if path == "/api/users" and method == "GET":
                require_admin(user)
                rows = conn.execute("SELECT * FROM users ORDER BY username").fetchall()
                self.json({"users": [auth.user_public(row) for row in rows]})
                return
            if path == "/api/users" and method == "POST":
                require_admin(user)
                payload = self.body_json()
                new_id = auth.create_user(
                    conn,
                    payload.get("username"),
                    payload.get("password"),
                    is_admin=bool(payload.get("is_admin")),
                )
                conn.commit()
                row = conn.execute("SELECT * FROM users WHERE id = ?", (new_id,)).fetchone()
                self.json({"user": auth.user_public(row)}, HTTPStatus.CREATED)
                return
            if len(parts) == 3 and parts[:2] == ["api", "users"] and parts[2].isdigit() and method == "PUT":
                require_admin(user)
                payload = self.body_json()
                updated = update_user(conn, user, int(parts[2]), payload)
                conn.commit()
                self.json({"user": updated})
                return
            if len(parts) == 3 and parts[:2] == ["api", "users"] and parts[2].isdigit() and method == "DELETE":
                require_admin(user)
                delete_user(conn, user, int(parts[2]))
                conn.commit()
                self.json({"ok": True})
                return
            if path == "/api/state" and method == "GET":
                projects = []
                for row in conn.execute(
                    "SELECT * FROM projects WHERE user_id = ? ORDER BY updated_at DESC",
                    (user_id,),
                ):
                    project = dict(row)
                    project["progress_status"] = progress_status(conn, project["id"])
                    projects.append(project)
                self.json(
                    {
                        "projects": projects,
                        "current_user": auth.user_public(user),
                        **settings_state(conn, user),
                    }
                )
                return
            if path == "/api/projects" and method == "POST":
                payload = self.body_json()
                require_project_name(payload)
                validate_timezone(payload.get("timezone") or "Asia/Shanghai")
                validate_provider(payload.get("report_provider") or REPORT_PROVIDER)
                validate_project_status(payload.get("status") or "active")
                project_id = create_project(conn, payload, user)
                conn.commit()
                self.json({"id": project_id}, HTTPStatus.CREATED)
                return
            if path == "/api/todos" and method == "GET":
                self.json({"todos": todo_rows(conn, user_id)})
                return
            if path == "/api/todos" and method == "POST":
                todo_id = create_todo(conn, self.body_json(), user_id)
                conn.commit()
                self.json({"id": todo_id, "todos": todo_rows(conn, user_id)}, HTTPStatus.CREATED)
                return
            if path == "/api/todos/voice" and method == "POST":
                payload = self.body_json()
                job_id = enqueue_voice_job(
                    conn,
                    self.server.db_path,
                    payload,
                    normalize_asr_endpoint(get_setting(conn, ASR_ENDPOINT_SETTING, DEFAULT_ASR_ENDPOINT)),
                    get_setting(conn, ASR_MODEL_SETTING, DEFAULT_ASR_MODEL) or DEFAULT_ASR_MODEL,
                    get_setting(conn, ASR_LANGUAGE_SETTING, DEFAULT_ASR_LANGUAGE) or DEFAULT_ASR_LANGUAGE,
                    user_id,
                )
                conn.commit()
                self.json({"id": job_id, "status": "queued"}, HTTPStatus.ACCEPTED)
                return
            if path == "/api/task-queue" and method == "GET":
                self.json(task_queue_state(conn, None if is_admin else user_id, is_admin=is_admin))
                return
            if path == "/api/voice-jobs/active" and method == "GET":
                self.json({"job": get_active_voice_job(conn, user_id)})
                return
            if len(parts) == 4 and parts[:2] == ["api", "voice-jobs"] and parts[2].isdigit() and parts[3] == "cancel" and method == "POST":
                job_id = cancel_voice_job(conn, int(parts[2]), user_id)
                conn.commit()
                print(f"voice job {job_id}: cancel requested", flush=True)
                self.json({"id": job_id, "status": "cancelled"})
                return
            if len(parts) == 3 and parts[:2] == ["api", "voice-jobs"] and parts[2].isdigit() and method == "GET":
                job = get_voice_job(conn, int(parts[2]), user_id)
                self.json(job)
                return
            if path == "/api/settings" and method == "PUT":
                # Partial update: only the keys present in the payload are
                # touched, so the appearance, git, and administrative panels
                # never reset each other's values. Appearance preferences are
                # per user; the rest of the keys are administrative.
                payload = self.body_json()
                if "ui_theme" in payload:
                    set_user_setting(conn, user_id, UI_THEME_SETTING, validate_ui_theme(payload.get("ui_theme")))
                if "ui_mode" in payload:
                    set_user_setting(conn, user_id, UI_MODE_SETTING, validate_ui_mode(payload.get("ui_mode")))
                # Per-user git credentials: a non-empty value stores the token,
                # an empty value clears it; the token itself never leaves the
                # server afterwards, only *_token_set flags.
                if GITHUB_TOKENS_SETTING in payload:
                    stored = load_github_tokens(conn, user_id)
                    merged = []
                    for index, entry in enumerate((payload.get(GITHUB_TOKENS_SETTING) or [])[:8]):
                        if not isinstance(entry, dict):
                            continue
                        token = (entry.get("token") or "").strip()
                        if not token and index < len(stored) and stored[index]["owner"] == (entry.get("owner") or "").strip().lower():
                            token = stored[index]["token"]
                        if not token:
                            continue
                        merged.append(
                            {
                                "label": (entry.get("label") or "").strip()[:64],
                                "owner": (entry.get("owner") or "").strip().lstrip("@").lower()[:64],
                                "token": token[:255],
                            }
                        )
                    set_user_setting(conn, user_id, GITHUB_TOKENS_SETTING, json.dumps(merged, ensure_ascii=False))
                    # once the list exists it replaces the legacy single token
                    set_user_setting(conn, user_id, GITHUB_TOKEN_SETTING, "")
                for token_key in (GITHUB_TOKEN_SETTING, GITLAB_TOKEN_SETTING):
                    if token_key in payload:
                        set_user_setting(conn, user_id, token_key, (payload.get(token_key) or "").strip())
                if GITLAB_URL_SETTING in payload:
                    set_user_setting(
                        conn,
                        user_id,
                        GITLAB_URL_SETTING,
                        validate_gitlab_server(payload.get(GITLAB_URL_SETTING)),
                    )
                if any(key in payload for key in ADMIN_ONLY_SETTING_KEYS):
                    require_admin(user)
                if GITHUB_ENABLED_SETTING in payload:
                    set_setting(conn, GITHUB_ENABLED_SETTING, "1" if payload.get(GITHUB_ENABLED_SETTING) else "0")
                if GITLAB_ENABLED_SETTING in payload:
                    set_setting(conn, GITLAB_ENABLED_SETTING, "1" if payload.get(GITLAB_ENABLED_SETTING) else "0")
                if "asr_endpoint" in payload:
                    set_setting(conn, ASR_ENDPOINT_SETTING, normalize_asr_endpoint(payload.get("asr_endpoint") or DEFAULT_ASR_ENDPOINT))
                if "asr_model" in payload:
                    set_setting(conn, ASR_MODEL_SETTING, (payload.get("asr_model") or "").strip() or DEFAULT_ASR_MODEL)
                if "asr_language" in payload:
                    set_setting(conn, ASR_LANGUAGE_SETTING, (payload.get("asr_language") or "").strip() or DEFAULT_ASR_LANGUAGE)
                llm_provider = get_setting(conn, LLM_PROVIDER_SETTING, DEFAULT_LLM_PROVIDER)
                if "llm_provider" in payload:
                    llm_provider = validate_llm_provider(payload.get("llm_provider") or DEFAULT_LLM_PROVIDER)
                    set_setting(conn, LLM_PROVIDER_SETTING, llm_provider)
                if "llm_base_url" in payload:
                    llm_base_url = (payload.get("llm_base_url") or "").strip()
                    set_setting(conn, LLM_BASE_URL_SETTING, validate_llm_base_url(llm_base_url) if llm_base_url else DEFAULT_LLM_BASE_URLS[llm_provider])
                if "llm_model" in payload:
                    set_setting(conn, LLM_MODEL_SETTING, (payload.get("llm_model") or "").strip())
                # Empty llm_api_key means "keep the stored key" so the
                # frontend never has to echo the secret back.
                api_key = (payload.get("llm_api_key") or "").strip()
                if api_key:
                    set_setting(conn, LLM_API_KEY_SETTING, api_key)
                if "queue_capacity" in payload:
                    set_setting(conn, QUEUE_CAPACITY_SETTING, str(validate_queue_capacity(payload.get("queue_capacity"))))
                if "queue_parallelism" in payload:
                    set_setting(conn, QUEUE_PARALLELISM_SETTING, str(validate_queue_parallelism(payload.get("queue_parallelism"))))
                conn.commit()
                self.json(settings_state(conn, user))
                return
            if len(parts) == 3 and parts[:2] == ["api", "todos"] and method == "PUT":
                update_todo(conn, int(parts[2]), self.body_json(), user_id)
                conn.commit()
                self.json({"todos": todo_rows(conn, user_id)})
                return
            if len(parts) == 4 and parts[:2] == ["api", "todos"] and parts[3] == "close" and method == "POST":
                material_id = close_todo(conn, int(parts[2]), self.body_json(), user_id)
                conn.commit()
                self.json({"material_id": material_id, "todos": todo_rows(conn, user_id)})
                return
            if len(parts) == 3 and parts[:2] == ["api", "todos"] and method == "DELETE":
                delete_todo(conn, int(parts[2]), user_id)
                conn.commit()
                self.json({"todos": todo_rows(conn, user_id)})
                return
            if len(parts) >= 3 and parts[0] == "api" and parts[1] == "projects":
                project_id = int(parts[2])
                owned = conn.execute(
                    "SELECT id FROM projects WHERE id = ? AND user_id = ?",
                    (project_id, user_id),
                ).fetchone()
                if not owned:
                    self.error(HTTPStatus.NOT_FOUND, "project not found")
                    return
                if len(parts) == 4 and parts[3] == "workspace" and method == "GET":
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 5 and parts[3] == "materials" and method == "GET":
                    material = material_detail(conn, project_id, int(parts[4]))
                    if not material:
                        self.error(HTTPStatus.NOT_FOUND, "material not found")
                        return
                    self.json(material)
                    return
                if len(parts) == 6 and parts[3] == "materials" and parts[5] == "content" and method == "GET":
                    self.material_content(conn, project_id, int(parts[4]))
                    return
                if len(parts) == 5 and parts[3] == "reports" and method == "GET":
                    archived = report_archive(conn, project_id, parts[4])
                    if not archived:
                        self.error(HTTPStatus.NOT_FOUND, "weekly report not found")
                        return
                    self.json(archived)
                    return
                if len(parts) == 6 and parts[3] == "reports" and parts[5] == "pdf" and method == "GET":
                    self.report_pdf(conn, project_id, parts[4])
                    return
                if len(parts) == 4 and parts[3] == "status" and method == "POST":
                    payload = self.body_json()
                    status = "active" if payload.get("enabled", True) else "paused"
                    conn.execute(
                        "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
                        (status, iso_now(), project_id),
                    )
                    conn.commit()
                    self.json({"id": project_id, "status": status})
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
                        material_ids = [material_id]
                    else:
                        files = payload.get("files") if "files" in payload else [payload]
                        if not isinstance(files, list) or not files:
                            raise ValidationError("at least one material file is required")
                        material_ids = [store_material(conn, project_id, item) for item in files]
                        summarize_uploaded_materials(conn, project_id, material_ids)
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json({"id": material_ids[0], "ids": material_ids}, HTTPStatus.CREATED)
                    return
                if len(parts) == 5 and parts[3] == "materials" and method == "PUT":
                    payload = self.body_json()
                    if "summary" in payload:
                        update_material_summary(conn, project_id, int(parts[4]), payload)
                    else:
                        update_manual_material(conn, project_id, int(parts[4]), payload)
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 5 and parts[3] == "materials" and method == "DELETE":
                    storage_path = delete_material(conn, project_id, int(parts[4]))
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    remove_material_file(storage_path)
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 4 and parts[3] == "repos" and method == "POST":
                    repo_id = add_repo(conn, project_id, self.body_json(), auth_info=git_auth_for_user(conn, user_id))
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json({"id": repo_id}, HTTPStatus.CREATED)
                    return
                if len(parts) == 5 and parts[3] == "repos" and method == "PUT":
                    update_repo_notes(conn, project_id, int(parts[4]), self.body_json(), auth_info=git_auth_for_user(conn, user_id))
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 5 and parts[3] == "repos" and method == "DELETE":
                    delete_repo(conn, project_id, int(parts[4]))
                    evaluate_risks(conn, project_id)
                    conn.commit()
                    self.json(workspace(conn, project_id))
                    return
                if len(parts) == 6 and parts[3] == "repos" and parts[5] == "branches" and method == "GET":
                    self.json(repo_branches(conn, project_id, int(parts[4]), auth_info=git_auth_for_user(conn, user_id)))
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
                    payload = self.body_json()
                    job_id = enqueue_report_generation(
                        conn, self.server.db_path, project_id, "manual", force=bool(payload.get("force", True))
                    )
                    conn.commit()
                    self.json({"id": job_id, "status": "queued"}, HTTPStatus.ACCEPTED)
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
                conn.execute(
                    "UPDATE risk_warnings SET status = ?, updated_at = ? WHERE id = ? AND project_id IN (SELECT id FROM projects WHERE user_id = ?)",
                    (status, iso_now(), int(parts[2]), user_id),
                )
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
        self._send_bytes(data, content_type)

    def json(self, payload, status=HTTPStatus.OK, extra_headers=None):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(data, "application/json; charset=utf-8", status=status, extra_headers=extra_headers)

    def bytes_response(self, data, content_type, filename=None, status=HTTPStatus.OK):
        extra = [("Content-Disposition", f'attachment; filename="{filename}"')] if filename else None
        self._send_bytes(data, content_type, status=status, extra_headers=extra)

    def report_pdf(self, conn, project_id, week_key):
        project = dict(conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())
        report = conn.execute(
            """
            SELECT id, week_key, content_md, latest_job_id, created_at, updated_at
            FROM weekly_reports
            WHERE project_id = ? AND week_key = ?
            """,
            (project_id, week_key),
        ).fetchone()
        if not report:
            self.error(HTTPStatus.NOT_FOUND, "weekly report not found")
            return
        report_dict = dict(report)
        pdf = report_pdf_bytes(project_id, project, report_dict)
        self.bytes_response(pdf, "application/pdf", pdf_filename(project["name"], week_key))

    def material_content(self, conn, project_id, material_id):
        row = conn.execute(
            "SELECT filename, content_type, storage_path, source_type FROM materials WHERE id = ? AND project_id = ?",
            (material_id, project_id),
        ).fetchone()
        if not row or row["source_type"] != "upload" or Path(row["filename"]).suffix.lower() != ".pdf":
            self.error(HTTPStatus.NOT_FOUND, "PDF material not found")
            return
        path = Path(row["storage_path"] or "").resolve()
        upload_root = UPLOAD_DIR.resolve()
        try:
            path.relative_to(upload_root)
        except ValueError:
            self.error(HTTPStatus.NOT_FOUND, "PDF material not found")
            return
        if not path.is_file():
            self.error(HTTPStatus.NOT_FOUND, "PDF material not found")
            return
        self.bytes_response(path.read_bytes(), "application/pdf")

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
        # Archived bodies load on demand through
        # /api/projects/{id}/reports/{week_key}; rendering every old report
        # here dominated project switch time.
        item.pop("content_md")
        report_history.append(item)
    return {
        "project": project,
        "week_key": week_key,
        "schedules": [dict(row) for row in conn.execute("SELECT * FROM update_schedules WHERE project_id = ? ORDER BY weekday, local_time", (project_id,))],
        "materials": material_rows(conn, project_id, project["timezone"]),
        "repos": repo_rows(conn, project_id),
        "plan": plan_dict(conn, project_id),
        "outcomes": [dict(row) for row in conn.execute("SELECT * FROM weekly_outcomes WHERE project_id = ? AND week_key = ? ORDER BY id", (project_id, week_key))],
        "weekly_update": row_to_dict(conn.execute("SELECT * FROM weekly_updates WHERE project_id = ? AND week_key = ?", (project_id, week_key)).fetchone()),
        "report": report_dict,
        "report_history": report_history,
        "jobs": [dict(row) for row in conn.execute("SELECT id, week_key, trigger_type, provider, status, input_snapshot_hash, input_summary, failure_reason, queued_at, started_at, completed_at FROM generation_jobs WHERE project_id = ? AND week_key = ? ORDER BY id DESC", (project_id, week_key))],
        "risks": [dict(row) for row in conn.execute("SELECT * FROM risk_warnings WHERE project_id = ? AND week_key = ? AND rule IN ('missing_update', 'overdue_milestone', 'blocked_outcome') ORDER BY status, severity DESC, updated_at DESC", (project_id, week_key))],
        "source_diagnostics": source_diagnostics(conn, project_id, week_key),
        "progress_status": progress_status(conn, project_id),
    }


def report_archive(conn, project_id, week_key):
    row = conn.execute(
        """
        SELECT week_key, content_md, updated_at
        FROM weekly_reports
        WHERE project_id = ? AND week_key = ?
        """,
        (project_id, week_key),
    ).fetchone()
    if not row:
        return None
    item = dict(row)
    item["content_html"] = render_markdown(item.pop("content_md"))
    return item


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
        SELECT id, repo, git_mode, status, status_message, updated_at
        FROM github_repos
        WHERE project_id = ? AND enabled = 1
          AND status IN ('disconnected', 'unauthenticated', 'inaccessible')
        ORDER BY updated_at DESC, id DESC
        """,
        (project_id,),
    ):
        label = "GitLab" if row["git_mode"] == "gitlab" else "GitHub"
        items.append(
            {
                "kind": "github",
                "severity": "warning",
                "title": f"{label} source unavailable",
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
               extraction_error, extracted_text, summary, summary_status, summary_error,
               created_at, updated_at
        FROM materials
        WHERE project_id = ?
          AND (source_type = 'manual' OR extraction_status != 'failed')
        ORDER BY id DESC
        """,
        (project_id,),
    ):
        item = dict(row)
        item["editable"] = material_is_editable(row, timezone)
        item["deletable"] = material_is_unlocked(row, timezone)
        if item["source_type"] == "manual":
            item["content"] = item.pop("extracted_text") or ""
        else:
            item.pop("extracted_text", None)
        rows.append(item)
    return rows


def material_detail(conn, project_id, material_id):
    row = conn.execute(
        """
        SELECT id, filename, source_type, content_type, size_bytes, extraction_status,
               extraction_error, extracted_text, summary, summary_status, created_at, updated_at
        FROM materials
        WHERE id = ? AND project_id = ?
        """,
        (material_id, project_id),
    ).fetchone()
    if not row:
        return None
    item = dict(row)
    item["content"] = item.pop("extracted_text") or ""
    suffix = Path(item["filename"]).suffix.lower()
    if suffix == ".pdf" and item["source_type"] == "upload":
        item["preview_kind"] = "pdf"
    elif item["source_type"] == "manual" or suffix in {".md", ".markdown"}:
        item["preview_kind"] = "markdown"
        item["content_html"] = render_markdown(item["content"])
    else:
        item["preview_kind"] = "text"
    return item


def update_settings(conn, project_id, payload):
    validate_timezone(payload.get("timezone") or "Asia/Shanghai")
    validate_provider(payload.get("report_provider") or REPORT_PROVIDER)
    validate_project_status(payload.get("status") or "active")
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
            payload.get("report_provider") or REPORT_PROVIDER,
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
            "INSERT INTO update_schedules (project_id, weekday, local_time, timezone, enabled, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, int(item["weekday"]), item["local_time"], item.get("timezone") or payload.get("timezone"), 1 if item.get("enabled", True) else 0, now),
        )


def add_repo(conn, project_id, payload, auth_info=None):
    raw_repo = (payload.get("repo") or "").strip()
    git_mode = validate_git_mode(payload.get("git_mode"))
    gitlab_server = ""
    if git_mode == "gitlab":
        gitlab_server = validate_gitlab_server(payload.get("gitlab_server")) or gitlab_server_from_url(raw_repo)
    repo = validate_repo(raw_repo, git_mode)
    info = auth_info or {}
    if git_mode == "gitlab" and not info.get("gitlab_enabled", True):
        raise ValidationError("GitLab 集成已在全局设置中停用，无法添加 GitLab 仓库")
    if git_mode == "github" and not info.get("github_enabled", True):
        raise ValidationError("GitHub 集成已在全局设置中停用，无法添加 GitHub 仓库")
    notes = payload.get("notes") or ""
    requested_branches = validate_branches(payload.get("branches") or [])
    existing = conn.execute(
        "SELECT id FROM github_repos WHERE project_id = ? AND git_mode = ? AND gitlab_server = ? AND repo = ?",
        (project_id, git_mode, gitlab_server, repo),
    ).fetchone()
    if existing:
        updates = ["notes = ?", "enabled = 1", "updated_at = ?"]
        values = [notes, iso_now()]
        if requested_branches:
            updates.insert(1, "tracked_branches_json = ?")
            values.insert(1, json.dumps(requested_branches))
        values.append(existing["id"])
        conn.execute(
            f"UPDATE github_repos SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        return existing["id"]
    result = check_repo(repo, git_mode, gitlab_server, auth_info=auth_info)
    branches = requested_branches or [result.get("default_branch") or "main"]
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO github_repos
        (project_id, repo, git_mode, gitlab_server, enabled, notes, tracked_branches_json, status, status_message, last_checked_at, last_activity_at, activity_summary, created_at, updated_at)
        VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            repo,
            git_mode,
            gitlab_server,
            notes,
            json.dumps(branches),
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


def update_repo_notes(conn, project_id, repo_id, payload, auth_info=None):
    row = conn.execute(
        "SELECT repo, notes, tracked_branches_json, enabled, git_mode, gitlab_server FROM github_repos WHERE id = ? AND project_id = ?",
        (repo_id, project_id),
    ).fetchone()
    if not row:
        raise ValidationError("repository not found")
    now = iso_now()
    notes = payload.get("notes") if "notes" in payload else (row["notes"] or "")
    branches = validate_branches(payload.get("branches") or [])
    if not branches:
        branches = json.loads(row["tracked_branches_json"] or '["main"]')
    enabled = row["enabled"] if "enabled" not in payload else (1 if payload.get("enabled") else 0)
    git_mode = validate_git_mode(payload.get("git_mode")) if "git_mode" in payload else row["git_mode"]
    gitlab_server = (
        validate_gitlab_server(payload.get("gitlab_server")) if git_mode == "gitlab" else ""
    )
    target_changed = git_mode != row["git_mode"] or gitlab_server != (row["gitlab_server"] or "")
    if target_changed:
        conflict = conn.execute(
            "SELECT id FROM github_repos WHERE project_id = ? AND git_mode = ? AND gitlab_server = ? AND repo = ? AND id != ?",
            (project_id, git_mode, gitlab_server, row["repo"], repo_id),
        ).fetchone()
        if conflict:
            raise ValidationError("a repository entry with this git mode and server already exists")
    result = check_repo(row["repo"], git_mode, gitlab_server, auth_info=auth_info) if target_changed else None
    if result:
        conn.execute(
            """
            UPDATE github_repos
            SET notes = ?, tracked_branches_json = ?, enabled = ?, git_mode = ?, gitlab_server = ?,
                status = ?, status_message = ?, activity_summary = ?, last_activity_at = ?,
                last_checked_at = ?, updated_at = ?
            WHERE id = ? AND project_id = ?
            """,
            (
                notes,
                json.dumps(branches),
                enabled,
                git_mode,
                gitlab_server,
                result["status"],
                result["status_message"],
                result["activity_summary"],
                result["last_activity_at"],
                now,
                now,
                repo_id,
                project_id,
            ),
        )
        return result
    conn.execute(
        "UPDATE github_repos SET notes = ?, tracked_branches_json = ?, enabled = ?, git_mode = ?, gitlab_server = ?, updated_at = ? WHERE id = ? AND project_id = ?",
        (notes, json.dumps(branches), enabled, git_mode, gitlab_server, now, repo_id, project_id),
    )
    return None


def delete_repo(conn, project_id, repo_id):
    cur = conn.execute(
        "DELETE FROM github_repos WHERE id = ? AND project_id = ?",
        (repo_id, project_id),
    )
    if cur.rowcount != 1:
        raise ValidationError("repository not found")


def repo_rows(conn, project_id):
    rows = []
    for row in conn.execute("SELECT * FROM github_repos WHERE project_id = ? ORDER BY id", (project_id,)):
        item = dict(row)
        item["tracked_branches"] = json.loads(item.pop("tracked_branches_json") or '["main"]')
        rows.append(item)
    return rows


def repo_branches(conn, project_id, repo_id, auth_info=None):
    row = conn.execute(
        "SELECT repo, git_mode, gitlab_server FROM github_repos WHERE id = ? AND project_id = ?",
        (repo_id, project_id),
    ).fetchone()
    if not row:
        raise ValidationError("repository not found")
    return list_branches(row["repo"], row["git_mode"], row["gitlab_server"], auth_info=auth_info)


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
