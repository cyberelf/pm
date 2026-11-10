# Tasks

## 1. Backend

- [x] Settings constants in `reports_app/config.py` (`backup_*` keys, defaults, `BACKUP_DIR_PREFIX` naming rule)
- [x] `backup_runs` table in `reports_app/db.py` (trigger, status, target/backup path, size, message, timestamps)
- [x] Validators in `reports_app/validation.py`: absolute-path target dir (expanduser), schedule type daily/interval, HH:MM time, bounded interval hours (1–168) and keep count (1–100)
- [x] `reports_app/backup.py`: effective-config reader, due logic (daily window vs interval elapsed; last run of any trigger satisfies the window), `run_backup` (sqlite3 online snapshot + uploads copy into `zreport-backup-*` dir, partial-dir cleanup on failure, retention prune restricted to the naming rule, process-wide lock against concurrent runs), `evaluate_backup` scheduler entry
- [x] `server.py`: scheduler loop calls `evaluate_backup`; `backup_*` keys join `ADMIN_ONLY_SETTING_KEYS` and the settings PUT handler (enable requires a target directory); `GET /api/backup` and `POST /api/backup/run` admin-only; settings state carries backup config for admins
- [x] Writability pre-flight on saving `backup_target_dir` (probe file; PermissionError surfaces the macOS TCC network/external-volume remediation hint) and the same hint in recorded run failures

## 2. Tests

- [x] `BackupTest` in `tests/test_core.py`: due-logic matrix (daily window, interval, disable/missing target), snapshot content (valid SQLite snapshot + uploads copy), failure recording with cleanup target, retention pruning leaving foreign files alone, `evaluate_backup` single-fire, API permission matrix (non-admin 403, bad target 400, enable-without-target 400) and manual run/history flow
- [x] Pre-flight tests: `verify_target_writable` (missing dir created, probe leaves nothing, unwritable dir → privacy hint, blocked path → raw error) and settings-save rejection keeping the stored value

## 3. Frontend

- [x] Admin-only 数据备份 panel in 全局设置: enable switch, target dir, daily/interval select with field swap, retention, autosave with client-side validation, explicit busy state on 立即备份, recent-runs table with success/failure badges
- [x] Bump static asset versions (`styles.css?v=61`, `app.js?v=65`)

## 4. Docs & Release

- [x] README Accounts bullet for 全局设置 → 数据备份
- [x] Bump `APP_VERSION` in `reports_app/config.py` (platform-only; no git tag, no PyPI release)
