import base64
import hashlib
import os
import re
from pathlib import Path

from .config import SUPPORTED_TEXT_EXTENSIONS, UPLOAD_DIR
from .timeutil import current_week_key, iso_now, parse_iso, week_key_for
from .validation import ValidationError, validate_material_filename


def safe_filename(name):
    base = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base) or "material"


def store_material(conn, project_id, payload):
    filename = safe_filename(payload.get("filename") or "")
    ext = validate_material_filename(filename)
    raw = base64.b64decode(payload.get("content_base64") or "", validate=True)
    checksum = hashlib.sha256(raw).hexdigest()
    project_dir = UPLOAD_DIR / f"project_{project_id}"
    project_dir.mkdir(parents=True, exist_ok=True)
    storage_name = f"{checksum[:12]}_{filename}"
    path = project_dir / storage_name
    path.write_bytes(raw)

    status = "pending"
    extracted = ""
    error = ""
    if ext in SUPPORTED_TEXT_EXTENSIONS:
        try:
            extracted = raw.decode("utf-8")
            status = "extracted"
        except UnicodeDecodeError as exc:
            status = "failed"
            error = f"text decode failed: {exc}"
    elif ext == ".pdf":
        status = "failed"
        error = "PDF stored; text extraction is not available in the standard-library MVP"

    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO materials
        (project_id, filename, content_type, storage_path, size_bytes, checksum,
         extraction_status, extracted_text, extraction_error, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            filename,
            payload.get("content_type") or "application/octet-stream",
            os.fspath(path),
            len(raw),
            checksum,
            status,
            extracted,
            error,
            now,
            now,
        ),
    )
    return cur.lastrowid


def store_manual_material(conn, project_id, payload):
    title = safe_manual_title(payload.get("title") or payload.get("filename") or "manual-note")
    content = payload.get("content") or ""
    if not content.strip():
        raise ValidationError("manual material content is required")
    raw = content.encode("utf-8")
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO materials
        (project_id, filename, content_type, storage_path, size_bytes, checksum,
         extraction_status, extracted_text, extraction_error, created_at, updated_at, source_type)
        VALUES (?, ?, 'text/markdown', '', ?, ?, 'extracted', ?, '', ?, ?, 'manual')
        """,
        (
            project_id,
            title,
            len(raw),
            hashlib.sha256(raw).hexdigest(),
            content,
            now,
            now,
        ),
    )
    return cur.lastrowid


def update_manual_material(conn, project_id, material_id, payload):
    row = conn.execute("SELECT * FROM materials WHERE id = ? AND project_id = ?", (material_id, project_id)).fetchone()
    if not row:
        raise ValidationError("material not found")
    if row["source_type"] != "manual":
        raise ValidationError("only manual materials can be edited")
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    created_at = parse_iso(row["created_at"])
    if not created_at or week_key_for(created_at, project["timezone"]) != current_week_key(project["timezone"]):
        raise ValidationError("previous-week materials are locked")
    title = safe_manual_title(payload.get("title") or row["filename"])
    content = payload.get("content") or ""
    if not content.strip():
        raise ValidationError("manual material content is required")
    raw = content.encode("utf-8")
    conn.execute(
        """
        UPDATE materials
        SET filename = ?, size_bytes = ?, checksum = ?, extracted_text = ?, updated_at = ?
        WHERE id = ? AND project_id = ?
        """,
        (title, len(raw), hashlib.sha256(raw).hexdigest(), content, iso_now(), material_id, project_id),
    )


def material_is_editable(row, timezone):
    if row["source_type"] != "manual":
        return False
    created_at = parse_iso(row["created_at"])
    return bool(created_at and week_key_for(created_at, timezone) == current_week_key(timezone))


def safe_manual_title(title):
    value = (title or "").strip()
    if not value:
        raise ValidationError("manual material title is required")
    return value[:160]
