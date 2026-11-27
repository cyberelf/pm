"""工作线: long-running lines of work inside a project.

A project has top-level workstreams and, one level down, 子工作线 (sub-
workstreams, `parent_id`); deeper nesting is rejected. Names stay unique per
project so a name always identifies one line. A parent's health rolls up
from its active children, and its activity counts theirs, so classifying
material to the most specific line never makes the parent look stale.

Workstreams follow the project's roles. Materials link to workstreams of
their own project, an account's TODOs link to workstreams of projects it can
upload materials to (one primary plus any related, each marked auto or manual), and weekly
snapshots keep a structured per-line record so the long-range view never has
to parse report Markdown. Health is derived deterministically.
"""

import json
import re
from datetime import date, timedelta

from .members import resolve_owner
from .sharing import project_role, require_role, role_at_least
from .timeutil import current_week_key, get_zone, iso_now, parse_iso, utc_now, week_key_for
from .validation import ValidationError

WORKSTREAM_STATUSES = ("active", "paused", "done")
SNAPSHOT_STATUSES = ("advanced", "steady", "blocked")
LINK_SOURCES = ("auto", "manual")
ITEM_STATUSES = ("open", "done")
MATRIX_WEEKS = 8
TIMELINE_FUTURE_MIN = 4
TIMELINE_FUTURE_MAX = 26
ITEM_TITLE_LIMIT = 200
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


def week_monday(week_key):
    year, week = week_key.split("-W")
    return date.fromisocalendar(int(year), int(week), 1)


def assert_current_week(tz_name, week_key):
    """Past weeks are locked: only the current week takes new snapshots."""
    if week_key != current_week_key(tz_name):
        raise ValidationError("过去的周已锁定，只能记录本周进展")


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


def tree_order(rows):
    """Top-level workstreams by position, each followed by its children."""
    ids = {row["id"] for row in rows}
    children = {}
    for row in rows:
        if row["parent_id"] in ids:
            children.setdefault(row["parent_id"], []).append(row)
    ordered = []
    for row in rows:
        if row["parent_id"] not in ids:
            ordered.append(row)
            ordered += children.get(row["id"], [])
    return ordered


def list_workstreams(conn, project_id):
    """Workstreams in display order (tree order)."""
    return tree_order(conn.execute(
        "SELECT * FROM workstreams WHERE project_id = ? ORDER BY position, id", (project_id,)
    ).fetchall())


def workstream_paths(rows):
    """{id: "父 / 子"} display paths."""
    names = {row["id"]: row["name"] for row in rows}
    return {
        row["id"]: f"{names[row['parent_id']]} / {row['name']}" if row["parent_id"] in names else row["name"]
        for row in rows
    }


def _parent_id(conn, project_id, value, workstream_id=None):
    """Validate a parent: same project, itself top-level, not the line
    itself, and the line must not have children of its own."""
    if value in (None, "", 0, "0"):
        return None
    try:
        parent_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("invalid parent workstream id") from exc
    if parent_id == workstream_id:
        raise ValidationError("a workstream cannot be its own parent")
    parent = conn.execute(
        "SELECT parent_id FROM workstreams WHERE id = ? AND project_id = ?", (parent_id, project_id)
    ).fetchone()
    if not parent:
        raise ValidationError("parent workstream does not belong to this project")
    if parent["parent_id"]:
        raise ValidationError("子工作线下不能再建子工作线（最多两级）")
    if workstream_id and conn.execute("SELECT 1 FROM workstreams WHERE parent_id = ?", (workstream_id,)).fetchone():
        raise ValidationError("这条工作线有子工作线，不能再挂到其他工作线下")
    return parent_id


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
    owner_member_id, owner_label = resolve_owner(conn, project_id, payload)
    cur = conn.execute(
        """
        INSERT INTO workstreams (project_id, parent_id, name, goal, owner_member_id, owner_label, status, target_date, position, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            _parent_id(conn, project_id, payload.get("parent_id")),
            name,
            _text(payload.get("goal"), 2000),
            owner_member_id,
            owner_label,
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
    owner_member_id, owner_label = resolve_owner(conn, project_id, payload, (row["owner_member_id"], row["owner_label"]))
    values = (
        name,
        _text(payload.get("goal", row["goal"]), 2000),
        owner_member_id,
        owner_label,
        _status(payload.get("status", row["status"])),
        _target_date(payload.get("target_date", row["target_date"])),
        _parent_id(conn, project_id, payload["parent_id"], workstream_id) if "parent_id" in payload else row["parent_id"],
    )
    if values == (row["name"], row["goal"], row["owner_member_id"], row["owner_label"], row["status"], row["target_date"], row["parent_id"]):
        return
    conn.execute(
        "UPDATE workstreams SET name = ?, goal = ?, owner_member_id = ?, owner_label = ?, status = ?, target_date = ?, parent_id = ?, updated_at = ? WHERE id = ?",
        (*values, iso_now(), workstream_id),
    )
    if values[6] != row["parent_id"]:
        # a line that changes level goes last among its new siblings
        conn.execute(
            "UPDATE workstreams SET position = (SELECT COALESCE(MAX(position), -1) + 1 FROM workstreams WHERE project_id = ?) WHERE id = ?",
            (project_id, workstream_id),
        )


def delete_workstream(conn, project_id, workstream_id):
    """Children become top-level lines; nothing of theirs is removed."""
    get_workstream(conn, project_id, workstream_id)
    conn.execute("UPDATE workstreams SET parent_id = NULL WHERE parent_id = ?", (workstream_id,))
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


_LIST_MARKER = re.compile(r"^[ \t\u3000]*(?:\d+\.\d+[.、)）]?|\d+[.、)）]|[（(]\d+[)）]|[-*•·])\s*")
_SUB_MARKER = re.compile(r"^(?:[ \t\u3000]+|\d+\.\d+)")


def parse_objective_lines(text):
    """(name, goal, is_sub) per numbered or bulleted objective line; the name
    is the first clause, the goal the whole line. An indented line or a
    `1.1`-style number under a top-level line marks a 子工作线."""
    result = []
    for line in (text or "").splitlines():
        if not _LIST_MARKER.match(line):
            continue
        goal = _LIST_MARKER.sub("", line, count=1).strip()
        if not goal:
            continue
        name = re.split(r"[，,：:；;。]", goal, maxsplit=1)[0].strip()[:SEED_NAME_LIMIT] or goal[:SEED_NAME_LIMIT]
        is_sub = bool(result) and bool(_SUB_MARKER.match(line))
        result.append((name, goal, is_sub))
    return result


def seed_from_objectives(conn, project_id):
    plan = conn.execute("SELECT objectives FROM project_plans WHERE project_id = ?", (project_id,)).fetchone()
    lines = parse_objective_lines(plan["objectives"] if plan else "")
    if not lines:
        raise ValidationError("项目目标里没有编号或列表行，无法生成工作线")
    rows = list_workstreams(conn, project_id)
    existing = {row["name"]: row for row in rows}
    created, parent = [], None
    for name, goal, is_sub in lines:
        row = existing.get(name)
        if not is_sub:
            parent = row["id"] if row and not row["parent_id"] else None
            if row:
                continue
        elif row:
            continue
        workstream_id = create_workstream(conn, project_id, {
            "name": name, "goal": goal, "parent_id": parent if is_sub else None,
        })
        existing[name] = {"id": workstream_id, "parent_id": parent if is_sub else None}
        if not is_sub:
            parent = workstream_id
        created.append(workstream_id)
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
    workstream must sit in a project the caller can upload materials to."""
    if not conn.execute("SELECT 1 FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id)).fetchone():
        raise ValidationError("TODO not found")
    primary_id, related_ids = _link_ids(primary, related)
    for workstream_id in ([primary_id] if primary_id else []) + related_ids:
        row = conn.execute("SELECT project_id FROM workstreams WHERE id = ?", (workstream_id,)).fetchone()
        role = project_role(conn, row["project_id"], user_id) if row else None
        if role is None:
            raise ValidationError("workstream not found")
        require_role(role, "upload")
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
        SELECT tw.todo_id, tw.workstream_id, tw.is_primary, w.name, w.project_id, p.name AS project_name,
               pw.name AS parent_name
        FROM todo_workstreams tw
        JOIN todos t ON t.id = tw.todo_id
        JOIN workstreams w ON w.id = tw.workstream_id
        JOIN projects p ON p.id = w.project_id
        LEFT JOIN workstreams pw ON pw.id = w.parent_id
        WHERE t.user_id = ?
        ORDER BY tw.is_primary DESC, tw.workstream_id
        """,
        (user_id,),
    ):
        if project_role(conn, row["project_id"], user_id) is None:
            continue
        item = {
            "id": row["workstream_id"], "name": row["name"], "project_id": row["project_id"],
            "project_name": row["project_name"],
            "path": f"{row['parent_name']} / {row['name']}" if row["parent_name"] else row["name"],
        }
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
        if not role_at_least(role, "upload"):
            continue
        rows = list_workstreams(conn, project["id"])
        paths = workstream_paths(rows)
        items = [
            {"id": row["id"], "name": row["name"], "path": paths[row["id"]], "parent_id": row["parent_id"], "status": row["status"]}
            for row in rows
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
    tz_name = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()["timezone"]
    week_key = str(payload.get("week_key") or "").strip() or current_week_key(tz_name)
    if not re.fullmatch(r"\d{4}-W\d{2}", week_key):
        raise ValidationError("week_key must look like 2026-W47")
    assert_current_week(tz_name, week_key)
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


# ---------------------------------------------------------------- 待跟踪项


def _due_date(value):
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("due date must be YYYY-MM-DD") from exc
    return value


def normalize_title(title):
    return re.sub(r"[\s，,。.;；:：!！?？、\"'“”‘’（）()]+", "", str(title or "")).lower()


def list_items(conn, workstream_id):
    """Open items first (earliest due first, undated last), then done ones
    newest first."""
    return [
        dict(r)
        for r in conn.execute(
            """
            SELECT id, workstream_id, title, owner_label, due_date, status, source, created_week, done_at, created_at, updated_at
            FROM workstream_items WHERE workstream_id = ?
            ORDER BY status = 'done', CASE WHEN status = 'open' AND due_date = '' THEN 1 ELSE 0 END,
                     CASE WHEN status = 'open' THEN due_date END, done_at DESC, id
            """,
            (workstream_id,),
        )
    ]


def get_item(conn, project_id, workstream_id, item_id):
    row = conn.execute(
        """
        SELECT i.* FROM workstream_items i JOIN workstreams w ON w.id = i.workstream_id
        WHERE i.id = ? AND i.workstream_id = ? AND w.project_id = ?
        """,
        (item_id, workstream_id, project_id),
    ).fetchone()
    if not row:
        raise LookupError("tracking item not found")
    return row


def create_item(conn, project_id, workstream_id, payload, source="manual"):
    get_workstream(conn, project_id, workstream_id)
    title = _text(payload.get("title"), ITEM_TITLE_LIMIT)
    if not title:
        raise ValidationError("tracking item title is required")
    tz_name = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()["timezone"]
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO workstream_items (workstream_id, title, owner_label, due_date, status, source, created_week, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?)
        """,
        (workstream_id, title, _text(payload.get("owner_label"), NAME_LIMIT), _due_date(payload.get("due_date")),
         source, current_week_key(tz_name), now, now),
    )
    return cur.lastrowid


def update_item(conn, project_id, workstream_id, item_id, payload):
    """A person's edit; it turns an agent item into a manual one, so the
    agent never closes it afterwards."""
    row = get_item(conn, project_id, workstream_id, item_id)
    title = _text(payload.get("title"), ITEM_TITLE_LIMIT) if "title" in payload else row["title"]
    if not title:
        raise ValidationError("tracking item title is required")
    status = str(payload.get("status") or row["status"])
    if status not in ITEM_STATUSES:
        raise ValidationError("tracking item status must be open or done")
    owner = _text(payload.get("owner_label"), NAME_LIMIT) if "owner_label" in payload else row["owner_label"]
    due = _due_date(payload.get("due_date")) if "due_date" in payload else row["due_date"]
    now = iso_now()
    done_at = (row["done_at"] or now) if status == "done" else ""
    conn.execute(
        """
        UPDATE workstream_items SET title = ?, owner_label = ?, due_date = ?, status = ?, source = 'manual',
            done_at = ?, updated_at = ? WHERE id = ?
        """,
        (title, owner, due, status, done_at, now, item_id),
    )


def delete_item(conn, project_id, workstream_id, item_id):
    get_item(conn, project_id, workstream_id, item_id)
    conn.execute("DELETE FROM workstream_items WHERE id = ?", (item_id,))


def add_agent_items(conn, workstream_id, week_key, titles, limit=3):
    """New follow-ups the agent found in this week's evidence; a title that
    matches any existing item of the workstream (open or done) is skipped."""
    seen = {normalize_title(r["title"]) for r in conn.execute("SELECT title FROM workstream_items WHERE workstream_id = ?", (workstream_id,))}
    added, now = 0, iso_now()
    for title in titles or []:
        title = _text(title, ITEM_TITLE_LIMIT)
        key = normalize_title(title)
        if not key or key in seen or added >= limit:
            continue
        conn.execute(
            """
            INSERT INTO workstream_items (workstream_id, title, status, source, created_week, created_at, updated_at)
            VALUES (?, ?, 'open', 'auto', ?, ?, ?)
            """,
            (workstream_id, title, week_key, now, now),
        )
        seen.add(key)
        added += 1
    return added


def close_agent_items(conn, workstream_id, item_ids):
    """The agent may close only its own open items; a person's items stay
    under their control."""
    ids = [i for i in item_ids or [] if isinstance(i, int)]
    if not ids:
        return 0
    now = iso_now()
    cur = conn.execute(
        f"""
        UPDATE workstream_items SET status = 'done', done_at = ?, updated_at = ?
        WHERE workstream_id = ? AND source = 'auto' AND status = 'open' AND id IN ({",".join("?" for _ in ids)})
        """,
        (now, now, workstream_id, *ids),
    )
    return cur.rowcount


def open_items_for_prompt(conn, workstream_id, limit=20):
    return [
        {"id": r["id"], "title": r["title"], "due_date": r["due_date"]}
        for r in conn.execute(
            "SELECT id, title, due_date FROM workstream_items WHERE workstream_id = ? AND status = 'open' ORDER BY id LIMIT ?",
            (workstream_id, limit),
        )
    ]


def _item_counts(conn, project_id, today):
    counts = {}
    for r in conn.execute(
        """
        SELECT i.workstream_id, i.status, i.due_date FROM workstream_items i
        JOIN workstreams w ON w.id = i.workstream_id WHERE w.project_id = ?
        """,
        (project_id,),
    ):
        c = counts.setdefault(r["workstream_id"], {"open": 0, "done": 0, "overdue": 0, "next_due": ""})
        c[r["status"]] = c.get(r["status"], 0) + 1
        if r["status"] == "open" and r["due_date"]:
            if r["due_date"] < today:
                c["overdue"] += 1
            elif not c["next_due"] or r["due_date"] < c["next_due"]:
                c["next_due"] = r["due_date"]
    return counts


# ---------------------------------------------------------------- health


def _plan_milestones(conn, project_id):
    from .plans import load_plan

    return load_plan(conn, project_id)["milestones"]


def _children(rows):
    result = {}
    for row in rows:
        if row["parent_id"]:
            result.setdefault(row["parent_id"], []).append(row["id"])
    return result


def workstream_conditions(conn, project_id, tz_name):
    """Per workstream: overdue / stale flags with reasons, from deterministic
    rules over dates, milestones and linked material and PR / issue
    activity."""
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
    from .workstream_git import activity_counts

    for workstream_id, weeks in activity_counts(conn, project_id).items():
        recent[workstream_id] = recent.get(workstream_id, 0) + sum(n for week, n in weeks.items() if week in window)
    items = _item_counts(conn, project_id, today)
    rows = list_workstreams(conn, project_id)
    children = _children(rows)
    result = {}
    for row in rows:
        overdue, stale = [], False
        counts = items.get(row["id"], {"open": 0, "done": 0, "overdue": 0, "next_due": ""})
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
            activity = recent.get(row["id"], 0) + sum(recent.get(child, 0) for child in children.get(row["id"], []))
            stale = older and not activity
        result[row["id"]] = {
            "overdue": overdue,
            "stale": stale,
            "recent_materials": recent.get(row["id"], 0),
            "items": counts,
            "items_overdue": counts["overdue"] if row["status"] == "active" else 0,
        }
    return result


def health_of(row, condition):
    if row["status"] == "done":
        return "complete"
    if row["status"] == "paused":
        return "paused"
    if condition["overdue"]:
        return "blocked"
    if condition["stale"] or condition.get("items_overdue"):
        return "at risk"
    return "on track"


HEALTH_RANK = {"on track": 0, "at risk": 1, "blocked": 2}


def roll_up(items):
    """An active parent takes the worst health of itself and its active
    children; `child_alerts` names the children that pulled it down."""
    by_id = {item["id"]: item for item in items}
    for item in items:
        kids = [by_id[i] for i in item["children"] if i in by_id]
        item["child_alerts"] = []
        if item["status"] != "active":
            continue
        for kid in kids:
            if kid["status"] == "active" and HEALTH_RANK.get(kid["health"], 0) > 0:
                item["child_alerts"].append(f"子工作线「{kid['name']}」{'受阻' if kid['health'] == 'blocked' else '有风险'}")
                if HEALTH_RANK[kid["health"]] > HEALTH_RANK.get(item["health"], 0):
                    item["health"] = kid["health"]
    return items


# ---------------------------------------------------------------- payloads


def _item(row, condition, paths=None, children=None):
    return {
        "id": row["id"],
        "name": row["name"],
        "parent_id": row["parent_id"],
        "path": (paths or {}).get(row["id"], row["name"]),
        "children": (children or {}).get(row["id"], []),
        "goal": row["goal"],
        "owner_member_id": row["owner_member_id"],
        "owner_label": row["owner_label"],
        "status": row["status"],
        "target_date": row["target_date"],
        "position": row["position"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "health": health_of(row, condition),
        "own_health": health_of(row, condition),
        "overdue_reasons": condition["overdue"],
        "recent_materials": condition["recent_materials"],
        "items_open": condition["items"]["open"],
        "items_done": condition["items"]["done"],
        "items_overdue": condition["items"]["overdue"],
        "next_due": condition["items"]["next_due"],
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
    from .workstream_git import activity_counts, unassigned_week_items

    git = activity_counts(conn, project_id)
    milestones = _plan_milestones(conn, project_id)
    paths, children = workstream_paths(rows), _children(rows)
    items = []
    for row in rows:
        item = _item(row, conditions[row["id"]], paths, children)
        item["material_total"] = totals.get(row["id"], 0)
        item["git_week"] = git.get(row["id"], {}).get(current, 0)
        item["last_material_at"] = last_at.get(row["id"], "")
        item["milestones"] = [m for m in milestones if str(m.get("workstream_id") or "") == str(row["id"])]
        item["cells"] = [
            {
                "week_key": week,
                "snapshot": snapshots.get(row["id"], {}).get(week),
                "materials": counts.get(row["id"], {}).get(week, 0),
                "git": git.get(row["id"], {}).get(week, 0),
            }
            for week in week_keys
        ]
        items.append(item)
    roll_up(items)
    unassigned = conn.execute(
        """
        SELECT COUNT(*) FROM materials m WHERE m.project_id = ?
        AND NOT EXISTS (SELECT 1 FROM material_workstreams mw WHERE mw.material_id = m.id)
        """,
        (project_id,),
    ).fetchone()[0]
    organized = conn.execute(
        "SELECT MAX(completed_at) FROM generation_jobs WHERE project_id = ? AND trigger_type = 'workstreams' AND status = 'success'",
        (project_id,),
    ).fetchone()[0]
    return {
        "weeks": week_keys,
        "current_week": current,
        "today": local_today(tz_name).isoformat(),
        "timeline": timeline_weeks(week_keys, items, local_today(tz_name)),
        "workstreams": items,
        "unassigned_materials": unassigned,
        "unassigned_git": unassigned_week_items(conn, project_id, current),
        "organized_at": organized or "",
    }


def timeline_weeks(week_keys, items, today):
    """Weeks for the progress view: the matrix weeks plus enough future weeks
    to reach the latest target, milestone or due date (4 to 26 ahead)."""
    dates = []
    for item in items:
        dates += [item["target_date"], item["next_due"]]
        dates += [m.get("target_date") for m in item["milestones"]]
    horizon = max([d for d in dates if d] or [""])
    first = week_monday(week_keys[0])
    current = week_monday(week_keys[-1])
    future = TIMELINE_FUTURE_MIN
    if horizon:
        try:
            future = (date.fromisoformat(horizon) - current).days // 7 + 1
        except ValueError:
            pass
    future = max(TIMELINE_FUTURE_MIN, min(TIMELINE_FUTURE_MAX, future))
    weeks = []
    for offset in range(len(week_keys) + future):
        monday = first + timedelta(days=7 * offset)
        year, week, _ = monday.isocalendar()
        weeks.append({"week_key": f"{year}-W{week:02d}", "start": monday.isoformat()})
    return weeks


def workstream_detail(conn, project_id, workstream_id, tz_name, user_id, material_limit=200):
    row = get_workstream(conn, project_id, workstream_id)
    rows = list_workstreams(conn, project_id)
    conditions = workstream_conditions(conn, project_id, tz_name)
    paths, children = workstream_paths(rows), _children(rows)
    family = [r for r in rows if r["id"] == row["id"] or r["parent_id"] == row["id"]]
    members = roll_up([_item(r, conditions[r["id"]], paths, children) for r in family])
    item = next(m for m in members if m["id"] == row["id"])
    item["child_items"] = [
        {k: m[k] for k in ("id", "name", "status", "health", "owner_label", "target_date", "items_open", "items_overdue")}
        for m in members if m["id"] != row["id"]
    ]
    item["parent"] = {"id": row["parent_id"], "name": paths[row["parent_id"]]} if row["parent_id"] in paths else None
    item["milestones"] = [m for m in _plan_milestones(conn, project_id) if str(m.get("workstream_id") or "") == str(row["id"])]
    item["snapshots"] = [
        dict(r)
        for r in conn.execute(
            "SELECT week_key, status, summary, next_step, source, updated_at FROM workstream_weekly WHERE workstream_id = ? ORDER BY week_key DESC",
            (workstream_id,),
        )
    ]
    item["materials"] = [
        {
            **dict(r),
            "is_primary": bool(r["is_primary"]),
            "week_key": week_key_for(parse_iso(r["created_at"]), tz_name) if parse_iso(r["created_at"]) else "",
        }
        for r in conn.execute(
            """
            SELECT m.id, m.filename, m.source_type, m.summary, m.extraction_status, m.created_at, mw.is_primary,
                   mw.source AS link_source
            FROM material_workstreams mw JOIN materials m ON m.id = mw.material_id
            WHERE mw.workstream_id = ? ORDER BY m.id DESC LIMIT ?
            """,
            (workstream_id, material_limit),
        )
    ]
    from .workstream_git import workstream_git_items

    item["git_items"] = workstream_git_items(conn, workstream_id)
    item["items"] = list_items(conn, workstream_id)
    item["current_week"] = current_week_key(tz_name)
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
    """Active lines for agent prompts; a 子工作线 names its parent."""
    rows = list_workstreams(conn, project_id)
    names = {row["id"]: row["name"] for row in rows}
    result = []
    for row in rows:
        if not (include_inactive or row["status"] == "active"):
            continue
        entry = {"id": row["id"], "name": row["name"], "goal": row["goal"][:300]}
        if row["parent_id"] in names:
            entry["parent"] = names[row["parent_id"]]
        result.append(entry)
    return result
