"""User accounts, password hashing, and cookie-backed sessions.

Passwords are hashed with PBKDF2-HMAC-SHA256 and a per-user random salt.
Sessions are opaque tokens stored in the sessions table and carried by an
HttpOnly cookie, so the stdlib HTTP server keeps no in-memory auth state and
restarts do not log anyone out. All helpers take an open connection so this
module stays free of database-path knowledge.
"""

import hashlib
import secrets
from datetime import timedelta
from http.cookies import SimpleCookie

from .timeutil import iso_now, parse_iso, utc_now
from .validation import ValidationError

SESSION_COOKIE = "reports_session"
SESSION_TTL_DAYS = 30
PBKDF2_ITERATIONS = 120_000
MIN_PASSWORD_LENGTH = 6
USERNAME_MAX_LENGTH = 64


def validate_username(username):
    name = (username or "").strip().lower()
    if not name or len(name) > USERNAME_MAX_LENGTH:
        raise ValidationError("username is required (max 64 characters)")
    if not all(part.isalnum() for part in name.replace(".", "").replace("_", "").replace("-", "").replace("@", "")):
        raise ValidationError("username may only contain letters, digits, and . _ - @")
    return name


def validate_new_password(password):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
    return password


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password, stored):
    try:
        scheme, iterations, salt, digest = (stored or "").split("$")
        if scheme != "pbkdf2":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", (password or "").encode("utf-8"), bytes.fromhex(salt), int(iterations)
        ).hex()
        return secrets.compare_digest(candidate, digest)
    except (ValueError, TypeError):
        return False


def create_user(conn, username, password, is_admin=False):
    name = validate_username(username)
    validate_new_password(password)
    if conn.execute("SELECT id FROM users WHERE username = ?", (name,)).fetchone():
        raise ValidationError("username already exists")
    now = iso_now()
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, is_admin, enabled, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?)",
        (name, hash_password(password), 1 if is_admin else 0, now, now),
    )
    return cur.lastrowid


def find_user(conn, username):
    return conn.execute(
        "SELECT * FROM users WHERE username = ?", ((username or "").strip().lower(),)
    ).fetchone()


def authenticate(conn, username, password):
    row = find_user(conn, username)
    if not row or not row["enabled"] or not verify_password(password or "", row["password_hash"]):
        raise ValidationError("invalid username or password")
    return row


def change_password(conn, user_id, old_password, new_password):
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise ValidationError("user not found")
    if not verify_password(old_password or "", row["password_hash"]):
        raise ValidationError("current password is incorrect")
    validate_new_password(new_password)
    conn.execute(
        "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
        (hash_password(new_password), iso_now(), user_id),
    )


def create_session(conn, user_id, ttl_days=None):
    token = secrets.token_urlsafe(32)
    expires = (utc_now() + timedelta(days=ttl_days or SESSION_TTL_DAYS)).isoformat()
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, iso_now(), expires),
    )
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (iso_now(),))
    return token


def user_for_session(conn, token):
    if not token:
        return None
    row = conn.execute(
        """
        SELECT u.*, s.expires_at FROM sessions s JOIN users u ON u.id = s.user_id
        WHERE s.token = ?
        """,
        (token,),
    ).fetchone()
    if not row or not row["enabled"]:
        return None
    if parse_iso(row["expires_at"]) and parse_iso(row["expires_at"]) < utc_now():
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        return None
    return row


def delete_session(conn, token):
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def user_public(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "is_admin": bool(row["is_admin"]),
        "enabled": bool(row["enabled"]),
        "created_at": row["created_at"],
    }


def session_cookie_header(token, secure=False):
    return (
        f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; "
        f"Max-Age={SESSION_TTL_DAYS * 24 * 3600}" + ("; Secure" if secure else "")
    )


def clear_cookie_header(secure=False):
    return f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0" + ("; Secure" if secure else "")


def token_from_cookie_header(header):
    if not header:
        return ""
    cookie = SimpleCookie()
    try:
        cookie.load(header)
    except Exception:
        return ""
    morsel = cookie.get(SESSION_COOKIE)
    return morsel.value if morsel else ""


def token_from_bearer_header(header):
    """Token from an 'Authorization: Bearer <token>' header (CLI clients);
    empty string when the header is absent or not a bearer token."""
    header = (header or "").strip()
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer":
        return ""
    return token.strip()
