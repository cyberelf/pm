import json
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from reports_app import assistant, auth, operations
from reports_app.operations import AgentToolbox
from reports_app.assistant import (
    REPORT_END,
    REPORT_START,
    answer_question,
    assistant_thread,
    split_report_proposal,
)
from reports_app.db import connect, create_project, ensure_bootstrap_admin, init_db
from reports_app.internal_agent import ChatCancelled, internal_chat, internal_tool_chat
from reports_app.server import Handler
from reports_app.sharing import set_share
from reports_app.timeutil import current_week_key, iso_now
from reports_app.validation import ValidationError


class AssistantTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        init_db(self.db_path)
        self.conn = connect(self.db_path)
        self.user = ensure_bootstrap_admin(self.conn)
        self.user_id = self.user["id"]
        self.project_id = create_project(
            self.conn,
            {"name": "Demo", "start_date": "2026-06-27", "timezone": "Asia/Shanghai", "report_provider": "internal"},
            self.user,
        )
        self.conn.commit()
        self.week_key = current_week_key("Asia/Shanghai")
        operations.clear_git_cache()
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"
        self.server = None

    def tearDown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self.conn.close()
        os.environ.pop("REPORTS_FAKE_PROVIDER", None)
        self.tmp.cleanup()

    def seed_report(self, week_key=None, content_md="# 周报\n\n## 本周总结\n进展顺利。"):
        self.conn.execute(
            """
            INSERT INTO weekly_reports (project_id, week_key, content_md, latest_job_id, created_at, updated_at)
            VALUES (?, ?, ?, 1, '2026-06-29T00:00:00+00:00', '2026-06-29T00:00:00+00:00')
            """,
            (self.project_id, week_key or self.week_key, content_md),
        )
        self.conn.commit()

    def start_server(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.db_path = self.db_path
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def call(self, method, path, body=None, user_id=None):
        token = auth.create_session(self.conn, user_id or self.user_id)
        self.conn.commit()
        headers = {"Cookie": f"reports_session={token}"}
        if body is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(body)
        client = HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        client.request(method, path, body=body, headers=headers)
        response = client.getresponse()
        payload = json.loads(response.read())
        client.close()
        return response.status, payload

    def stream(self, run_id, user_id=None, last_event_id=None):
        """Read a run's SSE stream to its end: [(id, event, data)]."""
        token = auth.create_session(self.conn, user_id or self.user_id)
        self.conn.commit()
        headers = {"Cookie": f"reports_session={token}"}
        if last_event_id is not None:
            headers["Last-Event-ID"] = str(last_event_id)
        client = HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        client.request("GET", f"/api/projects/{self.project_id}/assistant/runs/{run_id}/events", headers=headers)
        response = client.getresponse()
        self.assertEqual(response.status, 200)
        self.assertTrue(response.getheader("Content-Type").startswith("text/event-stream"))
        events = []
        for block in response.read().decode("utf-8").split("\n\n"):
            fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line and not line.startswith(":"))
            if "event" in fields:
                events.append((int(fields["id"]), fields["event"], json.loads(fields["data"])))
        client.close()
        return events

    def ask(self, question, user_id=None):
        """POST a question and follow its run; returns (status, thread or error)."""
        status, data = self.call("POST", f"/api/projects/{self.project_id}/assistant", {"question": question}, user_id=user_id)
        if status != 202:
            return status, data
        events = self.stream(data["run"]["id"], user_id=user_id)
        kind, payload = events[-1][1], events[-1][2]
        return (200 if kind == "done" else 400), payload

    def test_split_report_proposal(self):
        self.assertEqual(split_report_proposal("只是回答"), ("只是回答", ""))
        answer, proposal = split_report_proposal(f"改了总结。\n{REPORT_START}\n# 新周报\n{REPORT_END}\n其余不变。")
        self.assertEqual(proposal, "# 新周报")
        self.assertEqual(answer, "改了总结。\n\n其余不变。")
        _, proposal = split_report_proposal(f"{REPORT_START}\n```markdown\n# 新周报\n```\n{REPORT_END}")
        self.assertEqual(proposal, "# 新周报")
        # a missing end marker keeps the rest as the proposal
        _, proposal = split_report_proposal(f"说明\n{REPORT_START}\n# 截断周报")
        self.assertEqual(proposal, "# 截断周报")

    def test_endpoint_round_trip_question_adjust_apply_clear(self):
        self.seed_report()
        self.start_server()
        base = f"/api/projects/{self.project_id}/assistant"
        status, data = self.call("GET", base)
        self.assertEqual(status, 200)
        self.assertEqual(data["week_key"], self.week_key)
        self.assertTrue(data["has_report"])
        self.assertEqual(data["messages"], [])

        status, data = self.ask("本周进展如何？")
        self.assertEqual(status, 200)
        self.assertEqual([m["role"] for m in data["messages"]], ["user", "assistant"])
        self.assertIsNone(data["messages"][1]["proposal"])
        self.assertIn("本周进展如何", data["messages"][1]["content_html"])

        status, data = self.ask("把本周总结调整得更保守")
        self.assertEqual(status, 200)
        reply = data["messages"][-1]
        self.assertIn("助手调整", reply["proposal"]["content_md"])
        self.assertEqual(reply["proposal"]["applied_at"], "")
        self.assertNotIn(REPORT_START, reply["content"])

        status, data = self.call("POST", f"{base}/messages/{reply['id']}/apply", {})
        self.assertEqual(status, 200)
        self.assertTrue(data["report"]["edited_at"])
        self.assertIn("助手调整", data["report"]["content_html"])
        self.assertEqual(data["messages"][-1]["proposal"]["applied_at"], data["report"]["edited_at"])
        stored = self.conn.execute(
            "SELECT content_md, edited_at FROM weekly_reports WHERE project_id = ? AND week_key = ?",
            (self.project_id, self.week_key),
        ).fetchone()
        self.assertIn("助手调整", stored["content_md"])
        self.assertTrue(stored["edited_at"])

        # a plain answer has no proposal to apply
        status, _ = self.call("POST", f"{base}/messages/{data['messages'][1]['id']}/apply", {})
        self.assertEqual(status, 404)

        status, data = self.call("DELETE", base)
        self.assertEqual(status, 200)
        self.assertEqual(data["messages"], [])

    def test_validation_and_no_report(self):
        self.start_server()
        base = f"/api/projects/{self.project_id}/assistant"
        status, data = self.call("POST", base, {"question": "   "})
        self.assertEqual(status, 400)
        status, data = self.call("POST", base, {"question": "x" * 4001})
        self.assertEqual(status, 400)
        # without a current report an adjustment request yields prose only
        status, data = self.ask("把总结改短")
        self.assertEqual(status, 200)
        self.assertFalse(data["has_report"])
        self.assertIsNone(data["messages"][-1]["proposal"])

    def test_threads_are_per_account_and_apply_needs_write(self):
        self.seed_report()
        reader_id = auth.create_user(self.conn, "reader", "secret123")
        stranger_id = auth.create_user(self.conn, "stranger", "secret123")
        set_share(self.conn, self.project_id, {"username": "reader", "role": "read"})
        self.conn.commit()
        self.start_server()
        base = f"/api/projects/{self.project_id}/assistant"
        status, owner_data = self.ask("请修改风险结论")
        self.assertEqual(status, 200)
        owner_reply = owner_data["messages"][-1]

        status, data = self.call("GET", base, user_id=reader_id)
        self.assertEqual(status, 200)
        self.assertEqual(data["messages"], [])
        status, data = self.ask("请修改风险结论", user_id=reader_id)
        self.assertEqual(status, 200)
        reader_reply = data["messages"][-1]
        self.assertIsNotNone(reader_reply["proposal"])
        status, _ = self.call("POST", f"{base}/messages/{reader_reply['id']}/apply", {}, user_id=reader_id)
        self.assertEqual(status, 403)

        status, _ = self.call("GET", base, user_id=stranger_id)
        self.assertEqual(status, 404)
        # the owner cannot apply someone else's message either
        status, _ = self.call("POST", f"{base}/messages/{reader_reply['id']}/apply", {})
        self.assertEqual(status, 404)
        status, _ = self.call("POST", f"{base}/messages/{owner_reply['id']}/apply", {})
        self.assertEqual(status, 200)

    def test_old_week_proposal_cannot_be_applied(self):
        self.seed_report()
        answer_question(self.db_path, self.project_id, self.user_id, "调整总结")
        self.conn.execute("UPDATE assistant_messages SET week_key = '2020-W01'")
        self.conn.commit()
        message_id = self.conn.execute("SELECT id FROM assistant_messages WHERE role = 'assistant'").fetchone()["id"]
        self.start_server()
        status, payload = self.call("POST", f"/api/projects/{self.project_id}/assistant/messages/{message_id}/apply", {})
        self.assertEqual(status, 400)
        # last week's thread is not shown in this week's panel
        self.assertEqual(assistant_thread(self.conn, self.project_id, self.user_id)["messages"], [])

    def add_material(self, filename="notes.md", text="接口联调完成", summary="联调记录"):
        cur = self.conn.execute(
            """
            INSERT INTO materials (project_id, filename, storage_path, content_type, size_bytes, checksum,
                                   extracted_text, extraction_status, summary, created_at, updated_at)
            VALUES (?, ?, '', 'text/markdown', 18, 'x', ?, 'complete', ?, ?, ?)
            """,
            (self.project_id, filename, text, summary, iso_now(), iso_now()),
        )
        self.conn.commit()
        return cur.lastrowid

    def test_real_path_prompt_is_light_and_tools_run_on_demand(self):
        self.seed_report(content_md="# 当前周报\n\n结论：按计划推进。")
        self.seed_report(week_key="2020-W01", content_md="# 旧周报\n\n上周完成接口设计。")
        self.add_material()
        calls = []

        def fake_tool_chat(prompt, settings, tools, run_tools, system=None, history=None, **kwargs):
            calls.append({"prompt": prompt, "system": system, "history": history, "tools": tools})
            if len(calls) == 1:
                [result] = run_tools([{"id": "c1", "name": "weekly_show", "args": {"week_key": "2020-W01"}}])
                self.assertIn("上周完成接口设计", result)
                return "依据 2020-W01 周报，上周完成接口设计。"
            if len(calls) == 2:
                return f"已调整。\n{REPORT_START}\n# 当前周报\n\n结论：存在延期风险。\n{REPORT_END}"
            return "已精简。"

        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}), \
                mock.patch("reports_app.internal_agent.internal_tool_chat", side_effect=fake_tool_chat), \
                mock.patch("reports_app.internal_agent.resolve_llm_settings", return_value={}), \
                mock.patch("reports_app.reports.assemble_context", side_effect=AssertionError("no upfront evidence")):
            answer_question(self.db_path, self.project_id, self.user_id, "上周做了什么？")
            answer_question(self.db_path, self.project_id, self.user_id, "把结论改成有延期风险")
            answer_question(self.db_path, self.project_id, self.user_id, "再精简一点")
        first, second, third = calls
        # the prompt carries the report and a cheap inventory, not the evidence itself
        self.assertIn("结论：按计划推进", first["system"])
        self.assertIn('"materials_this_week": 1', first["system"])
        self.assertIn("2020-W01", first["system"])
        self.assertNotIn("上周完成接口设计", first["system"])
        self.assertNotIn("接口联调完成", first["system"])
        self.assertEqual({t["name"] for t in first["tools"]} >= {"weekly_show", "search", "material_show", "repos_commits"}, True)
        self.assertEqual(first["history"], [])
        self.assertEqual([h["role"] for h in second["history"]], ["user", "assistant"])
        self.assertIn("最近一次未应用的修改稿", third["system"])
        self.assertIn("存在延期风险", third["system"])
        self.assertIn("（已附修改稿）", third["history"][-1]["content"])
        thread = assistant_thread(self.conn, self.project_id, self.user_id)
        self.assertEqual(thread["messages"][1]["tools"][0]["name"], "weekly_show")

    def test_llm_failure_stores_nothing(self):
        self.seed_report()
        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}), \
                mock.patch("reports_app.internal_agent.internal_tool_chat", side_effect=RuntimeError("boom")), \
                mock.patch("reports_app.internal_agent.resolve_llm_settings", return_value={}):
            with self.assertRaises(ValidationError) as ctx:
                answer_question(self.db_path, self.project_id, self.user_id, "本周进展？")
        self.assertIn("boom", str(ctx.exception))
        count = self.conn.execute("SELECT COUNT(*) AS n FROM assistant_messages").fetchone()["n"]
        self.assertEqual(count, 0)

    def test_fake_path_records_tool_trace(self):
        self.seed_report()
        answer_question(self.db_path, self.project_id, self.user_id, "本周进展？")
        reply = assistant_thread(self.conn, self.project_id, self.user_id)["messages"][-1]
        self.assertEqual(reply["tools"][0]["name"], "weekly_list")

    def tools(self, user_id=None):
        return AgentToolbox(self.conn, user_id or self.user_id, self.project_id)

    def test_tools_are_scoped_bounded_and_report_errors(self):
        self.seed_report(content_md="# 本周")
        material_id = self.add_material(text="长" * 20000)
        other = create_project(
            self.conn,
            {"name": "Other", "start_date": "2026-06-27", "timezone": "Asia/Shanghai", "report_provider": "internal"},
            self.user,
        )
        foreign = self.conn.execute(
            """
            INSERT INTO materials (project_id, filename, storage_path, content_type, size_bytes, checksum,
                                   extracted_text, extraction_status, created_at, updated_at)
            VALUES (?, 'secret.md', '', 'text/markdown', 1, 'x', '别的项目', 'complete', ?, ?)
            """,
            (other, iso_now(), iso_now()),
        ).lastrowid
        self.conn.commit()
        tools = self.tools()
        listed = json.loads(tools.run("weekly_list", {}))
        self.assertEqual(listed["reports"][0]["week_key"], self.week_key)
        shown = json.loads(tools.run("material_show", {"id": material_id}))
        self.assertIn("已截断", shown["content"])
        self.assertIn("error", json.loads(tools.run("material_show", {"id": foreign})))
        self.assertIn("error", json.loads(tools.run("weekly_show", {"week_key": "1999-W01"})))
        self.assertIn("error", json.loads(tools.run("material_show", {"id": "abc"})))
        self.assertIn("error", json.loads(tools.run("material_show", {})))
        self.assertIn("error", json.loads(tools.run("rm_rf", {})))
        this_week = json.loads(tools.run("materials_list", {}))
        self.assertEqual([m["id"] for m in this_week["materials"]], [material_id])
        hits = json.loads(tools.run("search", {"query": "别的项目"}))["hits"]
        self.assertFalse(any(h["source_id"] == foreign for h in hits))
        self.assertIn("plan", json.loads(tools.run("plan_show", {})))
        self.assertEqual(json.loads(tools.run("repos_commits", {}))["repos"], [])
        self.assertLessEqual(len(tools.run("material_show", {"id": material_id})), 12100)

    def test_git_tools_cache_and_survive_provider_errors(self):
        self.conn.execute(
            """
            INSERT INTO github_repos (project_id, repo, status, created_at, updated_at)
            VALUES (?, 'acme/app', 'connected', ?, ?)
            """,
            (self.project_id, iso_now(), iso_now()),
        )
        self.conn.commit()
        tools = self.tools()
        with mock.patch("reports_app.operations.repo_commit_context", return_value={"repo": "acme/app", "commits": [{"message": "fix"}]}) as fetch:
            first = json.loads(tools.run("repos_commits", {"repo": "acme/app"}))
            tools.run("repos_commits", {})
            self.assertEqual(first["repos"][0]["commits"][0]["message"], "fix")
            self.assertEqual(fetch.call_count, 1)
        self.assertIn("error", json.loads(tools.run("repos_commits", {"repo": "nope/nope"})))
        operations.clear_git_cache()
        with mock.patch("reports_app.operations.repo_commit_context", side_effect=RuntimeError("rate limited")):
            self.assertIn("rate limited", json.loads(tools.run("repos_commits", {}))["error"])


    def test_run_streams_tool_and_text_events_then_persists(self):
        self.seed_report()
        self.start_server()
        status, data = self.call("POST", f"/api/projects/{self.project_id}/assistant", {"question": "把总结改短"})
        self.assertEqual(status, 202)
        events = self.stream(data["run"]["id"])
        kinds = [kind for _, kind, _ in events]
        self.assertEqual(kinds[:4], ["round", "tool_start", "tool_end", "round"])
        self.assertEqual(kinds[-1], "done")
        self.assertEqual([n for n, _, _ in events], list(range(1, len(events) + 1)))
        streamed = "".join(d["delta"] for _, kind, d in events if kind == "text")
        self.assertIn(REPORT_START, streamed)
        done = events[-1][2]
        self.assertIsNotNone(done["messages"][-1]["proposal"])
        self.assertEqual(done["messages"][-1]["tools"][0]["name"], "weekly_list")
        # resuming after an id replays only the rest
        tail = self.stream(data["run"]["id"], last_event_id=events[-3][0])
        self.assertEqual([n for n, _, _ in tail], [events[-2][0], events[-1][0]])
        status, _ = self.call("GET", f"/api/projects/{self.project_id}/assistant/runs/nope/events")
        self.assertEqual(status, 404)

    def test_one_active_run_cancel_and_reattach(self):
        self.seed_report()
        self.start_server()
        release = threading.Event()

        def slow_answer(db_path, project_id, user_id, question, emit=None, cancelled=None, **kwargs):
            emit("round", {"round": 0})
            emit("text", {"delta": "思考中"})
            while not cancelled():
                if release.wait(0.02):
                    break
            if cancelled():
                raise ChatCancelled()
            return 0

        with mock.patch("reports_app.assistant.answer_question", side_effect=slow_answer):
            status, data = self.call("POST", f"/api/projects/{self.project_id}/assistant", {"question": "慢问题"})
            self.assertEqual(status, 202)
            run_id = data["run"]["id"]
            status, busy = self.call("POST", f"/api/projects/{self.project_id}/assistant", {"question": "再问"})
            self.assertEqual(status, 409)
            # a reload finds the active run and can reattach to it
            status, thread = self.call("GET", f"/api/projects/{self.project_id}/assistant")
            self.assertEqual(thread["active_run"]["id"], run_id)
            other = auth.create_user(self.conn, "other", "secret123")
            set_share(self.conn, self.project_id, {"username": "other", "role": "read"})
            self.conn.commit()
            status, _ = self.call("POST", f"/api/projects/{self.project_id}/assistant/runs/{run_id}/cancel", {}, user_id=other)
            self.assertEqual(status, 404)
            status, _ = self.call("POST", f"/api/projects/{self.project_id}/assistant/runs/{run_id}/cancel", {})
            self.assertEqual(status, 200)
            events = self.stream(run_id)
        self.assertEqual(events[-1][1], "cancelled")
        status, thread = self.call("GET", f"/api/projects/{self.project_id}/assistant")
        self.assertIsNone(thread["active_run"])
        self.assertEqual(thread["messages"], [])

    def test_run_failure_is_an_error_event(self):
        self.seed_report()
        self.start_server()
        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}), \
                mock.patch("reports_app.internal_agent.internal_tool_chat", side_effect=RuntimeError("provider down")), \
                mock.patch("reports_app.internal_agent.resolve_llm_settings", return_value={}):
            status, payload = self.ask("本周进展？")
        self.assertEqual(status, 400)
        self.assertIn("provider down", payload["message"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM assistant_messages").fetchone()["n"], 0)

    def test_round_tools_run_concurrently(self):
        barrier = threading.Barrier(2, timeout=3)
        events = []

        def blocking_run(self_, name, args):
            barrier.wait()  # deadlocks (BrokenBarrierError) unless both run at once
            return json.dumps({"tool": name})

        toolbox = AgentToolbox(self.db_path, self.user_id, self.project_id)
        with mock.patch.object(AgentToolbox, "run", blocking_run):
            results, trace = toolbox.run_many(
                [{"id": "a", "name": "plan_show", "args": {}}, {"id": "b", "name": "risks_list", "args": {}}],
                on_event=lambda kind, data: events.append((kind, data["id"])),
            )
        self.assertEqual([json.loads(r)["tool"] for r in results], ["plan_show", "risks_list"])
        self.assertEqual([t["id"] for t in trace], ["a", "b"])
        kinds = [k for k, _ in events]
        self.assertEqual(kinds[:2], ["tool_start", "tool_start"])
        # real operations also run on their own connections in parallel
        results, trace = toolbox.run_many([
            {"id": "x", "name": "weekly_list", "args": {}},
            {"id": "y", "name": "materials_list", "args": {"scope": "all"}},
            {"id": "z", "name": "material_show", "args": {"id": 999}},
        ])
        self.assertIn("reports", json.loads(results[0]))
        self.assertIn("materials", json.loads(results[1]))
        self.assertTrue(trace[2]["error"])


class InternalChatHistoryTest(unittest.TestCase):
    def test_openai_and_anthropic_message_shapes(self):
        history = [{"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"}]
        openai_client = mock.Mock()
        openai_client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=" ok "))]
        )
        settings = {"provider": "openai", "model": "m", "api_key": "k", "base_url": "http://x"}
        with mock.patch("reports_app.internal_agent.build_client", return_value=openai_client):
            self.assertEqual(internal_chat("q2", settings, system="sys", history=history), "ok")
        sent = openai_client.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual([m["role"] for m in sent], ["system", "user", "assistant", "user"])
        self.assertEqual(sent[0]["content"], "sys")
        self.assertEqual(sent[-1]["content"], "q2")

        anthropic_client = mock.Mock()
        anthropic_client.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(type="text", text="ok")])
        settings = {**settings, "provider": "anthropic"}
        with mock.patch("reports_app.internal_agent.build_client", return_value=anthropic_client):
            self.assertEqual(internal_chat("q2", settings, system="sys", history=history), "ok")
        kwargs = anthropic_client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["system"], "sys")
        self.assertEqual([m["role"] for m in kwargs["messages"]], ["user", "assistant", "user"])


class FakeAnthropicStream:
    def __init__(self, texts, final):
        self.text_stream = iter(texts)
        self._final = final

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self._final


class InternalToolChatTest(unittest.TestCase):
    SPECS = [{"name": "weekly_show", "description": "d", "parameters": {"type": "object", "properties": {}}}]

    @staticmethod
    def chunk(content=None, tool_calls=None):
        delta = SimpleNamespace(content=content, tool_calls=tool_calls)
        return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])

    def test_openai_streams_text_and_runs_round_tools_together(self):
        client = mock.Mock()
        tc = lambda index, id=None, name=None, args=None: SimpleNamespace(
            index=index, id=id, function=SimpleNamespace(name=name, arguments=args))
        client.chat.completions.create.side_effect = [
            iter([
                self.chunk("先查"),
                self.chunk(tool_calls=[tc(0, "c1", "weekly_show", '{"week_')]),
                self.chunk(tool_calls=[tc(0, None, None, 'key": "2026-W46"}'), tc(1, "c2", "weekly_show", "{}")]),
                SimpleNamespace(choices=[]),
            ]),
            iter([self.chunk("答"), self.chunk("案")]),
        ]
        batches, events = [], []
        settings = {"provider": "openai", "model": "m", "api_key": "k", "base_url": "http://x"}
        with mock.patch("reports_app.internal_agent.build_client", return_value=client):
            text = internal_tool_chat(
                "q", settings, self.SPECS, lambda calls: batches.append(calls) or ['{"ok": 1}'] * len(calls),
                system="sys", on_event=lambda kind, data: events.append((kind, data)),
            )
        self.assertEqual(text, "答案")
        self.assertEqual(batches, [[
            {"id": "c1", "name": "weekly_show", "args": {"week_key": "2026-W46"}},
            {"id": "c2", "name": "weekly_show", "args": {}},
        ]])
        self.assertEqual([d["delta"] for k, d in events if k == "text"], ["先查", "答", "案"])
        self.assertEqual([k for k, _ in events].count("round"), 2)
        second = client.chat.completions.create.call_args_list[1].kwargs
        self.assertTrue(second["stream"])
        self.assertEqual([m["role"] for m in second["messages"]], ["system", "user", "assistant", "tool", "tool"])
        self.assertEqual(second["messages"][2]["tool_calls"][0]["function"]["arguments"], '{"week_key": "2026-W46"}')

    def test_anthropic_streams_and_final_round_forbids_tools(self):
        use = SimpleNamespace(type="tool_use", id="t1", name="weekly_show", input={})
        use.model_dump = lambda exclude_none=True: {"type": "tool_use", "id": "t1", "name": "weekly_show", "input": {}}
        looping = SimpleNamespace(content=[use])
        final = SimpleNamespace(content=[SimpleNamespace(type="text", text="最终")])
        client = mock.Mock()
        client.messages.stream.side_effect = [
            FakeAnthropicStream([], looping), FakeAnthropicStream([], looping), FakeAnthropicStream(["最", "终"], final),
        ]
        texts = []
        settings = {"provider": "anthropic", "model": "m", "api_key": "k", "base_url": "http://x"}
        with mock.patch("reports_app.internal_agent.build_client", return_value=client):
            text = internal_tool_chat(
                "q", settings, self.SPECS, lambda calls: ["{}"] * len(calls), system="sys", max_rounds=2,
                on_event=lambda kind, data: texts.append(data["delta"]) if kind == "text" else None,
            )
        self.assertEqual(text, "最终")
        self.assertEqual(texts, ["最", "终"])
        calls = client.messages.stream.call_args_list
        self.assertEqual(calls[0].kwargs["tools"][0]["input_schema"], {"type": "object", "properties": {}})
        self.assertNotIn("tool_choice", calls[0].kwargs)
        self.assertEqual(calls[2].kwargs["tool_choice"], {"type": "none"})
        followup = calls[1].kwargs["messages"]
        self.assertEqual(followup[1]["content"][0]["type"], "tool_use")
        self.assertEqual(followup[2]["content"][0], {"type": "tool_result", "tool_use_id": "t1", "content": "{}"})

    def test_cancel_stops_the_stream(self):
        client = mock.Mock()
        client.chat.completions.create.return_value = iter([self.chunk("a"), self.chunk("b")])
        settings = {"provider": "openai", "model": "m", "api_key": "k", "base_url": "http://x"}
        with mock.patch("reports_app.internal_agent.build_client", return_value=client):
            with self.assertRaises(ChatCancelled):
                internal_tool_chat("q", settings, self.SPECS, lambda calls: [], cancelled=lambda: True)


if __name__ == "__main__":
    unittest.main()
