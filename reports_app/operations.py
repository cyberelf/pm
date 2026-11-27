"""The single registry of zreport operations.

Each operation is defined once, in the shape MCP uses for tools: a name, a
description, typed parameters (rendered as JSON Schema), a read-only
annotation and one handler. Three adapters expose the same registry:

- HTTP: ``GET /api/ops`` publishes the manifest, ``POST /api/ops/<name>``
  invokes an operation as the signed-in account (``http_invoke``).
- CLI: the ``zreport`` command discovers the manifest at runtime and builds
  its subcommands, flags and terminal rendering from it, so a new operation
  ships without a CLI release (``manifest``).
- Agent: the report assistant gets every operation marked ``agent`` as an
  LLM tool, bound to one project with bounded output (``AgentToolbox``).

Handlers receive an ``OpContext`` and validated arguments; a ``project``
parameter arrives already resolved to a row the caller may access with the
operation's role. Handlers raise ValidationError (400), PermissionError
(403) or LookupError (404) and return JSON-serialisable dicts.
"""

import base64
import hashlib
import json
import mimetypes
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .db import connect
from .git_sources import fetch_org_projects, git_auth_for_user
from .materials import add_uploaded_materials, store_manual_material
from .reports import repo_commit_context, repo_extras_context, repo_fetch_switches_on
from .risks import evaluate_risks
from .search_index import search
from .sharing import ACCESSIBLE_PROJECTS_SQL, project_role, require_role, touch_share_access
from .timeutil import current_week_key, parse_iso, week_bounds, week_key_for
from .todos import OPEN_STATUSES, close_todo, create_todo, update_todo
from .validation import ValidationError
from .workstreams import (
    material_links_map,
    resolve_workstream,
    set_material_links,
    workstream_detail,
    workstream_overview,
)

AGENT_RESULT_MAX_CHARS = 12000
AGENT_CONTENT_MAX_CHARS = 10000
TOOL_PREVIEW_CHARS = 1500  # result excerpt shown in the assistant's work log
GIT_CACHE_SECONDS = 600


# ---------------------------------------------------------------- model


@dataclass(frozen=True)
class Param:
    name: str
    type: str  # string | text | integer | boolean | project | file
    description: str
    required: bool = False
    enum: tuple = ()
    default: object = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    positional: bool = False  # CLI positional instead of a flag
    flags: tuple = ()  # CLI flags, default --<name>
    multiple: bool = False  # a list (CLI nargs="+")
    stdin: bool = False  # CLI value "-" reads standard input

    def schema(self):
        if self.type == "file":
            item = {
                "type": "object",
                "properties": {"filename": {"type": "string"}, "content_base64": {"type": "string"}},
                "required": ["filename", "content_base64"],
            }
        else:
            kind = {"integer": "integer", "boolean": "boolean"}.get(self.type, "string")
            item = {"type": kind}
            if self.enum:
                item["enum"] = list(self.enum)
            if self.minimum is not None:
                item["minimum"] = self.minimum
            if self.maximum is not None:
                item["maximum"] = self.maximum
        schema = {"type": "array", "items": item} if self.multiple else item
        schema["description"] = self.description
        if self.default is not None:
            schema["default"] = self.default
        return schema

    def public(self):
        item = {"name": self.name, "type": self.type, "description": self.description, "required": self.required}
        for key in ("enum", "default", "minimum", "maximum"):
            value = getattr(self, key)
            if value not in (None, ()):
                item[key] = list(value) if key == "enum" else value
        item["cli"] = {
            "positional": self.positional,
            "flags": list(self.flags) or [f"--{self.name.replace('_', '-')}"],
            "multiple": self.multiple,
            "stdin": self.stdin,
        }
        return item


@dataclass(frozen=True)
class Operation:
    name: str
    command: tuple  # CLI path, e.g. ("project", "weekly", "show")
    summary: str  # one line, CLI help
    description: str  # what an agent needs to know to pick it
    handler: Callable
    params: tuple = ()
    read_only: bool = True
    agent: bool = False  # exposed to the report assistant (read-only only)
    role: str = "read"  # project role a project parameter must grant
    render: dict = field(default_factory=lambda: {"kind": "json"})

    @property
    def project_param(self):
        return next((p for p in self.params if p.type == "project"), None)

    def input_schema(self, bind_project=False):
        params = [p for p in self.params if not (bind_project and p.type == "project")]
        return {
            "type": "object",
            "properties": {p.name: p.schema() for p in params},
            "required": [p.name for p in params if p.required],
            "additionalProperties": False,
        }

    def public(self):
        return {
            "name": self.name,
            "command": list(self.command),
            "summary": self.summary,
            "description": self.description,
            "annotations": {"readOnlyHint": self.read_only, "agent": self.agent},
            "params": [p.public() for p in self.params],
            "input_schema": self.input_schema(),
            "render": self.render,
        }


@dataclass
class OpContext:
    conn: object
    user_id: int
    bound_project_id: Optional[int] = None  # set by the agent adapter
    for_agent: bool = False


# CLI help for intermediate command groups
GROUPS = {
    "project": "project operations",
    "project weekly": "weekly reports",
    "project materials": "project materials",
    "project supplement": "weekly supplement (本周补充)",
    "project plan": "project plan and milestones",
    "project risks": "system risk warnings",
    "project repos": "linked Git repositories",
    "project workstreams": "workstreams (工作线) inside a project",
    "todo": "TODO operations",
    "material": "material operations",
    "report": "weekly report operations",
}

REGISTRY = {}


def operation(**kwargs):
    def decorate(handler):
        op = Operation(handler=handler, **kwargs)
        if op.name in REGISTRY:
            raise RuntimeError(f"duplicate operation {op.name}")
        if op.agent and not op.read_only:
            raise RuntimeError(f"agent operation {op.name} must be read-only")
        REGISTRY[op.name] = op
        return handler

    return decorate


PROJECT = Param("project", "project", "project ID or name", required=True, flags=("-p", "--project"))
WEEK = Param("week_key", "string", "project week like 2026-W47 (default: current week)", positional=True)


def col(header, key, fmt=""):
    return {"header": header, "key": key, "format": fmt}


# ---------------------------------------------------------------- helpers


def resolve_project(ctx, ref, role="read"):
    """A project the caller may access, by ID or exact name; agent calls are
    pinned to their bound project whatever the model passes."""
    if ctx.bound_project_id is not None:
        ref = ctx.bound_project_id
    ref = str(ref or "").strip()
    if not ref:
        raise ValidationError("project is required")
    rows = ctx.conn.execute(
        f"SELECT * FROM projects WHERE id IN {ACCESSIBLE_PROJECTS_SQL} ORDER BY id",
        (ctx.user_id, ctx.user_id),
    ).fetchall()
    project = next((r for r in rows if str(r["id"]) == ref), None) or next((r for r in rows if r["name"] == ref), None)
    if not project:
        raise LookupError(f"project not found: {ref} (see `project list`)")
    role_here = project_role(ctx.conn, project["id"], ctx.user_id)
    require_role(role_here, role)
    if role_here != "owner" and not ctx.for_agent:
        # CLI use counts as 上次访问
        touch_share_access(ctx.conn, project["id"], ctx.user_id)
    return project


def scoped_project_ids_sql(ctx):
    """SQL and binds limiting rows to the bound project, else to every
    project the caller can access."""
    if ctx.bound_project_id is not None:
        return "(?)", (ctx.bound_project_id,)
    return ACCESSIBLE_PROJECTS_SQL, (ctx.user_id, ctx.user_id)


def clip(text, limit):
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…（已截断，原长度 {len(text)} 字符）"


def week_of(project, week_key):
    return (week_key or "").strip() or current_week_key(project["timezone"])


# ---------------------------------------------------------------- read operations


@operation(
    name="project_list",
    command=("project", "list"),
    summary="list projects",
    description="List the projects the account owns or that are shared with it.",
    render={
        "kind": "table",
        "items": "projects",
        "columns": [
            col("ID", "id"), col("PROJECT", "name"), col("STATUS", "status"), col("ROLE", "role"),
            col("TIMEZONE", "timezone"), col("UPDATED", "updated_at", "datetime"),
        ],
    },
)
def project_list(ctx):
    rows = ctx.conn.execute(
        """
        SELECT p.id, p.name, p.status, p.timezone, p.updated_at,
               CASE WHEN ps.user_id IS NULL THEN 'owner' ELSE ps.role END AS role
        FROM projects p
        LEFT JOIN project_shares ps ON ps.project_id = p.id AND ps.user_id = ?
        WHERE p.user_id = ? OR ps.user_id = ?
        ORDER BY p.updated_at DESC
        """,
        (ctx.user_id, ctx.user_id, ctx.user_id),
    ).fetchall()
    return {"projects": [dict(r) for r in rows]}


@operation(
    name="weekly_list",
    command=("project", "weekly", "list"),
    summary="list generated weekly reports",
    description="List the weeks that have a generated weekly report in the project, newest first.",
    params=(PROJECT,),
    agent=True,
    render={
        "kind": "table",
        "title": "Weekly reports of '{project_name}':",
        "items": "reports",
        "columns": [col("ID", "id"), col("WEEK", "week_key"), col("CURRENT", "is_current", "yesno"),
                    col("EDITED", "edited", "yesno"), col("UPDATED", "updated_at", "datetime")],
    },
)
def weekly_list(ctx, project):
    current = current_week_key(project["timezone"])
    rows = ctx.conn.execute(
        "SELECT id, week_key, updated_at, edited_at FROM weekly_reports WHERE project_id = ? ORDER BY week_key DESC",
        (project["id"],),
    ).fetchall()
    return {
        "project_id": project["id"],
        "project_name": project["name"],
        "current_week": current,
        "reports": [
            {"id": r["id"], "week_key": r["week_key"], "is_current": r["week_key"] == current,
             "edited": bool(r["edited_at"]), "updated_at": r["updated_at"]}
            for r in rows
        ],
    }


@operation(
    name="weekly_show",
    command=("project", "weekly", "show"),
    summary="show a weekly report (default: current week)",
    description="Read a week's report Markdown and the weekly supplement archived with it.",
    params=(WEEK, PROJECT),
    agent=True,
    render={"kind": "text", "field": "content_md"},
)
def weekly_show(ctx, project, week_key=None):
    week_key = week_of(project, week_key)
    row = ctx.conn.execute(
        "SELECT id, week_key, content_md, supplement_json, updated_at, edited_at FROM weekly_reports WHERE project_id = ? AND week_key = ?",
        (project["id"], week_key),
    ).fetchone()
    if not row:
        raise LookupError(f"weekly report not found for {week_key} (`project weekly list` shows available weeks)")
    raw = row["supplement_json"] or ""
    return {
        "id": row["id"],
        "project_name": project["name"],
        "week_key": row["week_key"],
        "updated_at": row["updated_at"],
        "edited": bool(row["edited_at"]),
        "content_md": row["content_md"],
        "supplement": json.loads(raw) if raw else None,
    }


@operation(
    name="search",
    command=("search",),
    summary="hybrid keyword + vector search over weekly reports and materials",
    description="Search weekly reports and materials; hits carry type and source_id for material_show / report_show.",
    params=(
        Param("query", "string", "search text (Chinese or English)", required=True, positional=True),
        Param("project", "project", "limit to one project (ID or name)", flags=("-p", "--project")),
        Param("top", "integer", "max results", default=10, minimum=1, maximum=50, flags=("-n", "--top")),
        Param("type", "string", "limit to weekly reports or materials", enum=("report", "material")),
    ),
    agent=True,
    render={
        "kind": "table",
        "items": "hits",
        "empty": "No matches.",
        "columns": [
            col("#", "@rank"), col("TYPE", "type"), col("ID", "source_id"), col("PROJECT", "project_name"),
            col("TITLE", "title", "clip:40"), col("WEEK", "week_key"), col("SNIPPET", "snippet", "oneline|clip:64"),
            col("SCORE", "score", "float4"),
        ],
    },
)
def search_op(ctx, query, project=None, top=10, type=None):
    query = (query or "").strip()
    if not query:
        raise ValidationError("query is required")
    project_id = project["id"] if project else ctx.bound_project_id
    result = search(ctx.conn, ctx.user_id, query, limit=top, source_type=type or None, project_id=project_id)
    ctx.conn.commit()
    warnings = []
    if not result.get("embedding_configured"):
        warnings.append("vector search is disabled — set an embedding model (llm_embedding_model) in 全局设置 for hybrid search")
    elif (result.get("index") or {}).get("embedding_error"):
        warnings.append(f"vector search failed this time: {result['index']['embedding_error']}")
    if ctx.for_agent:
        result = {"mode": result["mode"], "hits": [
            {k: h.get(k) for k in ("type", "source_id", "title", "week_key", "snippet")} for h in result["hits"]
        ]}
    if warnings:
        result["warnings"] = warnings
    return result


@operation(
    name="material_show",
    command=("material", "show"),
    summary="show a material's full content by ID (from `search`)",
    description="Read one material's summary and extracted full text by ID (IDs come from materials_list or search).",
    params=(Param("id", "integer", "material ID (the ID column of `search`)", required=True, positional=True),),
    agent=True,
    render={
        "kind": "record",
        "fields": [
            {"label": "Material", "template": "#{id} {filename}"}, {"label": "Project", "key": "project_name"},
            {"label": "Status", "key": "extraction_status"}, {"label": "Summary", "key": "summary"},
            {"label": "Created", "key": "created_at", "format": "datetime"},
        ],
        "body": "content",
        "empty_body": "(no extracted text)",
    },
)
def material_show(ctx, id):
    scope_sql, binds = scoped_project_ids_sql(ctx)
    row = ctx.conn.execute(
        f"""
        SELECT m.id, m.project_id, p.name AS project_name, m.filename, m.source_type, m.content_type,
               m.extraction_status, m.extraction_error, m.summary, m.extracted_text, m.created_at, m.updated_at
        FROM materials m JOIN projects p ON p.id = m.project_id
        WHERE m.id = ? AND m.project_id IN {scope_sql}
        """,
        (id, *binds),
    ).fetchone()
    if not row:
        raise LookupError(f"material #{id} not found")
    item = dict(row)
    content = item.pop("extracted_text") or ""
    item["content"] = clip(content, AGENT_CONTENT_MAX_CHARS) if ctx.for_agent else content
    return item


@operation(
    name="report_show",
    command=("report", "show"),
    summary="show a weekly report by ID (from `search`)",
    description="Read one weekly report by ID (IDs come from search or weekly_list).",
    params=(Param("id", "integer", "weekly report ID (the ID column of `search`)", required=True, positional=True),),
    agent=True,
    render={
        "kind": "record",
        "fields": [{"label": "Report", "template": "#{id}"}, {"label": "Project", "key": "project_name"},
                   {"label": "Week", "key": "week_key"}],
        "body": "content_md",
    },
)
def report_show(ctx, id):
    scope_sql, binds = scoped_project_ids_sql(ctx)
    row = ctx.conn.execute(
        f"""
        SELECT wr.id, wr.project_id, p.name AS project_name, wr.week_key, wr.content_md, wr.updated_at
        FROM weekly_reports wr JOIN projects p ON p.id = wr.project_id
        WHERE wr.id = ? AND wr.project_id IN {scope_sql}
        """,
        (id, *binds),
    ).fetchone()
    if not row:
        raise LookupError(f"weekly report #{id} not found")
    return dict(row)


def _todo_rows(ctx):
    return ctx.conn.execute(
        """
        SELECT t.id, t.title, t.description, t.status, t.close_reason, t.created_at, t.updated_at,
               t.closed_at, p.name AS project_name
        FROM todos t LEFT JOIN projects p ON p.id = t.project_id
        WHERE t.user_id = ?
        ORDER BY CASE t.status WHEN 'todo' THEN 0 WHEN 'doing' THEN 1 ELSE 2 END,
                 t.starred DESC, t.position ASC, t.updated_at DESC, t.id DESC
        """,
        (ctx.user_id,),
    ).fetchall()


@operation(
    name="todo_list",
    command=("todo", "list"),
    summary="list TODOs",
    description="List the asking account's TODOs; closed ones show the project they were archived into.",
    params=(Param("all", "boolean", "include closed TODOs"),),
    agent=True,
    render={"kind": "table", "items": "todos",
            "columns": [col("ID", "id"), col("STATUS", "status"), col("PROJECT", "project_name"), col("TITLE", "title")]},
)
def todo_list(ctx, all=False):
    rows = [dict(r) for r in _todo_rows(ctx) if all or r["status"] != "closed"]
    if ctx.for_agent:
        rows = [{k: r[k] for k in ("id", "status", "project_name", "title")} for r in rows[:100]]
    return {"todos": rows}


@operation(
    name="todo_show",
    command=("todo", "show"),
    summary="show a TODO's details by ID",
    description="Read one of the asking account's TODOs with its description and close reason.",
    params=(Param("id", "integer", "TODO ID", required=True, positional=True),),
    agent=True,
    render={
        "kind": "record",
        "fields": [{"label": "TODO", "template": "#{id} {title}"}, {"label": "Status", "key": "status"},
                   {"label": "Project", "key": "project_name"}, {"label": "Created", "key": "created_at", "format": "datetime"}],
        "body": "description",
        "after": [{"label": "Close reason", "key": "close_reason"}],
    },
)
def todo_show(ctx, id):
    row = next((r for r in _todo_rows(ctx) if r["id"] == id), None)
    if not row:
        raise LookupError(f"TODO #{id} not found")
    return dict(row)


@operation(
    name="materials_list",
    command=("project", "materials", "list"),
    summary="list project materials (default: added this week)",
    description="List the project's materials with ID, filename, source, creation time and AI summary; scope=this_week lists only this week's new ones.",
    params=(PROJECT, Param("scope", "string", "which materials", enum=("this_week", "all"), default="this_week")),
    agent=True,
    render={"kind": "table", "items": "materials",
            "columns": [col("ID", "id"), col("CREATED", "created_at", "datetime"), col("SOURCE", "source_type"),
                        col("WORKSTREAM", "workstream", "clip:16"),
                        col("FILENAME", "filename", "clip:40"), col("SUMMARY", "summary", "oneline|clip:60")]},
)
def materials_list(ctx, project, scope="this_week"):
    rows = ctx.conn.execute(
        "SELECT id, filename, source_type, extraction_status, summary, created_at FROM materials WHERE project_id = ? ORDER BY id DESC",
        (project["id"],),
    ).fetchall()
    week = current_week_key(project["timezone"])
    if scope != "all":
        rows = [r for r in rows if parse_iso(r["created_at"]) and week_key_for(parse_iso(r["created_at"]), project["timezone"]) == week]
    names = {
        r["id"]: r["name"]
        for r in ctx.conn.execute("SELECT id, name FROM workstreams WHERE project_id = ?", (project["id"],))
    }
    links = material_links_map(ctx.conn, project["id"])
    items = [{**dict(r), "workstream": names.get((links.get(r["id"]) or {}).get("primary"), "")} for r in rows]
    if ctx.for_agent:
        items = [{**r, "summary": (r["summary"] or "")[:400]} for r in items[:80]]
    return {"project_name": project["name"], "scope": scope, "week_key": week, "materials": items}


@operation(
    name="supplement_show",
    command=("project", "supplement", "show"),
    summary="show a week's supplement (本周补充)",
    description="Read the manually entered weekly supplement (completed, in progress, blockers, risks, next steps) for a week.",
    params=(WEEK, PROJECT),
    agent=True,
    render={
        "kind": "record",
        "fields": [{"label": "Week", "key": "week_key"}, {"label": "Completed", "key": "completed"},
                   {"label": "In progress", "key": "in_progress"}, {"label": "Blockers", "key": "blockers"},
                   {"label": "Risks", "key": "risks"}, {"label": "Next steps", "key": "next_steps"},
                   {"label": "Updated", "key": "updated_at", "format": "datetime"}],
        "empty_body": "",
    },
)
def supplement_show(ctx, project, week_key=None):
    week_key = week_of(project, week_key)
    row = ctx.conn.execute(
        "SELECT week_key, completed, in_progress, blockers, risks, next_steps, updated_at FROM weekly_updates WHERE project_id = ? AND week_key = ?",
        (project["id"], week_key),
    ).fetchone()
    if not row:
        return {"week_key": week_key, "present": False, "warnings": [f"no weekly supplement for {week_key}"]}
    return {**dict(row), "present": True}


@operation(
    name="plan_show",
    command=("project", "plan", "show"),
    summary="show the project profile, objectives, milestones and deliverables",
    description="Read the project profile (description, status, dates) and plan objectives, milestones and deliverables.",
    params=(PROJECT,),
    agent=True,
)
def plan_show(ctx, project):
    plan = ctx.conn.execute("SELECT * FROM project_plans WHERE project_id = ?", (project["id"],)).fetchone()
    return {
        "profile": {k: project[k] for k in ("name", "description", "status", "owner", "start_date", "end_date", "timezone")},
        "plan": {
            "objectives": plan["objectives"] if plan else "",
            "milestones": json.loads(plan["milestones_json"]) if plan else [],
            "deliverables": json.loads(plan["deliverables_json"]) if plan else [],
            "updated_at": plan["updated_at"] if plan else None,
        },
    }


@operation(
    name="risks_list",
    command=("project", "risks", "list"),
    summary="list this week's system risk warnings",
    description="List this week's active risk warnings produced by deterministic rules (missing supplement, overdue milestones).",
    params=(PROJECT,),
    agent=True,
    render={"kind": "table", "items": "risks", "empty": "No active risk warnings.",
            "columns": [col("SEVERITY", "severity"), col("RULE", "rule"), col("TITLE", "title", "clip:40"),
                        col("DETAILS", "details", "oneline|clip:60")]},
)
def risks_list(ctx, project):
    week = current_week_key(project["timezone"])
    rows = ctx.conn.execute(
        "SELECT rule, severity, title, details, status FROM risk_warnings WHERE project_id = ? AND week_key = ? AND status = 'active' ORDER BY severity DESC, id",
        (project["id"], week),
    ).fetchall()
    return {"week_key": week, "risks": [dict(r) for r in rows]}


@operation(
    name="workstream_list",
    command=("project", "workstreams", "list"),
    summary="list the project's workstreams with health and latest snapshot",
    description="List the project's workstreams (工作线, parallel long-running lines of work; a 子工作线 sits under its "
                "parent, shown as `parent / name`) with status, health from deterministic rules (a parent rolls up its "
                "children), linked material counts, open/overdue tracking items, this week's linked PR/issue count and each "
                "one's latest weekly snapshot.",
    params=(PROJECT,),
    agent=True,
    render={"kind": "table", "items": "workstreams", "empty": "No workstreams.",
            "columns": [col("ID", "id"), col("WORKSTREAM", "label", "clip:28"), col("STATUS", "status"),
                        col("HEALTH", "health"), col("OWNER", "owner_label", "clip:12"), col("MATERIALS", "material_total"),
                        col("OPEN", "items_open"), col("PR/ISSUE", "git_week"), col("LATEST", "latest", "oneline|clip:60")]},
)
def workstream_list(ctx, project):
    data = workstream_overview(ctx.conn, project["id"], project["timezone"])
    items = []
    for item in data["workstreams"]:
        latest = next((c for c in reversed(item["cells"]) if c["snapshot"]), None)
        items.append({
            "label": f"└ {item['name']}" if item["parent_id"] else item["name"],
            **{k: item[k] for k in ("id", "name", "path", "parent_id", "goal", "owner_label", "status", "target_date", "health",
                                     "overdue_reasons", "child_alerts", "material_total", "last_material_at", "items_open",
                                     "items_overdue", "next_due", "git_week")},
            "latest": f"{latest['week_key']} {latest['snapshot']['summary']}" if latest else "",
        })
    return {"project_name": project["name"], "week_key": data["current_week"], "workstreams": items,
            "unassigned_materials": data["unassigned_materials"]}


@operation(
    name="workstream_show",
    command=("project", "workstreams", "show"),
    summary="show one workstream: goal, sub-workstreams, tracking items, milestones, weekly snapshots and linked materials",
    description="Read one workstream (by ID or exact name) with its parent or sub-workstreams (子工作线), goal, "
                "tracking items (待跟踪项, open first), milestones, linked pull requests / issues, weekly snapshots "
                "across weeks and linked materials (newest first); use it for questions "
                "about one line of work over time or what is still open on it.",
    params=(Param("workstream", "string", "workstream ID or exact name", required=True, positional=True), PROJECT),
    agent=True,
    render={
        "kind": "record",
        "fields": [{"label": "Workstream", "template": "#{id} {path}"}, {"label": "Status", "key": "status"},
                   {"label": "Health", "key": "health"}, {"label": "Owner", "key": "owner_label"},
                   {"label": "Target", "key": "target_date"}],
        "body": "goal",
        "after": [{"label": "Sub-workstreams", "key": "children_text"}, {"label": "Milestones", "key": "milestones_text"},
                  {"label": "Tracking items", "key": "items_text"},
                  {"label": "Pull requests / issues", "key": "git_text"}, {"label": "Timeline", "key": "timeline"}],
    },
)
def workstream_show(ctx, workstream, project):
    row = resolve_workstream(ctx.conn, project["id"], workstream)
    item = workstream_detail(ctx.conn, project["id"], row["id"], project["timezone"], ctx.user_id,
                             material_limit=60 if ctx.for_agent else 200)
    if ctx.for_agent:
        item["materials"] = [{**m, "summary": (m["summary"] or "")[:300]} for m in item["materials"]]
        item["snapshots"] = item["snapshots"][:26]
    item["items_text"] = "\n".join(
        f"[{'x' if i['status'] == 'done' else ' '}] {i['title']}"
        + (f" (due {i['due_date']})" if i["due_date"] else "") + (f" @{i['owner_label']}" if i["owner_label"] else "")
        for i in item["items"]
    )
    item["children_text"] = "\n".join(
        f"#{c['id']} {c['name']} [{c['status']}/{c['health']}]" + (f" {c['items_open']} open" if c["items_open"] else "")
        for c in item["child_items"]
    )
    item["milestones_text"] = "\n".join(
        f"[{'x' if m.get('status') == 'complete' else ' '}] {m.get('title', '')}"
        + (f" ({m['target_date']})" if m.get("target_date") else "")
        for m in sorted(item["milestones"], key=lambda m: m.get("target_date") or "9999")
    )
    if ctx.for_agent:
        item["git_items"] = item["git_items"][:25]
    item["git_text"] = "\n".join(
        f"{g['repo']}#{g['number']} {g['kind']} [{g['state']}] {g['title']} ({g['week_key']})" for g in item["git_items"]
    )
    item["timeline"] = "\n".join(
        f"{s['week_key']} [{s['status']}] {s['summary']}" + (f" → {s['next_step']}" if s["next_step"] else "")
        for s in item["snapshots"]
    )
    return item


def _repos(ctx, project, repo=None):
    rows = ctx.conn.execute(
        "SELECT * FROM github_repos WHERE project_id = ? AND enabled = 1 ORDER BY id", (project["id"],)
    ).fetchall()
    if repo:
        rows = [r for r in rows if r["repo"].lower() == repo.strip().lower()]
        if not rows:
            raise LookupError(f"repository {repo} is not linked to this project (see `project repos list`)")
    return rows


REPO = Param("repo", "string", "repository (owner/name or GitLab path); default: every connected one", flags=("-r", "--repo"))


@operation(
    name="repos_list",
    command=("project", "repos", "list"),
    summary="list linked Git repositories",
    description="List the project's linked Git repositories with connection status, tracked branches, notes and last activity (local data, fast).",
    params=(PROJECT,),
    agent=True,
    render={"kind": "table", "items": "repos",
            "columns": [col("REPO", "repo"), col("MODE", "git_mode"), col("STATUS", "status"),
                        col("BRANCHES", "tracked_branches", "join"), col("LAST ACTIVITY", "last_activity_at", "datetime"),
                        col("NOTES", "notes", "oneline|clip:40")]},
)
def repos_list(ctx, project):
    return {"repos": [
        {
            "repo": r["repo"], "git_mode": r["git_mode"], "status": r["status"], "notes": r["notes"],
            "tracked_branches": json.loads(r["tracked_branches_json"] or '["main"]'),
            "last_activity_at": r["last_activity_at"], "activity_summary": r["activity_summary"],
        }
        for r in _repos(ctx, project)
    ]}


_git_cache = {}
_git_lock = threading.Lock()


def clear_git_cache():
    with _git_lock:
        _git_cache.clear()


def _git_cached(kind, project, row, fetch):
    """Git API results per repository, reused for GIT_CACHE_SECONDS while
    the week and the repository settings stay the same."""
    key = (project["id"], row["id"], kind)
    fingerprint = f"{current_week_key(project['timezone'])}|{row['updated_at']}"
    now = time.monotonic()
    with _git_lock:
        hit = _git_cache.get(key)
        if hit and hit[0] == fingerprint and now - hit[1] < GIT_CACHE_SECONDS:
            return hit[2]
    value = fetch()
    with _git_lock:
        _git_cache[key] = (fingerprint, now, value)
    return value


@operation(
    name="repos_commits",
    command=("project", "repos", "commits"),
    summary="this week's commits of the connected repositories",
    description="Fetch this week's commits on the tracked branches of connected repositories (calls GitHub/GitLab, slow; cached 10 minutes). Pass repo when only one matters.",
    params=(PROJECT, REPO),
    agent=True,
)
def repos_commits(ctx, project, repo=None):
    rows = [r for r in _repos(ctx, project, repo) if r["status"] == "connected"]
    if not rows:
        return {"repos": [], "warnings": ["no connected repositories"]}
    start, end = week_bounds(project["timezone"])
    auth_info = git_auth_for_user(ctx.conn, project["user_id"])
    return {
        "week_key": current_week_key(project["timezone"]),
        "repos": [_git_cached("commits", project, r, lambda r=r: repo_commit_context(r, start, end, auth_info)) for r in rows],
    }


@operation(
    name="repos_activity",
    command=("project", "repos", "activity"),
    summary="this week's PRs/MRs, issues, milestones and boards",
    description="Fetch this week's pull/merge requests, issues, milestones and Projects boards per the repositories' fetch switches, plus organization boards (calls remote APIs, slow; cached 10 minutes).",
    params=(PROJECT, REPO),
    agent=True,
)
def repos_activity(ctx, project, repo=None):
    rows = [r for r in _repos(ctx, project, repo) if r["status"] == "connected"]
    if not rows:
        return {"repos": [], "warnings": ["no connected repositories"]}
    start, end = week_bounds(project["timezone"])
    auth_info = git_auth_for_user(ctx.conn, project["user_id"])
    result = {
        "week_key": current_week_key(project["timezone"]),
        "repos": [
            _git_cached("extras", project, r, lambda r=r: repo_extras_context(r, start, end, auth_info))
            for r in rows if repo_fetch_switches_on(r)
        ],
    }
    if not repo:
        result["org_projects"] = fetch_org_projects(rows, auth_info)
    if not result["repos"] and not result.get("org_projects"):
        result["warnings"] = ["PR/issue/milestone/board fetching is switched off for these repositories"]
    return result


# ---------------------------------------------------------------- write operations


@operation(
    name="materials_add",
    command=("project", "materials", "add"),
    summary="add material (text or file attachments)",
    description="Add a text material or upload file attachments to a project.",
    params=(
        PROJECT,
        Param("text", "text", "text content; pass - to read from stdin", stdin=True),
        Param("title", "string", "text material title (default: CLI note)"),
        Param("file", "file", "file attachments (Markdown, text, HTML, PDF, Excel, Word, images)", multiple=True),
        Param("workstream", "string", "workstream ID or exact name to file the material under"),
    ),
    read_only=False,
    role="upload",
    render={"kind": "message"},
)
def materials_add(ctx, project, text=None, title=None, file=None, workstream=None):
    chosen = resolve_workstream(ctx.conn, project["id"], workstream)["id"] if workstream else None
    if file:
        uploads = []
        for item in file:
            filename = str(item.get("filename") or "")
            uploads.append({
                "filename": filename,
                "content_base64": item.get("content_base64") or "",
                "content_type": mimetypes.guess_type(filename)[0] or "application/octet-stream",
            })
        ids = add_uploaded_materials(ctx.conn, project["id"], uploads, chosen)
        evaluate_risks(ctx.conn, project["id"])
        return {
            "ids": ids,
            "message": f"Uploaded {len(ids)} attachment(s) to '{project['name']}' (material IDs: {', '.join(map(str, ids))})",
        }
    content = (text or "").strip()
    if not content:
        raise ValidationError('provide content: --text "..." (or --text - to read stdin), or attach files with --file')
    material_id = store_manual_material(
        ctx.conn, project["id"], {"title": (title or "").strip() or "CLI note", "content": content}
    )
    if chosen:
        set_material_links(ctx.conn, project["id"], material_id, chosen)
    evaluate_risks(ctx.conn, project["id"])
    return {"id": material_id, "message": f"Submitted text material to '{project['name']}' (material ID: {material_id})"}


@operation(
    name="todo_add",
    command=("todo", "add"),
    summary="create a TODO",
    description="Create a TODO for the account.",
    params=(Param("title", "string", "title", required=True, positional=True),
            Param("description", "string", "details", flags=("-d", "--description"))),
    read_only=False,
    render={"kind": "message"},
)
def todo_add(ctx, title, description=None):
    todo_id = create_todo(ctx.conn, {"title": title, "description": description or ""}, ctx.user_id)
    return {"id": todo_id, "message": f"Created TODO #{todo_id}: {title}"}


@operation(
    name="todo_status",
    command=("todo", "status"),
    summary="change a TODO's status",
    description="Move an open TODO between todo and doing.",
    params=(Param("id", "integer", "TODO ID", required=True, positional=True),
            Param("status", "string", "target status", required=True, positional=True, enum=tuple(sorted(OPEN_STATUSES)))),
    read_only=False,
    render={"kind": "message"},
)
def todo_status(ctx, id, status):
    update_todo(ctx.conn, id, {"status": status}, ctx.user_id)
    return {"id": id, "status": status, "message": f"TODO #{id} status set to {status}"}


@operation(
    name="todo_done",
    command=("todo", "done"),
    summary="close a TODO and archive it to a project",
    description="Close a TODO with a reason and archive it as a material of the project.",
    params=(Param("id", "integer", "TODO ID", required=True, positional=True),
            Param("project", "project", "project to archive into (ID or name)", required=True, flags=("-p", "--project")),
            Param("reason", "string", "closing reason", default="done", flags=("-r", "--reason"))),
    read_only=False,
    role="upload",
    render={"kind": "message"},
)
def todo_done(ctx, id, project, reason="done"):
    material_id = close_todo(ctx.conn, id, {"reason": reason, "project_id": project["id"]}, ctx.user_id)
    return {
        "id": id,
        "material_id": material_id,
        "message": f"TODO #{id} done, archived as material #{material_id} in '{project['name']}'",
    }


# ---------------------------------------------------------------- invocation


def coerce_args(op, args):
    if not isinstance(args, dict):
        raise ValidationError("arguments must be a JSON object")
    known = {p.name: p for p in op.params}
    unknown = sorted(set(args) - set(known))
    if unknown:
        raise ValidationError(f"unknown argument(s) for {op.name}: {', '.join(unknown)}")
    values = {}
    for p in op.params:
        value = args.get(p.name)
        if value is None or (value == "" and p.type != "text"):
            if p.required:
                raise ValidationError(f"{p.name} is required")
            if p.default is not None:
                values[p.name] = p.default
            continue
        if p.type == "file":
            if not isinstance(value, list) or not all(isinstance(v, dict) for v in value):
                raise ValidationError(f"{p.name} must be a list of {{filename, content_base64}} objects")
        elif p.type == "integer":
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise ValidationError(f"{p.name} must be an integer") from None
            if p.minimum is not None:
                value = max(p.minimum, value)
            if p.maximum is not None:
                value = min(p.maximum, value)
        elif p.type == "boolean":
            value = value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes"}
        else:
            value = str(value)
        if p.enum and value not in p.enum:
            raise ValidationError(f"{p.name} must be one of {', '.join(p.enum)}")
        values[p.name] = value
    return values


def invoke(ctx, name, args=None):
    op = REGISTRY.get(name)
    if not op:
        raise LookupError(f"unknown operation {name}")
    if ctx.for_agent and not op.agent:
        raise PermissionError(f"{name} is not available to the assistant")
    args = dict(args or {})
    pparam = op.project_param
    if pparam and ctx.bound_project_id is not None:
        args[pparam.name] = ctx.bound_project_id
    values = coerce_args(op, args)
    if pparam and pparam.name in values:
        values[pparam.name] = resolve_project(ctx, values[pparam.name], op.role)
    return op.handler(ctx, **values)


def manifest():
    ops = [op.public() for op in REGISTRY.values()]
    body = {"groups": GROUPS, "operations": ops}
    version = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    return {"version": version, **body}


def http_invoke(conn, user_id, name, args):
    """POST /api/ops/<name>: run as the signed-in account and commit writes."""
    result = invoke(OpContext(conn, user_id), name, args)
    conn.commit()
    return result


# ---------------------------------------------------------------- agent adapter


class AgentToolbox:
    """Read-only operations as LLM tools, bound to one project.

    Given a database path, every call opens its own connection, so the
    calls of one model round can run concurrently (``run_many``); given an
    open connection, calls must stay sequential on the caller's thread."""

    MAX_PARALLEL = 4

    def __init__(self, db, user_id, project_id):
        self.db = db
        self.user_id = user_id
        self.project_id = project_id

    @staticmethod
    def specs():
        return [
            {"name": op.name, "description": op.description, "parameters": op.input_schema(bind_project=True)}
            for op in REGISTRY.values()
            if op.agent
        ]

    def _invoke(self, conn, name, args):
        ctx = OpContext(conn, self.user_id, bound_project_id=self.project_id, for_agent=True)
        return invoke(ctx, name, args)

    def run(self, name, args):
        """Bounded JSON text; failures come back as {"error": ...} so the
        model can recover within the same turn."""
        try:
            if isinstance(self.db, (str, Path)):
                conn = connect(self.db)
                try:
                    result = self._invoke(conn, name, args)
                    conn.commit()
                finally:
                    conn.close()
            else:
                result = self._invoke(self.db, name, args)
        except (ValidationError, LookupError, PermissionError) as exc:
            result = {"error": str(exc).strip("'\"")}
        except Exception as exc:  # network or provider failures stay inside the turn
            result = {"error": f"{name} failed: {exc}"}
        return clip(json.dumps(result, ensure_ascii=False, default=str), AGENT_RESULT_MAX_CHARS)

    def run_many(self, calls, on_event=None):
        """Run one round's calls concurrently (database path only) and
        return their results in call order. on_event receives tool_start /
        tool_end as each call begins and finishes; the returned trace
        lists the finished calls."""
        emit = on_event or (lambda kind, data: None)
        trace = [None] * len(calls)

        def one(index, call):
            emit("tool_start", {"id": call["id"], "name": call["name"], "args": call["args"]})
            started = time.monotonic()
            result = self.run(call["name"], call["args"])
            entry = {
                "id": call["id"],
                "name": call["name"],
                "args": call["args"],
                "ms": int((time.monotonic() - started) * 1000),
                "chars": len(result),
                "error": result.startswith('{"error"'),
                "preview": result[:TOOL_PREVIEW_CHARS],
            }
            trace[index] = entry
            emit("tool_end", entry)
            return result

        if len(calls) > 1 and isinstance(self.db, (str, Path)):
            with ThreadPoolExecutor(max_workers=min(self.MAX_PARALLEL, len(calls))) as pool:
                results = list(pool.map(one, range(len(calls)), calls))
        else:
            results = [one(i, c) for i, c in enumerate(calls)]
        return results, trace


def agent_inventory(conn, project, week_key):
    """Cheap local overview placed in the assistant prompt so the model
    knows which tools are worth calling."""
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
    update = conn.execute("SELECT 1 FROM weekly_updates WHERE project_id = ? AND week_key = ?", (pid, week_key)).fetchone()
    risks = conn.execute(
        "SELECT COUNT(*) AS n FROM risk_warnings WHERE project_id = ? AND week_key = ? AND status = 'active'",
        (pid, week_key),
    ).fetchone()["n"]
    return {
        "report_weeks": weeks,
        "materials_total": len(materials),
        "materials_this_week": this_week,
        "weekly_supplement_this_week": bool(update),
        "repos": [f"{r['repo']} ({r['status']})" for r in repos],
        "workstreams": [
            r["name"] for r in conn.execute(
                "SELECT name FROM workstreams WHERE project_id = ? AND status = 'active' ORDER BY position, id", (pid,)
            )
        ],
        "active_risks": risks,
    }
