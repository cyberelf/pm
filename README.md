# Weekly Reports Workspace

Local personal project management workspace for weekly plans, updates, source materials, GitHub/GitLab activity, generated Markdown reports, and deterministic risk warnings.

## Run

Install Python dependencies:

```bash
python3 -m pip install --user -r requirements.txt
```

```bash
python3 run.py
```

Open `http://127.0.0.1:8000`.

For a steadier background service on port 8765:

```bash
scripts/start_server.sh
scripts/stop_server.sh
```

Set `PORT=9000` to choose another port.

Or keep machine-local settings in a `.env` file at the repo root (git-ignored):

```bash
PORT=8765
REPORTS_HOST=10.200.200.3
```

Both `python3 run.py` and `scripts/install_service.sh` read `.env` for `PORT`, `REPORTS_HOST`, and `REPORTS_FAKE_PROVIDER` defaults. Real environment variables always take precedence over the file.

The service also listens on HTTPS port `8443` (set `REPORTS_TLS_PORT` to change or set it empty to disable) with a self-signed certificate generated at `data/tls/`. Phones need this HTTPS listener to use microphone access for voice TODOs: open `https://<host>:8443` and accept the certificate warning once.

On macOS, use a LaunchAgent for the most stable local service:

```bash
PORT=8765 scripts/install_service.sh
scripts/uninstall_service.sh
```

The first release is local-only: the backend must run on the same machine as the workspace data, uploaded files, temporary files, `gh`/`glab`, Codex CLI, and Claude Code CLI. Remote backend deployment is intentionally out of scope.

## Local Tools

- Git repository activity uses the local authenticated `gh` CLI (GitHub) or `glab` CLI (GitLab, including self-hosted instances). Each repo selects its git mode; GitLab repos may configure a server address, defaulting to `https://gitlab.com`.
- Report generation supports `codex`, `claude`, and `internal`.
- Codex default command uses `codex exec`.
- Claude default command uses `claude --print`.
- Markdown report rendering uses `markdown-it-py` with a Python-Markdown fallback.
- Report agents retrieve project information through the read-only platform CLI `scripts/report_context.py`; they are instructed not to read SQLite, uploaded files, application files, git hosting services, or `gh`/`glab` directly.
- Set `REPORTS_CODEX_CMD` or `REPORTS_CLAUDE_CMD` to override provider commands.
- The `internal` agent runs in-process and calls the configured LLM directly through langchain's provider bindings (no agent CLI). Configure it in 全局设置 → 内部 Agent LLM: provider (`openai` or `anthropic`), endpoint base URL, model name, and API key. A blank base URL defaults to `https://api.openai.com/v1` / `https://api.anthropic.com`; any OpenAI-compatible or Anthropic-compatible endpoint (LM Studio, gateways) works. The API key is stored only in the local database (never returned by the API) and falls back to `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` environment variables when unset.
- Set `REPORTS_FAKE_PROVIDER=1` only for local tests or dry runs that generate a deterministic report without calling an agent CLI. Normal service startup uses real provider execution.

## Voice TODO

- A floating microphone button at the bottom right records while held. The browser only captures audio and converts it to a 16 kHz mono WAV locally (no speech leaves the machine at this stage); Safari and Chrome are supported. Microphone access requires a secure context: use `localhost` or the HTTPS listener (`https://<host>:8443`) from phones.
- On release, the WAV goes to `POST /api/todos/voice`, which starts a background voice job and returns immediately. Only one voice job runs at a time; while one is active the mic button becomes a stop button that cancels it (`POST /api/voice-jobs/{id}/cancel`), and the progress bubble with the transcript survives page reloads (`GET /api/voice-jobs/active`). The configured agent (`codex` CLI, `claude` CLI, or the `internal` agent backed by the LLM provider settings) structures the transcript into one or more TODO items.
- The ASR service is any OpenAI-compatible transcription endpoint. The default is the bundled whisper.cpp server (`/inference` on port 8766, large-v3-turbo model); install it with `scripts/install_asr_service.sh` after `brew install whisper-cpp` and placing a GGML model under `data/models/`.
- Transcription requests carry a `language` hint from the 识别语言 setting, defaulting to `zh` so short Chinese clips are not mis-detected as English. Clearing the field lets the service decide.
- If the configured agent fails, the raw transcript still creates TODO item(s) and the UI reports the fallback.

## Uploads

Supported project material types:

- Markdown: `.md`, `.markdown`
- Plain text: `.txt`
- PDF: `.pdf`

Markdown and plain text are extracted as UTF-8. PDF files are stored and surfaced in report context with extraction status; this standard-library MVP marks PDF text extraction as failed until a PDF parser is added.

## Report Context

Generated reports use a structured context snapshot for change detection and audit metadata, but agents receive only a read-only platform CLI entrypoint. The CLI supports progressive disclosure:

```bash
python3 scripts/report_context.py --project-id <id> --week-key <YYYY-Www> overview
python3 scripts/report_context.py --project-id <id> --week-key <YYYY-Www> materials
python3 scripts/report_context.py --project-id <id> --week-key <YYYY-Www> material --id <material_id>
python3 scripts/report_context.py --project-id <id> --week-key <YYYY-Www> commits
```

The most important current-week evidence is:

- `new_materials_this_week`: project materials uploaded or manually entered during the current ISO project week in `Asia/Shanghai`.
- `git_commits_this_week`: commits from each connected repository's (GitHub or GitLab) configured tracked branches during the current ISO project week.

The provider prompt explicitly asks the model to use these as primary evidence and to say when no new materials or commits exist.

## Tests

```bash
python3 -m unittest
openspec validate "add-weekly-project-management-system"
```
