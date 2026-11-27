"""项目组成员: the people a project's work is assigned to.

A member is either linked to an account (``user_id``, picked from the
enabled users) or a free-text name for someone without an account. Names
stay unique per project so a name always identifies one member. Workstream
owners (负责人) point at a member through ``workstreams.owner_member_id``;
``workstreams.owner_label`` keeps the member's current name as a
denormalised copy so every existing reader (reports, CLI, agent context)
keeps working, and renaming or removing a member rewrites it.
All helpers take an open connection, like sharing.py.
"""

from .timeutil import iso_now
from .validation import ValidationError

NAME_LIMIT = 60


def _name(value):
    return " ".join(str(value or "").split())[:NAME_LIMIT]


def list_members(conn, project_id):
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "user_id": row["user_id"],
            "username": row["username"] or "",
            "workstream_count": row["workstream_count"],
            "created_at": row["created_at"],
        }
        for row in conn.execute(
            """
            SELECT m.id, m.name, m.user_id, u.username, m.created_at,
                   (SELECT COUNT(*) FROM workstreams w WHERE w.owner_member_id = m.id) AS workstream_count
            FROM project_members m LEFT JOIN users u ON u.id = m.user_id
            WHERE m.project_id = ?
            ORDER BY m.position, m.id
            """,
            (project_id,),
        )
    ]


def member_candidates(conn, project_id):
    """Enabled accounts not yet linked to a member of the project."""
    return [
        {"id": row["id"], "username": row["username"]}
        for row in conn.execute(
            """
            SELECT id, username FROM users
            WHERE enabled = 1
              AND id NOT IN (SELECT user_id FROM project_members WHERE project_id = ? AND user_id IS NOT NULL)
            ORDER BY username
            """,
            (project_id,),
        )
    ]


def get_member(conn, project_id, member_id):
    try:
        member_id = int(member_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("invalid member id") from exc
    row = conn.execute(
        "SELECT * FROM project_members WHERE id = ? AND project_id = ?", (member_id, project_id)
    ).fetchone()
    if not row:
        raise LookupError("member not found")
    return row


def _assert_unique_name(conn, project_id, name, exclude_id=None):
    if conn.execute(
        "SELECT 1 FROM project_members WHERE project_id = ? AND name = ? AND id != ?",
        (project_id, name, exclude_id or 0),
    ).fetchone():
        raise ValidationError(f"项目组已有同名成员：{name}")


def _insert(conn, project_id, name, user_id):
    now = iso_now()
    position = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 FROM project_members WHERE project_id = ?", (project_id,)
    ).fetchone()[0]
    cur = conn.execute(
        """
        INSERT INTO project_members (project_id, user_id, name, position, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (project_id, user_id, name, position, now, now),
    )
    return cur.lastrowid


def add_member(conn, project_id, payload):
    """``{"user_id": n}`` links an account (name defaults to its username),
    ``{"name": "..."}`` adds a free-text member. Returns the new id."""
    user_id = _account(conn, project_id, payload.get("user_id"))
    name = _name(payload.get("name"))
    if user_id is not None:
        name = name or conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()["username"]
    elif not name:
        raise ValidationError("请填写成员名称或选择账号")
    _assert_unique_name(conn, project_id, name)
    return _insert(conn, project_id, name, user_id)


def _account(conn, project_id, user_id, exclude_member_id=None):
    """Validated account id for a member link; None for an empty value."""
    if user_id in (None, "", 0, "0"):
        return None
    try:
        user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError("invalid user id") from exc
    user = conn.execute("SELECT id, username, enabled FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise ValidationError("user not found")
    if not user["enabled"]:
        raise ValidationError("this account is disabled")
    if conn.execute(
        "SELECT 1 FROM project_members WHERE project_id = ? AND user_id = ? AND id != ?",
        (project_id, user_id, exclude_member_id or 0),
    ).fetchone():
        raise ValidationError(f"账号 {user['username']} 已在项目组中")
    return user_id


def update_member(conn, project_id, member_id, payload):
    """Rename a member and/or change its linked account (``user_id``,
    empty unlinks). The name follows to every workstream it owns."""
    row = get_member(conn, project_id, member_id)
    name = _name(payload.get("name", row["name"]))
    if not name:
        raise ValidationError("成员名称不能为空")
    user_id = _account(conn, project_id, payload["user_id"], row["id"]) if "user_id" in payload else row["user_id"]
    if name == row["name"] and user_id == row["user_id"]:
        return
    if name != row["name"]:
        _assert_unique_name(conn, project_id, name, row["id"])
    now = iso_now()
    conn.execute(
        "UPDATE project_members SET name = ?, user_id = ?, updated_at = ? WHERE id = ?", (name, user_id, now, row["id"])
    )
    if name != row["name"]:
        conn.execute(
            "UPDATE workstreams SET owner_label = ?, updated_at = ? WHERE owner_member_id = ?", (name, now, row["id"])
        )


def remove_member(conn, project_id, member_id):
    """Workstreams the member owned become unassigned."""
    row = get_member(conn, project_id, member_id)
    conn.execute(
        "UPDATE workstreams SET owner_member_id = NULL, owner_label = '', updated_at = ? WHERE owner_member_id = ?",
        (iso_now(), row["id"]),
    )
    conn.execute("DELETE FROM project_members WHERE id = ?", (row["id"],))


def ensure_member_by_name(conn, project_id, name):
    """The member with this name, created on demand. An exact username match
    among enabled accounts links the new member to that account. Returns the
    member id, or None for an empty name."""
    name = _name(name)
    if not name:
        return None
    row = conn.execute(
        "SELECT id FROM project_members WHERE project_id = ? AND name = ?", (project_id, name)
    ).fetchone()
    if row:
        return row["id"]
    user = conn.execute("SELECT id FROM users WHERE username = ? AND enabled = 1", (name,)).fetchone()
    user_id = None
    if user and not conn.execute(
        "SELECT 1 FROM project_members WHERE project_id = ? AND user_id = ?", (project_id, user["id"])
    ).fetchone():
        user_id = user["id"]
    return _insert(conn, project_id, name, user_id)


def resolve_owner(conn, project_id, payload, current=(None, "")):
    """(owner_member_id, owner_label) for a workstream write.

    ``owner_member_id`` picks a member of the project (empty clears the
    owner); a bare ``owner_label`` (older clients, CLI) is matched to — or
    creates — a member of that name. Neither key keeps ``current``."""
    if "owner_member_id" in payload:
        value = payload.get("owner_member_id")
        if value in (None, "", 0, "0"):
            return None, ""
        row = get_member_or_validation(conn, project_id, value)
        return row["id"], row["name"]
    if "owner_label" in payload:
        member_id = ensure_member_by_name(conn, project_id, payload.get("owner_label"))
        if member_id is None:
            return None, ""
        row = conn.execute("SELECT id, name FROM project_members WHERE id = ?", (member_id,)).fetchone()
        return row["id"], row["name"]
    return current


def get_member_or_validation(conn, project_id, member_id):
    try:
        return get_member(conn, project_id, member_id)
    except LookupError as exc:
        raise ValidationError("负责人必须是本项目的项目组成员") from exc


def migrate_workstream_owners(conn):
    """One-time move of free-text workstream owners into project members.
    Idempotent: only rows with a label and no member link are touched."""
    rows = conn.execute(
        "SELECT id, project_id, owner_label FROM workstreams WHERE owner_member_id IS NULL AND owner_label != ''"
    ).fetchall()
    for row in rows:
        member_id = ensure_member_by_name(conn, row["project_id"], row["owner_label"])
        if member_id is None:
            conn.execute("UPDATE workstreams SET owner_label = '' WHERE id = ?", (row["id"],))
            continue
        name = conn.execute("SELECT name FROM project_members WHERE id = ?", (member_id,)).fetchone()["name"]
        conn.execute(
            "UPDATE workstreams SET owner_member_id = ?, owner_label = ? WHERE id = ?", (member_id, name, row["id"])
        )
