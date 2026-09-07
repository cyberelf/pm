# Project Development Guide

## Scope

This repository implements a local personal weekly project reporting workspace. The first release is single-user and local-only.

## Architecture

- Backend: Python standard library HTTP server.
- Storage: SQLite at `data/reports.sqlite3`.
- Uploads: local files under `data/uploads/`.
- Frontend: dependency-free static HTML/CSS/JS in `static/`.
- Task queue: weekly report generation and voice TODO transcription run through a shared in-process queue (`reports_app/task_queue.py`). Capacity (queued + running, default 5) and parallelism (default 2) are configurable in 全局设置 or via `REPORTS_QUEUE_CAPACITY` / `REPORTS_QUEUE_PARALLELISM`; changes take effect without a restart. Submissions beyond capacity are rejected with HTTP 409.
- External tools: local `gh` (GitHub), `glab` (GitLab), Codex CLI, Claude Code CLI, a local whisper.cpp ASR service (`scripts/install_asr_service.sh`, port 8766) for voice TODO transcription, and the in-process internal agent (`reports_app/internal_agent.py`) that calls OpenAI/Anthropic-compatible LLM endpoints through langchain bindings configured in 全局设置.
- Stable service: macOS LaunchAgent scripts in `scripts/`, plus a Docker Compose deployment mode (`compose.yaml`, `Dockerfile`, `docker/entrypoint.sh`) with the same `data/` layout.

## Development Rules

- Keep changes small and aligned with the OpenSpec change under `openspec/changes/add-weekly-project-management-system`.
- Prefer standard library code unless a dependency clearly removes meaningful complexity.
- Preserve the local-only, single-user scope. Do not add teams, roles, OAuth, or remote runners without a new OpenSpec change.
- Store user-facing timestamps and scheduling in China time by default using `Asia/Shanghai`.
- Report generation must use temporary input/output files and must not let agent CLIs write directly to app data.
- Report generation defaults to real Codex/Claude provider execution. Use `REPORTS_FAKE_PROVIDER=1` only in tests or explicit dry runs.
- Report context must include this week's newly uploaded or manually entered materials and this week's Git commits for connected repositories.
- Agent CLIs must get platform information through `scripts/report_context.py`; do not prompt them to read SQLite, uploaded files, app files, or GitHub/`gh`/GitLab/`glab` directly. The internal agent receives the same bounded evidence inline instead of the platform CLI.
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
- The Docker Compose mode (`docker compose up -d --build`) is the deployment mode for hosts without the LaunchAgent. Never run it against a `data/` directory that the LaunchAgent service is using. After backend or static changes, rebuild with `docker compose up -d --build` and verify `http://127.0.0.1:${PORT:-8765}/api/state`. Container-internal bind address and port are fixed (`0.0.0.0`, 8765/8443); everything host-side comes from `.env` via compose substitution.
- The default service port is `8765`. Set `PORT` explicitly when installing or manually starting on another port, and use the same port in health checks.
- `PORT`, `REPORTS_HOST`, `REPORTS_FAKE_PROVIDER`, `REPORTS_QUEUE_CAPACITY`, and `REPORTS_QUEUE_PARALLELISM` may live in a `.env` file at the repo root (git-ignored). `run.py` and `install_service.sh` load it for missing variables only; real environment variables always take precedence, and stored 全局设置 values override both for the queue limits.
- The service additionally serves HTTPS on port `REPORTS_TLS_PORT` (default `8443`, empty disables it) with a self-signed cert under `data/tls/`; phones use that listener because microphone access requires a secure context. Health checks stay on the plain HTTP port.
- Frontend-only changes do not require a service restart, but verify them with a fresh browser load and account for static asset caching before diagnosing stale UI behavior.

## UI Guidelines

- Follow `DESIGN.md`.
- Keep the UI dense and operational. The 周报 workspace is light; the TODO 看板 is the one dark surface; shared components (buttons, inputs, dialogs, badges) follow the 周报 standard on both.
- Use explicit loading states for long actions.
- Avoid explanatory marketing copy inside the app.
