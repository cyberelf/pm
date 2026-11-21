# zreport (Zero Report) CLI

Command-line client for a [zreport](https://github.com/cyberelf/pm) server —
a local weekly-report workspace with projects, materials, TODOs, and
generated weekly reports. Standard library only; no dependencies.

This package ships the `zreport` command only. The server itself is a local
app you run from its own checkout (see the repository README).

## Install

```bash
pip install zreport
```

Requires Python 3.9+ and a reachable zreport server.

## Sign in

```bash
zreport login --server http://<server>:8765
```

The device flow prints an authorization code and a `/device` URL. Open the
URL in a browser, sign in, and enter the code to approve the device. For a
server with a self-signed TLS certificate add `--insecure` once — the choice
is remembered.

Credentials (a long-lived session token) are stored in
`~/.config/zreport/cli.json` with `0600` permissions; `zreport logout`
revokes it server-side. Disabling or deleting a user on the server revokes
their CLI sessions too.

## Commands

```
zreport project list                   list projects
zreport search "query" [-p project] [-n N] [--type report|material] [--json]
                                       hybrid keyword + vector search over
                                       weekly reports and materials (top 10
                                       by default; each hit shows a TYPE and
                                       an ID; the vector half needs an
                                       llm_embedding_model in 全局设置)
zreport material show <ID>             show a material's full extracted text
                                       (ID from `search`)
zreport report show <ID>               show a weekly report (ID from `search`)
zreport todo show <ID>                 show a TODO's details
zreport project materials add -p <project> --text "..." [--title "..."]
                                       submit a text material
echo "..." | zreport project materials add -p <project> --text -
                                       submit text material from stdin
zreport project materials add -p <project> --file a.md b.pdf
                                       upload attachments (Markdown, text, HTML,
                                       PDF, Excel, images)
zreport project materials list -p <project> [--scope all]
                                       list materials (default: this week's)
zreport project supplement show -p <project> [week_key]
                                       show the weekly supplement (本周补充)
zreport project plan show -p <project> show profile, objectives, milestones
zreport project risks list -p <project>
                                       this week's system risk warnings
zreport project repos list|commits|activity -p <project> [-r owner/name]
                                       linked repositories; this week's commits
                                       or PRs/issues/boards (remote APIs)
zreport project weekly list -p <project>
                                       list generated weekly reports
zreport project weekly show -p <project> [week_key]
                                       show a weekly report (Markdown)
zreport todo list [--all]              list TODOs (--all includes closed ones)
zreport todo add "Title" -d "Details"  create a TODO
zreport todo status <ID> doing|todo    change a TODO's status
zreport todo done <ID> -p <project> -r "closing note"
                                       close a TODO and archive it to a project
zreport skill install [--global]       install the agent skill into .agents/skills
zreport whoami | logout                session helpers
```

Except for `login`, `logout`, `whoami` and `skill`, commands are discovered
from the server at startup (`GET /api/ops`), so the list above is what a
current server offers and `zreport --help` always shows the connected
server's commands. They are the same operations the server's in-app report
assistant calls as tools. The manifest is cached per server next to the
credentials, so `--help` still works offline. Every server command accepts
`--json` for the raw result.

`<project>` accepts the project ID or its exact name. Global flags:
`--server`, `--token`, `--insecure`, `--config` — handy for scripting
without touching the stored credentials. The client bypasses system proxy
settings by design; the service is meant to be reached on a LAN or loopback.

## Agent skill

`zreport skill install` writes a `SKILL.md` (instructions for coding agents
on how to drive the CLI for weekly-report work) into
`./.agents/skills/zreport/`, or `~/.agents/skills/zreport/` with `--global`.
Point your agent at the `.agents/skills` directory.

## License

[MIT](https://github.com/cyberelf/pm/blob/main/LICENSE)
