---
name: zreport
description: Summarize and organize weekly-report material with the zreport CLI. Use when the user asks to collect or organize this week's work, draft a weekly report, review project progress or TODO status, submit work notes to a project, or manage TODOs.
---

# Summarize weekly-report material with zreport

zreport is the command-line client of a local weekly-report workspace
(projects, materials, TODOs, generated weekly reports). Drive the `zreport`
command only — do not call the server's HTTP API directly.

## Before you start

- Server URL: read `server` from `~/.config/zreport/cli.json` when it exists;
  otherwise ask the user. Every command also accepts `--server <URL>`.
- Sign-in check: run `zreport whoami`. If it reports "Not signed in", run
  `zreport login --server <URL>`: it prints a device code and a `/device`
  URL. The browser approval step belongs to the user — agents cannot
  approve their own device.

## Collect the current state (read-only)

- `zreport project list`
- `zreport todo list` and `zreport todo list --all` (`--all` includes closed
  TODOs; the PROJECT column shows which project a closed TODO was archived into)
- `zreport project weekly list -p <project>` — generated weekly reports
- `zreport project weekly show -p <project> [week_key]` — report body rendered
  as text (default week: the current one)

## Search across reports and materials (read-only)

- `zreport search "<query>"` — hybrid keyword + vector search over weekly
  reports and materials, top 10 hits by default.
- Each hit row shows a TYPE and an ID; `--json` returns the raw hit objects
  (`type` + `source_id`).
- `-p <project>` scopes to one project; `-n <N>` changes the number of
  results; `--type report|material` picks one source.
- The vector half requires the server admin to set an embedding model in
  全局设置 (llm_embedding_model); without it the command still works,
  keyword-only. The first search after new content may be slower while the
  server indexes chunks.

## Read a hit in full (read-only)

- `zreport material show <ID>` — a material's extracted text, summary, and
  metadata (ID from the search table or `--json` source_id).
- `zreport report show <ID>` — a generated weekly report rendered as text.
- `zreport todo show <ID>` — a TODO's status, description, and close reason
  (closed TODOs need `todo list --all` first to confirm the ID exists).

If the task truly needs something beyond these commands, tell the user to
open an issue at https://github.com/cyberelf/pm/issues instead of working
around the CLI.

## Organize the summary

- Evidence order: what the user dictates or points at, then active TODOs and
  TODOs closed this week, then the latest weekly report (`weekly show`) for
  continuity with last week.
- Time window: ISO week, timezone Asia/Shanghai.
- Suggested structure: done this week / in progress / blockers and risks /
  next week's plan. State only what the evidence supports; say explicitly
  when nothing new exists instead of padding.
- Show the draft to the user and get confirmation before writing anything.

## Write back (confirm each item with the user first)

- Text material: `echo "..." | zreport project materials add -p <project> --text - --title "Title"`
- Attachments: `zreport project materials add -p <project> --file a.md b.pdf`
  (supported: .md .markdown .txt .html .htm .pdf)
- TODOs: `zreport todo add "Title" -d "Details"`, then
  `zreport todo status <ID> doing`, then
  `zreport todo done <ID> -p <project> -r "closing note"` (done archives the
  TODO as a material of that project).
- Server-side constraint: only materials created in the current ISO week can
  be edited or deleted; older ones are locked. Surface server errors as-is.
