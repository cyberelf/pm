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

from reports_app import assistant, auth
from reports_app.assistant import (
    REPORT_END,
    REPORT_START,
    ask_assistant,
    assistant_thread,
    split_report_proposal,
)
from reports_app.db import connect, create_project, ensure_bootstrap_admin, init_db
from reports_app.internal_agent import internal_chat
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
        assistant.clear_evidence_cache()
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

        status, data = self.call("POST", base, {"question": "本周进展如何？"})
        self.assertEqual(status, 200)
        self.assertEqual([m["role"] for m in data["messages"]], ["user", "assistant"])
        self.assertIsNone(data["messages"][1]["proposal"])
        self.assertIn("本周进展如何", data["messages"][1]["content_html"])

        status, data = self.call("POST", base, {"question": "把本周总结调整得更保守"})
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
        status, data = self.call("POST", base, {"question": "把总结改短"})
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
        status, owner_data = self.call("POST", base, {"question": "请修改风险结论"})
        self.assertEqual(status, 200)
        owner_reply = owner_data["messages"][-1]

        status, data = self.call("GET", base, user_id=reader_id)
        self.assertEqual(status, 200)
        self.assertEqual(data["messages"], [])
        status, data = self.call("POST", base, {"question": "请修改风险结论"}, user_id=reader_id)
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
        ask_assistant(self.conn, self.project_id, self.user_id, "调整总结")
        self.conn.execute("UPDATE assistant_messages SET week_key = '2020-W01'")
        self.conn.commit()
        message_id = self.conn.execute("SELECT id FROM assistant_messages WHERE role = 'assistant'").fetchone()["id"]
        self.start_server()
        status, payload = self.call("POST", f"/api/projects/{self.project_id}/assistant/messages/{message_id}/apply", {})
        self.assertEqual(status, 400)
        # last week's thread is not shown in this week's panel
        self.assertEqual(assistant_thread(self.conn, self.project_id, self.user_id)["messages"], [])

    def test_real_path_sends_grounded_system_prompt_and_history(self):
        self.seed_report(content_md="# 当前周报\n\n结论：按计划推进。")
        self.seed_report(week_key="2020-W01", content_md="# 旧周报\n\n上周完成接口设计。")
        self.conn.execute(
            """
            INSERT INTO materials (project_id, filename, storage_path, content_type, size_bytes, checksum,
                                   extracted_text, extraction_status, created_at, updated_at)
            VALUES (?, 'notes.md', '', 'text/markdown', 18, 'x', '接口联调完成', 'complete', ?, ?)
            """,
            (self.project_id, iso_now(), iso_now()),
        )
        self.conn.commit()
        calls = []

        def fake_chat(prompt, settings, timeout=120, system=None, history=None, **kwargs):
            calls.append({"prompt": prompt, "system": system, "history": history})
            if len(calls) == 2:
                return f"已调整。\n{REPORT_START}\n# 当前周报\n\n结论：存在延期风险。\n{REPORT_END}"
            return "依据 notes.md，接口联调完成。"

        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}), \
                mock.patch("reports_app.internal_agent.internal_chat", side_effect=fake_chat), \
                mock.patch("reports_app.internal_agent.resolve_llm_settings", return_value={}):
            ask_assistant(self.conn, self.project_id, self.user_id, "本周做了什么？")
            ask_assistant(self.conn, self.project_id, self.user_id, "把结论改成有延期风险")
            ask_assistant(self.conn, self.project_id, self.user_id, "再精简一点")
        first, second, third = calls
        self.assertIn("结论：按计划推进", first["system"])
        self.assertIn("2020-W01", first["system"])
        self.assertIn("接口联调完成", first["system"])
        self.assertEqual(first["history"], [])
        self.assertEqual(first["prompt"], "本周做了什么？")
        self.assertEqual([h["role"] for h in second["history"]], ["user", "assistant"])
        # an unapplied revision is carried forward for iterative edits
        self.assertIn("最近一次未应用的修改稿", third["system"])
        self.assertIn("存在延期风险", third["system"])
        self.assertIn("（已附修改稿）", third["history"][-1]["content"])

    def test_llm_failure_stores_nothing(self):
        self.seed_report()
        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}), \
                mock.patch("reports_app.internal_agent.internal_chat", side_effect=RuntimeError("boom")), \
                mock.patch("reports_app.internal_agent.resolve_llm_settings", return_value={}):
            with self.assertRaises(ValidationError) as ctx:
                ask_assistant(self.conn, self.project_id, self.user_id, "本周进展？")
        self.assertIn("boom", str(ctx.exception))
        count = self.conn.execute("SELECT COUNT(*) AS n FROM assistant_messages").fetchone()["n"]
        self.assertEqual(count, 0)

    def test_evidence_is_cached_until_inputs_change(self):
        with mock.patch("reports_app.assistant.assemble_context", return_value=({"week_key": self.week_key}, "h")) as assemble:
            assistant.current_week_evidence(self.conn, self.project_id, self.week_key)
            assistant.current_week_evidence(self.conn, self.project_id, self.week_key)
            self.assertEqual(assemble.call_count, 1)
            self.conn.execute(
                "UPDATE projects SET updated_at = '2099-01-01T00:00:00+00:00' WHERE id = ?", (self.project_id,)
            )
            assistant.current_week_evidence(self.conn, self.project_id, self.week_key)
            self.assertEqual(assemble.call_count, 2)


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


if __name__ == "__main__":
    unittest.main()
