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
import secrets
import sys
import threading
import time
import traceback
from contextlib import closing

from .db import connect
from .operations import AgentToolbox, agent_inventory
from .markdown import render_markdown
from .reports import fake_provider_enabled
from .task_queue import QueueFullError
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
- 需要更多依据时按需调用工具，只取回答所需的部分：历史周报用 weekly_list/weekly_show，资料用 materials_list/material_show 或 search，计划与里程碑用 plan_show，本周补充用 supplement_show，系统预警用 risks_list，仓库用 repos_list，工作线（项目内并行的长线）的跨周进展用 workstream_list/workstream_show。
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
        "work": stored_work_log(row["tool_trace_json"]),
    }
    item["tools"] = [entry for entry in item["work"]["items"] if entry["kind"] == "tool"]
    if row["proposed_report_md"]:
        item["proposal"] = {
            "content_md": row["proposed_report_md"],
            "content_html": render_markdown(row["proposed_report_md"]),
            "applied_at": row["applied_at"],
        }
    return item


def stored_work_log(raw):
    """The persisted work log; rows from before the log existed stored a
    bare list of tool calls."""
    data = json.loads(raw) if raw else None
    if isinstance(data, list):
        return {"elapsed_ms": None, "items": [{"kind": "tool", **entry} for entry in data]}
    return data or {"elapsed_ms": None, "items": []}


class WorkRecorder:
    """Builds the answer's work log from run events, T3 Code style: thinking
    segments, tool calls and interim text in order, each with a duration.
    Every event gets "t", seconds since the run started, so live views and
    replays agree on timing."""

    PREAMBLE_MAX_CHARS = 600

    def __init__(self, forward=None):
        self.started = time.monotonic()
        self.forward = forward or (lambda kind, data: None)
        self.items = []
        self._thinking = None
        self._text = None

    def now(self):
        return round(time.monotonic() - self.started, 3)

    def _close_thinking(self, t):
        if self._thinking is not None:
            self._thinking["ms"] = int((t - self._thinking["t"]) * 1000)
            self._thinking = None

    def __call__(self, kind, data):
        t = self.now()
        data = {**data, "t": t}
        if kind == "round":
            self._close_thinking(t)
            self._text = None
            self._thinking = {"kind": "thinking", "t": t}
            self.items.append(self._thinking)
        elif kind == "text":
            self._close_thinking(t)
            if self._text is None:
                self._text = {"kind": "text", "t": t, "text": ""}
                self.items.append(self._text)
            self._text["text"] += data.get("delta", "")
        elif kind == "tool_start":
            self._close_thinking(t)
            self._text = None
            self.items.append({"kind": "tool", "t": t, "id": data["id"], "name": data["name"], "args": data["args"]})
        elif kind == "tool_end":
            for item in self.items:
                if item["kind"] == "tool" and item["id"] == data["id"] and "ms" not in item:
                    item.update({k: data[k] for k in ("ms", "chars", "error", "preview") if k in data})
                    break
        self.forward(kind, data)

    def finish(self):
        """The log to store: the final round's text is the answer itself."""
        self._close_thinking(self.now())
        items = list(self.items)
        if items and items[-1]["kind"] == "text":
            items.pop()
        for item in items:
            if item["kind"] == "text":
                item["text"] = item["text"].strip()[: self.PREAMBLE_MAX_CHARS]
        items = [item for item in items if item["kind"] != "text" or item["text"]]
        return {"elapsed_ms": int(self.now() * 1000), "items": items}


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


def assistant_thread(conn, project_id, user_id, include_active=True):
    _, week_key = project_week(conn, project_id)
    thread = {
        "week_key": week_key,
        "has_report": current_report(conn, project_id, week_key) is not None,
        "messages": [message_public(row) for row in thread_rows(conn, project_id, user_id, week_key)],
    }
    if include_active:
        run = active_run(project_id, user_id)
        thread["active_run"] = run.public() if run else None
    return thread


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


def validate_question(question):
    question = (question or "").strip()
    if not question:
        raise ValidationError("问题不能为空")
    if len(question) > QUESTION_MAX_CHARS:
        raise ValidationError(f"问题不能超过 {QUESTION_MAX_CHARS} 字")
    return question


def _open(db_path):
    return closing(connect(db_path))


def answer_question(db_path, project_id, user_id, question, emit=None, cancelled=None, timeout=180):
    """Answer one question in the caller's thread and persist both turns.

    emit(type, data) streams progress: "round", "text" deltas and
    "tool_start"/"tool_end" as the tools of a round run concurrently.
    cancelled() stops the run with ChatCancelled. Failures raise before
    anything is stored, so the thread keeps alternating user/assistant
    turns. Returns the stored answer's message id."""
    from .internal_agent import ChatCancelled

    emit = WorkRecorder(emit)
    cancelled = cancelled or (lambda: False)
    question = validate_question(question)
    with _open(db_path) as conn:
        project, week_key = project_week(conn, project_id)
        report = current_report(conn, project_id, week_key)
        report_md = (report["content_md"] or "") if report else ""
        rows = thread_rows(conn, project_id, user_id, week_key, limit=HISTORY_TURNS_FOR_LLM)
        if rows and rows[0]["role"] != "user":
            rows = rows[1:]
        system = build_assistant_system_prompt(
            project, week_key, report_md, agent_inventory(conn, project, week_key), latest_pending_proposal(rows)
        )
        settings = None
        if not fake_provider_enabled():
            from .internal_agent import resolve_llm_settings

            settings = resolve_llm_settings(conn)
    history = [
        {"role": row["role"], "content": row["content"] + ("\n\n（已附修改稿）" if row["proposed_report_md"] else "")}
        for row in rows
    ]
    tools = AgentToolbox(db_path, user_id, project_id)

    def run_tools(calls):
        if cancelled():
            raise ChatCancelled()
        results, _ = tools.run_many(calls, emit)
        if cancelled():
            raise ChatCancelled()
        return results

    if settings is None:
        # offline: exercise the tool executor and the text stream so the
        # whole pipeline stays covered without an LLM
        emit("round", {"round": 0})
        run_tools([{"id": "fake-1", "name": "weekly_list", "args": {}}])
        emit("round", {"round": 1})
        raw = fake_assistant_reply(question, report_md)
        for start in range(0, len(raw), 8):
            if cancelled():
                raise ChatCancelled()
            emit("text", {"delta": raw[start:start + 8]})
    else:
        from .internal_agent import internal_tool_chat

        try:
            raw = internal_tool_chat(
                question, settings, AgentToolbox.specs(), run_tools,
                system=system, history=history, timeout=timeout, max_rounds=MAX_TOOL_ROUNDS,
                on_event=emit, cancelled=cancelled,
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
    if cancelled():
        raise ChatCancelled()
    with _open(db_path) as conn:
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
            (project_id, user_id, week_key, answer, proposal, json.dumps(emit.finish(), ensure_ascii=False), iso_now()),
        )
        conn.commit()
        return cur.lastrowid


# ---------------------------------------------------------------- background runs


RUN_RETENTION_SECONDS = 300
TERMINAL_EVENTS = {"done", "error", "cancelled"}


class AssistantBusy(QueueFullError):
    """One run per account and project at a time (HTTP 409)."""


class AssistantRun:
    """An answer being produced in the background. Events are kept in
    order with 1-based ids so a stream can resume after any id."""

    def __init__(self, project_id, user_id, question):
        self.id = secrets.token_hex(8)
        self.project_id = project_id
        self.user_id = user_id
        self.question = question
        self.events = []
        self.cond = threading.Condition()
        self.cancel_requested = False
        self.finished_at = None
        self.created = time.monotonic()

    @property
    def done(self):
        return self.finished_at is not None

    def emit(self, kind, data):
        with self.cond:
            if self.done:
                return
            self.events.append((len(self.events) + 1, kind, data))
            if kind in TERMINAL_EVENTS:
                self.finished_at = time.monotonic()
            self.cond.notify_all()

    def events_after(self, seq, timeout):
        with self.cond:
            if len(self.events) <= seq and not self.done:
                self.cond.wait(timeout)
            return self.events[seq:], self.done

    def public(self):
        return {
            "id": self.id,
            "question": self.question,
            "done": self.done,
            "elapsed": round(time.monotonic() - self.created, 3),
        }


_runs = {}
_runs_lock = threading.Lock()


def _purge_runs():
    now = time.monotonic()
    for run_id in [k for k, r in _runs.items() if r.done and now - r.finished_at > RUN_RETENTION_SECONDS]:
        del _runs[run_id]


def active_run(project_id, user_id):
    with _runs_lock:
        return next(
            (r for r in _runs.values() if r.project_id == project_id and r.user_id == user_id and not r.done),
            None,
        )


def find_run(run_id, project_id, user_id):
    with _runs_lock:
        run = _runs.get(run_id)
    if not run or run.project_id != project_id or run.user_id != user_id:
        return None
    return run


def start_run(db_path, project_id, user_id, question):
    """Validate and start answering in a background thread; progress and
    the final thread arrive as run events."""
    question = validate_question(question)
    with _runs_lock:
        _purge_runs()
        if any(r.project_id == project_id and r.user_id == user_id and not r.done for r in _runs.values()):
            raise AssistantBusy("助手还在回答上一个问题，请稍候或先停止")
        run = AssistantRun(project_id, user_id, question)
        _runs[run.id] = run
    threading.Thread(target=_run_worker, args=(db_path, run), name=f"assistant-{run.id}", daemon=True).start()
    return run


def _run_worker(db_path, run):
    from .internal_agent import ChatCancelled

    try:
        message_id = answer_question(
            db_path, run.project_id, run.user_id, run.question,
            emit=run.emit, cancelled=lambda: run.cancel_requested,
        )
        with _open(db_path) as conn:
            thread = assistant_thread(conn, run.project_id, run.user_id, include_active=False)
        run.emit("done", {"message_id": message_id, **thread})
    except ChatCancelled:
        run.emit("cancelled", {})
    except (ValidationError, LookupError) as exc:
        run.emit("error", {"message": str(exc).strip("'\"")})
    except Exception as exc:
        print(f"assistant run {run.id} failed: {exc}\n{traceback.format_exc()}", file=sys.stderr, flush=True)
        run.emit("error", {"message": "助手内部错误，请重试"})


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
