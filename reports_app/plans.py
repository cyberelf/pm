"""项目计划: objectives, milestones and deliverables of a project.

The plan lives in `project_plans` as JSON lists and every save appends a
`plan_versions` snapshot. Milestones carry a stable integer `id` and an
optional `workstream_id`: those linked to a workstream are managed from that
workstream, the rest are project-level milestones edited in the 项目计划
panel of the 工作线 tab together with objectives and deliverables.
"""

import json
from datetime import date

from .timeutil import iso_now
from .validation import ValidationError

PLAN_STATUSES = ("planned", "in_progress", "blocked", "complete")
TITLE_LIMIT = 200


def load_plan(conn, project_id):
    row = conn.execute("SELECT * FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    if not row:
        return {"objectives": "", "milestones": [], "deliverables": [], "version": 0, "updated_at": None}
    milestones = [m for m in json.loads(row["milestones_json"] or "[]") if isinstance(m, dict)]
    for item in milestones:
        value = item.get("workstream_id")
        if isinstance(value, str):
            if value.strip().isdigit():
                item["workstream_id"] = int(value)
            else:
                item.pop("workstream_id", None)
    return {
        "objectives": row["objectives"],
        "milestones": milestones,
        "deliverables": [d for d in json.loads(row["deliverables_json"] or "[]") if isinstance(d, dict)],
        "version": row["version"],
        "updated_at": row["updated_at"],
    }


def assign_milestone_ids(milestones):
    """Give every milestone without a valid id the next free one, in place."""
    used = set()
    for item in milestones:
        value = item.get("id")
        if isinstance(value, int) and value > 0 and value not in used:
            used.add(value)
        else:
            item.pop("id", None)
    next_id = max(used, default=0) + 1
    for item in milestones:
        if "id" not in item:
            item["id"] = next_id
            next_id += 1
    return milestones


def save_plan(conn, project_id, payload):
    """Replace the whole plan (objectives, milestones, deliverables)."""
    now = iso_now()
    current = conn.execute("SELECT version FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    version = (current["version"] if current else 0) + 1
    milestones = assign_milestone_ids([dict(m) for m in payload.get("milestones") or [] if isinstance(m, dict)])
    deliverables = [dict(d) for d in payload.get("deliverables") or [] if isinstance(d, dict)]
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


def save_plan_payload(conn, project_id, payload):
    """PUT /plan. With `project_milestones` only the project-level
    milestones are replaced and workstream milestones stay as they are; a
    payload with `milestones` replaces the whole list (older clients)."""
    if "project_milestones" not in payload:
        save_plan(conn, project_id, payload)
        return
    plan = load_plan(conn, project_id)
    incoming = [dict(m) for m in payload.get("project_milestones") or [] if isinstance(m, dict)]
    incoming_ids = {m.get("id") for m in incoming if isinstance(m.get("id"), int)}
    kept = [m for m in plan["milestones"] if m.get("workstream_id") and m.get("id") not in incoming_ids]
    save_plan(conn, project_id, {
        "objectives": payload.get("objectives", plan["objectives"]),
        "milestones": kept + [_clean_link(conn, project_id, m) for m in incoming],
        "deliverables": payload.get("deliverables", plan["deliverables"]),
    })


def _clean_link(conn, project_id, item):
    value = item.get("workstream_id")
    if value in (None, "", 0, "0"):
        item.pop("workstream_id", None)
        return item
    item["workstream_id"] = _workstream_ref(conn, project_id, value)
    return item


def _workstream_ref(conn, project_id, value):
    try:
        workstream_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("invalid workstream id") from exc
    if not conn.execute("SELECT 1 FROM workstreams WHERE id = ? AND project_id = ?", (workstream_id, project_id)).fetchone():
        raise ValidationError("workstream does not belong to this project")
    return workstream_id


def _milestone_fields(payload, current=None):
    current = current or {}
    title = str(payload.get("title", current.get("title", "")) or "").strip()[:TITLE_LIMIT]
    if not title:
        raise ValidationError("milestone title is required")
    status = str(payload.get("status", current.get("status")) or "planned")
    if status not in PLAN_STATUSES:
        raise ValidationError("milestone status must be planned, in_progress, blocked or complete")
    target = str(payload.get("target_date", current.get("target_date", "")) or "").strip()
    if target:
        try:
            date.fromisoformat(target)
        except ValueError as exc:
            raise ValidationError("milestone date must be YYYY-MM-DD") from exc
    owner = str(payload.get("owner_label", current.get("owner_label", "")) or "").strip()[:60]
    return {"title": title, "owner_label": owner, "target_date": target, "status": status}


def workstream_milestones(milestones, workstream_id):
    return [m for m in milestones if str(m.get("workstream_id") or "") == str(workstream_id)]


def create_milestone(conn, project_id, workstream_id, payload):
    plan = load_plan(conn, project_id)
    milestones = assign_milestone_ids(plan["milestones"])
    item = {**_milestone_fields(payload), "id": max((m["id"] for m in milestones), default=0) + 1}
    if workstream_id:
        item["workstream_id"] = _workstream_ref(conn, project_id, workstream_id)
    save_plan(conn, project_id, {**plan, "milestones": milestones + [item]})
    return item["id"]


def _find(milestones, workstream_id, milestone_id):
    for item in milestones:
        if item.get("id") == milestone_id and str(item.get("workstream_id") or "") == str(workstream_id or ""):
            return item
    raise LookupError("milestone not found")


def update_milestone(conn, project_id, workstream_id, milestone_id, payload):
    """Edit a workstream's milestone; `workstream_id` in the payload moves it
    to another workstream ("" makes it project-level)."""
    plan = load_plan(conn, project_id)
    milestones = assign_milestone_ids(plan["milestones"])
    item = _find(milestones, workstream_id, milestone_id)
    item.update(_milestone_fields(payload, item))
    if "workstream_id" in payload:
        item["workstream_id"] = payload.get("workstream_id")
        _clean_link(conn, project_id, item)
    save_plan(conn, project_id, {**plan, "milestones": milestones})


def delete_milestone(conn, project_id, workstream_id, milestone_id):
    plan = load_plan(conn, project_id)
    milestones = assign_milestone_ids(plan["milestones"])
    item = _find(milestones, workstream_id, milestone_id)
    save_plan(conn, project_id, {**plan, "milestones": [m for m in milestones if m is not item]})


def ensure_milestone_ids(conn):
    """Migration: give stored milestones stable ids without a new version."""
    for row in conn.execute("SELECT project_id, milestones_json FROM project_plans").fetchall():
        items = [m for m in json.loads(row["milestones_json"] or "[]") if isinstance(m, dict)]
        if all(isinstance(m.get("id"), int) for m in items) and len({m.get("id") for m in items}) == len(items):
            continue
        conn.execute(
            "UPDATE project_plans SET milestones_json = ? WHERE project_id = ?",
            (json.dumps(assign_milestone_ids(items)), row["project_id"]),
        )
