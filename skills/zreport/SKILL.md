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

Limitation: the CLI cannot read material bodies yet (uploads are summarized
server-side, and no subcommand lists materials). If the task truly needs
them, tell the user to open an issue at https://github.com/cyberelf/pm/issues
instead of working around the CLI.

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
  (supported: .md .markdown .txt .pdf)
- TODOs: `zreport todo add "Title" -d "Details"`, then
  `zreport todo status <ID> doing`, then
  `zreport todo done <ID> -p <project> -r "closing note"` (done archives the
  TODO as a material of that project).
- Server-side constraint: only materials created in the current ISO week can
  be edited or deleted; older ones are locked. Surface server errors as-is.
