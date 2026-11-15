"""Local cold storage for original uploads; database text stays online."""
import calendar
import hashlib
import os
import shutil
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import DATA_DIR, DEFAULT_TIMEZONE, UPLOAD_DIR
from .db import get_setting, set_setting
from .timeutil import get_zone, parse_iso
from .validation import ValidationError

# Downloads open files and backups take snapshots under the same lock as moves.
# On-disk copies become authoritative only after their DB path is committed.
storage_lock = threading.RLock()


def cold_storage_config(conn):
    return {
        "cold_storage_enabled": get_setting(conn, "cold_storage_enabled") == "1",
        "cold_storage_target_dir": get_setting(conn, "cold_storage_target_dir"),
        "cold_storage_last_run": get_setting(conn, "cold_storage_last_run"),
        "cold_storage_last_error": get_setting(conn, "cold_storage_last_error"),
        "cold_storage_last_count": int(get_setting(conn, "cold_storage_last_count", "0") or "0"),
    }


def validate_cold_target(value, backup_target=""):
    text = (value or "").strip()
    if not text:
        return ""
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValidationError("冷存储目录必须是绝对路径")
    path = path.resolve()
    # Avoid recursive full backups and keeping cold files inside the hot tree.
    for other in (DATA_DIR.resolve(), Path(backup_target).resolve() if backup_target else None):
        if other is not None and (path == other or other in path.parents or path in other.parents):
            raise ValidationError("冷存储目录不能与应用数据目录或完整备份目录重叠")
    return str(path)


def material_file_path(row, upload_root=None):
    """Confine persisted paths to the upload root or this row's recorded archive."""
    if row is None or row["source_type"] != "upload" or not row["storage_path"]:
        raise FileNotFoundError("uploaded material not found")
    root = Path(row["archive_root"]) if row["archive_root"] else (upload_root or UPLOAD_DIR)
    path = Path(row["storage_path"]).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        raise FileNotFoundError("uploaded material not found") from None
    if not path.is_file():
        raise FileNotFoundError("uploaded material file not found")
    return path


def month_cutoff(now):
    local = now.astimezone(get_zone(DEFAULT_TIMEZONE))
    year, month = (local.year - 1, 12) if local.month == 1 else (local.year, local.month - 1)
    return local.replace(year=year, month=month, day=min(local.day, calendar.monthrange(year, month)[1]))


def _checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evaluate_cold_storage(conn, now=None, force=False):
    config = cold_storage_config(conn)
    if not config["cold_storage_enabled"]:
        return config
    now = now or datetime.now(timezone.utc)
    last = parse_iso(config["cold_storage_last_run"])
    if not force and last and now - last < timedelta(hours=1):
        return config
    target = validate_cold_target(config["cold_storage_target_dir"], get_setting(conn, "backup_target_dir"))
    if not target:
        raise ValidationError("启用冷存储前先填写目标目录")
    moved, errors = 0, []
    with storage_lock:
        rows = conn.execute("""SELECT id, project_id, source_type, storage_path, archive_root,
                                      created_at, size_bytes, checksum
                               FROM materials WHERE source_type = 'upload' AND archive_root = ''""").fetchall()
        for row in rows:
            created = parse_iso(row["created_at"])
            if created is None or created >= month_cutoff(now):
                continue
            temporary = None
            try:
                source = material_file_path(row)
                root = Path(target) / "zreport-cold"
                destination = root / f"project_{row['project_id']}" / f"material_{row['id']}" / source.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                # A symlink in the configured tree must not redirect the move.
                destination.resolve().relative_to(root.resolve())
                with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".transfer-", delete=False) as stream:
                    temporary = Path(stream.name)
                    with source.open("rb") as original:
                        shutil.copyfileobj(original, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                if temporary.stat().st_size != row["size_bytes"] or _checksum(temporary) != row["checksum"]:
                    raise ValueError("转存校验失败，已保留原文件")
                os.replace(temporary, destination)
                temporary = None
                conn.execute("UPDATE materials SET storage_path = ?, archive_root = ? WHERE id = ?",
                             (str(destination), str(root.resolve()), row["id"]))
                # Commit before unlink: failures/crashes never leave the DB pointing
                # to a deleted hot file. A remaining duplicate reference keeps it.
                conn.commit()
                moved += 1
                if not conn.execute("SELECT 1 FROM materials WHERE storage_path IN (?, ?) LIMIT 1", (row["storage_path"], str(source))).fetchone():
                    source.unlink()
            except Exception as exc:
                conn.rollback()
                errors.append(f"资料 {row['id']}: {exc}")
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        set_setting(conn, "cold_storage_last_run", now.isoformat())
        set_setting(conn, "cold_storage_last_count", str(moved))
        set_setting(conn, "cold_storage_last_error", "\n".join(errors)[:4000])
        conn.commit()
    return cold_storage_config(conn)
