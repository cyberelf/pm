"""Read-only tools the report assistant calls on demand.

Tool names mirror the zreport CLI read commands where one exists
(`project weekly list|show`, `search`, `material show`, `report show`,
`todo list|show`) and follow the same naming for project context the CLI
does not expose yet (materials list, plan, weekly supplement, risks, Git).
The application executes every tool itself, scoped to one project and the
asking account, and returns bounded JSON text: the model never touches the
database, uploaded files or Git credentials.
"""

import json
import threading
import time

from .git_sources import fetch_org_projects, git_auth_for_user
from .reports import repo_commit_context, repo_extras_context, repo_fetch_switches_on
from .search_index import search
from .timeutil import parse_iso, week_bounds, week_key_for

TOOL_RESULT_MAX_CHARS = 12000
MATERIAL_CONTENT_MAX_CHARS = 10000
GIT_CACHE_SECONDS = 600

_git_cache = {}
_git_lock = threading.Lock()

_WEEK = {"type": "string", "description": "项目周，格式 YYYY-Www，例如 2026-W47；省略表示当前周"}
_REPO = {"type": "string", "description": "仓库名（owner/name 或 GitLab 路径）；省略表示全部已连接仓库"}

TOOL_SPECS = [
    {
        "name": "weekly_list",
        "description": "列出本项目所有已生成周报的周次与更新时间（对应 CLI: zreport project weekly list）。",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "weekly_show",
        "description": "读取指定周的周报 Markdown 正文与该周补充（对应 CLI: zreport project weekly show [week]）。当前周报已在上下文中，只在需要历史周时调用。",
        "parameters": {"type": "object", "properties": {"week_key": _WEEK}},
    },
    {
        "name": "search",
        "description": "在本项目的周报和资料中做关键词+向量混合检索，返回带 ID 的片段（对应 CLI: zreport search --project）。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索词或问题"},
                "type": {"type": "string", "enum": ["report", "material"], "description": "只搜周报或只搜资料"},
                "top": {"type": "integer", "minimum": 1, "maximum": 20, "description": "返回条数，默认 8"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "material_show",
        "description": "按 ID 读取一份资料的摘要与提取全文（对应 CLI: zreport material show <id>）。ID 来自 materials_list 或 search。",
        "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
    },
    {
        "name": "report_show",
        "description": "按 ID 读取一份周报正文（对应 CLI: zreport report show <id>）。ID 来自 search。",
        "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
    },
    {
        "name": "todo_list",
        "description": "列出提问用户自己的 TODO 及其关联项目（对应 CLI: zreport todo list [--all]）。",
        "parameters": {
            "type": "object",
            "properties": {"all": {"type": "boolean", "description": "包含已关闭的 TODO"}},
        },
    },
    {
        "name": "todo_show",
        "description": "按 ID 读取提问用户的一条 TODO 详情与关闭原因（对应 CLI: zreport todo show <id>）。",
        "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
    },
    {
        "name": "materials_list",
        "description": "列出本项目的过程资料（ID、文件名、来源、创建时间、AI 摘要）。scope=this_week 只列本周新增。",
        "parameters": {
            "type": "object",
            "properties": {"scope": {"type": "string", "enum": ["this_week", "all"], "description": "默认 this_week"}},
        },
    },
    {
        "name": "weekly_update_show",
        "description": "读取某周的本周补充（已完成、进行中、阻塞、下周计划等手工填写内容）。",
        "parameters": {"type": "object", "properties": {"week_key": _WEEK}},
    },
    {
        "name": "plan_show",
        "description": "读取项目简介、状态、起止日期以及计划目标、里程碑和交付物。",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "risks_list",
        "description": "列出本周由确定性规则产生的系统风险预警（缺少补充、里程碑逾期等）。",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "git_repos_list",
        "description": "列出本项目关联的 Git 仓库、连接状态、跟踪分支、备注和最近活动（本地数据，速度快）。",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "git_commits",
        "description": "获取本周已连接仓库在跟踪分支上的提交（调用 GitHub/GitLab API，较慢，结果缓存 10 分钟）。",
        "parameters": {"type": "object", "properties": {"repo": _REPO}},
    },
    {
        "name": "git_activity",
        "description": "获取本周仓库的 PR/MR、Issue、里程碑、Projects 看板以及组织级看板（按仓库抓取开关，调用远程 API，较慢，结果缓存 10 分钟）。",
        "parameters": {"type": "object", "properties": {"repo": _REPO}},
    },
]

TOOL_NAMES = {spec["name"] for spec in TOOL_SPECS}


class ToolError(Exception):
    """A tool call the model can correct (bad id, unknown week, ...)."""


def clip(text, limit=TOOL_RESULT_MAX_CHARS):
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…（已截断，原长度 {len(text)} 字符）"


def clear_git_cache():
    with _git_lock:
        _git_cache.clear()


class AssistantTools:
    def __init__(self, conn, project, user_id, week_key):
        self.conn = conn
        self.project = project
        self.project_id = project["id"]
        self.user_id = user_id
        self.week_key = week_key

    def run(self, name, args):
        """Execute one tool and return its bounded text result; errors come
        back as text so the model can recover within the same turn."""
        if name not in TOOL_NAMES:
            return json.dumps({"error": f"unknown tool {name}"}, ensure_ascii=False)
        try:
            result = getattr(self, f"tool_{name}")(**(args or {}))
        except ToolError as exc:
            result = {"error": str(exc)}
        except (TypeError, ValueError) as exc:
            result = {"error": f"invalid arguments: {exc}"}
        except Exception as exc:  # network or provider failures stay inside the turn
            result = {"error": f"{name} failed: {exc}"}
        return clip(json.dumps(result, ensure_ascii=False, default=str))

    # ------------------------------------------------------------ CLI mirrors

    def tool_weekly_list(self):
        rows = self.conn.execute(
            "SELECT id, week_key, updated_at, edited_at FROM weekly_reports WHERE project_id = ? ORDER BY week_key DESC",
            (self.project_id,),
        ).fetchall()
        return {
            "current_week": self.week_key,
            "reports": [
                {"id": r["id"], "week_key": r["week_key"], "updated_at": r["updated_at"], "edited": bool(r["edited_at"])}
                for r in rows
            ],
        }

    def tool_weekly_show(self, week_key=None):
        week_key = (week_key or self.week_key).strip()
        row = self.conn.execute(
            "SELECT id, week_key, content_md, supplement_json, updated_at FROM weekly_reports WHERE project_id = ? AND week_key = ?",
            (self.project_id, week_key),
        ).fetchone()
        if not row:
            raise ToolError(f"no weekly report for {week_key}; weekly_list shows available weeks")
        raw = row["supplement_json"] or ""
        return {
            "id": row["id"],
            "week_key": row["week_key"],
            "updated_at": row["updated_at"],
            "content_md": row["content_md"],
            "supplement": json.loads(raw) if raw else None,
        }

    def tool_search(self, query, type=None, top=8):
        query = (query or "").strip()
        if not query:
            raise ToolError("query is required")
        if type not in (None, "", "report", "material"):
            raise ToolError("type must be report or material")
        top = max(1, min(int(top or 8), 20))
        result = search(self.conn, self.user_id, query, limit=top, source_type=type or None, project_id=self.project_id)
        self.conn.commit()
        return {
            "mode": result["mode"],
            "hits": [
                {k: hit.get(k) for k in ("type", "source_id", "title", "week_key", "snippet")}
                for hit in result["hits"]
            ],
        }

    def tool_material_show(self, id):
        row = self.conn.execute(
            """
            SELECT id, filename, source_type, extraction_status, extraction_error, extracted_text,
                   summary, created_at, updated_at
            FROM materials WHERE id = ? AND project_id = ?
            """,
            (int(id), self.project_id),
        ).fetchone()
        if not row:
            raise ToolError(f"material {id} not found in this project")
        item = dict(row)
        item["content"] = clip(item.pop("extracted_text") or "", MATERIAL_CONTENT_MAX_CHARS)
        return item

    def tool_report_show(self, id):
        row = self.conn.execute(
            "SELECT id, week_key, content_md, updated_at FROM weekly_reports WHERE id = ? AND project_id = ?",
            (int(id), self.project_id),
        ).fetchone()
        if not row:
            raise ToolError(f"weekly report {id} not found in this project")
        return dict(row)

    def _todos(self):
        return self.conn.execute(
            """
            SELECT t.id, t.title, t.description, t.status, t.close_reason, t.created_at, t.updated_at,
                   p.name AS project_name
            FROM todos t LEFT JOIN projects p ON p.id = t.project_id
            WHERE t.user_id = ?
            ORDER BY CASE t.status WHEN 'todo' THEN 0 WHEN 'doing' THEN 1 ELSE 2 END, t.updated_at DESC
            """,
            (self.user_id,),
        ).fetchall()

    def tool_todo_list(self, all=False):
        rows = [r for r in self._todos() if all or r["status"] != "closed"]
        return {
            "todos": [
                {"id": r["id"], "status": r["status"], "project": r["project_name"], "title": r["title"]}
                for r in rows[:100]
            ]
        }

    def tool_todo_show(self, id):
        row = next((r for r in self._todos() if r["id"] == int(id)), None)
        if not row:
            raise ToolError(f"TODO {id} not found")
        return dict(row)

    # ------------------------------------------------------- project context

    def tool_materials_list(self, scope="this_week"):
        rows = self.conn.execute(
            """
            SELECT id, filename, source_type, extraction_status, summary, created_at
            FROM materials WHERE project_id = ? ORDER BY id DESC
            """,
            (self.project_id,),
        ).fetchall()
        tz = self.project["timezone"]
        if scope != "all":
            rows = [r for r in rows if parse_iso(r["created_at"]) and week_key_for(parse_iso(r["created_at"]), tz) == self.week_key]
        return {
            "scope": "all" if scope == "all" else "this_week",
            "materials": [{**dict(r), "summary": (r["summary"] or "")[:400]} for r in rows[:80]],
        }

    def tool_weekly_update_show(self, week_key=None):
        week_key = (week_key or self.week_key).strip()
        row = self.conn.execute(
            "SELECT * FROM weekly_updates WHERE project_id = ? AND week_key = ?", (self.project_id, week_key)
        ).fetchone()
        if not row:
            return {"week_key": week_key, "weekly_update": None}
        item = dict(row)
        item.pop("project_id", None)
        return {"week_key": week_key, "weekly_update": item}

    def tool_plan_show(self):
        plan = self.conn.execute("SELECT * FROM project_plans WHERE project_id = ?", (self.project_id,)).fetchone()
        p = self.project
        return {
            "profile": {
                k: p[k] for k in ("name", "description", "status", "owner", "start_date", "end_date", "timezone")
            },
            "plan": {
                "objectives": plan["objectives"] if plan else "",
                "milestones": json.loads(plan["milestones_json"]) if plan else [],
                "deliverables": json.loads(plan["deliverables_json"]) if plan else [],
            },
        }

    def tool_risks_list(self):
        rows = self.conn.execute(
            """
            SELECT rule, severity, title, details, status FROM risk_warnings
            WHERE project_id = ? AND week_key = ? AND status = 'active' ORDER BY severity DESC, id
            """,
            (self.project_id, self.week_key),
        ).fetchall()
        return {"week_key": self.week_key, "risks": [dict(r) for r in rows]}

    def _repos(self, repo=None):
        rows = self.conn.execute(
            """
            SELECT * FROM github_repos WHERE project_id = ? AND enabled = 1 ORDER BY id
            """,
            (self.project_id,),
        ).fetchall()
        if repo:
            rows = [r for r in rows if r["repo"].lower() == repo.strip().lower()]
            if not rows:
                raise ToolError(f"repository {repo} is not linked to this project; git_repos_list shows them")
        return rows

    def tool_git_repos_list(self):
        return {
            "repos": [
                {
                    "repo": r["repo"],
                    "git_mode": r["git_mode"],
                    "status": r["status"],
                    "notes": r["notes"],
                    "tracked_branches": json.loads(r["tracked_branches_json"] or '["main"]'),
                    "last_activity_at": r["last_activity_at"],
                    "activity_summary": r["activity_summary"],
                }
                for r in self._repos()
            ]
        }

    def _git_cached(self, kind, row, fetch):
        key = (self.project_id, row["id"], kind)
        fingerprint = f"{self.week_key}|{row['updated_at']}"
        now = time.monotonic()
        with _git_lock:
            hit = _git_cache.get(key)
            if hit and hit[0] == fingerprint and now - hit[1] < GIT_CACHE_SECONDS:
                return hit[2]
        value = fetch()
        with _git_lock:
            _git_cache[key] = (fingerprint, now, value)
        return value

    def _week_window(self):
        return week_bounds(self.project["timezone"])

    def tool_git_commits(self, repo=None):
        rows = [r for r in self._repos(repo) if r["status"] == "connected"]
        if not rows:
            return {"repos": [], "note": "no connected repositories"}
        start, end = self._week_window()
        auth_info = git_auth_for_user(self.conn, self.project["user_id"])
        return {
            "week_key": self.week_key,
            "repos": [
                self._git_cached("commits", r, lambda r=r: repo_commit_context(r, start, end, auth_info)) for r in rows
            ],
        }

    def tool_git_activity(self, repo=None):
        rows = [r for r in self._repos(repo) if r["status"] == "connected"]
        if not rows:
            return {"repos": [], "note": "no connected repositories"}
        start, end = self._week_window()
        auth_info = git_auth_for_user(self.conn, self.project["user_id"])
        extras = [
            self._git_cached("extras", r, lambda r=r: repo_extras_context(r, start, end, auth_info))
            for r in rows
            if repo_fetch_switches_on(r)
        ]
        result = {"week_key": self.week_key, "repos": extras}
        if not repo:
            result["org_projects"] = fetch_org_projects(rows, auth_info)
        if not extras and not result.get("org_projects"):
            result["note"] = "PR/Issue/milestone/board fetching is switched off for these repositories"
        return result


def inventory(conn, project, week_key):
    """Cheap local overview placed in the prompt so the model knows which
    tools are worth calling."""
    pid = project["id"]
    tz = project["timezone"]
    materials = conn.execute("SELECT created_at FROM materials WHERE project_id = ?", (pid,)).fetchall()
    this_week = sum(
        1 for r in materials if parse_iso(r["created_at"]) and week_key_for(parse_iso(r["created_at"]), tz) == week_key
    )
    repos = conn.execute(
        "SELECT repo, status FROM github_repos WHERE project_id = ? AND enabled = 1 ORDER BY id", (pid,)
    ).fetchall()
    weeks = [r["week_key"] for r in conn.execute(
        "SELECT week_key FROM weekly_reports WHERE project_id = ? ORDER BY week_key DESC LIMIT 12", (pid,)
    )]
    update = conn.execute(
        "SELECT 1 FROM weekly_updates WHERE project_id = ? AND week_key = ?", (pid, week_key)
    ).fetchone()
    risks = conn.execute(
        "SELECT COUNT(*) AS n FROM risk_warnings WHERE project_id = ? AND week_key = ? AND status = 'active'",
        (pid, week_key),
    ).fetchone()["n"]
    return {
        "report_weeks": weeks,
        "materials_total": len(materials),
        "materials_this_week": this_week,
        "weekly_update_this_week": bool(update),
        "repos": [f"{r['repo']} ({r['status']})" for r in repos],
        "active_risks": risks,
    }
