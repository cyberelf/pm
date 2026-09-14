import json
import os
import secrets
import sqlite3
from pathlib import Path

from . import auth
from .config import (
    ADMIN_PASSWORD_ENV_VAR,
    BOOTSTRAP_ADMIN_USERNAME,
    DATA_DIR,
    DB_PATH,
    DEFAULT_TIMEZONE,
    REPORT_PROVIDER,
)
from .timeutil import iso_now


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    owner TEXT NOT NULL DEFAULT 'local-user',
    start_date TEXT NOT NULL,
    end_date TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    timezone TEXT NOT NULL DEFAULT 'Asia/Shanghai',
    report_provider TEXT NOT NULL DEFAULT 'codex',
    system_prompt TEXT NOT NULL DEFAULT '',
    report_template TEXT NOT NULL DEFAULT '',
    manual_background TEXT NOT NULL DEFAULT '',
    manual_objectives TEXT NOT NULL DEFAULT '',
    manual_constraints TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS update_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    weekday INTEGER NOT NULL,
    local_time TEXT NOT NULL,
    timezone TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_checked_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    checksum TEXT NOT NULL,
    extraction_status TEXT NOT NULL,
    extracted_text TEXT NOT NULL DEFAULT '',
    extraction_error TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    summary_status TEXT NOT NULL DEFAULT 'pending',
    summary_error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS github_repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    repo TEXT NOT NULL,
    git_mode TEXT NOT NULL DEFAULT 'github',
    gitlab_server TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    tracked_branches_json TEXT NOT NULL DEFAULT '["main"]',
    status TEXT NOT NULL,
    status_message TEXT NOT NULL DEFAULT '',
    last_checked_at TEXT,
    last_activity_at TEXT,
    activity_summary TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_plans (
    project_id INTEGER PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
    objectives TEXT NOT NULL DEFAULT '',
    milestones_json TEXT NOT NULL DEFAULT '[]',
    deliverables_json TEXT NOT NULL DEFAULT '[]',
    version INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weekly_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    week_key TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'planned',
    owner_label TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weekly_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    week_key TEXT NOT NULL,
    completed TEXT NOT NULL DEFAULT '',
    in_progress TEXT NOT NULL DEFAULT '',
    blockers TEXT NOT NULL DEFAULT '',
    risks TEXT NOT NULL DEFAULT '',
    next_steps TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, week_key)
);

CREATE TABLE IF NOT EXISTS weekly_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    week_key TEXT NOT NULL,
    content_md TEXT NOT NULL,
    latest_job_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, week_key)
);

CREATE TABLE IF NOT EXISTS generation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    week_key TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    provider TEXT NOT NULL,
    status TEXT NOT NULL,
    input_snapshot_hash TEXT NOT NULL DEFAULT '',
    input_summary TEXT NOT NULL DEFAULT '',
    output_md TEXT NOT NULL DEFAULT '',
    failure_reason TEXT NOT NULL DEFAULT '',
    queued_at TEXT,
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS risk_warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    week_key TEXT NOT NULL,
    rule TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    source_ref TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, week_key, rule, source_ref)
);

CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'todo',
    close_reason TEXT NOT NULL DEFAULT '',
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    material_id INTEGER REFERENCES materials(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS voice_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    status TEXT NOT NULL DEFAULT 'transcribing',
    transcript TEXT NOT NULL DEFAULT '',
    error TEXT NOT NULL DEFAULT '',
    fallback INTEGER NOT NULL DEFAULT 0,
    todo_ids_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS device_auth_codes (
    device_code TEXT PRIMARY KEY,
    user_code TEXT UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    attempts INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (user_id, key)
);
"""


def connect(path: Path = DB_PATH):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_setting(conn, key, default=""):
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row and row["value"] else default


def set_setting(conn, key, value):
    conn.execute(
        "INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )


def init_db(path: Path = DB_PATH):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
    return path


def migrate_schema(conn):
    schedule_columns = {row["name"] for row in conn.execute("PRAGMA table_info(update_schedules)")}
    if "enabled" not in schedule_columns:
        conn.execute("ALTER TABLE update_schedules ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1")
    material_columns = {row["name"] for row in conn.execute("PRAGMA table_info(materials)")}
    if "source_type" not in material_columns:
        conn.execute("ALTER TABLE materials ADD COLUMN source_type TEXT NOT NULL DEFAULT 'upload'")
    if "summary" not in material_columns:
        conn.execute("ALTER TABLE materials ADD COLUMN summary TEXT NOT NULL DEFAULT ''")
    if "summary_status" not in material_columns:
        conn.execute("ALTER TABLE materials ADD COLUMN summary_status TEXT NOT NULL DEFAULT 'pending'")
    if "summary_error" not in material_columns:
        conn.execute("ALTER TABLE materials ADD COLUMN summary_error TEXT NOT NULL DEFAULT ''")
    conn.execute(
        """
        UPDATE materials
        SET summary = filename || '：待生成或补充摘要'
        WHERE source_type = 'upload' AND summary = ''
        """
    )
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(github_repos)")}
    if "notes" not in columns:
        conn.execute("ALTER TABLE github_repos ADD COLUMN notes TEXT NOT NULL DEFAULT ''")
    if "enabled" not in columns:
        conn.execute("ALTER TABLE github_repos ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1")
    if "tracked_branches_json" not in columns:
        conn.execute("ALTER TABLE github_repos ADD COLUMN tracked_branches_json TEXT NOT NULL DEFAULT '[\"main\"]'")
    if "git_mode" not in columns:
        conn.execute("ALTER TABLE github_repos ADD COLUMN git_mode TEXT NOT NULL DEFAULT 'github'")
    if "gitlab_server" not in columns:
        conn.execute("ALTER TABLE github_repos ADD COLUMN gitlab_server TEXT NOT NULL DEFAULT ''")
    job_columns = {row["name"] for row in conn.execute("PRAGMA table_info(generation_jobs)")}
    if "queued_at" not in job_columns:
        conn.execute("ALTER TABLE generation_jobs ADD COLUMN queued_at TEXT")
    conn.execute(
        """
        DELETE FROM github_repos
        WHERE id NOT IN (
            SELECT MIN(id) FROM github_repos GROUP BY project_id, git_mode, repo
        )
        """
    )
    conn.execute("DROP INDEX IF EXISTS idx_github_repos_project_repo")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_github_repos_project_mode_repo ON github_repos(project_id, git_mode, gitlab_server, repo)"
    )
    # the per-repo GitLab server address is gone; 全局设置 → Git 集成 holds the
    # only GitLab URL, so legacy values would silently point repos elsewhere
    conn.execute("UPDATE github_repos SET gitlab_server = '' WHERE gitlab_server != ''")
    table_columns = {
        "projects": {row["name"] for row in conn.execute("PRAGMA table_info(projects)")},
        "todos": {row["name"] for row in conn.execute("PRAGMA table_info(todos)")},
        "voice_jobs": {row["name"] for row in conn.execute("PRAGMA table_info(voice_jobs)")},
    }
    for table, columns in table_columns.items():
        if "user_id" not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER REFERENCES users(id)")
    admin = ensure_bootstrap_admin(conn)
    admin_id = admin["id"]
    for table in table_columns:
        conn.execute(f"UPDATE {table} SET user_id = ? WHERE user_id IS NULL", (admin_id,))
    conn.execute(
        "UPDATE projects SET owner = ? WHERE owner = ?",
        (admin["username"], "local-user"),
    )
    # the Codex/Claude CLI providers are gone; every project now generates
    # through the internal agent
    conn.execute("UPDATE projects SET report_provider = ? WHERE report_provider != ?", (REPORT_PROVIDER, REPORT_PROVIDER))


def ensure_bootstrap_admin(conn):
    """Guarantee at least one enabled admin exists so a fresh database (or one
    whose only admin was removed) can always be signed into. The initial
    password comes from REPORTS_ADMIN_PASSWORD or the built-in default."""
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? ORDER BY id LIMIT 1",
        (BOOTSTRAP_ADMIN_USERNAME,),
    ).fetchone()
    if row:
        if not row["is_admin"] or not row["enabled"]:
            conn.execute(
                "UPDATE users SET is_admin = 1, enabled = 1, updated_at = ? WHERE id = ?",
                (iso_now(), row["id"]),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
        return row
    if conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]:
        row = conn.execute("SELECT * FROM users WHERE is_admin = 1 AND enabled = 1 ORDER BY id LIMIT 1").fetchone()
        if row:
            return row
    password = os.environ.get(ADMIN_PASSWORD_ENV_VAR) or ""
    generated = not password
    if generated:
        # Never ship a guessable default: when the operator did not choose a
        # password, mint a random one and print it once (on managed installs
        # it also lands in the service log).
        password = secrets.token_urlsafe(12)
    user_id = auth.create_user(conn, BOOTSTRAP_ADMIN_USERNAME, password, is_admin=True)
    if generated:
        print(
            f"bootstrap admin created: username={BOOTSTRAP_ADMIN_USERNAME} "
            f"password={password} (random one-time password; set "
            f"{ADMIN_PASSWORD_ENV_VAR} or change it after first login)",
            flush=True,
        )
    else:
        print(
            f"bootstrap admin created: username={BOOTSTRAP_ADMIN_USERNAME} "
            f"(password from {ADMIN_PASSWORD_ENV_VAR}; change it after first login)",
            flush=True,
        )
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_setting(conn, user_id, key, default=""):
    if not user_id:
        return default
    row = conn.execute(
        "SELECT value FROM user_settings WHERE user_id = ? AND key = ?",
        (user_id, key),
    ).fetchone()
    if row and row["value"]:
        return row["value"]
    return default


def set_user_setting(conn, user_id, key, value):
    conn.execute(
        """
        INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?)
        ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value
        """,
        (user_id, key, str(value)),
    )


def get_effective_user_setting(conn, user_id, key, default=""):
    """User setting first, then the pre-multiuser global value in app_settings
    (legacy ui_theme/ui_mode keep working after the upgrade)."""
    value = get_user_setting(conn, user_id, key, "")
    if value:
        return value
    return get_setting(conn, key, default)


def row_to_dict(row):
    if row is None:
        return None
    result = dict(row)
    for key in ("milestones_json", "deliverables_json", "snapshot_json"):
        if key in result:
            result[key[:-5] if key.endswith("_json") else key] = json.loads(result.pop(key) or "[]")
    return result


def create_project(conn, data, user=None):
    if user is None:
        user = ensure_bootstrap_admin(conn)
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO projects
        (name, description, owner, user_id, start_date, end_date, status, timezone, report_provider,
         report_template, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["name"].strip(),
            data.get("description", "").strip(),
            user["username"],
            user["id"],
            data["start_date"],
            data.get("end_date") or None,
            data.get("status") or "active",
            data.get("timezone") or DEFAULT_TIMEZONE,
            data.get("report_provider") or REPORT_PROVIDER,
            data.get("report_template") or "",
            now,
            now,
        ),
    )
    project_id = cur.lastrowid
    conn.execute(
        "INSERT INTO project_plans (project_id, objectives, milestones_json, deliverables_json, version, updated_at) VALUES (?, '', '[]', '[]', 1, ?)",
        (project_id, now),
    )
    return project_id
