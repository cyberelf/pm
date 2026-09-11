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
- On first startup the service bootstraps an administrator account named `darren`. The initial password comes from `REPORTS_ADMIN_PASSWORD` (`.env` or environment) and defaults to `changeme` — set it before the first start, then change it in 全局设置 → 修改密码.
- Administrators manage accounts in 全局设置 → 用户管理 (create users, reset passwords, toggle admin/enabled, delete). A user whose projects/TODOs still exist cannot be deleted; the last enabled admin cannot be removed or demoted.
- Users see only their own data: projects, TODOs, voice jobs, and queue tasks are filtered per account. Appearance preferences and Git tokens are stored per user too.
- 全局设置 panels for 内部 Agent LLM, 语音 TODO (ASR service), and 任务队列, plus the GitHub/GitLab enable switches and 用户管理, are visible to administrators only.

For a steadier background service on port 8765:

```bash
scripts/start_server.sh
scripts/stop_server.sh
```

Set `PORT=9000` to choose another port. These scripts need bash (macOS, Linux, WSL, or Git Bash on Windows).

Or keep machine-local settings in a `.env` file at the repo root (git-ignored):

```bash
PORT=8765
REPORTS_HOST=10.200.200.3
```

Both `python3 run.py` and `scripts/install_service.sh` read `.env` for `PORT`, `REPORTS_HOST`, and `REPORTS_FAKE_PROVIDER` defaults. Real environment variables always take precedence over the file.

The service also listens on HTTPS port `8443` (set `REPORTS_TLS_PORT` to change or set it empty to disable) with a self-signed certificate generated at `data/tls/`. Phones need this HTTPS listener to use microphone access for voice TODOs: open `https://<host>:8443` and accept the certificate warning once.

For the most stable local service, install it as a per-user login service (restarts with the machine, same `.env`/port knobs):

```bash
PORT=8765 scripts/install_service.sh
scripts/uninstall_service.sh            # add "asr" to remove the voice service instead
```

One script, three platforms:

- macOS: LaunchAgent (launchd), as before.
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
- Host-side settings come from the repo-root `.env` (`PORT`, `REPORTS_TLS_PORT`, `REPORTS_FAKE_PROVIDER`, `REPORTS_QUEUE_CAPACITY`, `REPORTS_QUEUE_PARALLELISM`, `REPORTS_ADMIN_PASSWORD`, and for the asr service `ASR_PORT`, `ASR_MODEL`, `WHISPER_CPP_VERSION`). Inside the container the server binds `0.0.0.0` on fixed ports 8765/8443, published as `${PORT:-8765}` / `${REPORTS_TLS_PORT:-8443}`.
- The image ships chromium for PDF export with CJK fonts. Set `REPORTS_ADMIN_PASSWORD` in `.env` before the first start so the bootstrapped `darren` admin does not use the default password.
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
- Report generation runs exclusively through the `internal` agent, which calls the configured LLM in-process through langchain's provider bindings. Configure it in 全局设置 → 内部 Agent LLM (admin only): provider (`openai` or `anthropic`), endpoint base URL, model name, and API key. A blank base URL defaults to `https://api.openai.com/v1` / `https://api.anthropic.com`; any OpenAI-compatible or Anthropic-compatible endpoint (LM Studio, gateways) works. The API key is stored only in the local database (never returned by the API) and falls back to `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` environment variables when unset.
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

Markdown and plain text are extracted as UTF-8. PDF files are parsed server-side with pypdf and surfaced in report context with extraction status; scans or unreadable PDFs are marked failed instead of blocking the report.

## Report Context

Generated reports use a structured context snapshot for change detection and audit metadata. The internal agent receives the bounded evidence inline (no tool execution, no direct database or file access). The most important current-week evidence is:

- `new_materials_this_week`: project materials uploaded or manually entered during the current ISO project week in `Asia/Shanghai`.
- `git_commits_this_week`: commits from each connected repository's (GitHub or GitLab) configured tracked branches during the current ISO project week.

The prompt explicitly asks the model to use these as primary evidence and to say when no new materials or commits exist.

## Tests

```bash
python3 -m unittest
openspec validate "add-weekly-project-management-system"
```

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
- Requests carry `Authorization: Bearer`, so every authenticated `/api` route works unchanged for CLI clients. The client always bypasses system proxy variables. The global flags `--server`, `--token`, `--insecure`, and `--config` allow scripting without touching the stored credentials.
- An agent skill (a `SKILL.md` teaching coding agents how to drive the CLI for weekly-report work) ships inside the package: `zreport skill install` writes it to `./.agents/skills/zreport/SKILL.md`, and `zreport skill install --global` to `~/.agents/skills/zreport/SKILL.md`. Point your agent at the `.agents/skills` directory (for Claude Code, symlink it into `~/.claude/skills`).

## Android Client

The native Android client lives in its own repository: `../pm-android`
(voice TODOs, TODO board, weekly report reading; talks to this service's
HTTPS API). It now needs a login: configure the same account as the web
UI (server responses require the session cookie). Build and setup
instructions are in that repo's README; the planning doc moved there too
(`ANDROID_APP_PLAN.md`).
