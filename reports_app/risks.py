from .timeutil import current_week_key, iso_now


def upsert_warning(conn, project_id, week_key, rule, severity, title, details="", source_ref=""):
    now = iso_now()
    conn.execute(
        """
        INSERT INTO risk_warnings
        (project_id, week_key, rule, severity, title, details, status, source_ref, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
        ON CONFLICT(project_id, week_key, rule, source_ref)
        DO UPDATE SET severity = excluded.severity, title = excluded.title, details = excluded.details,
                      status = 'active', updated_at = excluded.updated_at
        """,
        (project_id, week_key, rule, severity, title, details, source_ref, now, now),
    )


def evaluate_risks(conn, project_id):
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    week_key = current_week_key(project["timezone"])
    conn.execute(
        """
        UPDATE risk_warnings
        SET status = 'resolved', updated_at = ?
        WHERE project_id = ? AND week_key = ? AND status = 'active'
          AND rule IN (
            'missing_update',
            'overdue_milestone',
            'blocked_outcome',
            'generation_failed',
            'github_unavailable',
            'material_extraction_failed'
          )
        """,
        (iso_now(), project_id, week_key),
    )
    update = conn.execute(
        "SELECT * FROM weekly_updates WHERE project_id = ? AND week_key = ?", (project_id, week_key)
    ).fetchone()
    materials_changed = conn.execute("SELECT COUNT(*) AS n FROM materials WHERE project_id = ?", (project_id,)).fetchone()["n"]
    repos_active = conn.execute(
        "SELECT COUNT(*) AS n FROM github_repos WHERE project_id = ? AND status = 'connected'", (project_id,)
    ).fetchone()["n"]
    if not update and materials_changed == 0 and repos_active == 0:
        upsert_warning(conn, project_id, week_key, "missing_update", "medium", "No current-period update or source activity")

    plan = conn.execute("SELECT milestones_json FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    if plan:
        import json
        from datetime import date

        today = date.today().isoformat()
        for item in json.loads(plan["milestones_json"] or "[]"):
            if item.get("target_date") and item.get("target_date") < today and item.get("status") != "complete":
                upsert_warning(
                    conn,
                    project_id,
                    week_key,
                    "overdue_milestone",
                    "high",
                    "Milestone is overdue",
                    item.get("title", ""),
                    item.get("title", ""),
                )
    for row in conn.execute(
        "SELECT id, title FROM weekly_outcomes WHERE project_id = ? AND week_key = ? AND status = 'blocked'",
        (project_id, week_key),
    ):
        upsert_warning(conn, project_id, week_key, "blocked_outcome", "high", "Weekly outcome is blocked", row["title"], str(row["id"]))


def progress_status(conn, project_id):
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    week_key = current_week_key(project["timezone"])
    active = conn.execute(
        """
        SELECT severity FROM risk_warnings
        WHERE project_id = ? AND week_key = ? AND status = 'active'
          AND rule IN ('missing_update', 'overdue_milestone', 'blocked_outcome')
        """,
        (project_id, week_key),
    ).fetchall()
    if any(row["severity"] == "high" for row in active):
        return "blocked"
    if active:
        return "at risk"
    done = conn.execute(
        "SELECT COUNT(*) AS n FROM weekly_outcomes WHERE project_id = ? AND week_key = ? AND status = 'complete'",
        (project_id, week_key),
    ).fetchone()["n"]
    total = conn.execute(
        "SELECT COUNT(*) AS n FROM weekly_outcomes WHERE project_id = ? AND week_key = ?",
        (project_id, week_key),
    ).fetchone()["n"]
    if total and done == total:
        return "complete"
    return "on track"
