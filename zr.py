#!/usr/bin/env python3
"""Command-line client (zr) for the zreport server.

Standard library only. Sign in once with the OAuth-style device flow
(`zr login`), then work with projects, materials, and TODOs from
the terminal:

    python3 zr.py login --server http://127.0.0.1:8765
    python3 zr.py projects
    python3 zr.py materials add 周报系统 --text "本周完成设备授权" --title 进展
    python3 zr.py materials add 周报系统 --file notes.md 设计稿.pdf
    python3 zr.py todos
    python3 zr.py todo add "整理部署文档" -d "补充 GPU compose 说明"
    python3 zr.py todo status 3 doing
    python3 zr.py todo done 3 --project 周报系统 --reason "文档已合并"

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
from pathlib import Path

DEFAULT_SERVER = "http://127.0.0.1:8765"
LOGIN_TIMEOUT_SECONDS = 15 * 60
MATERIAL_EXTENSIONS = {".md": "text/markdown", ".markdown": "text/markdown", ".txt": "text/plain", ".pdf": "application/pdf"}
TODO_STATUSES = ("todo", "doing")


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
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    opener = build_opener(not config.get("tls_verify", True))
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if config.get("token"):
        headers["Authorization"] = f"Bearer {config['token']}"
    request = urllib.request.Request(config["server"].rstrip("/") + path, data=data, headers=headers, method=method)
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
        raise CliError(f"cannot reach {config['server']}: {exc.reason}") from exc
    return json.loads(body) if body else {}


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
    print(f"1. 打开授权页面: {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    print(f"2. 登录后输入授权码: {user_code}")
    print("等待授权", end="", flush=True)

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
            print(f"已登录为 {config['user']}（凭据保存在 {config_path}）")
            return 0
        if status == "denied":
            raise CliError("授权被拒绝")
        raise CliError("授权码已过期，请重新登录")
    print()
    raise CliError("等待授权超时，请重新登录")


def cmd_logout(args, config, config_path):
    if config.get("token"):
        try:
            api_request(config, "POST", "/api/auth/logout", payload={})
        except CliError:
            pass  # token may already be gone server-side; clear locally anyway
    config.pop("token", None)
    config.pop("user", None)
    save_config(config_path, config)
    print("已退出登录")
    return 0


def cmd_whoami(args, config, config_path):
    state = api_request(config, "GET", "/api/auth/state")
    user = state.get("current_user")
    if not user:
        print("未登录（运行 login 子命令）")
        return 1
    role = "管理员" if user.get("is_admin") else "用户"
    print(f"{user['username']}（{role}） @ {config['server']}（服务版本 v{state.get('version', '?')}）")
    return 0


# ---------------------------------------------------------------- projects & materials


def require_login(config):
    if not config.get("token"):
        raise CliError("尚未登录：先运行 login 子命令")


def fetch_projects(config):
    state = api_request(config, "GET", "/api/state")
    return state.get("projects") or []


def resolve_project(config, ref):
    projects = fetch_projects(config)
    for project in projects:
        if str(project["id"]) == str(ref) or project["name"] == ref:
            return project
    raise CliError(f"找不到项目：{ref}（用 projects 子命令查看列表）")


def cmd_projects(args, config, config_path):
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
    print_table(["ID", "项目", "状态", "时区", "更新时间"], rows)
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
                raise CliError(f"不支持的文件类型：{path.name}（支持 {' '.join(sorted(MATERIAL_EXTENSIONS))}）")
            try:
                raw = path.read_bytes()
            except OSError as exc:
                raise CliError(f"无法读取 {path}: {exc}") from exc
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
        print(f"已上传 {len(files)} 个附件到「{project['name']}」（材料 ID：{'、'.join(str(i) for i in result.get('ids', []))}）")
        return 0
    text = args.text
    if text == "-":
        text = sys.stdin.read()
    text = (text or "").strip()
    if not text:
        raise CliError("请提供内容：--text \"...\"（或 --text - 从管道读取），或用 --file 上传附件")
    title = (args.title or "").strip() or "CLI 笔记"
    result = api_request(
        config,
        "POST",
        f"/api/projects/{project['id']}/materials",
        payload={"source_type": "manual", "title": title, "content": text},
    )
    print(f"已提交文字资料到「{project['name']}」（材料 ID：{result.get('id')}）")
    return 0


# ---------------------------------------------------------------- todos


def cmd_todos(args, config, config_path):
    require_login(config)
    todos = api_request(config, "GET", "/api/todos").get("todos") or []
    if not args.all:
        todos = [todo for todo in todos if todo["status"] != "closed"]
    status_label = {"todo": "待办", "doing": "进行中", "closed": "已关闭"}
    rows = [
        (
            todo["id"],
            status_label.get(todo["status"], todo["status"]),
            todo.get("project_name") or "-",
            todo["title"],
        )
        for todo in todos
    ]
    print_table(["ID", "状态", "项目", "标题"], rows)
    return 0


def cmd_todo_add(args, config, config_path):
    require_login(config)
    result = api_request(config, "POST", "/api/todos", payload={"title": args.title, "description": args.description or ""})
    print(f"已创建 TODO #{result.get('id')}：{args.title}")
    return 0


def cmd_todo_status(args, config, config_path):
    require_login(config)
    api_request(config, "PUT", f"/api/todos/{args.id}", payload={"status": args.status})
    print(f"TODO #{args.id} 状态改为 {args.status}")
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
    archived = f"，归档为「{project['name']}」的材料 #{material_id}" if material_id else ""
    print(f"TODO #{args.id} 已完成{archived}")
    return 0


# ---------------------------------------------------------------- parser


def build_parser():
    parser = argparse.ArgumentParser(prog="zr", description="zreport (Zero Report) 命令行客户端")
    parser.add_argument("--server", help=f"服务地址（默认 {DEFAULT_SERVER}，登录后取自配置）")
    parser.add_argument("--token", help="直接使用给定的 Bearer token（默认取自配置）")
    parser.add_argument("--insecure", action="store_true", help="跳过自签名 TLS 证书校验")
    parser.add_argument("--config", help="凭据文件路径（默认 <config>/zreport/cli.json）")
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="设备授权登录")
    login.add_argument("--server", help="服务地址，例如 http://127.0.0.1:8765")
    login.add_argument("--insecure", action="store_true", help="跳过自签名 TLS 证书校验")
    login.set_defaults(func=cmd_login)

    logout = sub.add_parser("logout", help="退出登录并清除本地凭据")
    logout.set_defaults(func=cmd_logout)

    whoami = sub.add_parser("whoami", help="显示当前登录用户")
    whoami.set_defaults(func=cmd_whoami)

    projects = sub.add_parser("projects", help="列出项目")
    projects.set_defaults(func=cmd_projects)

    materials = sub.add_parser("materials", help="项目资料")
    materials_sub = materials.add_subparsers(dest="materials_command", required=True)
    materials_add = materials_sub.add_parser("add", help="提交资料（文字或附件）")
    materials_add.add_argument("project", help="项目 ID 或名称")
    materials_add.add_argument("--text", help="文字内容；传 - 时从标准输入读取")
    materials_add.add_argument("--title", help="文字资料标题（默认 CLI 笔记）")
    materials_add.add_argument("--file", nargs="+", metavar="PATH", help="附件（.md .markdown .txt .pdf，可多个）")
    materials_add.set_defaults(func=cmd_materials_add)

    todos = sub.add_parser("todos", help="列出 TODO")
    todos.add_argument("--all", action="store_true", help="包含已关闭的 TODO")
    todos.set_defaults(func=cmd_todos)

    todo = sub.add_parser("todo", help="TODO 操作")
    todo_sub = todo.add_subparsers(dest="todo_command", required=True)
    todo_add = todo_sub.add_parser("add", help="新建 TODO")
    todo_add.add_argument("title", help="标题")
    todo_add.add_argument("-d", "--description", help="补充说明")
    todo_add.set_defaults(func=cmd_todo_add)

    todo_status = todo_sub.add_parser("status", help="修改 TODO 状态")
    todo_status.add_argument("id", type=int, help="TODO ID")
    todo_status.add_argument("status", choices=TODO_STATUSES, help="目标状态")
    todo_status.set_defaults(func=cmd_todo_status)

    todo_done = todo_sub.add_parser("done", help="完成 TODO 并归档到项目")
    todo_done.add_argument("id", type=int, help="TODO ID")
    todo_done.add_argument("-p", "--project", required=True, help="归档到的项目（ID 或名称）")
    todo_done.add_argument("-r", "--reason", default="已完成", help="完成说明（默认：已完成）")
    todo_done.set_defaults(func=cmd_todo_done)

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
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n已取消", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
