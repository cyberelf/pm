"""数据备份：SQLite 数据库 + uploads 目录 → 管理员配置的目标目录。

备份内容是数据库的在线快照（sqlite3 backup API，服务运行期间也能拿到一致
副本，无需停机锁库）和上传文件的完整拷贝，写入目标目录下按北京时间命名的
`zreport-backup-YYYYMMDD-HHMMSS` 子目录；超出保留份数的旧备份目录自动清理。

调度复用 server 的分钟级调度循环（scheduler_loop → evaluate_backup），配置
存在 app_settings，修改即时生效。手动触发走 POST /api/backup/run。所有运行
（成功或失败）都记入 backup_runs 供管理界面查看。
"""

import re
import json
import shutil
import sqlite3
import threading
from datetime import datetime, time as dt_time, timezone
from pathlib import Path

from .config import (
    BACKUP_DIR_PREFIX,
    BACKUP_ENABLED_SETTING,
    BACKUP_INTERVAL_HOURS_SETTING,
    BACKUP_KEEP_SETTING,
    BACKUP_SCHEDULE_DAILY,
    BACKUP_SCHEDULE_INTERVAL,
    BACKUP_SCHEDULE_TIME_SETTING,
    BACKUP_SCHEDULE_TYPE_SETTING,
    BACKUP_TARGET_DIR_SETTING,
    DB_PATH,
    DEFAULT_BACKUP_INTERVAL_HOURS,
    DEFAULT_BACKUP_KEEP,
    DEFAULT_BACKUP_SCHEDULE_TIME,
    DEFAULT_BACKUP_SCHEDULE_TYPE,
    DEFAULT_TIMEZONE,
    SUPPORTED_BACKUP_SCHEDULE_TYPES,
    UPLOAD_DIR,
)
from .db import get_setting
from .cold_storage import storage_lock, material_file_path
from .timeutil import get_zone, iso_now, parse_iso
from .validation import ValidationError

# 同一进程内串行化备份执行：定时触发撞上手动触发时后者直接失败返回，
# 不排队也不并行拷贝两份
_backup_lock = threading.Lock()

_BACKUP_DIR_RE = re.compile(r"^" + re.escape(BACKUP_DIR_PREFIX) + r"\d{8}-\d{6}(?:-\d+)?$")


def _int_setting(conn, key, default):
    try:
        return int(str(get_setting(conn, key, "")).strip())
    except ValueError:
        return default


def _writable_error(exc):
    """目标目录写不进去时的可操作提示。macOS 对 LaunchAgent 后台进程访问
    SMB 挂载/外接磁盘有隐私保护（TCC），报 EPERM 而普通权限错误报 EACCES，
    两者都是 PermissionError，这里统一给出排查路径。"""
    if isinstance(exc, PermissionError):
        return (
            "目标目录拒绝写入（macOS 隐私保护拦截了后台服务访问网络卷或外接磁盘）："
            "在 系统设置 → 隐私与安全性 → 完全磁盘访问权限 中添加服务使用的 Python"
            "（如 /Library/Developer/CommandLineTools/usr/bin/python3）并重新触发备份，"
            "或改选本机磁盘上的目录"
        )
    return f"备份目标目录不可写：{exc}"


def verify_target_writable(target_dir):
    """设置保存时探测目标目录可写性：确保目录存在并试写一个探针文件。
    让配置错误在保存时立刻暴露（面板自动保存会显示错误），而不是等到
    定时任务失败后才发现。探针文件用完即删，不会残留。"""
    target = Path(target_dir)
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe = target / f"{BACKUP_DIR_PREFIX}.probe"
        probe.write_bytes(b"")
        probe.unlink()
    except OSError as exc:
        raise ValidationError(_writable_error(exc)) from None


def backup_config(conn):
    """生效配置，键名与 settings_state / 前端一致（带 backup_ 前缀）。"""
    schedule_type = get_setting(conn, BACKUP_SCHEDULE_TYPE_SETTING, "") or DEFAULT_BACKUP_SCHEDULE_TYPE
    if schedule_type not in SUPPORTED_BACKUP_SCHEDULE_TYPES:
        schedule_type = DEFAULT_BACKUP_SCHEDULE_TYPE
    return {
        "backup_enabled": get_setting(conn, BACKUP_ENABLED_SETTING) == "1",
        "backup_target_dir": get_setting(conn, BACKUP_TARGET_DIR_SETTING),
        "backup_schedule_type": schedule_type,
        "backup_schedule_time": get_setting(conn, BACKUP_SCHEDULE_TIME_SETTING, "") or DEFAULT_BACKUP_SCHEDULE_TIME,
        "backup_interval_hours": _int_setting(conn, BACKUP_INTERVAL_HOURS_SETTING, DEFAULT_BACKUP_INTERVAL_HOURS),
        "backup_keep": _int_setting(conn, BACKUP_KEEP_SETTING, DEFAULT_BACKUP_KEEP),
    }


def backup_state(conn):
    """管理接口用的完整快照：配置 + 最近 10 次运行记录。"""
    state = backup_config(conn)
    runs = [dict(row) for row in conn.execute("SELECT * FROM backup_runs ORDER BY id DESC LIMIT 10")]
    state["runs"] = runs
    state["last_run"] = runs[0] if runs else None
    return state


def backup_due(config, last_run_at, now=None):
    """是否到了下一次定时备份时间。

    以最近一次运行（不限触发方式）作为基准：手动备份同样满足当天的定时点，
    失败的运行也不会在同一时间窗口内反复重试，等下一个窗口再试。
    """
    if not config["backup_enabled"] or not config["backup_target_dir"]:
        return False
    now = now or datetime.now(timezone.utc)
    last = parse_iso(last_run_at)
    if config["backup_schedule_type"] == BACKUP_SCHEDULE_INTERVAL:
        if last is None:
            return True
        return (now - last).total_seconds() >= config["backup_interval_hours"] * 3600
    zone = get_zone(DEFAULT_TIMEZONE)
    local_now = now.astimezone(zone)
    hour, minute = (int(part) for part in config["backup_schedule_time"].split(":", 1))
    run_today = datetime.combine(local_now.date(), dt_time(hour, minute), tzinfo=zone).astimezone(timezone.utc)
    if now < run_today:
        return False
    return last is None or last < run_today


def evaluate_backup(conn, db_path=DB_PATH):
    """调度循环的备份入口：到期就跑一次定时备份。"""
    config = backup_config(conn)
    row = conn.execute("SELECT started_at FROM backup_runs ORDER BY id DESC LIMIT 1").fetchone()
    if not backup_due(config, row["started_at"] if row else None):
        return
    print(f"scheduled backup fired: target={config['backup_target_dir']}", flush=True)
    run_backup(conn, db_path, trigger="scheduled")


def run_backup(conn, db_path=DB_PATH, trigger="manual"):
    """执行一次备份并记录结果；无论成败都返回 backup_runs 行字典。"""
    started_at = iso_now()
    if not _backup_lock.acquire(blocking=False):
        return _record_run(
            conn, trigger, "failed", message="另一个备份任务正在进行中", started_at=started_at
        )
    try:
        with storage_lock:
            return _run_backup(conn, db_path, trigger, started_at)
    finally:
        _backup_lock.release()


def _run_backup(conn, db_path, trigger, started_at):
    try:
        config = backup_config(conn)
        if not config["backup_target_dir"]:
            raise ValueError("备份目标目录未配置")
        target = Path(config["backup_target_dir"])
        target.mkdir(parents=True, exist_ok=True)
        backup_dir = _unique_dir(target, datetime.now(get_zone(DEFAULT_TIMEZONE)).strftime("%Y%m%d-%H%M%S"))
        backup_dir.mkdir(parents=True)
        try:
            size_bytes = _snapshot_database(Path(db_path), backup_dir)
            upload_size, upload_count = _copy_uploads(backup_dir)
            cold_size, cold_count = _copy_cold_uploads(backup_dir)
            upload_size += cold_size
            upload_count += cold_count
        except Exception:
            # 快照或拷贝失败时清掉残缺目录，避免留下看似可用的半份备份
            shutil.rmtree(backup_dir, ignore_errors=True)
            raise
        size_bytes += upload_size
        pruned = _prune_old_backups(target, config["backup_keep"])
        message = f"已备份数据库与 {upload_count} 个上传文件"
        if pruned:
            message += f"；清理 {pruned} 个旧备份"
        return _record_run(
            conn,
            trigger,
            "success",
            target_dir=str(target),
            backup_path=str(backup_dir),
            size_bytes=size_bytes,
            file_count=upload_count,
            message=message,
            started_at=started_at,
        )
    except Exception as exc:
        message = _writable_error(exc) if isinstance(exc, PermissionError) else str(exc)
        return _record_run(conn, trigger, "failed", message=message, started_at=started_at)


def _record_run(conn, trigger, status, target_dir="", backup_path="", size_bytes=0, file_count=0, message="", started_at=None):
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO backup_runs
        (trigger_type, status, target_dir, backup_path, size_bytes, file_count, message, started_at, finished_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (trigger, status, target_dir, backup_path, size_bytes, file_count, message, started_at or now, now),
    )
    row = conn.execute("SELECT * FROM backup_runs WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def _snapshot_database(db_path, backup_dir):
    """sqlite3 在线备份 API 拷出一致的数据库快照，返回快照文件大小。"""
    dest_path = backup_dir / "reports.sqlite3"
    src = sqlite3.connect(str(db_path))
    try:
        dest = sqlite3.connect(str(dest_path))
        try:
            src.backup(dest)
        finally:
            dest.close()
    finally:
        src.close()
    return dest_path.stat().st_size


def _copy_uploads(backup_dir):
    """整个 uploads 目录树拷贝进备份目录，返回 (总字节, 文件数)。"""
    dest = backup_dir / "uploads"
    if not UPLOAD_DIR.exists():
        return 0, 0
    shutil.copytree(UPLOAD_DIR, dest)
    size = 0
    count = 0
    for path in dest.rglob("*"):
        if path.is_file():
            count += 1
            size += path.stat().st_size
    return size, count


def _copy_cold_uploads(backup_dir):
    """Use the snapshot's paths; fail the backup if any original is unavailable.

    The manifest maps portable backup paths to original cold-storage locations
    for restoration on the same machine or relocation by the administrator.
    """
    snapshot = sqlite3.connect(str(backup_dir / "reports.sqlite3"))
    snapshot.row_factory = sqlite3.Row
    try:
        rows = snapshot.execute("""SELECT id, source_type, storage_path, archive_root FROM materials
                                   WHERE archive_root != '' AND source_type = 'upload'""").fetchall()
    finally:
        snapshot.close()
    manifest, size = [], 0
    for row in rows:
        source = material_file_path(row)
        relative = Path("cold_uploads") / str(row["id"]) / source.name
        destination = backup_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        size += destination.stat().st_size
        manifest.append({"material_id": row["id"], "backup_path": relative.as_posix(), "storage_path": str(source)})
    if manifest:
        (backup_dir / "cold_uploads.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return size, len(manifest)


def _prune_old_backups(target, keep):
    """按目录名（时间戳字典序即时间序）保留最新 keep 份备份，只动本应用
    命名规则匹配的目录，目标目录里的其他内容不碰。"""
    dirs = sorted(
        (p for p in target.iterdir() if p.is_dir() and _BACKUP_DIR_RE.match(p.name)),
        key=lambda p: p.name,
        reverse=True,
    )
    removed = 0
    for path in dirs[max(int(keep), 0):]:
        shutil.rmtree(path, ignore_errors=True)
        removed += 1
    return removed


def _unique_dir(target, stamp):
    candidate = target / f"{BACKUP_DIR_PREFIX}{stamp}"
    counter = 2
    while candidate.exists():
        candidate = target / f"{BACKUP_DIR_PREFIX}{stamp}-{counter}"
        counter += 1
    return candidate
