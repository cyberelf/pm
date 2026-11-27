"""Project sharing: per-project collaborator roles granted by the owner.

Roles are ordered read < write < manage; the project owner (projects.user_id)
sits above every share role and is the only identity that can grant, change,
or revoke shares. Access checks raise PermissionError so the HTTP layer maps
them to 403; "no access at all" stays the caller's concern because routes
keep answering 404 for projects the caller cannot see (existence masking).
All helpers take an open connection, like auth.py.
"""

from . import auth
from datetime import timedelta

from .timeutil import iso_now, utc_now
from .validation import ValidationError

ROLES = ("read", "write", "manage")
# the implicit owner role outranks every share role
ROLE_RANK = {"read": 0, "write": 1, "manage": 2, "owner": 3}

# SQL fragment selecting every project the user may see: owned projects plus
# projects shared with them. Bind user_id twice.
ACCESSIBLE_PROJECTS_SQL = (
    "(SELECT id FROM projects WHERE user_id = ? UNION SELECT project_id FROM project_shares WHERE user_id = ?)"
)

ROLE_NEED_LABELS = {"read": "只读", "write": "读写", "manage": "管理"}

# 上次访问 is recorded at most this often per collaborator and project, so
# browsing a project does not turn every read into a write
ACCESS_TOUCH_INTERVAL = timedelta(minutes=5)


def project_role(conn, project_id, user_id):
    """'owner', one of ROLES, or None when the project does not exist or the
    user has no access to it."""
    row = conn.execute("SELECT user_id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        return None
    if user_id is not None and row["user_id"] == user_id:
        return "owner"
    if user_id is None:
        return None
    share = conn.execute(
        "SELECT role FROM project_shares WHERE project_id = ? AND user_id = ?",
        (project_id, user_id),
    ).fetchone()
    return share["role"] if share else None


def touch_share_access(conn, project_id, user_id):
    """Record a collaborator's access to a shared project (owners are not
    tracked). Self-contained: it reads first, writes and commits only its own
    update, and leaves a connection that already holds a transaction alone so
    it never commits someone else's writes. Returns True when recorded."""
    if user_id is None or conn.in_transaction:
        return False
    cutoff = (utc_now() - ACCESS_TOUCH_INTERVAL).isoformat()
    row = conn.execute(
        "SELECT last_accessed_at FROM project_shares WHERE project_id = ? AND user_id = ?",
        (project_id, user_id),
    ).fetchone()
    if not row or row["last_accessed_at"] >= cutoff:
        return False
    conn.execute(
        "UPDATE project_shares SET last_accessed_at = ? WHERE project_id = ? AND user_id = ?",
        (iso_now(), project_id, user_id),
    )
    conn.commit()
    return True


def require_role(role, need):
    """Raise PermissionError (→ HTTP 403) when the role is below what the
    action needs."""
    if role is None or ROLE_RANK.get(role, -1) < ROLE_RANK[need]:
        if need == "read":
            raise PermissionError("没有访问该项目的权限")
        raise PermissionError(f"该操作需要{ROLE_NEED_LABELS[need]}权限")


def share_rows(conn, project_id):
    return [
        {
            "user_id": row["user_id"],
            "username": row["username"],
            "role": row["role"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_accessed_at": row["last_accessed_at"],
        }
        for row in conn.execute(
            """
            SELECT ps.user_id, u.username, ps.role, ps.created_at, ps.updated_at, ps.last_accessed_at
            FROM project_shares ps JOIN users u ON u.id = ps.user_id
            WHERE ps.project_id = ?
            ORDER BY u.username
            """,
            (project_id,),
        )
    ]


def share_candidates(conn, project_id):
    """Enabled accounts that can still be added to the project: everyone
    except the owner and current members. Feeds the share-member dropdown."""
    project = conn.execute("SELECT user_id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        return []
    return [
        {"id": row["id"], "username": row["username"]}
        for row in conn.execute(
            """
            SELECT id, username FROM users
            WHERE enabled = 1 AND id != ?
              AND id NOT IN (SELECT user_id FROM project_shares WHERE project_id = ?)
            ORDER BY username
            """,
            (project["user_id"], project_id),
        )
    ]


def set_share(conn, project_id, payload):
    """Grant or update one collaborator's role. Validations mirror the member
    rules: the target must be an existing enabled account that is not the
    project owner."""
    role = payload.get("role") or ""
    if role not in ROLES:
        raise ValidationError("invalid share role; use read, write, or manage")
    target = auth.find_user(conn, payload.get("username"))
    if not target:
        raise ValidationError("user not found")
    project = conn.execute("SELECT user_id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if project and project["user_id"] == target["id"]:
        raise ValidationError("cannot share a project with its owner")
    if not target["enabled"]:
        raise ValidationError("this account is disabled")
    now = iso_now()
    conn.execute(
        """
        INSERT INTO project_shares (project_id, user_id, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(project_id, user_id) DO UPDATE SET role = excluded.role, updated_at = excluded.updated_at
        """,
        (project_id, target["id"], role, now, now),
    )
    return share_rows(conn, project_id)


def remove_share(conn, project_id, target_user_id):
    cur = conn.execute(
        "DELETE FROM project_shares WHERE project_id = ? AND user_id = ?",
        (project_id, target_user_id),
    )
    if cur.rowcount != 1:
        raise ValidationError("share not found")
    return share_rows(conn, project_id)
