"""工作线: one flat level of long-running lines of work inside a project.

Workstreams follow the project's roles. Materials link to workstreams of
their own project, an account's TODOs link to workstreams of projects it can
write (one primary plus any related, each marked auto or manual), and weekly
snapshots keep a structured per-line record so the long-range view never has
to parse report Markdown. Health is derived deterministically.
"""

import json
import re
from datetime import date, timedelta

from .sharing import project_role, require_role
from .timeutil import current_week_key, get_zone, iso_now, parse_iso, utc_now, week_key_for
from .validation import ValidationError

WORKSTREAM_STATUSES = ("active", "paused", "done")
SNAPSHOT_STATUSES = ("advanced", "steady", "blocked")
LINK_SOURCES = ("auto", "manual")
MATRIX_WEEKS = 8
NAME_LIMIT = 60
SEED_NAME_LIMIT = 30


# ---------------------------------------------------------------- weeks


def previous_week_key(tz_name, weeks=1, now=None):
    return current_week_key(tz_name, now=(now or utc_now()) - timedelta(days=7 * weeks))


def recent_week_keys(tz_name, count=MATRIX_WEEKS, now=None):
    """Oldest first, ending with the current project week."""
    return [previous_week_key(tz_name, weeks, now) for weeks in range(count - 1, -1, -1)]


def local_today(tz_name):
    return utc_now().astimezone(get_zone(tz_name)).date()


# ---------------------------------------------------------------- workstreams


def _text(value, limit):
    return str(value or "").strip()[:limit]


def _status(value, default="active"):
    status = str(value or default).strip()
    if status not in WORKSTREAM_STATUSES:
        raise ValidationError("workstream status must be active, paused or done")
    return status


def _target_date(value):
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("workstream target date must be YYYY-MM-DD") from exc
    return value


def list_workstreams(conn, project_id):
    return conn.execute(
        "SELECT * FROM workstreams WHERE project_id = ? ORDER BY position, id", (project_id,)
    ).fetchall()


def get_workstream(conn, project_id, workstream_id):
    row = conn.execute(
        "SELECT * FROM workstreams WHERE id = ? AND project_id = ?", (workstream_id, project_id)
    ).fetchone()
    if not row:
        raise LookupError("workstream not found")
    return row


def resolve_workstream(conn, project_id, ref):
    """A workstream of the project by ID or exact name."""
    ref = str(ref or "").strip()
    if not ref:
        raise ValidationError("workstream is required")
    rows = list_workstreams(conn, project_id)
    row = next((r for r in rows if str(r["id"]) == ref), None) or next((r for r in rows if r["name"] == ref), None)
    if not row:
        raise LookupError(f"workstream not found: {ref} (see `project workstreams list`)")
    return row


def _assert_unique_name(conn, project_id, name, exclude_id=None):
    row = conn.execute(
        "SELECT id FROM workstreams WHERE project_id = ? AND name = ? AND id != ?",
        (project_id, name, exclude_id or 0),
    ).fetchone()
    if row:
        raise ValidationError(f"workstream name already exists: {name}")


def create_workstream(conn, project_id, payload):
    name = _text(payload.get("name"), NAME_LIMIT)
    if not name:
        raise ValidationError("workstream name is required")
    _assert_unique_name(conn, project_id, name)
    now = iso_now()
    position = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 FROM workstreams WHERE project_id = ?", (project_id,)
    ).fetchone()[0]
    cur = conn.execute(
        """
        INSERT INTO workstreams (project_id, name, goal, owner_label, status, target_date, position, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            name,
            _text(payload.get("goal"), 2000),
            _text(payload.get("owner_label"), 60),
            _status(payload.get("status")),
            _target_date(payload.get("target_date")),
            position,
            now,
            now,
        ),
    )
    return cur.lastrowid


def update_workstream(conn, project_id, workstream_id, payload):
    row = get_workstream(conn, project_id, workstream_id)
    name = _text(payload.get("name", row["name"]), NAME_LIMIT)
    if not name:
        raise ValidationError("workstream name is required")
    _assert_unique_name(conn, project_id, name, workstream_id)
    values = (
        name,
        _text(payload.get("goal", row["goal"]), 2000),
        _text(payload.get("owner_label", row["owner_label"]), 60),
        _status(payload.get("status", row["status"])),
        _target_date(payload.get("target_date", row["target_date"])),
    )
    if values == (row["name"], row["goal"], row["owner_label"], row["status"], row["target_date"]):
        return
    conn.execute(
        "UPDATE workstreams SET name = ?, goal = ?, owner_label = ?, status = ?, target_date = ?, updated_at = ? WHERE id = ?",
        (*values, iso_now(), workstream_id),
    )


def delete_workstream(conn, project_id, workstream_id):
    get_workstream(conn, project_id, workstream_id)
    conn.execute("DELETE FROM workstreams WHERE id = ?", (workstream_id,))
    # milestones keep their place in the plan but lose the dangling link
    plan = conn.execute("SELECT milestones_json FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    if plan:
        milestones = json.loads(plan["milestones_json"] or "[]")
        changed = False
        for item in milestones:
            if isinstance(item, dict) and str(item.get("workstream_id") or "") == str(workstream_id):
                item.pop("workstream_id", None)
                changed = True
        if changed:
            conn.execute(
                "UPDATE project_plans SET milestones_json = ? WHERE project_id = ?",
                (json.dumps(milestones), project_id),
            )


def reorder_workstreams(conn, project_id, ids):
    if not isinstance(ids, list):
        raise ValidationError("workstream order must be a list of ids")
    existing = {row["id"] for row in list_workstreams(conn, project_id)}
    try:
        order = [int(item) for item in ids]
    except (TypeError, ValueError) as exc:
        raise ValidationError("invalid workstream id") from exc
    if set(order) != existing or len(order) != len(existing):
        raise ValidationError("workstream order must list every workstream of the project once")
    for index, workstream_id in enumerate(order):
        conn.execute("UPDATE workstreams SET position = ? WHERE id = ?", (index, workstream_id))


_LIST_MARKER = re.compile(r"^\s*(?:\d+[.、)）]|[（(]\d+[)）]|[-*•·])\s*")


def parse_objective_lines(text):
    """(name, goal) per numbered or bulleted objective line; the name is the
    first clause, the goal the whole line."""
    result = []
    for line in (text or "").splitlines():
        if not _LIST_MARKER.match(line):
            continue
        goal = _LIST_MARKER.sub("", line, count=1).strip()
        if not goal:
            continue
        name = re.split(r"[，,：:；;。]", goal, maxsplit=1)[0].strip()[:SEED_NAME_LIMIT] or goal[:SEED_NAME_LIMIT]
        result.append((name, goal))
    return result


def seed_from_objectives(conn, project_id):
    plan = conn.execute("SELECT objectives FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    lines = parse_objective_lines(plan["objectives"] if plan else "")
    if not lines:
        raise ValidationError("项目目标里没有编号或列表行，无法生成工作线")
    existing = {row["name"] for row in list_workstreams(conn, project_id)}
    created = []
    for name, goal in lines:
        if name in existing:
            continue
        existing.add(name)
        created.append(create_workstream(conn, project_id, {"name": name, "goal": goal}))
    return created


# ---------------------------------------------------------------- links


def _link_ids(primary, related):
    def as_id(value):
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("invalid workstream id") from exc

    primary_id = as_id(primary) if primary not in (None, "", 0, "0") else None
    related_ids = []
    for value in related or []:
        workstream_id = as_id(value)
        if workstream_id != primary_id and workstream_id not in related_ids:
            related_ids.append(workstream_id)
    if primary_id is None and related_ids:
        raise ValidationError("related workstreams need a primary workstream")
    return primary_id, related_ids


def set_material_links(conn, project_id, material_id, primary=None, related=(), source="manual"):
    """Replace a material's links. Every workstream must belong to the
    material's project."""
    if not conn.execute("SELECT 1 FROM materials WHERE id = ? AND project_id = ?", (material_id, project_id)).fetchone():
        raise LookupError("material not found")
    primary_id, related_ids = _link_ids(primary, related)
    for workstream_id in ([primary_id] if primary_id else []) + related_ids:
        if not conn.execute("SELECT 1 FROM workstreams WHERE id = ? AND project_id = ?", (workstream_id, project_id)).fetchone():
            raise ValidationError("workstream does not belong to this project")
    conn.execute("DELETE FROM material_workstreams WHERE material_id = ?", (material_id,))
    now = iso_now()
    for workstream_id in ([primary_id] if primary_id else []) + related_ids:
        conn.execute(
            "INSERT INTO material_workstreams (material_id, workstream_id, is_primary, source, created_at) VALUES (?, ?, ?, ?, ?)",
            (material_id, workstream_id, int(workstream_id == primary_id), source, now),
        )


def material_has_manual_links(conn, material_id):
    return bool(conn.execute(
        "SELECT 1 FROM material_workstreams WHERE material_id = ? AND source = 'manual'", (material_id,)
    ).fetchone())


def auto_link_material(conn, project_id, material_id, workstream_id):
    """Agent suggestion: applied only to an unassigned material and only to an
    active workstream of its project; unknown ids are ignored."""
    try:
        workstream_id = int(workstream_id)
    except (TypeError, ValueError):
        return False
    if conn.execute("SELECT 1 FROM material_workstreams WHERE material_id = ?", (material_id,)).fetchone():
        return False
    if not conn.execute(
        "SELECT 1 FROM workstreams WHERE id = ? AND project_id = ? AND status = 'active'", (workstream_id, project_id)
    ).fetchone():
        return False
    set_material_links(conn, project_id, material_id, workstream_id, (), source="auto")
    return True


def set_todo_links(conn, user_id, todo_id, primary=None, related=()):
    """Replace a TODO's links; the TODO must be the caller's and every
    workstream must sit in a project the caller can write."""
    if not conn.execute("SELECT 1 FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id)).fetchone():
        raise ValidationError("TODO not found")
    primary_id, related_ids = _link_ids(primary, related)
    for workstream_id in ([primary_id] if primary_id else []) + related_ids:
        row = conn.execute("SELECT project_id FROM workstreams WHERE id = ?", (workstream_id,)).fetchone()
        role = project_role(conn, row["project_id"], user_id) if row else None
        if role is None:
            raise ValidationError("workstream not found")
        require_role(role, "write")
    conn.execute("DELETE FROM todo_workstreams WHERE todo_id = ?", (todo_id,))
    now = iso_now()
    for workstream_id in ([primary_id] if primary_id else []) + related_ids:
        conn.execute(
            "INSERT INTO todo_workstreams (todo_id, workstream_id, is_primary, source, created_at) VALUES (?, ?, ?, 'manual', ?)",
            (todo_id, workstream_id, int(workstream_id == primary_id), now),
        )


def copy_todo_links_to_material(conn, todo_id, project_id, material_id):
    links = conn.execute(
        """
        SELECT tw.workstream_id, tw.is_primary FROM todo_workstreams tw
        JOIN workstreams w ON w.id = tw.workstream_id
        WHERE tw.todo_id = ? AND w.project_id = ?
        ORDER BY tw.is_primary DESC
        """,
        (todo_id, project_id),
    ).fetchall()
    if not links:
        return
    primary = next((r["workstream_id"] for r in links if r["is_primary"]), links[0]["workstream_id"])
    related = [r["workstream_id"] for r in links if r["workstream_id"] != primary]
    set_material_links(conn, project_id, material_id, primary, related, source="manual")


def material_links_map(conn, project_id):
    """{material_id: {"primary": id|None, "related": [ids], "source": ...}}"""
    result = {}
    for row in conn.execute(
        """
        SELECT mw.material_id, mw.workstream_id, mw.is_primary, mw.source
        FROM material_workstreams mw JOIN materials m ON m.id = mw.material_id
        WHERE m.project_id = ? ORDER BY mw.is_primary DESC, mw.workstream_id
        """,
        (project_id,),
    ):
        entry = result.setdefault(row["material_id"], {"primary": None, "related": [], "source": row["source"]})
        if row["is_primary"]:
            entry["primary"] = row["workstream_id"]
        else:
            entry["related"].append(row["workstream_id"])
    return result


def todo_links_map(conn, user_id):
    """{todo_id: {"primary": {...}|None, "related": [{...}]}} with workstream
    and project names, limited to workstreams the account can still read."""
    result = {}
    for row in conn.execute(
        """
        SELECT tw.todo_id, tw.workstream_id, tw.is_primary, w.name, w.project_id, p.name AS project_name
        FROM todo_workstreams tw
        JOIN todos t ON t.id = tw.todo_id
        JOIN workstreams w ON w.id = tw.workstream_id
        JOIN projects p ON p.id = w.project_id
        WHERE t.user_id = ?
        ORDER BY tw.is_primary DESC, tw.workstream_id
        """,
        (user_id,),
    ):
        if project_role(conn, row["project_id"], user_id) is None:
            continue
        item = {"id": row["workstream_id"], "name": row["name"], "project_id": row["project_id"], "project_name": row["project_name"]}
        entry = result.setdefault(row["todo_id"], {"primary": None, "related": []})
        if row["is_primary"]:
            entry["primary"] = item
        else:
            entry["related"].append(item)
    return result


def todo_workstream_options(conn, user_id):
    """Workstreams the account may link its TODOs to, grouped by project."""
    from .sharing import ACCESSIBLE_PROJECTS_SQL

    groups = []
    for project in conn.execute(
        f"SELECT id, name FROM projects WHERE id IN {ACCESSIBLE_PROJECTS_SQL} ORDER BY name",
        (user_id, user_id),
    ).fetchall():
        role = project_role(conn, project["id"], user_id)
        if role not in ("owner", "manage", "write"):
            continue
        items = [
            {"id": row["id"], "name": row["name"], "status": row["status"]}
            for row in list_workstreams(conn, project["id"])
            if row["status"] != "done"
        ]
        if items:
            groups.append({"project_id": project["id"], "project_name": project["name"], "workstreams": items})
    return groups


# ---------------------------------------------------------------- snapshots


def upsert_snapshot(conn, workstream_id, week_key, status, summary, next_step="", source="generated", overwrite_manual=False):
    status = status if status in SNAPSHOT_STATUSES else "steady"
    existing = conn.execute(
        "SELECT source FROM workstream_weekly WHERE workstream_id = ? AND week_key = ?", (workstream_id, week_key)
    ).fetchone()
    if existing and existing["source"] == "manual" and not overwrite_manual:
        return False
    now = iso_now()
    conn.execute(
        """
        INSERT INTO workstream_weekly (workstream_id, week_key, status, summary, next_step, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(workstream_id, week_key) DO UPDATE SET status = excluded.status, summary = excluded.summary,
            next_step = excluded.next_step, source = excluded.source, updated_at = excluded.updated_at
        """,
        (workstream_id, week_key, status, _text(summary, 300), _text(next_step, 300), source, now, now),
    )
    return True


def save_manual_snapshot(conn, project_id, workstream_id, payload):
    get_workstream(conn, project_id, workstream_id)
    week_key = str(payload.get("week_key") or "").strip()
    if not re.fullmatch(r"\d{4}-W\d{2}", week_key):
        raise ValidationError("week_key must look like 2026-W47")
    status = str(payload.get("status") or "steady")
    if status not in SNAPSHOT_STATUSES:
        raise ValidationError("snapshot status must be advanced, steady or blocked")
    summary = _text(payload.get("summary"), 300)
    if not summary:
        raise ValidationError("snapshot summary is required")
    upsert_snapshot(conn, workstream_id, week_key, status, summary, payload.get("next_step"), source="manual", overwrite_manual=True)


def week_materials_by_workstream(conn, project_id, tz_name, week_key, per_workstream=15):
    """{workstream_id: [{"id", "filename", "summary", "primary"}]} for
    materials created in the week, primary links first."""
    result = {}
    for row in conn.execute(
        """
        SELECT m.id, m.filename, m.summary, m.extracted_text, m.source_type, m.created_at, mw.workstream_id, mw.is_primary
        FROM material_workstreams mw JOIN materials m ON m.id = mw.material_id
        WHERE m.project_id = ? ORDER BY mw.is_primary DESC, m.id DESC
        """,
        (project_id,),
    ):
        created = parse_iso(row["created_at"])
        if not created or week_key_for(created, tz_name) != week_key:
            continue
        items = result.setdefault(row["workstream_id"], [])
        if len(items) < per_workstream:
            summary = row["summary"] or ((row["extracted_text"] or "")[:300] if row["source_type"] == "manual" else "")
            items.append({"id": row["id"], "filename": row["filename"], "summary": (summary or "")[:300], "primary": bool(row["is_primary"])})
    return result


# ---------------------------------------------------------------- health


def _plan_milestones(conn, project_id):
    plan = conn.execute("SELECT milestones_json FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    items = json.loads(plan["milestones_json"] or "[]") if plan else []
    return [item for item in items if isinstance(item, dict)]


def workstream_conditions(conn, project_id, tz_name):
    """Per workstream: overdue / stale flags with reasons, from deterministic
    rules over dates, milestones and linked material activity."""
    today = local_today(tz_name).isoformat()
    window = {current_week_key(tz_name), previous_week_key(tz_name)}
    previous = previous_week_key(tz_name)
    milestones = _plan_milestones(conn, project_id)
    recent = {}
    for row in conn.execute(
        """
        SELECT mw.workstream_id, m.created_at FROM material_workstreams mw
        JOIN materials m ON m.id = mw.material_id WHERE m.project_id = ?
        """,
        (project_id,),
    ):
        created = parse_iso(row["created_at"])
        if created and week_key_for(created, tz_name) in window:
            recent[row["workstream_id"]] = recent.get(row["workstream_id"], 0) + 1
    result = {}
    for row in list_workstreams(conn, project_id):
        overdue, stale = [], False
        if row["status"] == "active":
            if row["target_date"] and row["target_date"] < today:
                overdue.append(f"目标日期 {row['target_date']} 已过")
            for item in milestones:
                if (
                    str(item.get("workstream_id") or "") == str(row["id"])
                    and item.get("target_date") and item["target_date"] < today
                    and item.get("status") != "complete"
                ):
                    overdue.append(f"里程碑「{item.get('title', '')}」逾期（{item['target_date']}）")
            created = parse_iso(row["created_at"])
            older = bool(created and week_key_for(created, tz_name) < previous)
            stale = older and not recent.get(row["id"])
        result[row["id"]] = {"overdue": overdue, "stale": stale, "recent_materials": recent.get(row["id"], 0)}
    return result


def health_of(row, condition):
    if row["status"] == "done":
        return "complete"
    if row["status"] == "paused":
        return "paused"
    if condition["overdue"]:
        return "blocked"
    if condition["stale"]:
        return "at risk"
    return "on track"


# ---------------------------------------------------------------- payloads


def _item(row, condition):
    return {
        "id": row["id"],
        "name": row["name"],
        "goal": row["goal"],
        "owner_label": row["owner_label"],
        "status": row["status"],
        "target_date": row["target_date"],
        "position": row["position"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "health": health_of(row, condition),
        "overdue_reasons": condition["overdue"],
        "recent_materials": condition["recent_materials"],
    }


def workstream_overview(conn, project_id, tz_name, weeks=MATRIX_WEEKS):
    """The matrix payload: workstreams with health, per-week snapshot cells
    and current-week linked material counts, plus the unassigned count."""
    rows = list_workstreams(conn, project_id)
    week_keys = recent_week_keys(tz_name, weeks)
    current = week_keys[-1]
    conditions = workstream_conditions(conn, project_id, tz_name)
    snapshots = {}
    if rows:
        for snap in conn.execute(
            f"""
            SELECT workstream_id, week_key, status, summary, next_step, source, updated_at
            FROM workstream_weekly
            WHERE workstream_id IN ({",".join("?" for _ in rows)}) AND week_key >= ?
            """,
            (*[r["id"] for r in rows], week_keys[0]),
        ):
            snapshots.setdefault(snap["workstream_id"], {})[snap["week_key"]] = dict(snap)
    counts, totals, last_at = {}, {}, {}
    for row in conn.execute(
        """
        SELECT mw.workstream_id, m.created_at FROM material_workstreams mw
        JOIN materials m ON m.id = mw.material_id WHERE m.project_id = ?
        """,
        (project_id,),
    ):
        totals[row["workstream_id"]] = totals.get(row["workstream_id"], 0) + 1
        created = parse_iso(row["created_at"])
        if created:
            week = week_key_for(created, tz_name)
            counts.setdefault(row["workstream_id"], {})
            counts[row["workstream_id"]][week] = counts[row["workstream_id"]].get(week, 0) + 1
            if row["created_at"] > last_at.get(row["workstream_id"], ""):
                last_at[row["workstream_id"]] = row["created_at"]
    milestones = _plan_milestones(conn, project_id)
    items = []
    for row in rows:
        item = _item(row, conditions[row["id"]])
        item["material_total"] = totals.get(row["id"], 0)
        item["last_material_at"] = last_at.get(row["id"], "")
        item["milestones"] = [m for m in milestones if str(m.get("workstream_id") or "") == str(row["id"])]
        item["cells"] = [
            {
                "week_key": week,
                "snapshot": snapshots.get(row["id"], {}).get(week),
                "materials": counts.get(row["id"], {}).get(week, 0),
            }
            for week in week_keys
        ]
        items.append(item)
    unassigned = conn.execute(
        """
        SELECT COUNT(*) FROM materials m WHERE m.project_id = ?
        AND NOT EXISTS (SELECT 1 FROM material_workstreams mw WHERE mw.material_id = m.id)
        """,
        (project_id,),
    ).fetchone()[0]
    return {"weeks": week_keys, "current_week": current, "workstreams": items, "unassigned_materials": unassigned}


def workstream_detail(conn, project_id, workstream_id, tz_name, user_id, material_limit=200):
    row = get_workstream(conn, project_id, workstream_id)
    item = _item(row, workstream_conditions(conn, project_id, tz_name)[row["id"]])
    item["milestones"] = [m for m in _plan_milestones(conn, project_id) if str(m.get("workstream_id") or "") == str(row["id"])]
    item["snapshots"] = [
        dict(r)
        for r in conn.execute(
            "SELECT week_key, status, summary, next_step, source, updated_at FROM workstream_weekly WHERE workstream_id = ? ORDER BY week_key DESC",
            (workstream_id,),
        )
    ]
    item["materials"] = [
        {**dict(r), "is_primary": bool(r["is_primary"])}
        for r in conn.execute(
            """
            SELECT m.id, m.filename, m.source_type, m.summary, m.created_at, mw.is_primary, mw.source AS link_source
            FROM material_workstreams mw JOIN materials m ON m.id = mw.material_id
            WHERE mw.workstream_id = ? ORDER BY m.id DESC LIMIT ?
            """,
            (workstream_id, material_limit),
        )
    ]
    item["todos"] = [
        dict(r)
        for r in conn.execute(
            """
            SELECT t.id, t.title, t.status, t.updated_at, tw.is_primary FROM todo_workstreams tw
            JOIN todos t ON t.id = tw.todo_id
            WHERE tw.workstream_id = ? AND t.user_id = ? AND t.status != 'closed'
            ORDER BY t.updated_at DESC
            """,
            (workstream_id, user_id),
        )
    ]
    return item


def workstreams_for_prompt(conn, project_id, include_inactive=False):
    return [
        {"id": row["id"], "name": row["name"], "goal": row["goal"][:300]}
        for row in list_workstreams(conn, project_id)
        if include_inactive or row["status"] == "active"
    ]
