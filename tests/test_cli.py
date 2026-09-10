"""End-to-end tests for the zr command-line client against a live test server.

The device-authorization browser step is simulated server-side: the test
finds the pending user code in the database and approves it through the API
with a browser session, exactly like the /device page does.
"""

import io
import json
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import zr
from reports_app import auth
from reports_app.db import connect, create_project, ensure_bootstrap_admin, init_db
from reports_app.server import Handler


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        init_db(self.db_path)
        self.conn = connect(self.db_path)
        self.user = ensure_bootstrap_admin(self.conn)
        self.project_id = create_project(
            self.conn,
            {"name": "演示项目", "start_date": "2026-06-27", "timezone": "Asia/Shanghai"},
            self.user,
        )
        self.conn.commit()
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"
        self.config_path = Path(self.tmp.name) / "cli.json"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.db_path = self.db_path
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.conn.close()
        os.environ.pop("REPORTS_FAKE_PROVIDER", None)
        self.tmp.cleanup()

    def run_cli(self, *argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = zr.main(list(argv), config_file=self.config_path)
        return code, buffer.getvalue()

    def _approve_pending_code(self):
        row = self.conn.execute(
            "SELECT user_code FROM device_auth_codes WHERE status = 'pending' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        self.assertIsNotNone(row, "login did not create a pending device code")
        token = auth.create_session(self.conn, self.user["id"])
        self.conn.commit()
        client = HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        client.request(
            "POST",
            "/api/device/auth/approve",
            body=json.dumps({"user_code": row["user_code"]}),
            headers={"Content-Type": "application/json", "Cookie": f"reports_session={token}"},
        )
        response = client.getresponse()
        response.read()
        client.close()
        self.assertEqual(response.status, 200)

    def test_device_login_saves_token_and_cli_workflow(self):
        login_result = {}

        def run_login():
            with mock.patch("zr.time.sleep", new=lambda seconds: None), redirect_stdout(io.StringIO()):
                login_result["code"] = zr.main(
                    ["login", "--server", self.url], config_file=self.config_path
                )

        worker = threading.Thread(target=run_login)
        worker.start()
        for _ in range(200):
            pending = self.conn.execute(
                "SELECT COUNT(*) AS n FROM device_auth_codes WHERE status = 'pending'"
            ).fetchone()["n"]
            if pending:
                break
            threading.Event().wait(0.05)
        self._approve_pending_code()
        worker.join(timeout=10)
        self.assertEqual(login_result["code"], 0)
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertEqual(config["server"], self.url)
        self.assertEqual(config["user"], self.user["username"])
        self.assertTrue(config["token"])
        self.assertEqual(os.stat(self.config_path).st_mode & 0o777, 0o600)

        code, output = self.run_cli("whoami")
        self.assertEqual(code, 0)
        self.assertIn(self.user["username"], output)

        code, output = self.run_cli("projects")
        self.assertEqual(code, 0)
        self.assertIn("演示项目", output)

        code, output = self.run_cli("todo", "add", "整理部署文档", "-d", "补充 GPU compose 说明")
        self.assertEqual(code, 0)
        todo = self.conn.execute("SELECT * FROM todos ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(todo["title"], "整理部署文档")
        self.assertEqual(todo["description"], "补充 GPU compose 说明")
        self.assertEqual(todo["status"], "todo")

        code, output = self.run_cli("todos")
        self.assertEqual(code, 0)
        self.assertIn("整理部署文档", output)
        code, output = self.run_cli("todos", "--all")
        self.assertEqual(code, 0)

        code, output = self.run_cli("todo", "status", str(todo["id"]), "doing")
        self.assertEqual(code, 0)
        self.assertEqual(self.conn.execute("SELECT status FROM todos WHERE id = ?", (todo["id"],)).fetchone()["status"], "doing")

        note_path = Path(self.tmp.name) / "本周记录.md"
        note_path.write_text("# 本周记录\n\nCLI 上传测试内容。", encoding="utf-8")
        code, output = self.run_cli("materials", "add", "演示项目", "--text", "本周进展顺利", "--title", "进展")
        self.assertEqual(code, 0)
        manual = self.conn.execute(
            "SELECT * FROM materials WHERE source_type = 'manual' AND project_id = ? ORDER BY id DESC LIMIT 1",
            (self.project_id,),
        ).fetchone()
        self.assertEqual(manual["filename"], "进展")
        self.assertIn("本周进展顺利", manual["extracted_text"])

        code, output = self.run_cli("materials", "add", "演示项目", "--file", str(note_path))
        self.assertEqual(code, 0)
        uploaded = self.conn.execute(
            "SELECT * FROM materials WHERE source_type = 'upload' AND project_id = ? ORDER BY id DESC LIMIT 1",
            (self.project_id,),
        ).fetchone()
        self.assertEqual(uploaded["filename"], "本周记录.md")
        self.assertEqual(uploaded["extraction_status"], "extracted")

        code, output = self.run_cli("todo", "done", str(todo["id"]), "-p", "演示项目", "-r", "文档已合并")
        self.assertEqual(code, 0)
        closed = self.conn.execute("SELECT * FROM todos WHERE id = ?", (todo["id"],)).fetchone()
        self.assertEqual(closed["status"], "closed")
        self.assertEqual(closed["project_id"], self.project_id)
        self.assertIsNotNone(closed["material_id"])
        archived = self.conn.execute("SELECT * FROM materials WHERE id = ?", (closed["material_id"],)).fetchone()
        self.assertEqual(archived["project_id"], self.project_id)
        self.assertIn("TODO 完成：整理部署文档", archived["filename"])

    def test_cli_requires_login_and_reports_server_errors(self):
        code, output = self.run_cli("projects")
        self.assertEqual(code, 1)
        code, _ = self.run_cli("--server", self.url, "todo", "add", "未登录也应失败")
        self.assertEqual(code, 1)
        self.assertFalse(
            self.conn.execute("SELECT COUNT(*) AS n FROM todos").fetchone()["n"]
        )

        # logged in but wrong ids / unknown projects surface server errors
        config = {"server": self.url, "token": auth.create_session(self.conn, self.user["id"]), "user": self.user["username"]}
        self.config_path.write_text(json.dumps(config), encoding="utf-8")
        code, _ = self.run_cli("todo", "status", "999", "doing")
        self.assertEqual(code, 1)
        code, _ = self.run_cli("materials", "add", "不存在", "--text", "内容")
        self.assertEqual(code, 1)
        code, _ = self.run_cli("materials", "add", "演示项目", "--file", "missing.md")
        self.assertEqual(code, 1)
        code, _ = self.run_cli("materials", "add", "演示项目", "--text", "  ")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
