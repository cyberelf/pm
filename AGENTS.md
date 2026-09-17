# Project Development Guide

## Scope

This repository implements zreport (Zero Report), a local weekly project reporting workspace with account-based data isolation. A system administrator manages accounts; regular users see only their own projects, TODOs, and voice jobs. Local-only: the backend runs on the same machine as the workspace data.

## Architecture

- Backend: Python standard library HTTP server.
- Storage: SQLite at `data/reports.sqlite3`.
- Uploads: local files under `data/uploads/`.
- Frontend: dependency-free static HTML/CSS/JS in `static/`.
- Task queue: weekly report generation and voice TODO transcription run through a shared in-process queue (`reports_app/task_queue.py`). Capacity (queued + running, default 5) and parallelism (default 2) are configurable in 全局设置 or via `REPORTS_QUEUE_CAPACITY` / `REPORTS_QUEUE_PARALLELISM`; changes take effect without a restart. Submissions beyond capacity are rejected with HTTP 409.
- Accounts: users, PBKDF2 password hashes, and cookie sessions live in the database (`users`, `sessions`, `user_settings`; logic in `reports_app/auth.py`). The first startup bootstraps an admin named `darren` with `REPORTS_ADMIN_PASSWORD`; when it is unset, a random one-time password is generated and printed to the server log. Every `/api` route requires a session except auth state/login; admin-only management covers users, LLM/ASR/queue settings, and the GitHub/GitLab enable switches. Git credentials are per-user tokens stored in `user_settings`. CLI clients authenticate through the OAuth-style device flow (`reports_app/device_auth.py`: `/api/device/auth/start|poll` plus the `/device` approval page) and receive a long-lived session sent as `Authorization: Bearer`; `zreport.py` at the repo root is the bundled `zreport` command (projects, materials, todos).
- External tools: the GitHub REST API and GitLab REST API v4 called directly with per-user tokens (`reports_app/github.py`, `reports_app/gitlab.py` — no `gh`/`glab` CLIs), a local whisper.cpp ASR service (`scripts/install_asr_service.sh`, port 8766) for voice TODO transcription, and the in-process internal agent (`reports_app/internal_agent.py`) that calls OpenAI/Anthropic-compatible LLM endpoints through langchain bindings configured in 全局设置. The Codex/Claude CLI agent paths were removed; the internal agent is the only report/voice/summary provider.
- Stable service: cross-platform login-service scripts in `scripts/` (macOS LaunchAgent, Linux systemd user unit, Windows Startup-folder `.bat` via Git Bash; `uninstall_service.sh [reports|asr]` removes them), plus a Docker Compose deployment mode (`compose.yaml`, `Dockerfile`, `docker/asr/Dockerfile`, `docker/entrypoint.sh`) that also runs the whisper.cpp ASR container, with state in the docker named volume `zreport_reports-data`, separate from `data/`. On NVIDIA GPU hosts layer on `compose.gpu.yaml` (`docker compose -f compose.yaml -f compose.gpu.yaml up -d --build`), which switches the asr build to `docker/asr/Dockerfile.cuda` and reserves all host GPUs.

## Development Rules

- Keep changes small and aligned with the OpenSpec change under `openspec/changes/add-weekly-project-management-system`.
- Prefer standard library code unless a dependency clearly removes meaningful complexity.
- Preserve the local-only scope and the account model: one admin manages users, per-user data isolation stays intact, and report/voice/summary generation stays on the internal agent. Do not add remote runners, OAuth, or additional providers without a new OpenSpec change.
- Store user-facing timestamps and scheduling in China time by default using `Asia/Shanghai`.
- Report generation runs in-process; no external agent CLI writes to app data.
- Report generation defaults to real internal-agent execution. Use `REPORTS_FAKE_PROVIDER=1` only in tests or explicit dry runs.
- Report context must include this week's newly uploaded or manually entered materials and this week's Git commits for connected repositories.
- The internal agent receives bounded evidence inline (`build_internal_evidence_prompt`); it never reads SQLite, uploaded files, or app files directly, and git activity comes from the assembled context.
- Generated risk forecasts stay in Markdown report content. System risk warnings must come from deterministic rules.

## Versioning & Release

- Two independent version tracks: the CLI/PyPI version `__version__` in `zreport.py`, and the platform version `APP_VERSION` in `reports_app/config.py` (server + UI; shown on the login page and sidebar). Never bump them together by default.
- Release to PyPI only when the CLI actually changed (the bundled `zreport` command, its skill, or CLI docs): bump `__version__`, commit, `git tag vX.Y.Z`, push the tag — this triggers the GitHub Actions Trusted Publishing workflow, and PyPI versions can never be re-uploaded.
- Platform-only changes (server or static UI) bump `APP_VERSION` alone and must not create a release tag or PyPI release. (v1.3.0 on PyPI is such an accidental no-op release — its CLI content is identical to 1.2.0; the next CLI change ships as 1.4.0.)

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

- Use the macOS LaunchAgent as the normal long-running service. Install or restart it with `scripts/install_service.sh`; the service label is `com.cyberelf.zreport`.
- Re-run `scripts/install_service.sh` after changing backend Python code, the service environment, the port, or LaunchAgent configuration so the running process uses the new version.
- Verify the running service with `curl --noproxy '*' http://127.0.0.1:8765/api/auth/state` (public); authenticated endpoints need a session cookie from `POST /api/auth/login`. When a change adds or modifies an API, verify that endpoint against the running service as well.
- Inspect `data/server.log` and `data/server.err.log` when startup or API verification fails. Check the loaded service with `launchctl print "gui/$(id -u)/com.cyberelf.zreport"`.
- Remove the LaunchAgent with `scripts/uninstall_service.sh` when it should no longer run. Reinstall it with `scripts/install_service.sh` rather than editing the generated plist directly.
- `scripts/start_server.sh` and `scripts/stop_server.sh` are for temporary manual operation. Do not run the manual server and LaunchAgent on the same port; stop or uninstall one mode before starting the other.
- The Docker Compose mode (`docker compose up -d --build`) is the deployment mode for hosts without the LaunchAgent. Its state lives in the `zreport_reports-data` named volume (removed only by `docker compose down -v`), so it never touches the native service's `data/` directory. After backend or static changes, rebuild with `docker compose up -d --build` and verify `http://127.0.0.1:${PORT:-8765}/api/state`. Container-internal bind address and port are fixed (`0.0.0.0`, 8765/8443); everything host-side comes from `.env` via compose substitution. Host-side port mappings bind `127.0.0.1` by default; `REPORTS_BIND` in `.env` overrides.
- The default service port is `8765`. Set `PORT` explicitly when installing or manually starting on another port, and use the same port in health checks.
- `PORT`, `REPORTS_HOST`, `REPORTS_FAKE_PROVIDER`, `REPORTS_QUEUE_CAPACITY`, and `REPORTS_QUEUE_PARALLELISM` may live in a `.env` file at the repo root (git-ignored). `run.py` and `install_service.sh` load it for missing variables only; real environment variables always take precedence, and stored 全局设置 values override both for the queue limits.
- The service additionally serves HTTPS on port `REPORTS_TLS_PORT` (default `8443`, empty disables it) with a self-signed cert under `data/tls/`; phones use that listener because microphone access requires a secure context. Health checks stay on the plain HTTP port.
- Frontend-only changes do not require a service restart, but verify them with a fresh browser load and account for static asset caching before diagnosing stale UI behavior.

## UI Guidelines

- Follow `DESIGN.md`.
- Keep the UI dense and operational. The 周报 workspace is light; the TODO 看板 is the one dark surface; shared components (buttons, inputs, dialogs, badges) follow the 周报 standard on both.
- Use explicit loading states for long actions.
- Avoid explanatory marketing copy inside the app.
