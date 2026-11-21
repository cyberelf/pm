"""The operation registry and its three interfaces: HTTP, CLI and agent."""

import io
import json
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import zreport
from reports_app import auth
from reports_app.db import connect, create_project, ensure_bootstrap_admin, init_db
from reports_app.materials import store_manual_material
from reports_app.operations import REGISTRY, AgentToolbox, GROUPS, OpContext, invoke, manifest
from reports_app.server import Handler
from reports_app.sharing import set_share
from reports_app.timeutil import current_week_key, iso_now

NATIVE = {"login", "logout", "whoami", "skill"}


class RegistryTest(unittest.TestCase):
    def test_definitions_are_consistent(self):
        commands = [tuple(op.command) for op in REGISTRY.values()]
        self.assertEqual(len(commands), len(set(commands)), "duplicate CLI commands")
        for op in REGISTRY.values():
            self.assertNotIn(op.command[0], NATIVE, op.name)
            self.assertTrue(op.summary and op.description, op.name)
            if op.agent:
                self.assertTrue(op.read_only, f"{op.name}: agent tools must be read-only")
            for depth in range(1, len(op.command)):
                # a leaf can never double as a command group
                self.assertNotIn(tuple(op.command[:depth]), commands, op.name)
                self.assertIn(" ".join(op.command[:depth]), GROUPS, op.name)
            positional = [p for p in op.params if p.positional]
            optional_seen = False
            for p in positional:
                if not p.required:
                    optional_seen = True
                self.assertFalse(optional_seen and p.required, f"{op.name}: required positional after optional")
            if op.project_param:
                self.assertNotIn("project", op.input_schema(bind_project=True)["properties"], op.name)
        # the assistant sees exactly the read-only agent operations
        self.assertEqual(
            {spec["name"] for spec in AgentToolbox.specs()},
            {op.name for op in REGISTRY.values() if op.agent},
        )
        self.assertTrue({"weekly_show", "search", "repos_commits"} <= {s["name"] for s in AgentToolbox.specs()})
        self.assertFalse({"todo_add", "materials_add", "todo_done"} & {s["name"] for s in AgentToolbox.specs()})

    def test_manifest_version_tracks_content(self):
        first = manifest()
        self.assertEqual(first, manifest())
        self.assertEqual(len(first["operations"]), len(REGISTRY))
        weekly = next(op for op in first["operations"] if op["name"] == "weekly_show")
        self.assertEqual(weekly["command"], ["project", "weekly", "show"])
        self.assertTrue(weekly["annotations"]["readOnlyHint"])
        self.assertEqual(weekly["input_schema"]["required"], ["project"])


class InterfaceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        init_db(self.db_path)
        self.conn = connect(self.db_path)
        self.user = ensure_bootstrap_admin(self.conn)
        self.user_id = self.user["id"]
        project = {"start_date": "2026-06-27", "timezone": "Asia/Shanghai", "report_provider": "internal"}
        self.project_id = create_project(self.conn, {"name": "Alpha", **project}, self.user)
        self.other_id = create_project(self.conn, {"name": "Beta", **project}, self.user)
        self.reader_id = auth.create_user(self.conn, "reader", "secret123")
        set_share(self.conn, self.project_id, {"username": "reader", "role": "read"})
        self.conn.execute(
            "INSERT INTO weekly_reports (project_id, week_key, content_md, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (self.project_id, current_week_key("Asia/Shanghai"), "# Alpha 周报\n\n联调完成", iso_now(), iso_now()),
        )
        self.alpha_material = store_manual_material(self.conn, self.project_id, {"title": "alpha-note", "content": "联调 alpha"})
        self.beta_material = store_manual_material(self.conn, self.other_id, {"title": "beta-secret", "content": "联调 beta 机密"})
        self.conn.commit()
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.db_path = self.db_path
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.config_path = Path(self.tmp.name) / "cli.json"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.conn.close()
        os.environ.pop("REPORTS_FAKE_PROVIDER", None)
        self.tmp.cleanup()

    def http(self, method, path, body=None, user_id=None, auth_cookie=True):
        headers = {}
        if auth_cookie:
            token = auth.create_session(self.conn, user_id or self.user_id)
            self.conn.commit()
            headers["Cookie"] = f"reports_session={token}"
        if body is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(body)
        client = HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        client.request(method, path, body=body, headers=headers)
        response = client.getresponse()
        payload = json.loads(response.read())
        client.close()
        return response.status, payload

    def cli(self, *argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer), redirect_stderr(buffer):
            code = zreport.main(list(argv), config_file=self.config_path)
        return code, buffer.getvalue()

    def login_cli(self):
        token = auth.create_session(self.conn, self.user_id)
        self.conn.commit()
        self.config_path.write_text(json.dumps({"server": self.url, "token": token}), encoding="utf-8")

    def test_http_manifest_is_public_and_invoke_enforces_roles(self):
        status, data = self.http("GET", "/api/ops", auth_cookie=False)
        self.assertEqual(status, 200)
        self.assertEqual(data, manifest())
        status, _ = self.http("POST", "/api/ops/weekly_list", {"project": "Alpha"}, auth_cookie=False)
        self.assertEqual(status, 401)

        status, data = self.http("POST", "/api/ops/weekly_list", {"project": "Alpha"})
        self.assertEqual(status, 200)
        self.assertEqual(data["reports"][0]["week_key"], current_week_key("Asia/Shanghai"))
        status, data = self.http("POST", "/api/ops/weekly_list", {"project": "Alpha"}, user_id=self.reader_id)
        self.assertEqual(status, 200)
        status, data = self.http("POST", "/api/ops/materials_add", {"project": "Alpha", "text": "x"}, user_id=self.reader_id)
        self.assertEqual(status, 403)
        status, data = self.http("POST", "/api/ops/weekly_list", {"project": "Beta"}, user_id=self.reader_id)
        self.assertEqual(status, 404)
        status, data = self.http("POST", "/api/ops/material_show", {"id": self.beta_material}, user_id=self.reader_id)
        self.assertEqual(status, 404)
        status, _ = self.http("POST", "/api/ops/nope", {})
        self.assertEqual(status, 404)
        status, data = self.http("POST", "/api/ops/weekly_list", {"project": "Alpha", "bogus": 1})
        self.assertEqual(status, 400)
        self.assertIn("bogus", data["error"])
        status, _ = self.http("POST", "/api/ops/material_show", {"id": "abc"})
        self.assertEqual(status, 400)

    def test_agent_adapter_is_bound_to_its_project_and_read_only(self):
        tools = AgentToolbox(self.conn, self.user_id, self.project_id)
        # a model-supplied project is ignored; the binding wins
        listed = json.loads(tools.run("materials_list", {"project": "Beta", "scope": "all"}))
        self.assertEqual(listed["project_name"], "Alpha")
        listed = json.loads(tools.run("materials_list", {"scope": "all"}))
        self.assertEqual([m["id"] for m in listed["materials"]], [self.alpha_material])
        self.assertIn("error", json.loads(tools.run("material_show", {"id": self.beta_material})))
        self.assertIn("alpha", json.loads(tools.run("material_show", {"id": self.alpha_material}))["content"])
        hits = json.loads(tools.run("search", {"query": "联调"}))["hits"]
        self.assertTrue(hits)
        self.assertTrue(all(h["source_id"] != self.beta_material or h["type"] != "material" for h in hits))
        self.assertIn("not available", json.loads(tools.run("todo_add", {"title": "x"}))["error"])
        with self.assertRaises(PermissionError):
            invoke(OpContext(self.conn, self.user_id, self.project_id, for_agent=True), "materials_add", {"text": "x"})

    def test_cli_commands_come_from_the_manifest(self):
        self.login_cli()
        code, output = self.cli("project", "materials", "list", "-p", "Alpha", "--scope", "all")
        self.assertEqual(code, 0, output)
        self.assertIn("alpha-note", output)
        code, output = self.cli("project", "plan", "show", "-p", "Alpha")
        self.assertEqual(code, 0, output)
        self.assertIn('"profile"', output)
        code, output = self.cli("project", "supplement", "show", "-p", "Alpha")
        self.assertEqual(code, 0, output)
        self.assertIn("no weekly supplement", output)
        code, output = self.cli("project", "repos", "list", "-p", "Alpha")
        self.assertEqual(code, 0, output)
        code, output = self.cli("project", "weekly", "list", "-p", "Alpha", "--json")
        self.assertEqual(json.loads(output)["project_name"], "Alpha")
        # the same operation through every interface returns the same data
        via_http = self.http("POST", "/api/ops/weekly_list", {"project": "Alpha"})[1]
        via_agent = json.loads(AgentToolbox(self.conn, self.user_id, self.project_id).run("weekly_list", {}))
        self.assertEqual(json.loads(output), via_http)
        self.assertEqual(via_agent, via_http)

        cache = json.loads(zreport.manifest_cache_path(self.config_path).read_text(encoding="utf-8"))
        self.assertEqual(cache[self.url]["version"], manifest()["version"])

    def test_cli_falls_back_to_cache_and_reports_missing_manifest(self):
        self.login_cli()
        code, _ = self.cli("project", "list")
        self.assertEqual(code, 0)
        self.server.shutdown()
        self.server.server_close()
        # offline: help still lists the server commands from the cache
        with self.assertRaises(SystemExit) as ctx:
            self.cli("project", "weekly", "--help")
        self.assertEqual(ctx.exception.code, 0)
        code, output = self.cli("project", "list")
        self.assertEqual(code, 1)
        self.assertIn("cannot reach", output)
        # no cache for this server: say why the command is unknown
        zreport.manifest_cache_path(self.config_path).unlink()
        code, output = self.cli("todo", "list")
        self.assertEqual(code, 1)
        self.assertIn("cannot load the command list", output)
        # native commands never need the manifest
        code, output = self.cli("whoami")
        self.assertEqual(code, 1)
        self.assertNotIn("command list", output)
        self.assertIn("cannot reach", output)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)  # for tearDown
        self.server.db_path = self.db_path
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


if __name__ == "__main__":
    unittest.main()
