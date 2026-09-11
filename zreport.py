#!/usr/bin/env python3
"""Command-line client (zreport) for the zreport server.

Standard library only. Sign in once with the OAuth-style device flow
(`zreport login`), then work with projects, materials, TODOs, and weekly
reports from the terminal:

    python3 zreport.py login --server http://127.0.0.1:8765
    python3 zreport.py project list
    python3 zreport.py project weekly list --project my-project
    python3 zreport.py project weekly show --project my-project
    python3 zreport.py project materials add --project my-project --text "shipped device auth" --title progress
    python3 zreport.py project materials add --project my-project --file notes.md spec.pdf
    python3 zreport.py todo list
    python3 zreport.py todo add "write deploy docs" -d "include the GPU compose guide"
    python3 zreport.py todo status 3 doing
    python3 zreport.py todo done 3 --project my-project --reason "merged"

The token is stored in <config>/zreport/cli.json (0600). Self-signed
TLS: log in with --insecure once and the choice is remembered.
"""

import argparse
import base64
import json
import os
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import webbrowser
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_SERVER = "http://127.0.0.1:8765"
__version__ = "1.1.0"
LOGIN_TIMEOUT_SECONDS = 15 * 60
MATERIAL_EXTENSIONS = {".md": "text/markdown", ".markdown": "text/markdown", ".txt": "text/plain", ".pdf": "application/pdf"}
TODO_STATUSES = ("todo", "doing")
# The editable copy lives at skills/zreport/SKILL.md in the repo; this
# embedded copy ships inside the wheel (the package is a single module), and
# a test asserts the two stay identical.
SKILL_MD = """\
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
"""


class CliError(Exception):
    pass


# ---------------------------------------------------------------- config


def default_config_path():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return Path(base) / "zreport" / "cli.json"


def load_config(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        raise CliError(f"cannot read config {path}: {exc}") from exc
    return data if isinstance(data, dict) else {}


def save_config(path, config):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # create with 0600 from the first byte: a plain write_text would briefly
    # expose the token at the umask's default mode before chmod runs; the
    # trailing chmod still tightens files written by older versions
    payload = (json.dumps(config, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(payload)
    path.chmod(0o600)


# ---------------------------------------------------------------- http


def build_opener(insecure):
    # bypass http_proxy/https_proxy: the service is reached on the LAN or
    # loopback, a system proxy would only break the request
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl._create_unverified_context() if insecure else None),
    )


def api_request(config, method, path, payload=None, timeout=30):
    server = config["server"].rstrip("/")
    # keep urllib's file/ftp handlers out of reach via a crafted --server
    if urlparse(server).scheme not in ("http", "https"):
        raise CliError(f"unsupported server URL: {config['server']} (only http:// or https://)")
    opener = build_opener(not config.get("tls_verify", True))
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if config.get("token"):
        headers["Authorization"] = f"Bearer {config['token']}"
    request = urllib.request.Request(server + path, data=data, headers=headers, method=method)
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        try:
            detail = json.loads(detail).get("error") or detail
        except ValueError:
            pass
        raise CliError(f"HTTP {exc.code}: {detail.strip()}") from exc
    except urllib.error.URLError as exc:
        hint = connection_error_hint(str(exc.reason))
        raise CliError(f"cannot reach {config['server']}: {exc.reason}{hint}") from exc
    try:
        return json.loads(body) if body else {}
    except ValueError:
        preview = body.strip()[:120]
        raise CliError(f"server returned non-JSON content; this is probably not a zreport server: {preview}") from None


def connection_error_hint(reason):
    """Turn bare SSL noise into an actionable hint."""
    if "CERTIFICATE_VERIFY_FAILED" in reason:
        return " (self-signed certificates trigger this: double-check the URL, or pass --insecure to skip verification)"
    if "CERTIFICATE_REQUIRED" in reason:
        return " (the peer demands a client certificate: this is probably not a zreport server, check URL and port)"
    return ""


# ---------------------------------------------------------------- output


def display_width(text):
    return sum(2 if unicodedata.east_asian_width(char) in ("F", "W") else 1 for char in str(text))


def print_table(headers, rows):
    widths = [display_width(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], display_width(cell))

    def format_row(cells):
        padded = ""
        for index, cell in enumerate(cells):
            pad = " " * (widths[index] - display_width(cell))
            padded += str(cell) + pad + ("  " if index + 1 < len(cells) else "")
        return padded.rstrip()

    print(format_row(headers))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))


class _HTMLToText(HTMLParser):
    """Render server-provided report HTML as readable terminal text."""
    HEADINGS = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ", "h5": "#### ", "h6": "#### "}
    NEWLINE = {"p", "div", "br", "tr", "table", "ul", "ol", "section", "hr", "blockquote"}

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.HEADINGS:
            self.parts.append("\n\n" + self.HEADINGS[tag])
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in self.NEWLINE:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.HEADINGS or tag in self.NEWLINE or tag == "li":
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(unescape(data))


def html_to_text(html):
    parser = _HTMLToText()
    parser.feed(html or "")
    text = "".join(parser.parts)
    lines = [line.rstrip() for line in text.splitlines()]
    out, blank = [], 0
    for line in lines:
        if not line.strip():
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        out.append(line)
    return "\n".join(out).strip()


# ---------------------------------------------------------------- login


def cmd_login(args, config, config_path):
    server = (args.server or config.get("server") or DEFAULT_SERVER).rstrip("/")
    login_config = {"server": server, "tls_verify": not args.insecure}
    start = api_request(login_config, "POST", "/api/device/auth/start", payload={}, timeout=30)
    user_code = start["user_code"]
    url = server + start.get("verification_path", "/device")
    print(f"1. Open the authorization page: {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    print(f"2. Sign in and enter the code: {user_code}")
    print("waiting for approval", end="", flush=True)

    deadline = time.monotonic() + min(int(start.get("expires_in", 900)), LOGIN_TIMEOUT_SECONDS)
    interval = max(1, int(start.get("interval", 5)))
    while time.monotonic() < deadline:
        time.sleep(interval)
        result = api_request(login_config, "POST", "/api/device/auth/poll", payload={"device_code": start["device_code"]}, timeout=30)
        status = result.get("status")
        if status == "pending":
            print(".", end="", flush=True)
            continue
        print()
        if status == "approved":
            config.update(login_config)
            config["token"] = result["access_token"]
            config["user"] = (result.get("user") or {}).get("username")
            save_config(config_path, config)
            print(f"Signed in as {config['user']} (credentials saved to {config_path})")
            return 0
        if status == "denied":
            raise CliError("authorization denied")
        raise CliError("device code expired, log in again")
    print()
    raise CliError("timed out waiting for approval, log in again")


def cmd_logout(args, config, config_path):
    if config.get("token"):
        try:
            api_request(config, "POST", "/api/auth/logout", payload={})
        except CliError:
            pass  # token may already be gone server-side; clear locally anyway
    config.pop("token", None)
    config.pop("user", None)
    save_config(config_path, config)
    print("Signed out")
    return 0


def cmd_whoami(args, config, config_path):
    state = api_request(config, "GET", "/api/auth/state")
    user = state.get("current_user")
    if not user:
        print("Not signed in (run the login command)")
        return 1
    role = "admin" if user.get("is_admin") else "user"
    print(f"{user['username']} ({role}) @ {config['server']} (server v{state.get('version', '?')})")
    return 0


# ---------------------------------------------------------------- projects & materials


def require_login(config):
    if not config.get("token"):
        raise CliError("not signed in: run the login command first")


def fetch_projects(config):
    state = api_request(config, "GET", "/api/state")
    return state.get("projects") or []


def resolve_project(config, ref):
    projects = fetch_projects(config)
    for project in projects:
        if str(project["id"]) == str(ref) or project["name"] == ref:
            return project
    raise CliError(f"project not found: {ref} (see the projects command)")


def cmd_project_list(args, config, config_path):
    require_login(config)
    rows = [
        (
            project["id"],
            project["name"],
            project["status"],
            project.get("timezone", ""),
            (project.get("updated_at") or "")[:16].replace("T", " "),
        )
        for project in fetch_projects(config)
    ]
    print_table(["ID", "PROJECT", "STATUS", "TIMEZONE", "UPDATED"], rows)
    return 0


def cmd_materials_add(args, config, config_path):
    require_login(config)
    project = resolve_project(config, args.project)
    if args.file:
        files = []
        for raw_path in args.file:
            path = Path(raw_path).expanduser()
            ext = path.suffix.lower()
            if ext not in MATERIAL_EXTENSIONS:
                raise CliError(f"unsupported file type: {path.name} (supported: {' '.join(sorted(MATERIAL_EXTENSIONS))})")
            try:
                raw = path.read_bytes()
            except OSError as exc:
                raise CliError(f"cannot read {path}: {exc}") from exc
            files.append(
                {
                    "filename": path.name,
                    "content_base64": base64.b64encode(raw).decode("ascii"),
                    "content_type": MATERIAL_EXTENSIONS[ext],
                }
            )
        result = api_request(
            config,
            "POST",
            f"/api/projects/{project['id']}/materials",
            payload={"files": files},
            timeout=300,
        )
        print(f"Uploaded {len(files)} attachment(s) to '{project['name']}' (material IDs: {', '.join(str(i) for i in result.get('ids', []))})")
        return 0
    text = args.text
    if text == "-":
        text = sys.stdin.read()
    text = (text or "").strip()
    if not text:
        raise CliError('provide content: --text "..." (or --text - to read stdin), or attach files with --file')
    title = (args.title or "").strip() or "CLI note"
    result = api_request(
        config,
        "POST",
        f"/api/projects/{project['id']}/materials",
        payload={"source_type": "manual", "title": title, "content": text},
    )
    print(f"Submitted text material to '{project['name']}' (material ID: {result.get('id')})")
    return 0


def cmd_weekly_list(args, config, config_path):
    require_login(config)
    project = resolve_project(config, args.project)
    workspace = api_request(config, "GET", f"/api/projects/{project['id']}/workspace")
    rows = [
        (
            item["week_key"],
            "yes" if item.get("is_current_week") else "",
            (item.get("updated_at") or "")[:16].replace("T", " "),
        )
        for item in workspace.get("report_history") or []
    ]
    print(f"Weekly reports of '{project['name']}':")
    print_table(["WEEK", "CURRENT", "UPDATED"], rows)
    return 0


def cmd_weekly_show(args, config, config_path):
    require_login(config)
    project = resolve_project(config, args.project)
    if args.week_key:
        report = api_request(config, "GET", f"/api/projects/{project['id']}/reports/{args.week_key}")
    else:
        workspace = api_request(config, "GET", f"/api/projects/{project['id']}/workspace")
        report = workspace.get("report")
        if not report:
            raise CliError(
                f"no weekly report for the current week of '{project['name']}' "
                f"(weekly list shows the archived ones)"
            )
    print(html_to_text(report["content_html"]))
    return 0


# ---------------------------------------------------------------- todos


def cmd_todo_list(args, config, config_path):
    require_login(config)
    todos = api_request(config, "GET", "/api/todos").get("todos") or []
    if not args.all:
        todos = [todo for todo in todos if todo["status"] != "closed"]
    rows = [
        (
            todo["id"],
            todo["status"],
            todo.get("project_name") or "-",
            todo["title"],
        )
        for todo in todos
    ]
    print_table(["ID", "STATUS", "PROJECT", "TITLE"], rows)
    return 0


def cmd_todo_add(args, config, config_path):
    require_login(config)
    result = api_request(config, "POST", "/api/todos", payload={"title": args.title, "description": args.description or ""})
    print(f"Created TODO #{result.get('id')}: {args.title}")
    return 0


def cmd_todo_status(args, config, config_path):
    require_login(config)
    api_request(config, "PUT", f"/api/todos/{args.id}", payload={"status": args.status})
    print(f"TODO #{args.id} status set to {args.status}")
    return 0


def cmd_todo_done(args, config, config_path):
    require_login(config)
    project = resolve_project(config, args.project)
    result = api_request(
        config,
        "POST",
        f"/api/todos/{args.id}/close",
        payload={"reason": args.reason, "project_id": project["id"]},
    )
    material_id = result.get("material_id")
    archived = f", archived as material #{material_id} in '{project['name']}'" if material_id else ""
    print(f"TODO #{args.id} done{archived}")
    return 0


# ---------------------------------------------------------------- agent skill


def cmd_skill_install(args, config, config_path):
    base = Path.home() / ".agents" if args.global_install else Path.cwd() / ".agents"
    target = base / "skills" / "zreport" / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(SKILL_MD, encoding="utf-8")
    print(f"Skill installed: {target}")
    print("Point your coding agent at the .agents/skills directory (e.g. symlink it into ~/.claude/skills for Claude Code).")
    return 0


# ---------------------------------------------------------------- parser


def build_parser():
    parser = argparse.ArgumentParser(prog="zreport", description="zreport (Zero Report) command-line client")
    parser.add_argument("--server", help=f"server URL (default {DEFAULT_SERVER}; from saved config after login)")
    parser.add_argument("--token", help="use this Bearer token (default: from saved config)")
    parser.add_argument("--insecure", action="store_true", help="skip TLS certificate verification (self-signed certs)")
    parser.add_argument("--config", help="credentials file path (default <config>/zreport/cli.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="sign in with the device authorization flow")
    login.add_argument("--server", help="server URL, e.g. http://127.0.0.1:8765")
    login.add_argument("--insecure", action="store_true", help="skip TLS certificate verification (self-signed certs)")
    login.set_defaults(func=cmd_login)

    logout = sub.add_parser("logout", help="sign out and clear local credentials")
    logout.set_defaults(func=cmd_logout)

    whoami = sub.add_parser("whoami", help="show the signed-in user")
    whoami.set_defaults(func=cmd_whoami)

    project = sub.add_parser("project", help="project operations")
    project_sub = project.add_subparsers(dest="project_command", required=True)

    project_list = project_sub.add_parser("list", help="list projects")
    project_list.set_defaults(func=cmd_project_list)

    project_materials = project_sub.add_parser("materials", help="project materials")
    project_materials_sub = project_materials.add_subparsers(dest="project_materials_command", required=True)
    materials_add = project_materials_sub.add_parser("add", help="add material (text or file attachment)")
    materials_add.add_argument("-p", "--project", required=True, help="project ID or name")
    materials_add.add_argument("--text", help="text content; pass - to read from stdin")
    materials_add.add_argument("--title", help="text material title (default: CLI note)")
    materials_add.add_argument("--file", nargs="+", metavar="PATH", help="file attachments (.md .markdown .txt .pdf, multiple allowed)")
    materials_add.set_defaults(func=cmd_materials_add)

    project_weekly = project_sub.add_parser("weekly", help="weekly reports")
    project_weekly_sub = project_weekly.add_subparsers(dest="project_weekly_command", required=True)
    weekly_list = project_weekly_sub.add_parser("list", help="list generated weekly reports")
    weekly_list.add_argument("-p", "--project", required=True, help="project ID or name")
    weekly_list.set_defaults(func=cmd_weekly_list)
    weekly_show = project_weekly_sub.add_parser("show", help="show a weekly report (default: current week)")
    weekly_show.add_argument("week_key", nargs="?", help="week key like 2026-W37 (default: current week)")
    weekly_show.add_argument("-p", "--project", required=True, help="project ID or name")
    weekly_show.set_defaults(func=cmd_weekly_show)

    todo = sub.add_parser("todo", help="TODO operations")
    todo_sub = todo.add_subparsers(dest="todo_command", required=True)
    todo_list = todo_sub.add_parser("list", help="list TODOs")
    todo_list.add_argument("--all", action="store_true", help="include closed TODOs")
    todo_list.set_defaults(func=cmd_todo_list)

    todo_add = todo_sub.add_parser("add", help="create a TODO")
    todo_add.add_argument("title", help="title")
    todo_add.add_argument("-d", "--description", help="details")
    todo_add.set_defaults(func=cmd_todo_add)

    todo_status = todo_sub.add_parser("status", help="change a TODO's status")
    todo_status.add_argument("id", type=int, help="TODO ID")
    todo_status.add_argument("status", choices=TODO_STATUSES, help="target status")
    todo_status.set_defaults(func=cmd_todo_status)

    todo_done = todo_sub.add_parser("done", help="close a TODO and archive it to a project")
    todo_done.add_argument("id", type=int, help="TODO ID")
    todo_done.add_argument("-p", "--project", required=True, help="project to archive into (ID or name)")
    todo_done.add_argument("-r", "--reason", default="done", help="closing reason (default: done)")
    todo_done.set_defaults(func=cmd_todo_done)

    skill = sub.add_parser("skill", help="manage the agent skill for coding agents")
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)
    skill_install = skill_sub.add_parser(
        "install",
        help="install the skill into .agents/skills/zreport/ (current directory, or home with --global)",
    )
    skill_install.add_argument(
        "--global", dest="global_install", action="store_true",
        help="install into ~/.agents instead of ./.agents",
    )
    skill_install.set_defaults(func=cmd_skill_install)

    return parser


def main(argv=None, config_file=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = Path(args.config or config_file or default_config_path())
    config = load_config(config_path)
    if args.server:
        config["server"] = args.server.rstrip("/")
    elif not config.get("server"):
        config["server"] = DEFAULT_SERVER
    if args.token:
        config["token"] = args.token
    if args.insecure:
        config["tls_verify"] = False
    if not hasattr(args, "func"):
        parser.print_usage()
        return 2
    try:
        return args.func(args, config, config_path)
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ncancelled", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
