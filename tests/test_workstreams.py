import base64
import json
import os
import tempfile
import threading
import unittest
from datetime import timedelta
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from reports_app import auth
from reports_app.db import connect, create_project, ensure_bootstrap_admin, init_db
from reports_app.materials import add_uploaded_materials, store_manual_material, store_material
from reports_app.operations import OpContext, invoke
from reports_app.reports import assemble_context, compact_evidence, generate_report, latest_success
from reports_app.risks import evaluate_risks, progress_status
from reports_app.server import Handler, workspace
from reports_app.timeutil import current_week_key, iso_now, utc_now
from reports_app.todos import close_todo, create_todo, todo_rows
from reports_app.validation import ValidationError
from reports_app.workstream_agent import run_workstream_job
from reports_app.workstreams import (
    create_workstream,
    delete_workstream,
    parse_objective_lines,
    previous_week_key,
    save_manual_snapshot,
    seed_from_objectives,
    set_material_links,
    set_todo_links,
    update_workstream,
    workstream_detail,
    workstream_overview,
)

AGENT_GUARD_OBJECTIVES = """1. 东风交付，包括座舱安全软件和智驾安全研究，以及风险规则生成平台
2. 产品设计和优化，包括软件栈，AI Box，具身安全，云端运维/运营系统
3. 推动和智联云安的合作
4. 浩瀚融资
说明：不带编号的行不生成工作线"""


class WorkstreamTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        os.environ["REPORTS_ADMIN_PASSWORD"] = "changeme"
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"
        init_db(self.db_path)
        self.conn = connect(self.db_path)
        self.owner = ensure_bootstrap_admin(self.conn)
        self.project = create_project(self.conn, {"name": "agent guard", "start_date": "2026-01-01"}, self.owner)
        self.other = create_project(self.conn, {"name": "embody", "start_date": "2026-01-01"}, self.owner)
        self.reader = auth.create_user(self.conn, "reader", "secret1")
        self.writer = auth.create_user(self.conn, "writer", "secret1")
        for user_id, role in ((self.reader, "read"), (self.writer, "write")):
            self.conn.execute(
                "INSERT INTO project_shares (project_id, user_id, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (self.project, user_id, role, iso_now(), iso_now()),
            )
        self.conn.execute(
            "UPDATE project_plans SET objectives = ? WHERE project_id = ?", (AGENT_GUARD_OBJECTIVES, self.project)
        )
        self.conn.commit()
        patch = mock.patch("reports_app.materials.UPLOAD_DIR", Path(self.tmp.name) / "uploads")
        patch.start()
        self.addCleanup(patch.stop)
        self.tz = "Asia/Shanghai"

    def tearDown(self):
        self.conn.close()
        os.environ.pop("REPORTS_FAKE_PROVIDER", None)
        os.environ.pop("REPORTS_ADMIN_PASSWORD", None)
        self.tmp.cleanup()

    @staticmethod
    def file(name, text):
        return {"filename": name, "content_base64": base64.b64encode(text.encode()).decode()}

    def upload(self, name, text, project=None):
        return store_material(self.conn, project or self.project, self.file(name, text))

    def age(self, workstream_id, weeks=3):
        old = (utc_now() - timedelta(days=7 * weeks)).isoformat()
        self.conn.execute("UPDATE workstreams SET created_at = ? WHERE id = ?", (old, workstream_id))

    def overview_item(self, workstream_id):
        data = workstream_overview(self.conn, self.project, self.tz)
        return next(item for item in data["workstreams"] if item["id"] == workstream_id)

    # ------------------------------------------------------------ model

    def test_seed_from_objectives_and_crud(self):
        self.assertEqual(
            [name for name, _goal in parse_objective_lines(AGENT_GUARD_OBJECTIVES)],
            ["东风交付", "产品设计和优化", "推动和智联云安的合作", "浩瀚融资"],
        )
        created = seed_from_objectives(self.conn, self.project)
        self.assertEqual(len(created), 4)
        self.assertEqual(seed_from_objectives(self.conn, self.project), [])  # names already exist
        first = workstream_detail(self.conn, self.project, created[0], self.tz, self.owner["id"])
        self.assertIn("座舱安全软件", first["goal"])
        with self.assertRaises(ValidationError):
            create_workstream(self.conn, self.project, {"name": "浩瀚融资"})
        with self.assertRaises(ValidationError):
            create_workstream(self.conn, self.project, {"name": "  "})
        with self.assertRaises(ValidationError):
            update_workstream(self.conn, self.project, created[0], {"status": "blocked"})
        update_workstream(self.conn, self.project, created[0], {"name": "东风", "target_date": "2026-12-31"})
        self.assertEqual(self.overview_item(created[0])["name"], "东风")
        with self.assertRaises(LookupError):
            update_workstream(self.conn, self.other, created[0], {"name": "x"})

    def test_material_links_cascade_and_project_boundary(self):
        a = create_workstream(self.conn, self.project, {"name": "东风交付"})
        b = create_workstream(self.conn, self.project, {"name": "融资"})
        foreign = create_workstream(self.conn, self.other, {"name": "具身"})
        material = store_manual_material(self.conn, self.project, {"title": "会议纪要", "content": "东风与融资"})
        set_material_links(self.conn, self.project, material, a, [b, a])
        links = self.conn.execute(
            "SELECT workstream_id, is_primary FROM material_workstreams WHERE material_id = ? ORDER BY workstream_id", (material,)
        ).fetchall()
        self.assertEqual([tuple(r) for r in links], [(a, 1), (b, 0)])
        with self.assertRaises(ValidationError):
            set_material_links(self.conn, self.project, material, foreign)
        with self.assertRaises(ValidationError):
            set_material_links(self.conn, self.project, material, None, [b])
        delete_workstream(self.conn, self.project, a)
        self.assertTrue(self.conn.execute("SELECT 1 FROM materials WHERE id = ?", (material,)).fetchone())
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM material_workstreams WHERE material_id = ?", (material,)).fetchone()[0], 1
        )
        self.conn.execute("DELETE FROM materials WHERE id = ?", (material,))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM material_workstreams").fetchone()[0], 0)

    def test_upload_auto_classification_never_overrides_manual(self):
        dongfeng = create_workstream(self.conn, self.project, {"name": "东风交付"})
        financing = create_workstream(self.conn, self.project, {"name": "融资"})
        auto, none = add_uploaded_materials(self.conn, self.project, [
            self.file("周会.txt", "东风交付本周完成座舱安全联调"),
            self.file("杂项.txt", "与任何工作线无关"),
        ])
        [manual] = add_uploaded_materials(self.conn, self.project, [self.file("纪要.txt", "东风交付里程碑")], financing)
        rows = {
            r["material_id"]: (r["workstream_id"], r["source"])
            for r in self.conn.execute("SELECT material_id, workstream_id, source FROM material_workstreams")
        }
        self.assertEqual(rows[auto], (dongfeng, "auto"))
        self.assertEqual(rows[manual], (financing, "manual"))
        self.assertNotIn(none, rows)
        self.assertEqual(workstream_overview(self.conn, self.project, self.tz)["unassigned_materials"], 1)

    def test_todo_links_private_and_copied_on_close(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        foreign = create_workstream(self.conn, self.other, {"name": "具身"})
        todo = create_todo(self.conn, {"title": "准备东风材料"}, self.writer)
        set_todo_links(self.conn, self.writer, todo, ws)
        with self.assertRaises(ValidationError):  # other project stays masked as not found
            set_todo_links(self.conn, self.writer, todo, foreign)
        self.conn.execute(
            "INSERT INTO project_shares (project_id, user_id, role, created_at, updated_at) VALUES (?, ?, 'read', ?, ?)",
            (self.other, self.writer, iso_now(), iso_now()),
        )
        with self.assertRaises(PermissionError):  # read role cannot link
            set_todo_links(self.conn, self.writer, todo, foreign)
        with self.assertRaises(ValidationError):  # not the reader's TODO
            set_todo_links(self.conn, self.reader, todo, ws)
        row = next(r for r in todo_rows(self.conn, self.writer) if r["id"] == todo)
        self.assertEqual(row["workstreams"]["primary"]["name"], "东风交付")
        self.assertEqual(workstream_detail(self.conn, self.project, ws, self.tz, self.writer)["todos"][0]["id"], todo)
        self.assertEqual(workstream_detail(self.conn, self.project, ws, self.tz, self.owner["id"])["todos"], [])
        material = close_todo(self.conn, todo, {"reason": "已交付", "project_id": self.project}, self.writer)
        self.assertEqual(
            self.conn.execute("SELECT workstream_id FROM material_workstreams WHERE material_id = ? AND is_primary = 1", (material,)).fetchone()[0],
            ws,
        )

    # ------------------------------------------------------------ rules

    def test_stale_and_overdue_rules(self):
        stale = create_workstream(self.conn, self.project, {"name": "融资"})
        paused = create_workstream(self.conn, self.project, {"name": "合作", "status": "paused"})
        fresh = create_workstream(self.conn, self.project, {"name": "东风交付"})
        for ws in (stale, paused, fresh):
            self.age(ws)
        set_material_links(self.conn, self.project, store_manual_material(self.conn, self.project, {"title": "n", "content": "x"}), fresh)
        evaluate_risks(self.conn, self.project)
        active = {
            r["source_ref"]: r["rule"]
            for r in self.conn.execute("SELECT rule, source_ref FROM risk_warnings WHERE status = 'active' AND rule LIKE 'workstream_%'")
        }
        self.assertEqual(active, {f"workstream:{stale}": "workstream_stale"})
        self.assertEqual(self.overview_item(stale)["health"], "at risk")
        self.assertEqual(self.overview_item(paused)["health"], "paused")
        self.assertEqual(self.overview_item(fresh)["health"], "on track")
        self.assertEqual(progress_status(self.conn, self.project), "on track")  # stale does not move project status

        update_workstream(self.conn, self.project, fresh, {"target_date": "2020-01-01"})
        evaluate_risks(self.conn, self.project)
        self.assertEqual(self.overview_item(fresh)["health"], "blocked")
        self.assertEqual(progress_status(self.conn, self.project), "blocked")
        update_workstream(self.conn, self.project, fresh, {"target_date": ""})
        set_material_links(self.conn, self.project, store_manual_material(self.conn, self.project, {"title": "m", "content": "y"}), stale)
        evaluate_risks(self.conn, self.project)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM risk_warnings WHERE status = 'active' AND rule LIKE 'workstream_%'").fetchone()[0], 0
        )

    def test_overdue_linked_milestone(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        milestones = [{"title": "AI Box Demo", "target_date": "2020-01-01", "status": "in_progress", "workstream_id": ws}]
        self.conn.execute("UPDATE project_plans SET milestones_json = ? WHERE project_id = ?", (json.dumps(milestones), self.project))
        item = self.overview_item(ws)
        self.assertEqual(item["health"], "blocked")
        self.assertEqual(item["milestones"][0]["title"], "AI Box Demo")
        delete_workstream(self.conn, self.project, ws)
        plan = json.loads(self.conn.execute("SELECT milestones_json FROM project_plans WHERE project_id = ?", (self.project,)).fetchone()[0])
        self.assertNotIn("workstream_id", plan[0])

    # ------------------------------------------------------------ agent

    def test_report_evidence_and_snapshots_after_generation(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        quiet = create_workstream(self.conn, self.project, {"name": "融资"})
        add_uploaded_materials(self.conn, self.project, [self.file("东风周报.txt", "东风交付进展")])
        week = current_week_key(self.tz)
        save_manual_snapshot(self.conn, self.project, quiet, {"week_key": week, "status": "blocked", "summary": "等待投资人反馈"})
        context, _hash = assemble_context(self.conn, self.project)
        evidence = compact_evidence(context)
        self.assertEqual([w["name"] for w in evidence["workstreams"]], ["东风交付", "融资"])
        self.assertEqual(evidence["new_materials_this_week"][0]["workstream"], "东风交付")
        generate_report(self.conn, self.project, "manual", force=True)
        snaps = {
            r["workstream_id"]: dict(r)
            for r in self.conn.execute("SELECT workstream_id, status, summary, source FROM workstream_weekly WHERE week_key = ?", (week,))
        }
        self.assertEqual(snaps[ws]["status"], "advanced")
        self.assertEqual(snaps[ws]["source"], "generated")
        self.assertEqual(snaps[quiet]["summary"], "等待投资人反馈")  # manual snapshot kept
        cell = self.overview_item(ws)["cells"][-1]
        self.assertEqual((cell["week_key"], cell["materials"], cell["snapshot"]["status"]), (week, 1, "advanced"))

    def test_job_stays_running_until_snapshots_exist(self):
        create_workstream(self.conn, self.project, {"name": "东风交付"})
        seen = []

        def spy(conn, project_id, week_key, report_md, source="generated", timeout=120):
            seen.append(conn.execute("SELECT status FROM generation_jobs ORDER BY id DESC LIMIT 1").fetchone()[0])
            seen.append(bool(conn.execute("SELECT 1 FROM weekly_reports WHERE project_id = ?", (project_id,)).fetchone()))
            return 0

        with mock.patch("reports_app.workstream_agent.extract_snapshots", side_effect=spy):
            job = generate_report(self.conn, self.project, "manual", force=True)
        self.assertEqual(seen, ["running", True])
        self.assertEqual(self.conn.execute("SELECT status FROM generation_jobs WHERE id = ?", (job,)).fetchone()[0], "success")

    def test_snapshot_failure_never_fails_report(self):
        create_workstream(self.conn, self.project, {"name": "东风交付"})
        with mock.patch("reports_app.workstream_agent.extract_snapshots", side_effect=RuntimeError("boom")):
            job = generate_report(self.conn, self.project, "manual", force=True)
        self.assertEqual(self.conn.execute("SELECT status FROM generation_jobs WHERE id = ?", (job,)).fetchone()[0], "success")

    def test_organize_job_classifies_and_backfills(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        material = store_manual_material(self.conn, self.project, {"title": "东风交付周会", "content": "联调完成"})
        unrelated = store_manual_material(self.conn, self.project, {"title": "杂项", "content": "无关"})
        last_week = previous_week_key(self.tz)
        self.conn.execute(
            "INSERT INTO weekly_reports (project_id, week_key, content_md, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (self.project, last_week, "# 周报\n东风交付推进", iso_now(), iso_now()),
        )
        self.conn.execute(
            "INSERT INTO generation_jobs (project_id, week_key, trigger_type, provider, status, started_at) VALUES (?, ?, 'workstreams', 'internal', 'queued', ?)",
            (self.project, current_week_key(self.tz), iso_now()),
        )
        job = self.conn.execute("SELECT MAX(id) FROM generation_jobs").fetchone()[0]
        self.conn.commit()
        run_workstream_job(self.db_path, job, self.project)
        row = self.conn.execute("SELECT status, output_md FROM generation_jobs WHERE id = ?", (job,)).fetchone()
        self.assertEqual(row["status"], "success")
        self.assertIn("归类 1 份资料，补齐 1 周快照", row["output_md"])
        links = dict(self.conn.execute("SELECT material_id, source FROM material_workstreams").fetchall())
        self.assertEqual(links, {material: "auto"})
        self.assertNotIn(unrelated, links)
        self.assertEqual(
            self.conn.execute("SELECT source FROM workstream_weekly WHERE workstream_id = ? AND week_key = ?", (ws, last_week)).fetchone()[0],
            "backfill",
        )
        # a successful 「AI 整理」 job is not a report success
        self.assertIsNone(latest_success(self.conn, self.project, current_week_key(self.tz)))

    # ------------------------------------------------------------ operations

    def test_operations_list_show_and_materials_add(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付", "goal": "座舱安全交付"})
        ctx = OpContext(self.conn, self.owner["id"])
        result = invoke(ctx, "materials_add", {"project": "agent guard", "text": "联调完成", "title": "日报", "workstream": "东风交付"})
        listing = invoke(ctx, "materials_list", {"project": "agent guard"})
        self.assertEqual(listing["materials"][0]["workstream"], "东风交付")
        save_manual_snapshot(self.conn, self.project, ws, {"week_key": "2026-W40", "status": "advanced", "summary": "完成联调", "next_step": "验收"})
        rows = invoke(ctx, "workstream_list", {"project": "agent guard"})["workstreams"]
        self.assertEqual((rows[0]["name"], rows[0]["material_total"]), ("东风交付", 1))
        agent = OpContext(self.conn, self.owner["id"], bound_project_id=self.project, for_agent=True)
        shown = invoke(agent, "workstream_show", {"workstream": "东风交付", "project": "embody"})
        self.assertEqual(shown["materials"][0]["id"], result["id"])
        self.assertIn("2026-W40 [advanced] 完成联调 → 验收", shown["timeline"])
        with self.assertRaises(LookupError):
            invoke(ctx, "workstream_show", {"workstream": "不存在", "project": "agent guard"})

    # ------------------------------------------------------------ API

    def test_api_roles_routes_and_workspace(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        tokens = {name: auth.create_session(self.conn, uid) for name, uid in (("owner", self.owner["id"]), ("reader", self.reader), ("writer", self.writer))}
        outsider = auth.create_user(self.conn, "outsider", "secret1")
        tokens["outsider"] = auth.create_session(self.conn, outsider)
        self.conn.commit()

        def call(who, method, path, body=None):
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=30)
            client.request(method, path, json.dumps(body) if body is not None else None,
                           {"Authorization": f"Bearer {tokens[who]}", "Content-Type": "application/json"})
            response = client.getresponse()
            data = json.loads(response.read() or b"{}")
            client.close()
            return response.status, data

        base = f"/api/projects/{self.project}/workstreams"
        self.assertEqual(call("reader", "POST", base, {"name": "x"})[0], 403)
        self.assertEqual(call("outsider", "GET", base)[0], 404)
        status, data = call("writer", "POST", f"{base}/seed")
        self.assertEqual((status, data["created"], len(data["workstreams"])), (200, 4, 4))
        ids = [w["id"] for w in data["workstreams"]]
        status, data = call("writer", "POST", f"{base}/reorder", {"ids": list(reversed(ids))})
        self.assertEqual([w["id"] for w in data["workstreams"]], list(reversed(ids)))
        self.assertEqual(call("reader", "GET", f"{base}/{ids[0]}")[1]["name"], "东风交付")
        self.assertEqual(call("reader", "GET", f"{base}/999999")[0], 404)
        status, detail = call("writer", "PUT", f"{base}/{ids[0]}/snapshots", {"week_key": "2026-W40", "status": "advanced", "summary": "推进"})
        self.assertEqual((status, detail["snapshots"][0]["source"]), (200, "manual"))

        upload = {"files": [{"filename": "周报.txt", "content_base64": base64.b64encode("浩瀚融资".encode()).decode()}], "workstream_id": ids[0]}
        status, created = call("writer", "POST", f"/api/projects/{self.project}/materials", upload)
        self.assertEqual(status, 201)
        ws_payload = workspace(self.conn, self.project)
        material = next(m for m in ws_payload["materials"] if m["id"] == created["id"])
        self.assertEqual(material["workstreams"], {"primary": ids[0], "related": [], "source": "manual"})
        self.assertEqual(len(ws_payload["workstreams"]["workstreams"]), 4)
        self.conn.commit()  # workspace() evaluates risks on this connection
        status, _ = call("reader", "PUT", f"/api/projects/{self.project}/materials/{created['id']}/workstreams", {"primary": ids[1]})
        self.assertEqual(status, 403)
        status, _ = call("writer", "PUT", f"/api/projects/{self.project}/materials/{created['id']}/workstreams", {"primary": ids[1], "related": [ids[2]]})
        self.assertEqual(status, 200)

        status, data = call("writer", "POST", f"{base}/organize")
        self.assertEqual(status, 202)
        status, data = call("writer", "GET", "/api/todos")
        self.assertEqual(data["workstream_options"][0]["project_name"], "agent guard")
        self.assertEqual(call("writer", "DELETE", f"{base}/{ids[3]}")[0], 200)


if __name__ == "__main__":
    unittest.main()
