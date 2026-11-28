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
    create_item,
    create_workstream,
    delete_item,
    delete_workstream,
    parse_objective_lines,
    previous_week_key,
    save_manual_snapshot,
    seed_from_objectives,
    set_material_links,
    set_todo_links,
    update_item,
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
            [name for name, _goal, _sub in parse_objective_lines(AGENT_GUARD_OBJECTIVES)],
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

        def spy(conn, project_id, week_key, report_md, source="generated", timeout=120, **kwargs):
            seen.append(conn.execute("SELECT status FROM generation_jobs ORDER BY id DESC LIMIT 1").fetchone()[0])
            seen.append(bool(conn.execute("SELECT 1 FROM weekly_reports WHERE project_id = ?", (project_id,)).fetchone()))
            return {"snapshots": 0, "items_added": 0, "items_closed": 0}

        with mock.patch("reports_app.workstream_agent.extract_snapshots", side_effect=spy):
            job = generate_report(self.conn, self.project, "manual", force=True)
        self.assertEqual(seen, ["running", True])
        self.assertEqual(self.conn.execute("SELECT status FROM generation_jobs WHERE id = ?", (job,)).fetchone()[0], "success")

    def test_snapshot_failure_never_fails_report(self):
        create_workstream(self.conn, self.project, {"name": "东风交付"})
        with mock.patch("reports_app.workstream_agent.extract_snapshots", side_effect=RuntimeError("boom")):
            job = generate_report(self.conn, self.project, "manual", force=True)
        self.assertEqual(self.conn.execute("SELECT status FROM generation_jobs WHERE id = ?", (job,)).fetchone()[0], "success")

    def queue_organize(self):
        self.conn.execute(
            "INSERT INTO generation_jobs (project_id, week_key, trigger_type, provider, status, started_at) VALUES (?, ?, 'workstreams', 'internal', 'queued', ?)",
            (self.project, current_week_key(self.tz), iso_now()),
        )
        job = self.conn.execute("SELECT MAX(id) FROM generation_jobs").fetchone()[0]
        self.conn.commit()
        run_workstream_job(self.db_path, job, self.project)
        row = self.conn.execute("SELECT status, output_md, failure_reason FROM generation_jobs WHERE id = ?", (job,)).fetchone()
        self.assertEqual(row["status"], "success", row["failure_reason"])
        return row["output_md"]

    def backdate(self, material_id, weeks=1):
        old = (utc_now() - timedelta(days=7 * weeks)).isoformat()
        self.conn.execute("UPDATE materials SET created_at = ? WHERE id = ?", (old, material_id))
        self.conn.commit()

    def test_organize_job_initialises_history_once_then_only_current_week(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        material = store_manual_material(self.conn, self.project, {"title": "东风交付周会", "content": "联调完成"})
        unrelated = store_manual_material(self.conn, self.project, {"title": "杂项", "content": "无关"})
        self.backdate(material)
        last_week = previous_week_key(self.tz)
        self.conn.execute(
            "INSERT INTO weekly_reports (project_id, week_key, content_md, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (self.project, last_week, "# 周报\n东风交付推进", iso_now(), iso_now()),
        )
        self.conn.commit()
        self.assertEqual(self.queue_organize(), "首次整理：归类 1 份资料，补齐 1 周历史快照，更新本周 1 条快照")
        links = dict(self.conn.execute("SELECT material_id, source FROM material_workstreams").fetchall())
        self.assertEqual(links, {material: "auto"})
        self.assertNotIn(unrelated, links)
        past = self.conn.execute(
            "SELECT source, summary, updated_at FROM workstream_weekly WHERE workstream_id = ? AND week_key = ?", (ws, last_week)
        ).fetchone()
        self.assertEqual(past["source"], "backfill")
        self.assertTrue(workstream_overview(self.conn, self.project, self.tz)["organized_at"])
        # a successful 「AI 整理」 job is not a report success
        self.assertIsNone(latest_success(self.conn, self.project, current_week_key(self.tz)))

        # later runs: past weeks are locked, only this week is touched
        new_ws = create_workstream(self.conn, self.project, {"name": "融资"})
        old_note = store_manual_material(self.conn, self.project, {"title": "东风交付旧纪要", "content": "上周的"})
        self.backdate(old_note)
        fresh = store_manual_material(self.conn, self.project, {"title": "融资路演", "content": "本周两场"})
        self.conn.commit()
        self.assertEqual(self.queue_organize(), "本周：归类 1 份资料，更新本周 2 条快照")
        links = dict(self.conn.execute("SELECT material_id, workstream_id FROM material_workstreams").fetchall())
        self.assertEqual(links.get(fresh), new_ws)
        self.assertNotIn(old_note, links)
        self.assertEqual(
            dict(self.conn.execute(
                "SELECT source, summary, updated_at FROM workstream_weekly WHERE workstream_id = ? AND week_key = ?", (ws, last_week)
            ).fetchone()),
            dict(past),
        )
        self.assertIsNone(self.conn.execute(
            "SELECT 1 FROM workstream_weekly WHERE workstream_id = ? AND week_key = ?", (new_ws, last_week)
        ).fetchone())

    def test_past_weeks_are_locked_for_snapshots(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        with self.assertRaises(ValidationError):
            save_manual_snapshot(self.conn, self.project, ws, {"week_key": previous_week_key(self.tz), "status": "advanced", "summary": "补记"})
        save_manual_snapshot(self.conn, self.project, ws, {"status": "advanced", "summary": "本周推进"})
        row = self.conn.execute("SELECT week_key, source FROM workstream_weekly WHERE workstream_id = ?", (ws,)).fetchone()
        self.assertEqual(tuple(row), (current_week_key(self.tz), "manual"))
        # a report for a past week never rewrites that week's snapshots
        from reports_app.workstream_agent import refresh_after_report

        self.assertEqual(refresh_after_report(self.conn, self.project, previous_week_key(self.tz), "# 旧周报"), 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM workstream_weekly").fetchone()[0], 1)

    def test_tracking_items_crud_health_and_warning(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        first = create_item(self.conn, self.project, ws, {"title": "确认实车排期", "owner_label": "高鹏", "due_date": "2026-01-05"})
        second = create_item(self.conn, self.project, ws, {"title": "提交安全报告"})
        with self.assertRaises(ValidationError):
            create_item(self.conn, self.project, ws, {"title": " "})
        with self.assertRaises(ValidationError):
            create_item(self.conn, self.project, ws, {"title": "x", "due_date": "明天"})
        with self.assertRaises(LookupError):
            update_item(self.conn, self.other, ws, first, {"status": "done"})
        item = self.overview_item(ws)
        self.assertEqual((item["items_open"], item["items_overdue"], item["health"]), (2, 1, "at risk"))
        evaluate_risks(self.conn, self.project)
        warning = self.conn.execute(
            "SELECT severity, title FROM risk_warnings WHERE rule = 'workstream_item_overdue' AND status = 'active'"
        ).fetchone()
        self.assertEqual(warning["severity"], "medium")
        self.assertIn("1 条待跟踪项逾期", warning["title"])
        update_item(self.conn, self.project, ws, first, {"status": "done"})
        items = workstream_detail(self.conn, self.project, ws, self.tz, self.owner["id"])["items"]
        self.assertEqual([(i["id"], i["status"]) for i in items], [(second, "open"), (first, "done")])
        self.assertTrue(items[1]["done_at"])
        evaluate_risks(self.conn, self.project)
        self.assertIsNone(self.conn.execute(
            "SELECT 1 FROM risk_warnings WHERE rule = 'workstream_item_overdue' AND status = 'active'"
        ).fetchone())
        self.assertEqual(self.overview_item(ws)["health"], "on track")
        delete_item(self.conn, self.project, ws, second)
        delete_workstream(self.conn, self.project, ws)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM workstream_items").fetchone()[0], 0)

    def test_agent_adds_and_closes_only_its_own_items(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        manual = create_item(self.conn, self.project, ws, {"title": "签署交付确认单"})
        add_uploaded_materials(self.conn, self.project, [self.file("东风周会.txt", "东风交付 待跟进：确认实车排期")])
        self.conn.commit()
        self.assertIn("新增 1 条待跟踪项", self.queue_organize())
        auto = self.conn.execute("SELECT id, source, title FROM workstream_items WHERE id != ?", (manual,)).fetchone()
        self.assertEqual((auto["source"], auto["title"]), ("auto", "确认实车排期"))
        # the same follow-up again is a duplicate; finished items close only when the agent created them
        add_uploaded_materials(self.conn, self.project, [
            self.file("东风周会2.txt", "东风交付 待跟进：确认 实车排期。已完成：确认实车排期 已完成：签署交付确认单"),
        ])
        self.conn.commit()
        self.assertIn("关闭 1 条", self.queue_organize())
        rows = dict(self.conn.execute("SELECT id, status FROM workstream_items").fetchall())
        self.assertEqual(rows, {manual: "open", auto["id"]: "done"})
        context, _hash = assemble_context(self.conn, self.project)
        self.assertEqual(context["workstreams"][0]["open_items"], [{"title": "签署交付确认单", "due_date": ""}])

    def test_timeline_reaches_latest_target(self):
        create_workstream(self.conn, self.project, {"name": "东风交付", "target_date": (utc_now() + timedelta(days=70)).date().isoformat()})
        data = workstream_overview(self.conn, self.project, self.tz)
        weeks = [w["week_key"] for w in data["timeline"]]
        self.assertEqual(weeks[:8], data["weeks"])
        self.assertIn(len(weeks) - 8, (10, 11, 12))
        create_workstream(self.conn, self.project, {"name": "远期", "target_date": "2030-01-01"})
        self.assertEqual(len(workstream_overview(self.conn, self.project, self.tz)["timeline"]), 8 + 26)

    # ------------------------------------------------------------ 子工作线

    def test_sub_workstream_rules_order_and_delete(self):
        parent = create_workstream(self.conn, self.project, {"name": "东风交付"})
        other = create_workstream(self.conn, self.project, {"name": "融资"})
        child = create_workstream(self.conn, self.project, {"name": "实车测试", "parent_id": parent})
        order = [w["id"] for w in workstream_overview(self.conn, self.project, self.tz)["workstreams"]]
        self.assertEqual(order, [parent, child, other])
        with self.assertRaises(ValidationError):  # two levels at most
            create_workstream(self.conn, self.project, {"name": "孙", "parent_id": child})
        with self.assertRaises(ValidationError):  # a line with children stays top-level
            update_workstream(self.conn, self.project, parent, {"parent_id": other})
        with self.assertRaises(ValidationError):
            update_workstream(self.conn, self.project, other, {"parent_id": other})
        foreign = create_workstream(self.conn, self.other, {"name": "外部"})
        with self.assertRaises(ValidationError):
            create_workstream(self.conn, self.project, {"name": "跨项目", "parent_id": foreign})
        with self.assertRaises(ValidationError):  # names stay unique across levels
            create_workstream(self.conn, self.project, {"name": "融资", "parent_id": parent})
        update_workstream(self.conn, self.project, other, {"parent_id": parent})
        item = self.overview_item(parent)
        self.assertEqual((item["children"], self.overview_item(other)["path"]), ([child, other], "东风交付 / 融资"))
        update_workstream(self.conn, self.project, other, {"parent_id": None})
        self.assertIsNone(self.overview_item(other)["parent_id"])
        delete_workstream(self.conn, self.project, parent)
        self.assertIsNone(self.overview_item(child)["parent_id"])

    def test_closing_parent_closes_children_and_reopening_child_reopens_parent(self):
        parent = create_workstream(self.conn, self.project, {"name": "东风交付"})
        child = create_workstream(self.conn, self.project, {"name": "实车测试", "parent_id": parent})
        paused = create_workstream(self.conn, self.project, {"name": "标定", "parent_id": parent, "status": "paused"})
        status = lambda wid: self.overview_item(wid)["status"]
        update_workstream(self.conn, self.project, parent, {"status": "done"})
        self.assertEqual([status(w) for w in (parent, child, paused)], ["done", "done", "done"])
        self.assertEqual(self.overview_item(parent)["health"], "complete")
        update_workstream(self.conn, self.project, child, {"status": "active"})
        self.assertEqual([status(w) for w in (parent, child, paused)], ["active", "active", "done"])
        update_workstream(self.conn, self.project, parent, {"status": "done"})
        create_workstream(self.conn, self.project, {"name": "新子线", "parent_id": parent})
        self.assertEqual(status(parent), "active")  # a new open child reopens its parent
        update_workstream(self.conn, self.project, child, {"status": "done"})
        self.assertEqual(status(parent), "active")  # closing a child leaves the parent open

    def test_parent_health_rolls_up_and_counts_child_activity(self):
        parent = create_workstream(self.conn, self.project, {"name": "东风交付"})
        child = create_workstream(self.conn, self.project, {"name": "实车测试", "parent_id": parent})
        self.age(parent)
        self.age(child)
        set_material_links(self.conn, self.project, store_manual_material(self.conn, self.project, {"title": "n", "content": "x"}), child)
        create_item(self.conn, self.project, child, {"title": "确认排期", "due_date": "2020-01-01"})
        evaluate_risks(self.conn, self.project)
        item = self.overview_item(parent)
        # the child's material keeps the parent from looking stale; the child's overdue item pulls it to at risk
        self.assertEqual((item["own_health"], item["health"]), ("on track", "at risk"))
        self.assertEqual(item["child_alerts"], ["子工作线「实车测试」有风险"])
        refs = {r[0] for r in self.conn.execute("SELECT source_ref FROM risk_warnings WHERE status = 'active' AND rule LIKE 'workstream_%'")}
        self.assertEqual(refs, {f"workstream:{child}"})  # warnings stay per line
        detail = workstream_detail(self.conn, self.project, parent, self.tz, self.owner["id"])
        self.assertEqual([(c["id"], c["health"], c["items_overdue"]) for c in detail["child_items"]], [(child, "at risk", 1)])
        child_detail = workstream_detail(self.conn, self.project, child, self.tz, self.owner["id"])
        self.assertEqual(child_detail["parent"], {"id": parent, "name": "东风交付"})
        update_workstream(self.conn, self.project, parent, {"status": "paused"})
        self.assertEqual(self.overview_item(parent)["health"], "paused")

    def test_seed_nested_objectives(self):
        self.conn.execute("UPDATE project_plans SET objectives = ? WHERE project_id = ?", (
            "1. 东风交付，座舱安全\n   - 实车测试\n   - 风险规则平台\n1.1 智驾安全研究\n2. 浩瀚融资", self.project))
        created = seed_from_objectives(self.conn, self.project)
        rows = {w["name"]: w for w in workstream_overview(self.conn, self.project, self.tz)["workstreams"]}
        self.assertEqual(len(created), 5)
        parent = rows["东风交付"]["id"]
        self.assertEqual({n for n, w in rows.items() if w["parent_id"] == parent}, {"实车测试", "风险规则平台", "智驾安全研究"})
        self.assertIsNone(rows["浩瀚融资"]["parent_id"])
        self.assertEqual(seed_from_objectives(self.conn, self.project), [])

    def test_agent_prompts_know_the_hierarchy(self):
        from reports_app.workstream_agent import build_classify_prompt, extract_snapshots
        from reports_app.workstreams import workstreams_for_prompt

        parent = create_workstream(self.conn, self.project, {"name": "东风交付"})
        child = create_workstream(self.conn, self.project, {"name": "实车测试", "parent_id": parent})
        listed = workstreams_for_prompt(self.conn, self.project)
        self.assertEqual(listed[1], {"id": child, "name": "实车测试", "goal": "", "parent": "东风交付"})
        self.assertIn("子工作线", build_classify_prompt(listed, []))
        material = store_manual_material(self.conn, self.project, {"title": "实车周会", "content": "待跟进：确认场地"})
        set_material_links(self.conn, self.project, material, child)
        result = extract_snapshots(self.conn, self.project, current_week_key(self.tz), "")
        self.assertEqual(result["snapshots"], 2)
        summaries = dict(self.conn.execute("SELECT workstream_id, summary FROM workstream_weekly").fetchall())
        self.assertIn("实车周会", summaries[parent])  # the parent's snapshot sees its children's material
        items = self.conn.execute("SELECT workstream_id, title FROM workstream_items").fetchall()
        self.assertEqual([tuple(r) for r in items], [(child, "确认场地")])  # follow-ups stay on the child
        context, _hash = assemble_context(self.conn, self.project)
        self.assertEqual(context["workstreams"][1]["parent"], "东风交付")
        self.assertEqual(context["new_materials_this_week"][0]["workstream"], "东风交付 / 实车测试")

    # ------------------------------------------------------------ milestones

    def test_workstream_milestones_and_project_plan(self):
        from reports_app.plans import create_milestone, delete_milestone, load_plan, save_plan_payload, update_milestone

        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        self.conn.execute("UPDATE project_plans SET milestones_json = ? WHERE project_id = ?", (json.dumps([
            {"title": "旧里程碑", "target_date": "2020-01-01", "status": "planned"},
            {"title": "旧关联", "target_date": "2020-01-02", "status": "planned", "workstream_id": str(ws)},
        ]), self.project))
        from reports_app.plans import ensure_milestone_ids

        ensure_milestone_ids(self.conn)
        plan = load_plan(self.conn, self.project)
        self.assertEqual([(m["id"], m.get("workstream_id")) for m in plan["milestones"]], [(1, None), (2, ws)])
        evaluate_risks(self.conn, self.project)
        rules = {r[0]: r[1] for r in self.conn.execute("SELECT rule, details FROM risk_warnings WHERE status = 'active' AND rule IN ('overdue_milestone', 'workstream_overdue')")}
        # the workstream's milestone is reported once, by its workstream
        self.assertEqual(rules["overdue_milestone"], "旧里程碑")
        self.assertIn("旧关联", rules["workstream_overdue"])

        new_id = create_milestone(self.conn, self.project, ws, {"title": "实车测试", "target_date": "2030-01-01"})
        self.assertEqual(new_id, 3)
        with self.assertRaises(ValidationError):
            create_milestone(self.conn, self.project, ws, {"title": "", "target_date": "2030-01-01"})
        with self.assertRaises(LookupError):  # a project-level milestone is not this workstream's
            update_milestone(self.conn, self.project, ws, 1, {"status": "complete"})
        update_milestone(self.conn, self.project, ws, 2, {"status": "complete"})
        self.assertEqual(self.overview_item(ws)["health"], "on track")
        # the 项目计划 panel replaces only project-level milestones
        save_plan_payload(self.conn, self.project, {
            "objectives": "目标", "deliverables": [{"title": "交付物"}],
            "project_milestones": [{"id": 1, "title": "旧里程碑", "status": "complete"}, {"title": "项目发布", "target_date": "2030-02-01"}],
        })
        plan = load_plan(self.conn, self.project)
        self.assertEqual(sorted(m["title"] for m in plan["milestones"]), ["实车测试", "旧关联", "旧里程碑", "项目发布"])
        released = next(m for m in plan["milestones"] if m["title"] == "项目发布")
        save_plan_payload(self.conn, self.project, {"project_milestones": [{**released, "workstream_id": ws}]})
        detail = workstream_detail(self.conn, self.project, ws, self.tz, self.owner["id"])
        self.assertEqual(sorted(m["title"] for m in detail["milestones"]), ["实车测试", "旧关联", "项目发布"])
        self.assertEqual([m["title"] for m in load_plan(self.conn, self.project)["milestones"] if not m.get("workstream_id")], [])
        update_milestone(self.conn, self.project, ws, new_id, {"workstream_id": None})
        self.assertNotIn(new_id, [m["id"] for m in workstream_detail(self.conn, self.project, ws, self.tz, self.owner["id"])["milestones"]])
        delete_milestone(self.conn, self.project, ws, 2)
        self.assertEqual(sorted(m["id"] for m in load_plan(self.conn, self.project)["milestones"]), [3, 4])

    # ------------------------------------------------------------ PR / issue

    def add_repo_row(self, repo, workstream_id=None, project=None):
        cur = self.conn.execute(
            """
            INSERT INTO github_repos (project_id, repo, git_mode, enabled, fetch_pull_requests, fetch_issues, status, workstream_id, created_at, updated_at)
            VALUES (?, ?, 'github', 1, 1, 1, 'connected', ?, ?, ?)
            """,
            (project or self.project, repo, workstream_id, iso_now(), iso_now()),
        )
        self.conn.commit()
        return cur.lastrowid

    @staticmethod
    def extras(repo, pulls=(), issues=()):
        def entry(number, title, state="open", merged=False):
            return {"number": number, "title": title, "state": state, "merged": merged, "draft": False, "author": "dev",
                    "updated_at": iso_now(), "url": f"https://github.com/{repo}/pull/{number}"}
        return {"repo": repo, "git_mode": "github",
                "pull_requests": {"status": "ok", "pull_requests": [entry(*p) for p in pulls]},
                "issues": {"status": "ok", "issues": [entry(*i) for i in issues]}}

    def test_git_activity_syncs_into_workstreams(self):
        from reports_app.workstream_git import set_item_link, set_repo_workstream, unassigned_week_items

        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        fund = create_workstream(self.conn, self.project, {"name": "融资"})
        self.age(ws)
        self.age(fund)
        cog = self.add_repo_row("CogDefend/cogdefend", ws)
        cloud = self.add_repo_row("CogDefend/cogdefend-cloud")
        self.add_repo_row("other/repo", project=self.other)
        fetched = {
            "CogDefend/cogdefend": self.extras("CogDefend/cogdefend", pulls=[(12, "规则引擎重构", "closed", True)], issues=[(30, "排查告警误报")]),
            "CogDefend/cogdefend-cloud": self.extras("CogDefend/cogdefend-cloud", pulls=[(5, "融资演示环境部署", "closed", True)], issues=[(7, "升级依赖")]),
        }
        calls = []

        def fake_fetch(repo, since, until, flags, git_mode="github", auth_info=None, timeout=30):
            calls.append((repo, flags))
            return fetched[repo]

        with mock.patch("reports_app.git_sources.fetch_repo_extras", side_effect=fake_fetch):
            summary = self.queue_organize()
        self.assertIn("同步 4 条 PR/Issue（AI 归类 1 条）", summary)
        self.assertEqual(sorted(c[0] for c in calls), ["CogDefend/cogdefend", "CogDefend/cogdefend-cloud"])
        self.assertEqual(calls[0][1], {"fetch_pull_requests": 1, "fetch_issues": 1})
        links = {(r["repo_id"], r["number"]): (r["workstream_id"], r["link_source"]) for r in self.conn.execute("SELECT * FROM workstream_git_items")}
        self.assertEqual(links, {(cog, 12): (ws, "repo"), (cog, 30): (ws, "repo"), (cloud, 5): (fund, "auto"), (cloud, 7): (None, "")})
        week = current_week_key(self.tz)
        self.assertEqual([g["number"] for g in unassigned_week_items(self.conn, self.project, week)], [7])
        # PR / issue activity is evidence for the snapshot and keeps the line from looking stale
        snapshot = self.conn.execute("SELECT status, summary FROM workstream_weekly WHERE workstream_id = ?", (fund,)).fetchone()
        self.assertEqual((snapshot["status"], snapshot["summary"]), ("advanced", "本周 1 条 PR/Issue：融资演示环境部署"))
        item = self.overview_item(ws)
        self.assertEqual((item["health"], item["git_week"], item["cells"][-1]["git"]), ("on track", 2, 2))
        detail = workstream_detail(self.conn, self.project, ws, self.tz, self.owner["id"])
        self.assertEqual({(g["number"], g["state"]) for g in detail["git_items"]}, {(12, "merged"), (30, "open")})

        # a person's choice wins over the repository default, now and in later weeks
        pr = self.conn.execute("SELECT id FROM workstream_git_items WHERE number = 30").fetchone()[0]
        set_item_link(self.conn, self.project, pr, fund)
        set_repo_workstream(self.conn, self.project, cog, None)
        rows = {r["number"]: (r["workstream_id"], r["link_source"]) for r in self.conn.execute("SELECT * FROM workstream_git_items")}
        self.assertEqual((rows[30], rows[12]), ((fund, "manual"), (None, "")))
        with self.assertRaises(ValidationError):
            set_item_link(self.conn, self.project, pr, create_workstream(self.conn, self.other, {"name": "外部"}))
        self.conn.execute("UPDATE workstream_git_items SET week_key = '2026-W01'")
        set_repo_workstream(self.conn, self.project, cog, ws)
        with mock.patch("reports_app.git_sources.fetch_repo_extras", side_effect=fake_fetch):
            self.queue_organize()
        rows = {r["number"]: (r["workstream_id"], r["link_source"]) for r in self.conn.execute(
            "SELECT * FROM workstream_git_items WHERE week_key = ?", (week,))}
        self.assertEqual((rows[30], rows[12]), ((fund, "manual"), (ws, "repo")))

    def test_report_reuses_fetched_git_extras(self):
        from reports_app.workstream_agent import refresh_after_report
        from reports_app.workstream_git import annotate_extras

        ws = create_workstream(self.conn, self.project, {"name": "东风交付"})
        self.add_repo_row("CogDefend/cogdefend", ws)
        extras = [self.extras("CogDefend/cogdefend", pulls=[(12, "规则引擎重构", "open")])]
        with mock.patch("reports_app.git_sources.fetch_repo_extras", side_effect=AssertionError("no remote call")):
            refresh_after_report(self.conn, self.project, current_week_key(self.tz), "# 周报", git_extras=extras)
        self.assertEqual(self.conn.execute("SELECT workstream_id FROM workstream_git_items").fetchone()[0], ws)
        tagged = annotate_extras(self.conn, self.project, [self.extras("CogDefend/cogdefend", pulls=[(12, "规则引擎重构")])])
        self.assertEqual(tagged[0]["pull_requests"]["pull_requests"][0]["workstream"], "东风交付")
        ctx = OpContext(self.conn, self.owner["id"])
        shown = invoke(ctx, "workstream_show", {"workstream": "东风交付", "project": "agent guard"})
        self.assertEqual(shown["git_text"], f"CogDefend/cogdefend#12 pr [open] 规则引擎重构 ({current_week_key(self.tz)})")

    # ------------------------------------------------------------ operations

    def test_operations_list_show_and_materials_add(self):
        ws = create_workstream(self.conn, self.project, {"name": "东风交付", "goal": "座舱安全交付"})
        ctx = OpContext(self.conn, self.owner["id"])
        result = invoke(ctx, "materials_add", {"project": "agent guard", "text": "联调完成", "title": "日报", "workstream": "东风交付"})
        listing = invoke(ctx, "materials_list", {"project": "agent guard"})
        self.assertEqual(listing["materials"][0]["workstream"], "东风交付")
        create_item(self.conn, self.project, ws, {"title": "确认实车排期", "due_date": "2030-01-05"})
        save_manual_snapshot(self.conn, self.project, ws, {"status": "advanced", "summary": "完成联调", "next_step": "验收"})
        rows = invoke(ctx, "workstream_list", {"project": "agent guard"})["workstreams"]
        self.assertEqual((rows[0]["name"], rows[0]["material_total"]), ("东风交付", 1))
        agent = OpContext(self.conn, self.owner["id"], bound_project_id=self.project, for_agent=True)
        shown = invoke(agent, "workstream_show", {"workstream": "东风交付", "project": "embody"})
        self.assertEqual(shown["materials"][0]["id"], result["id"])
        self.assertIn(f"{current_week_key(self.tz)} [advanced] 完成联调 → 验收", shown["timeline"])
        self.assertEqual(shown["items_text"], "[ ] 确认实车排期 (due 2030-01-05)")
        self.assertEqual(rows[0]["items_open"], 1)
        child = create_workstream(self.conn, self.project, {"name": "实车测试", "parent_id": ws})
        from reports_app.plans import create_milestone

        create_milestone(self.conn, self.project, ws, {"title": "验收", "target_date": "2030-02-01"})
        rows = invoke(ctx, "workstream_list", {"project": "agent guard"})["workstreams"]
        self.assertEqual([(r["label"], r["parent_id"]) for r in rows], [("东风交付", None), ("└ 实车测试", ws)])
        shown = invoke(ctx, "workstream_show", {"workstream": "东风交付", "project": "agent guard"})
        self.assertEqual(shown["children_text"], f"#{child} 实车测试 [active/on track]")
        self.assertEqual(shown["milestones_text"], "[ ] 验收 (2030-02-01)")
        self.assertEqual(invoke(ctx, "workstream_show", {"workstream": "实车测试", "project": "agent guard"})["path"], "东风交付 / 实车测试")
        with self.assertRaises(LookupError):
            invoke(ctx, "workstream_show", {"workstream": "不存在", "project": "agent guard"})

    # ------------------------------------------------------------ members

    def test_members_own_workstreams(self):
        from reports_app.db import migrate_schema
        from reports_app.members import add_member, list_members, member_candidates, remove_member, update_member

        linked = add_member(self.conn, self.project, {"user_id": self.writer})
        typed = add_member(self.conn, self.project, {"name": " 高鹏 "})
        self.assertEqual([(m["name"], m["username"]) for m in list_members(self.conn, self.project)],
                         [("writer", "writer"), ("高鹏", "")])
        self.assertNotIn("writer", [u["username"] for u in member_candidates(self.conn, self.project)])
        with self.assertRaises(ValidationError):
            add_member(self.conn, self.project, {"name": "高鹏"})
        with self.assertRaises(ValidationError):
            add_member(self.conn, self.project, {"user_id": self.writer})
        other_member = add_member(self.conn, self.other, {"name": "外部"})

        ws = create_workstream(self.conn, self.project, {"name": "东风交付", "owner_member_id": typed})
        row = self.conn.execute("SELECT owner_member_id, owner_label FROM workstreams WHERE id = ?", (ws,)).fetchone()
        self.assertEqual(tuple(row), (typed, "高鹏"))
        with self.assertRaises(ValidationError):
            update_workstream(self.conn, self.project, ws, {"owner_member_id": other_member})
        update_workstream(self.conn, self.project, ws, {"goal": "交付"})
        self.assertEqual(self.conn.execute("SELECT owner_member_id FROM workstreams WHERE id = ?", (ws,)).fetchone()[0], typed)
        # legacy owner_label writes match or create a member
        update_workstream(self.conn, self.project, ws, {"owner_label": "史哲昊"})
        names = [m["name"] for m in list_members(self.conn, self.project)]
        self.assertEqual(names, ["writer", "高鹏", "史哲昊"])
        # the linked account can change or be dropped later
        update_member(self.conn, self.project, typed, {"user_id": self.reader})
        with self.assertRaises(ValidationError):
            update_member(self.conn, self.project, linked, {"user_id": self.reader})
        update_member(self.conn, self.project, typed, {"user_id": None})
        self.assertEqual([m["user_id"] for m in list_members(self.conn, self.project)][:2], [self.writer, None])
        update_workstream(self.conn, self.project, ws, {"owner_member_id": linked})
        update_member(self.conn, self.project, linked, {"name": "王写"})
        self.assertEqual(self.conn.execute("SELECT owner_label FROM workstreams WHERE id = ?", (ws,)).fetchone()[0], "王写")
        self.assertEqual(workstream_overview(self.conn, self.project, self.tz)["workstreams"][0]["owner_label"], "王写")
        remove_member(self.conn, self.project, linked)
        row = self.conn.execute("SELECT owner_member_id, owner_label FROM workstreams WHERE id = ?", (ws,)).fetchone()
        self.assertEqual(tuple(row), (None, ""))

        # migration: free-text owners become members, usernames link accounts
        self.conn.execute("UPDATE workstreams SET owner_label = 'reader', owner_member_id = NULL WHERE id = ?", (ws,))
        legacy = create_workstream(self.conn, self.project, {"name": "融资"})
        self.conn.execute("UPDATE workstreams SET owner_label = '高鹏' WHERE id = ?", (legacy,))
        migrate_schema(self.conn)
        migrate_schema(self.conn)
        members = {m["name"]: m for m in list_members(self.conn, self.project)}
        self.assertEqual(members["reader"]["user_id"], self.reader)
        self.assertEqual(members["高鹏"]["workstream_count"], 1)
        self.assertEqual(self.conn.execute("SELECT owner_member_id FROM workstreams WHERE id = ?", (legacy,)).fetchone()[0], typed)

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

        members = f"/api/projects/{self.project}/members"
        self.assertEqual(call("writer", "POST", members, {"name": "高鹏"})[0], 403)
        self.assertEqual(call("writer", "GET", f"{members}/candidates")[0], 403)
        status, data = call("owner", "POST", members, {"name": "高鹏"})
        self.assertEqual((status, [m["name"] for m in data["members"]]), (201, ["高鹏"]))
        member_id = data["id"]
        self.assertEqual(call("reader", "GET", members)[1]["members"][0]["id"], member_id)
        self.assertEqual(call("owner", "PUT", f"{members}/{member_id}", {"name": ""})[0], 400)
        status, data = call("owner", "PUT", f"{members}/{member_id}", {"user_id": self.writer})
        self.assertEqual((status, data["members"][0]["username"]), (200, "writer"))
        self.assertEqual(call("writer", "PUT", f"{members}/{member_id}", {"user_id": None})[0], 403)
        self.assertEqual(call("owner", "DELETE", f"{members}/999999")[0], 404)
        self.assertEqual(call("outsider", "GET", members)[0], 404)

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
        self.assertEqual(call("writer", "PUT", f"{base}/{ids[0]}/snapshots", {"week_key": "2026-W40", "status": "advanced", "summary": "推进"})[0], 400)
        status, detail = call("writer", "PUT", f"{base}/{ids[0]}/snapshots", {"status": "advanced", "summary": "推进"})
        self.assertEqual((status, detail["snapshots"][0]["source"]), (200, "manual"))

        self.assertEqual(call("reader", "POST", f"{base}/{ids[0]}/items", {"title": "确认排期"})[0], 403)
        status, detail = call("writer", "POST", f"{base}/{ids[0]}/items", {"title": "确认排期", "due_date": "2030-01-01"})
        self.assertEqual((status, [i["title"] for i in detail["items"]]), (200, ["确认排期"]))
        item_id = detail["items"][0]["id"]
        self.assertEqual(call("writer", "PUT", f"{base}/{ids[1]}/items/{item_id}", {"status": "done"})[0], 404)
        status, detail = call("writer", "PUT", f"{base}/{ids[0]}/items/{item_id}", {"status": "done"})
        self.assertEqual((status, detail["items"][0]["status"]), (200, "done"))
        status, detail = call("writer", "DELETE", f"{base}/{ids[0]}/items/{item_id}")
        self.assertEqual((status, detail["items"]), (200, []))

        upload = {"files": [{"filename": "周报.txt", "content_base64": base64.b64encode("浩瀚融资".encode()).decode()}], "workstream_id": ids[0]}
        status, created = call("writer", "POST", f"/api/projects/{self.project}/materials", upload)
        self.assertEqual(status, 201)
        ws_payload = workspace(self.conn, self.project)
        material = next(m for m in ws_payload["materials"] if m["id"] == created["id"])
        self.assertEqual(material["workstreams"], {"primary": ids[0], "related": [], "source": "manual"})
        self.assertEqual(len(ws_payload["workstreams"]["workstreams"]), 4)
        self.assertEqual([m["name"] for m in ws_payload["members"]], ["高鹏"])
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

        # 子工作线 and milestones through the API
        status, data = call("writer", "POST", base, {"name": "实车测试", "parent_id": ids[0]})
        child = data["id"]
        self.assertEqual((status, next(w for w in data["workstreams"] if w["id"] == child)["path"]), (201, "东风交付 / 实车测试"))
        self.assertEqual(call("writer", "POST", base, {"name": "孙", "parent_id": child})[0], 400)
        status, data = call("writer", "GET", "/api/todos")
        option = next(w for w in data["workstream_options"][0]["workstreams"] if w["id"] == child)
        self.assertEqual((option["path"], option["parent_id"]), ("东风交付 / 实车测试", ids[0]))
        self.assertEqual(call("reader", "POST", f"{base}/{child}/milestones", {"title": "进场"})[0], 403)
        status, detail = call("writer", "POST", f"{base}/{child}/milestones", {"title": "进场", "target_date": "2030-01-01"})
        self.assertEqual((status, [m["title"] for m in detail["milestones"]]), (200, ["进场"]))
        milestone = detail["milestones"][0]["id"]
        self.assertEqual(call("writer", "PUT", f"{base}/{ids[1]}/milestones/{milestone}", {"status": "complete"})[0], 404)
        status, detail = call("writer", "PUT", f"{base}/{child}/milestones/{milestone}", {"status": "complete"})
        self.assertEqual((status, detail["milestones"][0]["status"]), (200, "complete"))
        status, parent = call("reader", "GET", f"{base}/{ids[0]}")
        self.assertEqual([c["name"] for c in parent["child_items"]], ["实车测试"])
        status, detail = call("writer", "DELETE", f"{base}/{child}/milestones/{milestone}")
        self.assertEqual((status, detail["milestones"]), (200, []))
        status, data = call("writer", "PUT", f"/api/projects/{self.project}/plan",
                            {"objectives": "目标", "project_milestones": [{"title": "发布", "target_date": "2030-03-01"}], "deliverables": []})
        self.assertEqual((status, [m["title"] for m in data["plan"]["milestones"]]), (200, ["发布"]))

        # PR / issue links: repository default (manage) and per-item choice (write)
        repo = self.add_repo_row("CogDefend/cogdefend")
        self.assertEqual(call("writer", "PUT", f"/api/projects/{self.project}/repos/{repo}", {"workstream_id": ids[0]})[0], 403)
        status, data = call("owner", "PUT", f"/api/projects/{self.project}/repos/{repo}", {"workstream_id": ids[0]})
        self.assertEqual((status, next(r for r in data["repos"] if r["id"] == repo)["workstream_id"]), (200, ids[0]))
        self.conn.execute(
            "INSERT INTO workstream_git_items (project_id, repo_id, kind, number, week_key, title, synced_at) VALUES (?, ?, 'issue', 9, ?, '排查', ?)",
            (self.project, repo, current_week_key(self.tz), iso_now()),
        )
        git_id = self.conn.execute("SELECT MAX(id) FROM workstream_git_items").fetchone()[0]
        self.conn.commit()
        self.assertEqual(call("reader", "PUT", f"{base}/git/{git_id}/link", {"workstream_id": ids[1]})[0], 403)
        status, data = call("writer", "PUT", f"{base}/git/{git_id}/link", {"workstream_id": ids[1]})
        self.assertEqual((status, data["unassigned_git"]), (200, []))
        status, detail = call("reader", "GET", f"{base}/{ids[1]}")
        self.assertEqual([(g["number"], g["link_source"]) for g in detail["git_items"]], [(9, "manual")])
        self.assertEqual(call("writer", "PUT", f"{base}/git/999999/link", {"workstream_id": ids[1]})[0], 404)


if __name__ == "__main__":
    unittest.main()
