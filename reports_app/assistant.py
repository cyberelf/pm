"""Weekly report assistant: grounded Q&A over the current week's report.

Each account keeps its own conversation per project and project week. The
prompt carries only the current report and a cheap local inventory; the
internal agent pulls everything else on demand through read-only tools that
come from the shared operation registry (operations.py) that also backs the zreport CLI, so simple questions never wait
for Git APIs. When the user asks to adjust the report the agent returns a
complete revised report between fixed markers; the revision is stored with
the answer and only replaces the report when a writer applies it explicitly.
"""

import json
import re

from .operations import AgentToolbox, agent_inventory
from .markdown import render_markdown
from .reports import fake_provider_enabled
from .timeutil import current_week_key, iso_now
from .validation import ValidationError

QUESTION_MAX_CHARS = 4000
HISTORY_TURNS_FOR_LLM = 20
THREAD_LIMIT = 200
REPORT_MAX_CHARS = 20000
MAX_TOOL_ROUNDS = 6
REPORT_START = "<<<REPORT>>>"
REPORT_END = "<<<END_REPORT>>>"
ADJUST_PATTERN = re.compile(r"改|调整|修订|补充|删除|删掉|重写|替换|更新周报|润色")

SYSTEM_PROMPT = f"""你是项目周报助手，帮助用户理解、追问和调整这个项目的周报。

取证方式：
- 当前周报和项目概况已在下方；能直接根据它们回答的问题不要调用工具。
- 需要更多依据时按需调用工具，只取回答所需的部分：历史周报用 weekly_list/weekly_show，资料用 materials_list/material_show 或 search，计划与里程碑用 plan_show，本周补充用 supplement_show，系统预警用 risks_list，仓库用 repos_list。
- repos_commits 和 repos_activity 会访问远程 API、较慢，只在问题确实涉及代码提交、PR/Issue 或看板时调用，并尽量指定 repo。
- 能并行的工具调用请在同一轮一起发出。

回答规则：
- 只依据当前周报和工具返回的内容回答；查不到的信息明确说明“现有资料中没有相关记录”，不要编造事实、数字、人员或日期。
- 解释进展、问题原因或结论依据时，指明来源：资料文件名、仓库和提交信息、PR/Issue、本周补充字段或历史周报周次。
- 用户要求修改、调整、补充、删除或改写周报内容/结论时：先用一两句话说明改了什么、依据是什么，然后在回复末尾输出修改后的完整周报 Markdown，单独一行写 {REPORT_START}，接着是完整周报，最后单独一行写 {REPORT_END}。未涉及的部分保持原文不变。若存在“最近一次未应用的修改稿”，在它的基础上继续修改。
- 只有用户明确要求调整周报时才输出修改稿；普通提问不要输出该标记块。
- 没有当前周报时不能输出修改稿，请建议用户先生成周报，但仍可根据工具取得的资料回答问题。
- 使用中文和 Markdown，回答简洁、直接，不要复述规则或描述你的取证过程。"""


def project_week(conn, project_id):
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        raise LookupError("project not found")
    return project, current_week_key(project["timezone"])


def current_report(conn, project_id, week_key):
    return conn.execute(
        "SELECT content_md, updated_at, edited_at FROM weekly_reports WHERE project_id = ? AND week_key = ?",
        (project_id, week_key),
    ).fetchone()


def message_public(row):
    item = {
        "id": row["id"],
        "role": row["role"],
        "content": row["content"],
        "content_html": render_markdown(row["content"]) if row["role"] == "assistant" else "",
        "created_at": row["created_at"],
        "proposal": None,
        "tools": json.loads(row["tool_trace_json"]) if row["tool_trace_json"] else [],
    }
    if row["proposed_report_md"]:
        item["proposal"] = {
            "content_md": row["proposed_report_md"],
            "content_html": render_markdown(row["proposed_report_md"]),
            "applied_at": row["applied_at"],
        }
    return item


def thread_rows(conn, project_id, user_id, week_key, limit=THREAD_LIMIT):
    rows = conn.execute(
        """
        SELECT * FROM assistant_messages
        WHERE project_id = ? AND user_id = ? AND week_key = ?
        ORDER BY id DESC LIMIT ?
        """,
        (project_id, user_id, week_key, limit),
    ).fetchall()
    return list(reversed(rows))


def assistant_thread(conn, project_id, user_id):
    _, week_key = project_week(conn, project_id)
    return {
        "week_key": week_key,
        "has_report": current_report(conn, project_id, week_key) is not None,
        "messages": [message_public(row) for row in thread_rows(conn, project_id, user_id, week_key)],
    }


def clear_assistant_thread(conn, project_id, user_id):
    _, week_key = project_week(conn, project_id)
    conn.execute(
        "DELETE FROM assistant_messages WHERE project_id = ? AND user_id = ? AND week_key = ?",
        (project_id, user_id, week_key),
    )


def latest_pending_proposal(rows):
    for row in reversed(rows):
        if row["role"] == "assistant" and row["proposed_report_md"]:
            return "" if row["applied_at"] else row["proposed_report_md"]
    return ""


def build_assistant_system_prompt(project, week_key, report_md, overview, pending_proposal):
    profile = {k: project[k] for k in ("name", "description", "status", "owner", "start_date", "end_date")}
    sections = [
        SYSTEM_PROMPT,
        f"当前项目周：{week_key}（时区 {project['timezone']}）。",
        "## 项目概况\n\n```json\n"
        + json.dumps({"profile": profile, "inventory": overview}, ensure_ascii=False, indent=2)
        + "\n```",
        "## 当前周报\n\n" + (report_md[:REPORT_MAX_CHARS] if report_md else "（本周还没有生成周报）"),
    ]
    if pending_proposal:
        sections.append("## 最近一次未应用的修改稿\n\n" + pending_proposal[:REPORT_MAX_CHARS])
    return "\n\n".join(sections)


def split_report_proposal(raw):
    """Separate the visible answer from an optional revised report block."""
    text = (raw or "").strip()
    start = text.find(REPORT_START)
    if start < 0:
        return text, ""
    answer = text[:start].strip()
    rest = text[start + len(REPORT_START):]
    end = rest.find(REPORT_END)
    proposal = rest if end < 0 else rest[:end]
    if end >= 0:
        tail = rest[end + len(REPORT_END):].strip()
        if tail:
            answer = f"{answer}\n\n{tail}".strip()
    proposal = proposal.strip()
    if proposal.startswith("```"):
        proposal = re.sub(r"^```(?:markdown|md)?\s*|\s*```$", "", proposal, flags=re.IGNORECASE).strip()
    return answer, proposal


def fake_assistant_reply(question, report_md):
    answer = f"（离线模式）已收到问题：{question}"
    if report_md and ADJUST_PATTERN.search(question):
        revised = f"{report_md.rstrip()}\n\n> 助手调整：{question}\n"
        return f"已按要求调整周报。\n\n{REPORT_START}\n{revised}\n{REPORT_END}"
    return answer


def ask_assistant(conn, project_id, user_id, question, timeout=180):
    """Answer one question in the caller's thread and persist both turns.
    Failures raise before anything is stored, so the thread keeps
    alternating user/assistant turns."""
    question = (question or "").strip()
    if not question:
        raise ValidationError("问题不能为空")
    if len(question) > QUESTION_MAX_CHARS:
        raise ValidationError(f"问题不能超过 {QUESTION_MAX_CHARS} 字")
    project, week_key = project_week(conn, project_id)
    report = current_report(conn, project_id, week_key)
    report_md = (report["content_md"] or "") if report else ""
    rows = thread_rows(conn, project_id, user_id, week_key, limit=HISTORY_TURNS_FOR_LLM)
    if rows and rows[0]["role"] != "user":
        rows = rows[1:]
    tools = AgentToolbox(conn, user_id, project_id)
    if fake_provider_enabled():
        # exercise the executor offline so traces and storage stay covered
        trace = [{"name": "weekly_list", "args": {}, "ms": 0, "chars": len(tools.run("weekly_list", {})), "error": False}]
        raw = fake_assistant_reply(question, report_md)
    else:
        from .internal_agent import internal_tool_chat, resolve_llm_settings

        system = build_assistant_system_prompt(
            project, week_key, report_md, agent_inventory(conn, project, week_key), latest_pending_proposal(rows)
        )
        history = [
            {
                "role": row["role"],
                "content": row["content"] + ("\n\n（已附修改稿）" if row["proposed_report_md"] else ""),
            }
            for row in rows
        ]
        try:
            raw, trace = internal_tool_chat(
                question, resolve_llm_settings(conn), AgentToolbox.specs(), tools.run,
                system=system, history=history, timeout=timeout, max_rounds=MAX_TOOL_ROUNDS,
            )
        except RuntimeError as exc:
            raise ValidationError(f"助手回答失败：{exc}") from exc
    answer, proposal = split_report_proposal(raw)
    if proposal and not report:
        # nothing to apply it to; keep the prose only
        proposal = ""
    if not answer and not proposal:
        raise ValidationError("助手没有返回内容，请重试")
    if not answer:
        answer = "已生成修改稿，确认后可应用到本周周报。"
    now = iso_now()
    conn.execute(
        """
        INSERT INTO assistant_messages (project_id, user_id, week_key, role, content, created_at)
        VALUES (?, ?, ?, 'user', ?, ?)
        """,
        (project_id, user_id, week_key, question, now),
    )
    cur = conn.execute(
        """
        INSERT INTO assistant_messages
        (project_id, user_id, week_key, role, content, proposed_report_md, tool_trace_json, created_at)
        VALUES (?, ?, ?, 'assistant', ?, ?, ?, ?)
        """,
        (project_id, user_id, week_key, answer, proposal, json.dumps(trace, ensure_ascii=False), iso_now()),
    )
    return cur.lastrowid


def proposal_for_apply(conn, project_id, user_id, message_id):
    """The stored revision of one of the caller's current-week answers."""
    _, week_key = project_week(conn, project_id)
    row = conn.execute(
        """
        SELECT * FROM assistant_messages
        WHERE id = ? AND project_id = ? AND user_id = ? AND role = 'assistant'
        """,
        (message_id, project_id, user_id),
    ).fetchone()
    if not row or not row["proposed_report_md"]:
        raise LookupError("assistant proposal not found")
    if row["week_key"] != week_key:
        raise ValidationError("只能应用本周对话中的修改稿")
    return row


def mark_proposal_applied(conn, message_id, applied_at):
    conn.execute("UPDATE assistant_messages SET applied_at = ? WHERE id = ?", (applied_at, message_id))
