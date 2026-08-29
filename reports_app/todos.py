import hashlib

from .materials import store_manual_material
from .markdown import render_markdown
from .timeutil import iso_now
from .validation import ValidationError


OPEN_STATUSES = {"todo", "doing"}


def todo_rows(conn):
    rows = []
    for row in conn.execute(
            """
            SELECT todos.*, projects.name AS project_name
            FROM todos
            LEFT JOIN projects ON projects.id = todos.project_id
            ORDER BY CASE todos.status WHEN 'todo' THEN 0 WHEN 'doing' THEN 1 ELSE 2 END,
                     todos.updated_at DESC, todos.id DESC
            """
        ):
        item = dict(row)
        item["description_html"] = render_markdown(item["description"])
        item["close_reason_html"] = render_markdown(item["close_reason"])
        rows.append(item)
    return rows


def create_todo(conn, payload):
    title = _required_text(payload.get("title"), "TODO title is required", 200)
    description = (payload.get("description") or "").strip()[:4000]
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO todos (title, description, status, created_at, updated_at)
        VALUES (?, ?, 'todo', ?, ?)
        """,
        (title, description, now, now),
    )
    return cur.lastrowid


def update_todo(conn, todo_id, payload):
    row = _todo(conn, todo_id)
    status = payload.get("status", row["status"])
    if row["status"] == "closed" and status != "closed":
        raise ValidationError("closed TODO status cannot be changed")
    if row["status"] != "closed" and status not in OPEN_STATUSES:
        raise ValidationError("TODO status must be todo or doing; use close to finish it")
    title = _required_text(payload.get("title", row["title"]), "TODO title is required", 200)
    description = (payload.get("description", row["description"]) or "").strip()[:4000]
    conn.execute(
        "UPDATE todos SET title = ?, description = ?, status = ?, updated_at = ? WHERE id = ?",
        (title, description, status, iso_now(), todo_id),
    )
    if row["status"] == "closed" and row["material_id"]:
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


def close_todo(conn, todo_id, payload):
    row = _todo(conn, todo_id)
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
        project = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
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
            closed_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (reason, project_id, material_id, now, now, todo_id),
    )
    return material_id


def _todo(conn, todo_id):
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
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
