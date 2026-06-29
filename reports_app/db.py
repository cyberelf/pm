import json
import sqlite3
from pathlib import Path

from .config import DATA_DIR, DB_PATH, DEFAULT_SYSTEM_PROMPT, DEFAULT_TIMEZONE, WORKSPACE_USER
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
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS github_repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    repo TEXT NOT NULL,
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
"""


def connect(path: Path = DB_PATH):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path = DB_PATH):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        migrate_schema(conn)
    return path


def migrate_schema(conn):
    material_columns = {row["name"] for row in conn.execute("PRAGMA table_info(materials)")}
    if "source_type" not in material_columns:
        conn.execute("ALTER TABLE materials ADD COLUMN source_type TEXT NOT NULL DEFAULT 'upload'")
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(github_repos)")}
    if "notes" not in columns:
        conn.execute("ALTER TABLE github_repos ADD COLUMN notes TEXT NOT NULL DEFAULT ''")
    conn.execute(
        """
        DELETE FROM github_repos
        WHERE id NOT IN (
            SELECT MIN(id) FROM github_repos GROUP BY project_id, repo
        )
        """
    )
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_github_repos_project_repo ON github_repos(project_id, repo)")


def row_to_dict(row):
    if row is None:
        return None
    result = dict(row)
    for key in ("milestones_json", "deliverables_json", "snapshot_json"):
        if key in result:
            result[key[:-5] if key.endswith("_json") else key] = json.loads(result.pop(key) or "[]")
    return result


def create_project(conn, data):
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO projects
        (name, description, owner, start_date, end_date, status, timezone, report_provider,
         system_prompt, report_template, manual_background, manual_objectives, manual_constraints,
         created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["name"].strip(),
            data.get("description", "").strip(),
            WORKSPACE_USER,
            data["start_date"],
            data.get("end_date") or None,
            data.get("status") or "active",
            data.get("timezone") or DEFAULT_TIMEZONE,
            data.get("report_provider") or "codex",
            data.get("system_prompt") or DEFAULT_SYSTEM_PROMPT,
            data.get("report_template") or "",
            data.get("manual_background") or "",
            data.get("manual_objectives") or "",
            data.get("manual_constraints") or "",
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
