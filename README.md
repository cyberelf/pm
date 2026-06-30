# Weekly Reports Workspace

Local personal project management workspace for weekly plans, updates, source materials, GitHub activity, generated Markdown reports, and deterministic risk warnings.

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

On macOS, use a LaunchAgent for the most stable local service:

```bash
PORT=8765 scripts/install_service.sh
scripts/uninstall_service.sh
```

The first release is local-only: the backend must run on the same machine as the workspace data, uploaded files, temporary files, `gh`, Codex CLI, and Claude Code CLI. Remote backend deployment is intentionally out of scope.

## Local Tools

- GitHub activity uses the local authenticated `gh` CLI.
- Report generation supports `codex` and `claude`.
- Codex default command uses `codex exec`.
- Claude default command uses `claude --print`.
- Markdown report rendering uses `markdown-it-py` with a Python-Markdown fallback.
- Report agents retrieve project information through the read-only platform CLI `scripts/report_context.py`; they are instructed not to read SQLite, uploaded files, application files, GitHub, or `gh` directly.
- Set `REPORTS_CODEX_CMD` or `REPORTS_CLAUDE_CMD` to override provider commands.
- Set `REPORTS_FAKE_PROVIDER=1` only for local tests or dry runs that generate a deterministic report without calling an agent CLI. Normal service startup uses real provider execution.

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
- `git_commits_this_week`: commits from connected GitHub repositories during the current ISO project week.

The provider prompt explicitly asks the model to use these as primary evidence and to say when no new materials or commits exist.

## Tests

```bash
python3 -m unittest
openspec validate "add-weekly-project-management-system"
```
