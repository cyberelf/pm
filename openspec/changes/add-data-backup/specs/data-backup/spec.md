## ADDED Requirements

### Requirement: Admin-configured backup schedule
The system SHALL let administrators configure automatic data backup in 全局设置 → 数据备份 — an enable switch, a target directory (absolute path on the local machine), a schedule type (每天定时 daily HH:MM in Beijing time, or 固定间隔 every N hours, 1–168), and a retention count (1–100, default 14) — stored in `app_settings` so changes take effect without a restart. All backup configuration and actions SHALL be admin-only.

#### Scenario: Enable backup requires a target directory
- **WHEN** an administrator enables scheduled backup without a configured target directory
- **THEN** the system rejects the change and keeps backup disabled

#### Scenario: Reject invalid configuration
- **WHEN** an administrator saves a relative target directory, an unknown schedule type, a malformed time, or an out-of-range interval or retention count
- **THEN** the system rejects the change with a validation error and keeps the previous configuration

#### Scenario: Non-administrators cannot configure or trigger backup
- **WHEN** a non-administrator account calls the backup configuration, history, or manual-run APIs or changes backup settings
- **THEN** the system rejects the request with a permission error

#### Scenario: Saving the target directory probes writability
- **WHEN** an administrator saves a backup target directory
- **THEN** the system creates it when missing and writes and removes a probe file, rejecting the save with an actionable error when the service cannot write there (with a macOS privacy-protection remediation hint for network/external volumes when the denial is a permission error)

### Requirement: Backup run contents and layout
The system SHALL back up the SQLite database as a consistent online snapshot (the sqlite3 backup API) and a full copy of the uploads directory into `<target>/zreport-backup-YYYYMMDD-HHMMSS/` (timestamp in Beijing time, deduplicated with a numeric suffix when needed); a failed run SHALL record the failure and SHALL NOT leave a partial backup directory behind.

#### Scenario: Successful run writes a complete backup
- **WHEN** a backup runs
- **THEN** the target directory receives a `zreport-backup-*` folder containing `reports.sqlite3` (openable, containing the workspace data) and the `uploads/` tree, and the run is recorded as successful with path, size, and file count

#### Scenario: Failed run records and cleans up
- **WHEN** a backup cannot complete (for example the target path cannot be created)
- **THEN** the run is recorded as failed with the error message and no partial backup folder is left in the target directory

#### Scenario: Concurrent runs are serialized
- **WHEN** a backup is triggered while another backup is still running
- **THEN** the new trigger does not run a second concurrent copy and is recorded as failed with a busy message

### Requirement: Retention pruning
After each successful run the system SHALL delete the oldest `zreport-backup-*` directories in the target directory beyond the configured retention count and SHALL NOT touch any other file or directory in the target.

#### Scenario: Prune beyond retention
- **WHEN** more backups exist in the target directory than the retention count allows after a successful run
- **THEN** the oldest backup directories by timestamp name are removed and non-backup files stay untouched

### Requirement: Scheduled trigger
The system SHALL evaluate the backup schedule in the existing minute scheduler loop and SHALL run a scheduled backup when the configured window has been reached and no earlier run (scheduled or manual) has happened since the previous window; a daily schedule therefore does not re-run within the same day after a run, and an interval schedule fires again only after the full interval has elapsed since the last run.

#### Scenario: Daily window fires once per day
- **WHEN** the scheduler reaches the configured daily time and the last run happened before that window (or never)
- **THEN** exactly one scheduled backup runs, and later ticks in the same window do not run again

#### Scenario: Interval fires after the full interval
- **WHEN** the configured interval has elapsed since the last run (or no run exists yet)
- **THEN** a scheduled backup runs; ticks within the interval do nothing

#### Scenario: Disabled backup never runs
- **WHEN** backup is disabled or no target directory is configured
- **THEN** the scheduler makes no backup and triggers nothing

### Requirement: Run history and manual trigger
The system SHALL record every backup run (trigger type scheduled/manual, status, target and backup path, size, file count, message, timestamps) in `backup_runs`, SHALL expose configuration plus the last 10 runs via admin-only `GET /api/backup`, and SHALL let an administrator run an immediate backup via admin-only `POST /api/backup/run`.

#### Scenario: Manual run and history
- **WHEN** an administrator requests an immediate backup and then loads the backup API
- **THEN** the run executes (recording success or failure like any scheduled run) and the history lists it with trigger 手动

#### Scenario: History reflects scheduled runs
- **WHEN** a scheduled backup completes
- **THEN** the run appears in the history with trigger 定时 and its result
