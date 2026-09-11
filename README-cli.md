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
zreport projects                       list projects
zreport todos [--all]                  list TODOs (--all includes closed ones)
zreport materials add <project> --text "..." [--title "..."]
                                       submit a text material
echo "..." | zreport materials add <project> --text -
                                       submit text material from stdin
zreport materials add <project> --file a.md b.pdf
                                       upload attachments (.md .markdown .txt .pdf)
zreport todo add "Title" -d "Details"  create a TODO
zreport todo status <ID> doing|todo    change a TODO's status
zreport todo done <ID> -p <project> -r "closing note"
                                       close a TODO and archive it to a project
zreport skill install [--global]       install the agent skill into .agents/skills
zreport whoami | logout                session helpers
```

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
