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
    python3 zreport.py search "部署优化" -n 5
    python3 zreport.py search "GPU compose" --type material --json
    python3 zreport.py project plan show -p my-project

Apart from login/logout/whoami/skill, commands are not defined here: they
come from the server's operation registry (GET /api/ops), the same
definitions the in-app report assistant uses as tools. The manifest is
cached per server next to the credentials so --help works offline.

The token is stored in <config>/zreport/cli.json (0600). Self-signed
TLS: log in with --insecure once and the choice is remembered.
"""

import argparse
import base64
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import urlencode, urlparse

DEFAULT_SERVER = "http://127.0.0.1:8765"
# CLI 版本号：仅 CLI（本文件）有实际变化时递增并发 PyPI，勿随平台版本联动
__version__ = "1.6.0"
LOGIN_TIMEOUT_SECONDS = 15 * 60
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
- `zreport project weekly show -p <project> [week_key]` — report body as
  Markdown (default week: the current one)
- `zreport project materials list -p <project> [--scope all]` — materials with
  IDs and AI summaries (default: added this week)
- `zreport project supplement show -p <project> [week_key]` — the weekly
  supplement (本周补充: completed / in progress / blockers / next steps)
- `zreport project plan show -p <project>` — profile, objectives, milestones,
  deliverables
- `zreport project risks list -p <project>` — this week's system risk warnings
- `zreport project repos list -p <project>` — linked Git repositories;
  `project repos commits|activity -p <project> [-r owner/name]` fetch this
  week's commits or PRs/issues/boards from GitHub/GitLab (slower)

Commands other than login/logout/whoami/skill are discovered from the server
at startup, so `zreport --help` (and `--help` on any group) always lists what
the connected server supports. Every server command accepts `--json` for the
raw result.

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
  (the server accepts Markdown, text, HTML, PDF, Excel and images)
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


# ---------------------------------------------------------------- server operations
#
# Every command except login/logout/whoami/skill is an operation from the
# server's registry (the same one behind the report assistant's tools).
# The CLI discovers the manifest from GET /api/ops at startup, caches it
# per server next to the credentials, and builds subcommands, flags and
# terminal rendering from it; POST /api/ops/<name> runs the operation.

NATIVE_COMMANDS = {"login", "logout", "whoami", "skill"}
MANIFEST_TIMEOUT_SECONDS = 5


def require_login(config):
    if not config.get("token"):
        raise CliError("not signed in: run the login command first")


def manifest_cache_path(config_path):
    return Path(config_path).with_name("ops-cache.json")


def load_operations(config, config_path):
    """(manifest, error): the server's live manifest, else the cached copy
    for the same server, else None with the reason."""
    cache_path = manifest_cache_path(config_path)
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        if not isinstance(cache, dict):
            cache = {}
    except (OSError, ValueError):
        cache = {}
    server = config["server"].rstrip("/")
    try:
        manifest = api_request(config, "GET", "/api/ops", timeout=MANIFEST_TIMEOUT_SECONDS)
        if not isinstance(manifest.get("operations"), list):
            raise CliError("server does not publish an operation manifest (upgrade the zreport server)")
    except CliError as exc:
        cached = cache.get(server)
        if cached:
            return cached, None
        return None, str(exc)
    if cache.get(server, {}).get("version") != manifest.get("version"):
        cache[server] = manifest
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass  # the cache only speeds up offline --help
    return manifest, None


def add_operation_arguments(parser, op):
    for param in op["params"]:
        cli = param.get("cli") or {}
        kwargs = {"help": param["description"]}
        if param.get("enum"):
            kwargs["choices"] = param["enum"]
        if param["type"] == "integer":
            kwargs["type"] = int
        if param.get("default") is not None:
            kwargs["default"] = param["default"]
            kwargs["help"] += f" (default: {param['default']})"
        if cli.get("positional"):
            if not param["required"]:
                kwargs["nargs"] = "?"
            elif cli.get("multiple"):
                kwargs["nargs"] = "+"
            parser.add_argument(param["name"], **kwargs)
            continue
        kwargs["dest"] = param["name"]
        if param["type"] == "boolean":
            kwargs.pop("type", None)
            kwargs["action"] = "store_true"
        else:
            kwargs["required"] = bool(param["required"])
            if cli.get("multiple"):
                kwargs["nargs"] = "+"
            if param["type"] == "file":
                kwargs["metavar"] = "PATH"
        parser.add_argument(*cli.get("flags") or [f"--{param['name']}"], **kwargs)
    parser.add_argument("--json", dest="_json", action="store_true", help="print the raw JSON result")


def add_operations(sub, manifest):
    groups = manifest.get("groups") or {}
    nodes = {(): sub}
    parsers = {}
    for op in manifest["operations"]:
        command = op["command"]
        for depth in range(1, len(command)):
            path = tuple(command[:depth])
            if path in nodes:
                continue
            group = nodes[path[:-1]].add_parser(path[-1], help=groups.get(" ".join(path), ""))
            parsers[path] = group
            nodes[path] = group.add_subparsers(dest="_".join(path) + "_command", required=True)
        leaf = nodes[tuple(command[:-1])].add_parser(command[-1], help=op["summary"], description=op["description"])
        add_operation_arguments(leaf, op)
        leaf.set_defaults(func=cmd_operation, operation=op)


def operation_payload(args, op):
    payload = {}
    for param in op["params"]:
        value = getattr(args, param["name"], None)
        if value is None or value is False:
            continue
        if param["type"] == "file":
            files = []
            for raw_path in value:
                path = Path(raw_path).expanduser()
                try:
                    raw = path.read_bytes()
                except OSError as exc:
                    raise CliError(f"cannot read {path}: {exc}") from exc
                files.append({"filename": path.name, "content_base64": base64.b64encode(raw).decode("ascii")})
            value = files
        elif (param.get("cli") or {}).get("stdin") and value == "-":
            value = sys.stdin.read()
        payload[param["name"]] = value
    return payload


def cmd_operation(args, config, config_path):
    require_login(config)
    op = args.operation
    result = api_request(config, "POST", f"/api/ops/{op['name']}", payload=operation_payload(args, op), timeout=300)
    if args._json:
        # warnings stay inside the JSON so stdout remains parseable
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    render_result(op.get("render") or {"kind": "json"}, result)
    for warning in result.get("warnings") or []:
        print(f"note: {warning}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- rendering


def format_value(value, fmt=""):
    if value is None or value == "":
        return "-"
    for step in filter(None, (fmt or "").split("|")):
        name, _, arg = step.partition(":")
        if name == "datetime":
            value = str(value)[:16].replace("T", " ")
        elif name == "yesno":
            value = "yes" if value else ""
        elif name == "float4":
            value = f"{float(value or 0):.4f}"
        elif name == "join":
            value = ", ".join(map(str, value)) if isinstance(value, (list, tuple)) else value
        elif name == "oneline":
            value = re.sub(r"\s+", " ", str(value)).strip()
        elif name == "clip":
            value = clip_text(str(value), int(arg or 64))
    return str(value)


def fill_template(template, data):
    return re.sub(r"\{(\w+)\}", lambda m: str(data.get(m.group(1)) if data.get(m.group(1)) is not None else ""), template).strip()


def clip_text(text, width=64):
    """Clip to a display width, counting East-Asian characters as 2 columns."""
    out, used = "", 0
    for char in text:
        w = 2 if unicodedata.east_asian_width(char) in ("F", "W") else 1
        if used + w > width:
            return out + "…"
        out += char
        used += w
    return out


def render_result(render, result):
    kind = render.get("kind")
    if kind == "table":
        items = result.get(render["items"]) or []
        if render.get("title"):
            print(fill_template(render["title"], result))
        if not items and render.get("empty"):
            print(render["empty"])
            return
        columns = render["columns"]
        rows = [
            [str(rank) if c["key"] == "@rank" else format_value(item.get(c["key"]), c.get("format")) for c in columns]
            for rank, item in enumerate(items, start=1)
        ]
        print_table([c["header"] for c in columns], rows)
    elif kind == "record":
        for field in render.get("fields") or []:
            value = fill_template(field["template"], result) if "template" in field else result.get(field["key"])
            if value not in (None, ""):
                print(f"{field['label']}: {format_value(value, field.get('format'))}")
        if "body" in render:
            body = (result.get(render["body"]) or "").strip()
            print("\n" + (body or render.get("empty_body", "")))
        for field in render.get("after") or []:
            value = (result.get(field["key"]) or "").strip()
            if value:
                print(f"\n{field['label']}: {value}")
    elif kind == "text":
        print((result.get(render["field"]) or "").strip())
    elif kind == "message":
        print(result.get("message") or "done")
    else:
        # warnings go to stderr below; keep them out of the rendered body
        body = {k: v for k, v in result.items() if k != "warnings"}
        print(json.dumps(body, ensure_ascii=False, indent=2))


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


def add_global_arguments(parser):
    parser.add_argument("--server", help=f"server URL (default {DEFAULT_SERVER}; from saved config after login)")
    parser.add_argument("--token", help="use this Bearer token (default: from saved config)")
    parser.add_argument("--insecure", action="store_true", help="skip TLS certificate verification (self-signed certs)")
    parser.add_argument("--config", help="credentials file path (default <config>/zreport/cli.json)")


def build_parser(manifest=None):
    parser = argparse.ArgumentParser(
        prog="zreport",
        description="zreport (Zero Report) command-line client",
        epilog=None if manifest else "Project, TODO and search commands are discovered from the server; run `zreport --server URL --help` to list them.",
    )
    parser.add_argument("--version", action="version", version=f"zreport {__version__}")
    add_global_arguments(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="sign in with the device authorization flow")
    login.add_argument("--server", help="server URL, e.g. http://127.0.0.1:8765")
    login.add_argument("--insecure", action="store_true", help="skip TLS certificate verification (self-signed certs)")
    login.set_defaults(func=cmd_login)

    logout = sub.add_parser("logout", help="sign out and clear local credentials")
    logout.set_defaults(func=cmd_logout)

    whoami = sub.add_parser("whoami", help="show the signed-in user")
    whoami.set_defaults(func=cmd_whoami)

    if manifest:
        add_operations(sub, manifest)

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


def first_command(argv):
    """The first positional token, skipping global options and their values."""
    takes_value = {"--server", "--token", "--config"}
    skip = False
    for token in argv:
        if skip:
            skip = False
            continue
        if token in takes_value:
            skip = True
            continue
        if token.startswith("-"):
            continue
        return token
    return None


def main(argv=None, config_file=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    pre = argparse.ArgumentParser(add_help=False)
    add_global_arguments(pre)
    early, _ = pre.parse_known_args(argv)
    config_path = Path(early.config or config_file or default_config_path())
    try:
        config = load_config(config_path)
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if early.server:
        config["server"] = early.server.rstrip("/")
    elif not config.get("server"):
        config["server"] = DEFAULT_SERVER
    if early.token:
        config["token"] = early.token
    if early.insecure:
        config["tls_verify"] = False
    command = first_command(argv)
    manifest, manifest_error = (None, None)
    if command not in NATIVE_COMMANDS:
        manifest, manifest_error = load_operations(config, config_path)
        if manifest is None and command is not None:
            print(f"error: cannot load the command list from {config['server']}: {manifest_error}", file=sys.stderr)
            return 1
    parser = build_parser(manifest)
    args = parser.parse_args(argv)
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
