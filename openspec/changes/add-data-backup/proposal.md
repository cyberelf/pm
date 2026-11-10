## Why

Workspace data lives in a single SQLite database plus the uploads directory with no backup story; a mistaken delete, disk failure, or bad migration loses projects, reports, TODOs, and uploaded materials permanently. The service already runs an in-process minute scheduler, so a backup job belongs there rather than in an external cron the operator has to remember.

## What Changes

- Add a `data-backup` capability: administrators configure an automatic backup of the SQLite database and the `uploads/` tree into an admin-chosen target directory.
- Configuration lives in 全局设置 → 数据备份 (admin-only, stored in `app_settings`): enable switch, target directory (absolute path), schedule type — 每天定时 (daily HH:MM, Beijing time) or 固定间隔 (every N hours) — and retention count (keep last N backups, default 14).
- Each run writes `<target>/zreport-backup-YYYYMMDD-HHMMSS/` containing the database as an online sqlite3 snapshot (`reports.sqlite3`) plus a full copy of `uploads/`; runs past the retention count are pruned automatically, and only directories matching the `zreport-backup-*` naming rule are ever deleted.
- Scheduling piggybacks on the existing minute scheduler loop — a run fires when the configured time has been reached and no run (scheduled or manual) has happened since the previous window; changes to settings take effect without a restart.
- New admin-only APIs: `GET /api/backup` (configuration + last 10 runs) and `POST /api/backup/run` (immediate backup); every run, success or failure, is recorded in the new `backup_runs` table.
- UI: admin-only 数据备份 panel in 全局设置 with autosave, a 立即备份 button with explicit loading state, and a table of recent runs.
- Stays local-only: backups go to a local directory the service account can write; no cloud destinations, no new providers.

## Capabilities

### New Capabilities

- `data-backup`: Admin-configured scheduled backup of the workspace database and uploads to a local target directory with retention pruning, run history, and a manual trigger.

## Impact

- Code: `reports_app/backup.py` (new), `reports_app/config.py` (settings constants), `reports_app/db.py` (`backup_runs` table), `reports_app/validation.py` (target/schedule validators), `reports_app/server.py` (scheduler hook, settings keys, backup routes), `static/index.html`, `static/app.js`.
- Platform-only change: bumps `APP_VERSION`; no CLI/PyPI release.
- Backups contain all accounts' data and are written wherever the admin points them, so the feature stays admin-only end to end.
