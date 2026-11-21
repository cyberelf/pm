# zreport (Zero Report)

Local project management workspace for weekly plans, updates, source materials, GitHub/GitLab activity, generated Markdown reports, and deterministic risk warnings. Accounts are managed by a system administrator; every user only sees their own projects, TODOs, and voice jobs.

## Run

Install Python dependencies and start the server (on Windows use the `py` launcher — `py -m pip install -r requirements.txt`, `py run.py` — or run the commands below from Git Bash):

```bash
python3 -m pip install --user -r requirements.txt
python3 run.py
```

Open `http://127.0.0.1:8000` and sign in.

## Accounts

- All API access requires login; the login screen appears on first visit.
- On first startup the service bootstraps an administrator account named `darren`. The initial password comes from `REPORTS_ADMIN_PASSWORD` (`.env` or environment); when it is unset, a random one-time password is generated and printed to the server log — set it before the first start, then change it in 全局设置 → 修改密码.
- Administrators manage accounts in 全局设置 → 用户管理 (create users, reset passwords, toggle admin/enabled, delete). A user whose projects/TODOs still exist cannot be deleted; the last enabled admin cannot be removed or demoted.
- Users see only their own data: projects, TODOs, voice jobs, and queue tasks are filtered per account. Appearance preferences and Git tokens are stored per user too.
- Project sharing: a project's owner can share it with other accounts from 项目设置 → 共享 and assign 只读 (view everything, export PDFs), 读写 (also contribute materials/weekly updates/plan/report edits/generation), or 管理 (also project settings, Git repositories, material deletion) access. Only the owner manages share members; revoked members immediately lose access. Shared projects show a 「共享 · 角色」 badge in the sidebar.
- 全局设置 panels for 内部 Agent LLM, 语音 TODO (ASR service), and 任务队列, plus the GitHub/GitLab enable switches and 用户管理, are visible to administrators only.
- Data backup: administrators configure scheduled backups in 全局设置 → 数据备份 — target directory, 每天定时 (HH:MM Beijing time) or 固定间隔 (hours), and retention count. Each run snapshots the SQLite database (online, consistent), uploads and cold originals locally, then compresses them into a single `zreport-backup-YYYYMMDD-HHMMSS.zip` under the target. A complete ZIP is published only after compression finishes; failed runs remove their temporary files. The displayed size is the compressed archive size. Retention counts both ZIPs and legacy backup directories together, leaving unrelated files untouched; existing directories are not automatically converted. 立即备份 triggers one on demand, and the panel lists recent runs (success/failure). Setting changes take effect without a restart. Saving the target directory probes writability immediately so permission errors surface at configuration time. Local temporary disk space must accommodate the uncompressed snapshot and originals.

For a steadier background service on port 8765:

```bash
scripts/start_server.sh
scripts/stop_server.sh
```

Set `PORT=9000` to choose another port. These scripts need bash (macOS, Linux, WSL, or Git Bash on Windows).

Or keep machine-local settings in a `.env` file at the repo root (git-ignored):

```bash
PORT=8765
# The server binds the loopback address by default; set REPORTS_HOST to a
# VPN/LAN address (e.g. 10.200.200.3) when other devices need access.
REPORTS_HOST=10.200.200.3
```

Both `python3 run.py` and `scripts/install_service.sh` read `.env` for `PORT`, `REPORTS_HOST`, and `REPORTS_FAKE_PROVIDER` defaults. Real environment variables always take precedence over the file.

Built-in safeguards: the server answers only on the configured bind address (default `127.0.0.1`), API request bodies are capped at 64 MB, repeated failed logins are throttled (5 per username / 10 per source IP per minute), and static files are served strictly from `static/`.

The service also listens on HTTPS port `8443` (set `REPORTS_TLS_PORT` to change or set it empty to disable) with a self-signed certificate generated at `data/tls/`. Phones need this HTTPS listener to use microphone access for voice TODOs: open `https://<host>:8443` and accept the certificate warning once.

For the most stable local service, install it as a per-user login service (restarts with the machine, same `.env`/port knobs):

```bash
PORT=8765 scripts/install_service.sh
scripts/uninstall_service.sh            # add "asr" to remove the voice service instead
```

One script, three platforms:

- macOS: LaunchAgent (launchd). For network/external backup volumes, add the service entry point `/usr/bin/python3` (also printed by the installer) to 系统设置 → 隐私与安全性 → 完全磁盘访问权限, then re-run `scripts/install_service.sh`. If an existing enabled entry still fails, remove and re-add that entry to refresh the grant. Apple's launcher can select a different framework interpreter: authorizing that framework file or Python.app does not necessarily authorize the service entry point. Directory and SMB share permissions must also allow writes; backup errors include the original failing path, OS error, service entry point and actual interpreter.
- Linux: systemd user service `zreport.service`; run `sudo loginctl enable-linger $USER` once so it also survives logout.
- Windows: a `.bat` in the Start Menu Startup folder (run the script from Git Bash); a console window appears at login — minimize it. Inside WSL2, use the Linux flow instead.

## Docker Compose

An alternative server deployment mode that runs the backend and the local voice model as containers, with the same data layout as the native service:

```bash
docker compose up -d --build
curl --noproxy '*' "http://127.0.0.1:${PORT:-8765}/api/auth/state"
```

- Two services: `reports` (the backend) and `asr` (a local voice model — the whisper.cpp server built from source at `docker/asr/Dockerfile`, pinned by `WHISPER_CPP_VERSION`, default `v1.9.3`). The first build compiles whisper.cpp and takes a few minutes.
- Data (SQLite, uploads, TLS certificates) lives in a docker-managed named volume (`zreport_reports-data`), never in the checkout and never in the native service's `data/` directory — the volume starts empty and the two modes never share state. It survives `docker compose down`; remove it with `docker compose down -v`, and back it up with `docker compose cp reports:/app/data ./data-backup`. Deployments from before the zreport rename still hold their data in `weekly-reports_reports-data`; copy it across once with `docker run --rm -v weekly-reports_reports-data:/from -v zreport_reports-data:/to alpine sh -c 'cp -a /from/. /to/'`.
- Host-side settings come from the repo-root `.env` (`PORT`, `REPORTS_BIND`, `REPORTS_TLS_PORT`, `REPORTS_FAKE_PROVIDER`, `REPORTS_QUEUE_CAPACITY`, `REPORTS_QUEUE_PARALLELISM`, `REPORTS_ADMIN_PASSWORD`, and for the asr service `ASR_PORT`, `ASR_MODEL`, `WHISPER_CPP_VERSION`). Inside the container the server binds `0.0.0.0` on fixed ports 8765/8443, published on the host loopback by default (`REPORTS_BIND` overrides, e.g. a VPN address or `0.0.0.0`) as `${PORT:-8765}` / `${REPORTS_TLS_PORT:-8443}`.
- The image ships chromium for PDF export with CJK fonts. Set `REPORTS_ADMIN_PASSWORD` in `.env` before the first start; when unset, the bootstrapped `darren` admin gets a random one-time password printed to the container log (`docker compose logs reports | grep 'bootstrap admin'`).
- Voice TODOs: put the GGML model in `data/models/` (see Voice TODO below) before starting — the `asr` container mounts that directory read-only and serves `/inference` on container port 8766. Set the ASR endpoint in 全局设置 to `http://asr:8766/inference` (container-to-container over the compose network). The port is also published on the host as `${ASR_PORT:-8766}`; if the native whisper service already listens there, set `ASR_PORT` in `.env` to a different host port. To use a natively installed whisper service instead of the container, point the endpoint at `http://host.docker.internal:8766/inference` (reachable through the `host-gateway` mapping).
- NVIDIA GPU hosts: layer on the GPU override so the `asr` container runs whisper.cpp on the GPU instead of the CPU (needs nvidia-container-toolkit):

  ```bash
  docker compose -f compose.yaml -f compose.gpu.yaml up -d --build
  ```

  This builds `docker/asr/Dockerfile.cuda` (same runtime layout, CUDA kernels; the first build compiles for every architecture in the list and takes a while). Extra `.env` knobs: `CUDA_VERSION` (default `12.4.1`) and `CUDA_ARCHITECTURES` (default `75;80;90` — covers Turing through Hopper; set `120` for RTX 50 / Blackwell consumer cards). The large-v3-turbo model fits in roughly 6 GB of VRAM; use a smaller GGML model on smaller cards.
- The self-signed TLS certificate is generated at startup. `REPORTS_TLS_SAN` (defaulting to `REPORTS_HOST` from `.env`) is added to the certificate SANs so the address phones use is covered.
- On networks where `deb.debian.org` is unreachable, set `APT_MIRROR` (for example `mirrors.tuna.tsinghua.edu.cn`) in `.env` before building — it applies to both images.

## Local Tools

- Git repository activity goes through the GitHub REST API (api.github.com) and GitLab REST API v4 (self-hosted instances supported; the GitLab server address is configured once per account in 全局设置 → Git 集成, defaulting to `https://gitlab.com`). No `gh`/`glab` CLIs are needed.
- Users configure their own access tokens in 全局设置 → Git 集成 (stored per account, never returned by the API — only a last-4 hint comes back). GitHub supports multiple tokens: an entry with an organization name is used only for that org's repositories (fine-grained token with that org as resource owner), and an entry with an empty organization is the fallback for everything else (classic token, or a personal fine-grained token). Read-only access is enough: fine-grained tokens need `Contents: Read-only`, classic tokens need `repo` (or `public_repo` for public repos only); org repos additionally require org approval (Settings → Third-party access) and, when the org enforces SAML SSO, a per-token SSO authorization. GitLab uses one personal access token with the `read_api` scope (Reporter role for private projects) plus the shared server address from 全局设置; for self-signed certificates, 跳过 SSL 证书校验 in the same panel disables TLS verification for that account's GitLab connections. Without a token only public repositories are reachable, and GitHub's anonymous rate limit is low. Administrators can disable either integration globally.
- Report generation runs exclusively through the `internal` agent, which calls the configured LLM in-process through the official OpenAI/Anthropic SDKs. Configure it in 全局设置 → 内部 Agent LLM (admin only): provider (`openai` or `anthropic`), endpoint base URL, model name, and API key. A blank base URL defaults to `https://api.openai.com/v1` / `https://api.anthropic.com`; any OpenAI-compatible or Anthropic-compatible endpoint (LM Studio, gateways) works. The API key is stored only in the local database (never returned by the API) and falls back to `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` environment variables when unset.
- Markdown report rendering uses `markdown-it-py` with a Python-Markdown fallback.
- Set `REPORTS_FAKE_PROVIDER=1` only for local tests or dry runs that generate a deterministic report without calling the LLM. Normal service startup uses real provider execution.

## Voice TODO

- A floating microphone button at the bottom right records while held. The browser only captures audio and converts it to a 16 kHz mono WAV locally (no speech leaves the machine at this stage); Safari and Chrome are supported. Microphone access requires a secure context: use `localhost` or the HTTPS listener (`https://<host>:8443`) from phones.
- On release, the WAV goes to `POST /api/todos/voice`, which starts a background voice job and returns immediately. Only one voice job runs at a time; while one is active the mic button becomes a stop button that cancels it (`POST /api/voice-jobs/{id}/cancel`), and the progress bubble with the transcript survives page reloads (`GET /api/voice-jobs/active`). The internal agent structures the transcript into one or more TODO items.
- The ASR service is any OpenAI-compatible transcription endpoint. The bundled choice is the whisper.cpp server (`/inference` on port 8766, large-v3-turbo model), registered as a per-user login service by `scripts/install_asr_service.sh` — same three-platform flow as the main service (macOS LaunchAgent / Linux systemd user unit / Windows Startup-folder `.bat` from Git Bash; inside WSL2 use the Linux flow; `scripts/uninstall_service.sh asr` removes it). It needs two things first:
  1. a `whisper-server` binary — macOS: `brew install whisper-cpp`; Linux: build once (`git clone https://github.com/ggml-org/whisper.cpp && cmake -S whisper.cpp -B whisper.cpp/build && cmake --build whisper.cpp/build --target whisper-server`, keep `build/bin/whisper-server` on `PATH` or point `WHISPER_SERVER` at it); Windows: a build from the [whisper.cpp releases](https://github.com/ggml-org/whisper.cpp/releases) (or the same CMake build), with `WHISPER_SERVER` pointing at the `.exe`.
  2. the GGML model under `data/models/` (same file the docker `asr` container mounts):

     ```bash
     curl -L -o data/models/ggml-large-v3-turbo-q5_0.bin \
       https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin
     # if huggingface.co is unreachable: https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin
     ```
- Transcription requests carry a `language` hint from the 识别语言 dropdown, defaulting to 中文 (`zh`) so short Chinese clips are not mis-detected as English. `自动检测` omits the field so the service decides.
- Appearance (theme color and light/dark mode) is stored per account server-side; `PUT /api/settings` is a partial update, so each settings panel only writes the keys it manages.
- If the configured agent fails, the raw transcript still creates TODO item(s) and the UI reports the fallback.

## Uploads

Supported project material types:

- Markdown: `.md`, `.markdown`
- Plain text: `.txt`
- PDF: `.pdf`
- HTML: `.html`, `.htm`
- Excel: `.xlsx`, `.xls`
- Images: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`

Image uploads are checked by file signature (a renamed non-image is rejected, SVG is never accepted) and stored with the sniffed media type. Recognition uses **全局设置 → 图片识别模型** (optional, image-capable, sharing the LLM API key, and by default the provider and API address). Set **图片识别 API 地址** to call an OpenAI-compatible endpoint instead: some Anthropic-compatible gateways silently drop image blocks (Zhipu's `/api/anthropic` does, so with a GLM Coding Plan key use `glm-4.6v` with `https://open.bigmodel.cn/api/coding/paas/v4`). It handles each image up to 5 MiB, transcribing visible text and describing the content, and that Markdown becomes the extracted text used for summaries and report evidence. It is separate from the report model because a text-only model answers "I cannot see the image", which would pollute report evidence. With no vision model configured, a larger image, or an endpoint that rejects the image, the material is marked failed while the original stays previewable and downloadable. The preview dialog shows the image above its recognised text.

Excel uploads support `.xlsx` and `.xls` using openpyxl and xlrd. Text extraction preserves worksheet names, rows, numbers, dates and formulas where available (formulas are not executed). Extraction is limited to 200,000 cells and 2,000,000 text characters; XLSX expanded data is limited to 64 MiB. Empty, encrypted or corrupt workbooks are marked failed while their original files remain downloadable. Every uploaded file has a 下载 action, including historical and failed-extraction files, subject to project read access.

Administrators configure **全局设置 → 文件冷存储** with an enable switch and an absolute target directory. The scheduler checks hourly and moves uploads strictly older than one calendar month in Asia/Shanghai (month-end dates clamp to the previous month's last day); 立即转存 runs a check immediately. Files are copied into `<target>/zreport-cold/project_<id>/material_<id>/`, verified by SHA-256 and size, and their database paths committed before hot copies are deleted. Failed files retain their hot originals and the panel displays the last scan, count and errors. Extracted text, timestamps and report context remain unchanged. Keep the cold volume mounted: preview and download read it directly. Changing the target applies to future transfers; existing archived files keep their recorded locations. Disabling the feature stops transfers and does not move files back.

Cold storage must not overlap the application data directory or the full-backup destination. Full backups also include archived originals under `cold_uploads/<material-id>/` with a `cold_uploads.json` manifest mapping backup paths to original storage paths. To restore a ZIP backup, extract it into an empty directory first (legacy directory backups already have the same layout), stop the service, restore `reports.sqlite3` and `uploads/`, then copy each manifest entry back to its recorded `storage_path` (or update the database `storage_path` and `archive_root` together if relocating) before restarting. A missing cold original fails the full backup rather than silently omitting it. Docker deployments must bind-mount the cold target into the reports container and configure that container path.

Markdown and plain text are extracted as UTF-8. PDF files are parsed server-side with pypdf and surfaced in report context with extraction status; scans or unreadable PDFs are marked failed instead of blocking the report.

## Report Context

Generated reports use a structured context snapshot for change detection and audit metadata. The internal agent receives the bounded evidence inline (no tool execution, no direct database or file access). The most important current-week evidence is:

- `new_materials_this_week`: project materials uploaded or manually entered during the current ISO project week in `Asia/Shanghai`.
- `git_commits_this_week`: commits from each connected repository's (GitHub or GitLab) configured tracked branches during the current ISO project week.

The prompt explicitly asks the model to use these as primary evidence and to say when no new materials or commits exist.

## Report Assistant

The 周报 workspace has a 助手问答 side panel (topbar button or 问助手 on the 当前周报 panel). Ask about this week's progress, the causes behind a problem, or ask it to adjust a conclusion. The internal agent starts from the current report and a local inventory, then calls read-only tools only when a question needs them. The tools are the read-only operations of the shared operation registry (see Operations), so they are exactly the CLI's read commands. Answers stream into the panel as they are generated: a question starts a background run (`POST .../assistant` → `202 {run}`), and the page follows `GET .../assistant/runs/<id>/events` (server-sent events: `round`, `text`, `tool_start`, `tool_end`, then `done`/`error`/`cancelled`; EventSource resumes with `Last-Event-ID`). Tools requested in the same model round run in parallel on their own database connections. Progress shows as a work log in the style of T3 Code: thinking segments, raw tool calls (`name {args}`) and interim notes in order, one muted line each, with live ticking timers and a 工作中 total; finished rows show their duration, failed calls a ✕, and tool rows expand to the raw input and a result excerpt. The stored answer keeps the log folded as 已工作 Ns · N 次工具调用. 停止 cancels a run (`POST .../runs/<id>/cancel`); reloading the page reattaches to an unfinished run. One run per account and project at a time (409 otherwise). Each answer lists the tools it used. Git operations call the remote APIs and are cached for 10 minutes. Adjustment requests return a full revised report that only replaces the current week's report after you click 应用到周报 (requires write access; the report is then marked 已手工调整). Each account keeps its own conversation per project week.

## Tests

```bash
python3 -m unittest
openspec validate "add-weekly-project-management-system"
```

## Operations

Project, material, report, TODO, search and Git read/write operations are defined once in `reports_app/operations.py`, in the shape MCP uses for tools: name, description, typed parameters rendered as JSON Schema, a `readOnlyHint` annotation, a CLI command path, a terminal render hint, and one handler. Three thin adapters expose the registry:

- HTTP: `GET /api/ops` publishes the manifest (public, metadata only); `POST /api/ops/<name>` runs an operation as the signed-in account, with project access resolved from the `project` argument (ID or name) and the operation's role.
- CLI: `zreport` builds its subcommands, flags and table/record rendering from the manifest at startup, so a new operation ships without a CLI release.
- Assistant: operations marked `agent` (read-only only) become LLM tools bound to the current project with bounded output.

To add a capability, add one `@operation` in `reports_app/operations.py`; do not hand-write a separate CLI command or assistant tool.

## CLI Client

`zreport` is the standard-library command-line client (`zreport.py` in the repo root). On machines without the checkout, install it from PyPI (`pip install zreport`); otherwise symlink it onto your PATH (`ln -sf "$PWD/zreport.py" ~/.local/bin/zreport`; on Windows create a `zreport.cmd` shim running `@python path\to\zreport.py %*`). Sign in once with the device flow — it prints a URL and a code; open the URL, sign in, and approve (the page is the same one a phone or another machine would use) — then work from the terminal:

```bash
zreport login --server http://127.0.0.1:8765    # add --insecure once for the self-signed HTTPS port
zreport whoami
zreport project list
zreport project weekly list -p 周报系统
zreport project weekly show -p 周报系统          # current week; add a week key like 2026-W37 for older ones
zreport project materials add -p 周报系统 --text "本周完成设备授权" --title 进展
zreport project materials add -p 周报系统 --text - < notes.txt   # pipe content through stdin
zreport project materials add -p 周报系统 --file notes.md 设计稿.pdf
zreport todo list
zreport todo add "整理部署文档" -d "补充 GPU compose 说明"
zreport todo status 3 doing
zreport todo done 3 -p 周报系统 --reason "文档已合并"
```

- The login exchanges a device code for a long-lived session token (365 days) stored in `<config>/zreport/cli.json` with `0600` permissions; `logout` revokes it server-side. Disabling or deleting a user revokes their CLI sessions too.
- Commands other than login/logout/whoami/skill come from the server's operation manifest (see Operations) and are cached per server in `<config>/zreport/ops-cache.json`, so `--help` works offline.
- Requests carry `Authorization: Bearer`, so every authenticated `/api` route works unchanged for CLI clients. The client always bypasses system proxy variables. The global flags `--server`, `--token`, `--insecure`, and `--config` allow scripting without touching the stored credentials.
- An agent skill (a `SKILL.md` teaching coding agents how to drive the CLI for weekly-report work) ships inside the package: `zreport skill install` writes it to `./.agents/skills/zreport/SKILL.md`, and `zreport skill install --global` to `~/.agents/skills/zreport/SKILL.md`. Point your agent at the `.agents/skills` directory (for Claude Code, symlink it into `~/.claude/skills`).

## Android Client

The native Android client lives in its own repository: `../pm-android`
(voice TODOs, TODO board, weekly report reading; talks to this service's
HTTPS API). It now needs a login: configure the same account as the web
UI (server responses require the session cookie). Build and setup
instructions are in that repo's README; the planning doc moved there too
(`ANDROID_APP_PLAN.md`).
