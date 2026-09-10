"""OAuth-style device authorization for CLI clients.

The CLI asks the server for a device code (POST /api/device/auth/start),
shows the short user code, and the user opens /device in a browser, signs
in, and approves. The CLI polls /api/device/auth/poll until the code is
approved and receives a long-lived session token, which it sends as an
Authorization: Bearer header. Device sessions live in the same sessions
table as browser sessions, so disabling a user revokes their CLI tokens
too, and every authenticated API route works unchanged for the CLI.
"""

import secrets
import sqlite3
from datetime import timedelta

from . import auth
from .timeutil import iso_now, parse_iso, utc_now
from .validation import ValidationError

DEVICE_CODE_TTL_SECONDS = 15 * 60
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 500
DEVICE_SESSION_TTL_DAYS = 365
# 8 unambiguous characters (no 0/O/1/I) split as XXXX-XXXX.
USER_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def normalize_user_code(value):
    text = (value or "").strip().upper().replace(" ", "")
    if "-" not in text and len(text) == 8:
        text = f"{text[:4]}-{text[4:]}"
    return text


def start_device_auth(conn):
    conn.execute("DELETE FROM device_auth_codes WHERE expires_at < ?", (iso_now(),))
    device_code = secrets.token_urlsafe(32)
    for _ in range(20):
        user_code = "-".join(
            "".join(secrets.choice(USER_CODE_ALPHABET) for _ in range(4)) for _ in range(2)
        )
        try:
            conn.execute(
                """
                INSERT INTO device_auth_codes (device_code, user_code, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    device_code,
                    user_code,
                    iso_now(),
                    (utc_now() + timedelta(seconds=DEVICE_CODE_TTL_SECONDS)).isoformat(),
                ),
            )
            break
        except sqlite3.IntegrityError:
            continue  # user_code collision; draw a new one
    else:
        raise ValidationError("could not allocate a unique device code, try again")
    return {
        "device_code": device_code,
        "user_code": user_code,
        "verification_path": "/device",
        "interval": POLL_INTERVAL_SECONDS,
        "expires_in": DEVICE_CODE_TTL_SECONDS,
    }


def approve_device_auth(conn, user_code, user_id):
    row = _pending_code(conn, normalize_user_code(user_code))
    if not row:
        raise ValidationError("device code not found or expired")
    conn.execute(
        "UPDATE device_auth_codes SET status = 'approved', user_id = ?, attempts = 0 WHERE device_code = ?",
        (user_id, row["device_code"]),
    )


def deny_device_auth(conn, user_code):
    row = _pending_code(conn, normalize_user_code(user_code))
    if not row:
        raise ValidationError("device code not found or expired")
    conn.execute(
        "UPDATE device_auth_codes SET status = 'denied' WHERE device_code = ?",
        (row["device_code"],),
    )


def poll_device_auth(conn, device_code):
    """One poll step. Returns a dict the API answers with verbatim:
    {"status": pending|denied|expired|approved, ...} — approved carries the
    access token and consumes the code."""
    device_code = (device_code or "").strip()
    if not device_code:
        raise ValidationError("device_code is required")
    row = conn.execute(
        "SELECT * FROM device_auth_codes WHERE device_code = ?", (device_code,)
    ).fetchone()
    if not row:
        return {"status": "expired"}
    if parse_iso(row["expires_at"]) and parse_iso(row["expires_at"]) < utc_now():
        conn.execute("DELETE FROM device_auth_codes WHERE device_code = ?", (device_code,))
        return {"status": "expired"}
    if row["attempts"] >= MAX_POLL_ATTEMPTS:
        conn.execute("DELETE FROM device_auth_codes WHERE device_code = ?", (device_code,))
        return {"status": "expired"}
    conn.execute(
        "UPDATE device_auth_codes SET attempts = attempts + 1 WHERE device_code = ?",
        (device_code,),
    )
    if row["status"] == "denied":
        conn.execute("DELETE FROM device_auth_codes WHERE device_code = ?", (device_code,))
        return {"status": "denied"}
    if row["status"] != "approved" or not row["user_id"]:
        return {"status": "pending"}
    token = auth.create_session(conn, row["user_id"], ttl_days=DEVICE_SESSION_TTL_DAYS)
    user = conn.execute("SELECT * FROM users WHERE id = ?", (row["user_id"],)).fetchone()
    conn.execute("DELETE FROM device_auth_codes WHERE device_code = ?", (device_code,))
    return {"status": "approved", "access_token": token, "user": auth.user_public(user)}


def _pending_code(conn, user_code):
    row = conn.execute(
        "SELECT * FROM device_auth_codes WHERE user_code = ?", (user_code,)
    ).fetchone()
    if not row or row["status"] != "pending":
        return None
    if parse_iso(row["expires_at"]) and parse_iso(row["expires_at"]) < utc_now():
        conn.execute("DELETE FROM device_auth_codes WHERE device_code = ?", (row["device_code"],))
        return None
    return row
