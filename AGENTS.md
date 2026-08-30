# Project Development Guide

## Scope

This repository implements a local personal weekly project reporting workspace. The first release is single-user and local-only.

## Architecture

- Backend: Python standard library HTTP server.
- Storage: SQLite at `data/reports.sqlite3`.
- Uploads: local files under `data/uploads/`.
- Frontend: dependency-free static HTML/CSS/JS in `static/`.
- External tools: local `gh`, Codex CLI, and Claude Code CLI.
- Stable service: macOS LaunchAgent scripts in `scripts/`.

## Development Rules

- Keep changes small and aligned with the OpenSpec change under `openspec/changes/add-weekly-project-management-system`.
- Prefer standard library code unless a dependency clearly removes meaningful complexity.
- Preserve the local-only, single-user scope. Do not add teams, roles, OAuth, or remote runners without a new OpenSpec change.
- Store user-facing timestamps and scheduling in China time by default using `Asia/Shanghai`.
- Report generation must use temporary input/output files and must not let agent CLIs write directly to app data.
- Report generation defaults to real Codex/Claude provider execution. Use `REPORTS_FAKE_PROVIDER=1` only in tests or explicit dry runs.
- Report context must include this week's newly uploaded or manually entered materials and this week's Git commits for connected repositories.
- Agent CLIs must get platform information through `scripts/report_context.py`; do not prompt them to read SQLite, uploaded files, app files, or GitHub/`gh` directly.
- Generated risk forecasts stay in Markdown report content. System risk warnings must come from deterministic rules.

## Verification

Run before handing off changes:

```bash
python3 -m unittest
openspec validate "add-weekly-project-management-system"
```

For local service checks:

```bash
scripts/install_service.sh
curl --noproxy '*' http://127.0.0.1:8765/api/state
```

## Service Management

- Use the macOS LaunchAgent as the normal long-running service. Install or restart it with `scripts/install_service.sh`; the service label is `com.cyberelf.weeklyreports`.
- Re-run `scripts/install_service.sh` after changing backend Python code, the service environment, the port, or LaunchAgent configuration so the running process uses the new version.
- Verify the running service with `curl --noproxy '*' http://127.0.0.1:8765/api/state`. When a change adds or modifies an API, verify that endpoint against the running service as well.
- Inspect `data/server.log` and `data/server.err.log` when startup or API verification fails. Check the loaded service with `launchctl print "gui/$(id -u)/com.cyberelf.weeklyreports"`.
- Remove the LaunchAgent with `scripts/uninstall_service.sh` when it should no longer run. Reinstall it with `scripts/install_service.sh` rather than editing the generated plist directly.
- `scripts/start_server.sh` and `scripts/stop_server.sh` are for temporary manual operation. Do not run the manual server and LaunchAgent on the same port; stop or uninstall one mode before starting the other.
- The default service port is `8765`. Set `PORT` explicitly when installing or manually starting on another port, and use the same port in health checks.
- Frontend-only changes do not require a service restart, but verify them with a fresh browser load and account for static asset caching before diagnosing stale UI behavior.

## UI Guidelines

- Follow `DESIGN.md`.
- Keep the UI dense and operational. The 周报 workspace is light; the TODO 看板 is the one dark surface; shared components (buttons, inputs, dialogs, badges) follow the 周报 standard on both.
- Use explicit loading states for long actions.
- Avoid explanatory marketing copy inside the app.
