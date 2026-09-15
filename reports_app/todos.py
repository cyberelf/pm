import hashlib

from .materials import material_is_unlocked, store_manual_material
from .markdown import render_markdown
from .timeutil import iso_now
from .validation import ValidationError


OPEN_STATUSES = {"todo", "doing"}
TODO_LANES = ("todo", "doing", "closed")


def _lane_top_position(conn, user_id, status):
    """New arrivals sit at the top of their lane, matching the historical
    newest-first order that updated_at DESC used to provide."""
    return conn.execute(
        "SELECT COALESCE(MIN(position), 0) - 1 FROM todos WHERE user_id = ? AND status = ?",
        (user_id, status),
    ).fetchone()[0]


def todo_rows(conn, user_id):
    rows = []
    for row in conn.execute(
            """
            SELECT todos.*, projects.name AS project_name
            FROM todos
            LEFT JOIN projects ON projects.id = todos.project_id
            WHERE todos.user_id = ?
            ORDER BY CASE todos.status WHEN 'todo' THEN 0 WHEN 'doing' THEN 1 ELSE 2 END,
                     todos.position ASC, todos.updated_at DESC, todos.id DESC
            """,
            (user_id,),
        ):
        item = dict(row)
        item["description_html"] = _render_todo_markdown(item["description"])
        item["close_reason_html"] = _render_todo_markdown(item["close_reason"])
        rows.append(item)
    return rows


def _render_todo_markdown(md):
    """TODO card links open in a new tab; raw HTML is escaped by render_markdown,
    so every <a> here comes from the renderer itself."""
    return render_markdown(md).replace(
        "<a href=", '<a target="_blank" rel="noopener noreferrer" href='
    )


def create_todo(conn, payload, user_id):
    title = _required_text(payload.get("title"), "TODO title is required", 200)
    description = (payload.get("description") or "").strip()[:4000]
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO todos (title, description, status, user_id, created_at, updated_at, position)
        VALUES (?, ?, 'todo', ?, ?, ?, (SELECT COALESCE(MIN(position), 0) - 1
                                        FROM todos WHERE user_id = ? AND status = 'todo'))
        """,
        (title, description, user_id, now, now, user_id),
    )
    return cur.lastrowid


def update_todo(conn, todo_id, payload, user_id):
    row = _todo(conn, todo_id, user_id)
    status = payload.get("status", row["status"])
    if row["status"] == "closed" and status != "closed":
        raise ValidationError("closed TODO status cannot be changed")
    if row["status"] != "closed" and status not in OPEN_STATUSES:
        raise ValidationError("TODO status must be todo or doing; use close to finish it")
    title = _required_text(payload.get("title", row["title"]), "TODO title is required", 200)
    description = (payload.get("description", row["description"]) or "").strip()[:4000]
    sync_material = (
        row["status"] == "closed"
        and row["material_id"]
        and (title != row["title"] or description != (row["description"] or ""))
    )
    if sync_material:
        _assert_material_unlocked(conn, row)
    position = row["position"]
    if status != row["status"]:
        position = _lane_top_position(conn, user_id, status)
    conn.execute(
        "UPDATE todos SET title = ?, description = ?, status = ?, position = ?, updated_at = ? WHERE id = ?",
        (title, description, status, position, iso_now(), todo_id),
    )
    if sync_material:
        content = _material_content({"title": title, "description": description}, row["close_reason"])
        raw = content.encode("utf-8")
        conn.execute(
            """
            UPDATE materials
            SET filename = ?, size_bytes = ?, checksum = ?, extracted_text = ?, updated_at = ?
            WHERE id = ? AND source_type = 'manual'
            """,
            (
                f"TODO 完成：{title}"[:160],
                len(raw),
                hashlib.sha256(raw).hexdigest(),
                content,
                iso_now(),
                row["material_id"],
            ),
        )


def delete_todo(conn, todo_id, user_id):
    """Delete a closed TODO. The archived weekly-report material
    (material_id) is intentionally left untouched."""
    row = _todo(conn, todo_id, user_id)
    if row["status"] != "closed":
        raise ValidationError("only closed TODO items can be deleted")
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))


def close_todo(conn, todo_id, payload, user_id):
    row = _todo(conn, todo_id, user_id)
    if row["status"] == "closed":
        raise ValidationError("TODO is already closed")
    reason = _required_text(payload.get("reason"), "close reason is required", 4000)
    raw_project_id = payload.get("project_id")
    project_id = None
    material_id = None
    if raw_project_id not in (None, ""):
        try:
            project_id = int(raw_project_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("invalid project") from exc
        project = conn.execute(
            "SELECT id FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
        ).fetchone()
        if not project:
            raise ValidationError("project not found")
        material_id = store_manual_material(
            conn,
            project_id,
            {
                "title": f"TODO 完成：{row['title']}",
                "content": _material_content(row, reason),
            },
        )
    now = iso_now()
    conn.execute(
        """
        UPDATE todos
        SET status = 'closed', close_reason = ?, project_id = ?, material_id = ?,
            closed_at = ?, updated_at = ?, position = ?
        WHERE id = ?
        """,
        (reason, project_id, material_id, now, now, _lane_top_position(conn, user_id, "closed"), todo_id),
    )
    return material_id


def reorder_todos(conn, payload, user_id):
    """Persist a board drag result: {"lanes": {lane: [todo_id, ...]}}.
    Cards reorder freely between 待办 and 进行中; 已关闭 only accepts
    in-lane reordering, and closed cards can never leave it."""
    lanes = payload.get("lanes")
    if not isinstance(lanes, dict) or not lanes:
        raise ValidationError("lanes mapping is required")
    positions = {}
    for lane, ids in lanes.items():
        if lane not in TODO_LANES:
            raise ValidationError("unknown TODO lane")
        if not isinstance(ids, list):
            raise ValidationError("lane order must be a list of todo ids")
        for index, raw_id in enumerate(ids):
            try:
                todo_id = int(raw_id)
            except (TypeError, ValueError) as exc:
                raise ValidationError("invalid todo id") from exc
            if todo_id in positions:
                raise ValidationError("todo listed in multiple positions")
            positions[todo_id] = (lane, index)
    rows = {todo_id: _todo(conn, todo_id, user_id) for todo_id in positions}
    for todo_id, (lane, _index) in positions.items():
        status = rows[todo_id]["status"]
        if status == "closed" and lane != "closed":
            raise ValidationError("closed TODO status cannot be changed")
        if status != "closed" and lane == "closed":
            raise ValidationError("close a TODO with a reason; drag only between todo and doing")
    now = iso_now()
    for todo_id, (lane, index) in positions.items():
        row = rows[todo_id]
        if row["status"] == lane and row["position"] == index:
            continue
        conn.execute(
            "UPDATE todos SET status = ?, position = ?, updated_at = ? WHERE id = ?",
            (lane, index, now, todo_id),
        )


def _assert_material_unlocked(conn, row):
    material = conn.execute(
        "SELECT * FROM materials WHERE id = ? AND source_type = 'manual'",
        (row["material_id"],),
    ).fetchone()
    if not material:
        return
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (row["project_id"],)).fetchone()
    timezone = project["timezone"] if project else "UTC"
    if not material_is_unlocked(material, timezone):
        raise ValidationError("previous-week materials are locked; closed TODO cannot be updated")


def _todo(conn, todo_id, user_id):
    row = conn.execute("SELECT * FROM todos WHERE id = ? AND user_id = ?", (todo_id, user_id)).fetchone()
    if not row:
        raise ValidationError("TODO not found")
    return row


def _required_text(value, message, limit):
    text = (value or "").strip()
    if not text:
        raise ValidationError(message)
    return text[:limit]


def _material_content(todo, reason):
    description = (todo["description"] or "").strip() or "（无补充说明）"
    return (
        f"# TODO 完成：{todo['title']}\n\n"
        f"## TODO 内容\n\n{description}\n\n"
        f"## 关闭原因\n\n{reason}\n"
    )
