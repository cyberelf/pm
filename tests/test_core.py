import base64
import json
import os
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from reports_app.db import create_project, init_db, connect
from reports_app.markdown import render_markdown
from reports_app.materials import store_manual_material, store_material, update_manual_material
from reports_app.reports import assemble_context, build_claude_evidence_prompt, build_tool_prompt, compact_previous_report, generate_report, changed_since_last_success, fake_provider_enabled, input_summary, provider_command, transient_provider_error
from reports_app.risks import evaluate_risks, progress_status
from reports_app.server import add_repo, evaluate_schedules, save_outcomes, save_plan, save_weekly_update, schedule_due, update_repo_notes, update_settings, workspace
from reports_app.timeutil import current_week_key
from reports_app.validation import ValidationError, validate_material_filename, validate_schedule_item


class CoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        init_db(self.db_path)
        self.conn = connect(self.db_path)
        self.project_id = create_project(
            self.conn,
            {
                "name": "Demo",
                "start_date": "2026-06-27",
                "timezone": "Asia/Shanghai",
                "report_provider": "codex",
            },
        )
        self.conn.commit()
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"

    def tearDown(self):
        self.conn.close()
        os.environ.pop("REPORTS_FAKE_PROVIDER", None)
        self.tmp.cleanup()

    def test_validation(self):
        validate_schedule_item({"weekday": 1, "local_time": "09:30", "timezone": "Asia/Shanghai"})
        with self.assertRaises(ValidationError):
            validate_schedule_item({"weekday": 8, "local_time": "09:30", "timezone": "Asia/Shanghai"})
        with self.assertRaises(ValidationError):
            validate_material_filename("notes.docx")
        self.assertEqual(validate_material_filename("notes.md"), ".md")

    def test_project_settings_and_schedule(self):
        update_settings(
            self.conn,
            self.project_id,
            {
                "name": "Demo",
                "description": "desc",
                "start_date": "2026-06-27",
                "timezone": "Asia/Shanghai",
                "status": "active",
                "report_provider": "claude",
                "system_prompt": "prompt",
                "report_template": "# T",
                "schedules": [{"weekday": 5, "local_time": "18:00", "timezone": "Asia/Shanghai"}],
            },
        )
        row = self.conn.execute("SELECT report_provider FROM projects WHERE id = ?", (self.project_id,)).fetchone()
        self.assertEqual(row["report_provider"], "claude")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM update_schedules").fetchone()["n"], 1)

    def test_report_context_includes_project_profile_and_plan(self):
        update_settings(
            self.conn,
            self.project_id,
            {
                "name": "Demo",
                "description": "desc",
                "start_date": "2026-06-27",
                "timezone": "Asia/Shanghai",
                "status": "active",
                "report_provider": "codex",
                "manual_background": "background",
                "manual_objectives": "profile objective",
                "manual_constraints": "constraint",
            },
        )
        save_plan(
            self.conn,
            self.project_id,
            {
                "objectives": "plan objective",
                "milestones": [{"title": "M1", "target_date": "2026-07-01", "status": "planned"}],
                "deliverables": [{"title": "D1", "target_date": "2026-07-02", "status": "planned"}],
            },
        )
        context, _hash = assemble_context(self.conn, self.project_id)
        self.assertEqual(context["project_profile"]["description"], "desc")
        self.assertEqual(context["project_profile"]["background"], "background")
        self.assertEqual(context["project_profile"]["objectives"], "profile objective")
        self.assertEqual(context["project_profile"]["constraints"], "constraint")
        self.assertEqual(context["plan"]["objectives"], "plan objective")
        self.assertEqual(context["plan"]["milestones"][0]["title"], "M1")
        self.assertIn("profile=yes", input_summary(context))
        self.assertIn("plan=yes", input_summary(context))

    def test_material_upload_and_extraction_failure(self):
        txt = base64.b64encode(b"hello").decode()
        material_id = store_material(self.conn, self.project_id, {"filename": "notes.txt", "content_base64": txt})
        row = self.conn.execute("SELECT source_type, extraction_status, extracted_text FROM materials WHERE id = ?", (material_id,)).fetchone()
        self.assertEqual(row["source_type"], "upload")
        self.assertEqual(row["extraction_status"], "extracted")
        self.assertEqual(row["extracted_text"], "hello")
        pdf = base64.b64encode(b"%PDF").decode()
        material_id = store_material(self.conn, self.project_id, {"filename": "brief.pdf", "content_base64": pdf})
        row = self.conn.execute("SELECT extraction_status FROM materials WHERE id = ?", (material_id,)).fetchone()
        self.assertEqual(row["extraction_status"], "failed")

    def test_manual_material_can_be_updated_only_in_current_week(self):
        material_id = store_manual_material(
            self.conn,
            self.project_id,
            {"title": "Decision note", "content": "initial content"},
        )
        update_manual_material(
            self.conn,
            self.project_id,
            material_id,
            {"title": "Decision note updated", "content": "updated content"},
        )
        row = self.conn.execute(
            "SELECT source_type, filename, extracted_text, created_at, updated_at FROM materials WHERE id = ?",
            (material_id,),
        ).fetchone()
        self.assertEqual(row["source_type"], "manual")
        self.assertEqual(row["filename"], "Decision note updated")
        self.assertEqual(row["extracted_text"], "updated content")
        self.assertGreaterEqual(row["updated_at"], row["created_at"])

        self.conn.execute(
            "UPDATE materials SET created_at = '2026-06-01T00:00:00+00:00' WHERE id = ?",
            (material_id,),
        )
        with self.assertRaises(ValidationError):
            update_manual_material(
                self.conn,
                self.project_id,
                material_id,
                {"title": "Locked", "content": "locked content"},
            )

    def test_report_context_includes_current_week_materials_and_commits(self):
        txt = base64.b64encode(b"weekly context").decode()
        store_material(self.conn, self.project_id, {"filename": "week.md", "content_base64": txt})
        store_manual_material(self.conn, self.project_id, {"title": "manual", "content": "manual context"})
        self.conn.execute(
            """
            INSERT INTO github_repos
            (project_id, repo, status, status_message, activity_summary, created_at, updated_at)
            VALUES (?, 'owner/repo', 'connected', 'ok', 'summary', '2026-06-27T00:00:00+00:00', '2026-06-27T00:00:00+00:00')
            """,
            (self.project_id,),
        )
        with mock.patch("reports_app.reports.weekly_commits") as commits:
            commits.return_value = {
                "repo": "owner/repo",
                "status": "ok",
                "status_message": "1 commits",
                "commits": [{"sha": "abc", "message": "ship", "author": "A", "date": "2026-06-27T00:00:00Z", "url": ""}],
            }
            context, _hash = assemble_context(self.conn, self.project_id)
        material_names = {item["filename"] for item in context["new_materials_this_week"]}
        self.assertIn("week.md", material_names)
        self.assertIn("manual", material_names)
        manual = next(item for item in context["new_materials_this_week"] if item["filename"] == "manual")
        self.assertEqual(manual["source_type"], "manual")
        self.assertEqual(manual["excerpt"], "manual context")
        self.assertEqual(context["git_commits_this_week"][0]["commits"][0]["message"], "ship")

    def test_agent_prompt_uses_platform_cli_instead_of_inline_context(self):
        store_manual_material(self.conn, self.project_id, {"title": "manual", "content": "sentinel manual context"})
        self.conn.execute(
            """
            INSERT INTO github_repos
            (project_id, repo, status, status_message, activity_summary, created_at, updated_at)
            VALUES (?, 'owner/repo', 'connected', 'ok', 'summary', '2026-06-27T00:00:00+00:00', '2026-06-27T00:00:00+00:00')
            """,
            (self.project_id,),
        )
        with mock.patch("reports_app.reports.weekly_commits") as commits:
            commits.return_value = {
                "repo": "owner/repo",
                "status": "ok",
                "status_message": "1 commits",
                "commits": [{"sha": "abc", "message": "sentinel commit", "author": "A", "date": "2026-06-27T00:00:00Z", "url": ""}],
            }
            context, _hash = assemble_context(self.conn, self.project_id)
        prompt = build_tool_prompt(context, "claude")
        self.assertIn("scripts/report_context.py", prompt)
        self.assertIn("overview", prompt)
        self.assertIn("Do not run `gh`", prompt)
        self.assertNotIn("sentinel manual context", prompt)
        self.assertNotIn("sentinel commit", prompt)

    def test_claude_prompt_uses_bounded_platform_evidence(self):
        store_manual_material(self.conn, self.project_id, {"title": "manual", "content": "manual context"})
        context, _hash = assemble_context(self.conn, self.project_id)
        prompt = build_claude_evidence_prompt(context)
        self.assertIn("Evidence JSON", prompt)
        self.assertIn("platform context CLI", prompt)
        self.assertIn("manual context", prompt)
        self.assertIn("Do not run `gh`", prompt)

    def test_claude_default_command_reads_prompt_from_stdin(self):
        command = provider_command("claude", "", Path(self.tmp.name), Path(self.tmp.name) / "report.md")
        self.assertEqual(command, ["claude", "--print", "--permission-mode", "dontAsk", "--no-session-persistence"])

    def test_previous_report_compaction_does_not_inline_body(self):
        compacted = compact_previous_report({"updated_at": "t", "content_md": "sentinel body"})
        self.assertEqual(compacted, {"available": True, "updated_at": "t"})

    def test_agent_context_cli_progressively_discloses_materials(self):
        material_id = store_manual_material(
            self.conn,
            self.project_id,
            {"title": "manual", "content": "manual body for cli"},
        )
        self.conn.commit()
        base = [
            "python3",
            "scripts/report_context.py",
            "--db",
            os.fspath(self.db_path),
            "--project-id",
            str(self.project_id),
            "--week-key",
            current_week_key("Asia/Shanghai"),
        ]
        overview = json.loads(subprocess.check_output(base + ["overview"], text=True))
        self.assertEqual(overview["project"]["name"], "Demo")
        materials = json.loads(subprocess.check_output(base + ["materials"], text=True))
        self.assertEqual(materials["materials"][0]["id"], material_id)
        self.assertNotIn("excerpt", materials["materials"][0])
        detail = json.loads(subprocess.check_output(base + ["material", "--id", str(material_id)], text=True))
        self.assertEqual(detail["material"]["extracted_text"], "manual body for cli")

    def test_github_repo_is_unique_and_notes_enter_report_context(self):
        with mock.patch("reports_app.server.check_repo") as mocked:
            mocked.return_value = {
                "status": "connected",
                "status_message": "ok",
                "activity_summary": "summary",
                "last_activity_at": "2026-06-27T00:00:00Z",
            }
            first = add_repo(self.conn, self.project_id, {"repo": "owner/repo", "notes": "first note"})
            second = add_repo(self.conn, self.project_id, {"repo": "owner/repo", "notes": "reporting name"})
        self.assertEqual(first, second)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM github_repos").fetchone()["n"], 1)
        update_repo_notes(self.conn, self.project_id, first, {"notes": "repo purpose"})
        with mock.patch("reports_app.reports.weekly_commits") as commits:
            commits.return_value = {"repo": "owner/repo", "status": "ok", "status_message": "0 commits", "commits": []}
            context, _hash = assemble_context(self.conn, self.project_id)
        self.assertEqual(context["github_activity"][0]["notes"], "repo purpose")
        self.assertEqual(context["git_commits_this_week"][0]["notes"], "repo purpose")

    def test_fake_provider_flag_requires_truthy_value(self):
        os.environ["REPORTS_FAKE_PROVIDER"] = "0"
        self.assertFalse(fake_provider_enabled())
        os.environ["REPORTS_FAKE_PROVIDER"] = "false"
        self.assertFalse(fake_provider_enabled())
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"
        self.assertTrue(fake_provider_enabled())

    def test_transient_provider_error_detection(self):
        self.assertTrue(transient_provider_error("API Error: 529 模型当前访问量过大，请稍后再试"))
        self.assertFalse(transient_provider_error("unsupported report provider"))

    def test_iso_week_boundary(self):
        self.assertRegex(current_week_key("Asia/Shanghai"), r"^\d{4}-W\d{2}$")

    def test_schedule_due_uses_local_weekday_time_and_last_check(self):
        zone = ZoneInfo("Asia/Shanghai")
        schedule = {"weekday": 5, "local_time": "18:00", "timezone": "Asia/Shanghai", "last_checked_at": None}
        self.assertFalse(schedule_due(schedule, datetime(2026, 6, 26, 17, 59, tzinfo=zone)))
        self.assertTrue(schedule_due(schedule, datetime(2026, 6, 26, 18, 1, tzinfo=zone)))
        schedule["last_checked_at"] = datetime(2026, 6, 26, 18, 1, tzinfo=zone).isoformat()
        self.assertFalse(schedule_due(schedule, datetime(2026, 6, 26, 19, 0, tzinfo=zone)))

    def test_manual_generation_overwrites_report_and_preserves_history(self):
        save_weekly_update(self.conn, self.project_id, {"completed": "A", "in_progress": "", "blockers": "", "risks": "", "next_steps": ""})
        job1 = generate_report(self.conn, self.project_id, "manual", force=True)
        save_weekly_update(self.conn, self.project_id, {"completed": "B", "in_progress": "", "blockers": "", "risks": "", "next_steps": ""})
        job2 = generate_report(self.conn, self.project_id, "manual", force=True)
        self.assertNotEqual(job1, job2)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM weekly_reports").fetchone()["n"], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM generation_jobs WHERE status = 'success'").fetchone()["n"], 2)

    def test_workspace_includes_read_only_report_history(self):
        now_week = current_week_key("Asia/Shanghai")
        self.conn.execute(
            """
            INSERT INTO weekly_reports (project_id, week_key, content_md, latest_job_id, created_at, updated_at)
            VALUES (?, '2026-W25', '# Old Report', 1, '2026-06-21T00:00:00+00:00', '2026-06-21T00:00:00+00:00')
            """,
            (self.project_id,),
        )
        self.conn.execute(
            """
            INSERT INTO weekly_reports (project_id, week_key, content_md, latest_job_id, created_at, updated_at)
            VALUES (?, ?, '# Current Report', 2, '2026-06-29T00:00:00+00:00', '2026-06-29T00:00:00+00:00')
            """,
            (self.project_id, now_week),
        )
        data = workspace(self.conn, self.project_id)
        self.assertEqual(data["report"]["week_key"], now_week)
        self.assertEqual([item["week_key"] for item in data["report_history"]], [now_week, "2026-W25"])
        self.assertTrue(data["report_history"][0]["is_current_week"])
        self.assertFalse(data["report_history"][1]["is_current_week"])
        self.assertIn("<h1>Old Report</h1>", data["report_history"][1]["content_html"])

    def test_scheduled_duplicate_skip_but_manual_forces(self):
        save_weekly_update(self.conn, self.project_id, {"completed": "A"})
        generate_report(self.conn, self.project_id, "manual", force=True)
        self.assertFalse(changed_since_last_success(self.conn, self.project_id, current_week_key("Asia/Shanghai")))
        skipped = generate_report(self.conn, self.project_id, "scheduled", force=False)
        self.assertIsNone(skipped)
        forced = generate_report(self.conn, self.project_id, "manual", force=True)
        self.assertIsNotNone(forced)

    def test_project_profile_change_counts_as_report_input_change(self):
        save_weekly_update(self.conn, self.project_id, {"completed": "A"})
        generate_report(self.conn, self.project_id, "manual", force=True)
        self.assertFalse(changed_since_last_success(self.conn, self.project_id, current_week_key("Asia/Shanghai")))
        update_settings(
            self.conn,
            self.project_id,
            {
                "name": "Demo",
                "description": "new description",
                "start_date": "2026-06-27",
                "timezone": "Asia/Shanghai",
                "status": "active",
                "report_provider": "codex",
                "manual_background": "new background",
                "manual_objectives": "new objective",
                "manual_constraints": "new constraint",
            },
        )
        self.assertTrue(changed_since_last_success(self.conn, self.project_id, current_week_key("Asia/Shanghai")))

    def test_generation_failure_is_not_project_risk(self):
        week_key = current_week_key("Asia/Shanghai")
        save_weekly_update(self.conn, self.project_id, {"completed": "project work happened"})
        self.conn.execute(
            """
            INSERT INTO generation_jobs
            (project_id, week_key, trigger_type, provider, status, failure_reason, started_at, completed_at)
            VALUES (?, ?, 'manual', 'codex', 'failed', 'provider failed', '2026-06-27T00:00:00+00:00', '2026-06-27T00:00:01+00:00')
            """,
            (self.project_id, week_key),
        )
        evaluate_risks(self.conn, self.project_id)
        active = self.conn.execute(
            """
            SELECT COUNT(*) AS n FROM risk_warnings
            WHERE project_id = ? AND week_key = ? AND rule = 'generation_failed' AND status = 'active'
            """,
            (self.project_id, week_key),
        ).fetchone()["n"]
        self.assertEqual(active, 0)
        self.assertEqual(progress_status(self.conn, self.project_id), "on track")

    def test_evaluate_schedules_respects_configured_time(self):
        with mock.patch("reports_app.server.schedule_due", return_value=True):
            update_settings(
                self.conn,
                self.project_id,
                {
                    "name": "Demo",
                    "description": "",
                    "start_date": "2026-06-27",
                    "timezone": "Asia/Shanghai",
                    "status": "active",
                    "report_provider": "codex",
                    "schedules": [{"weekday": 5, "local_time": "18:00", "timezone": "Asia/Shanghai"}],
                },
            )
            save_weekly_update(self.conn, self.project_id, {"completed": "scheduled"})
            evaluate_schedules(self.conn, self.project_id)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM generation_jobs WHERE trigger_type = 'scheduled'").fetchone()["n"], 1)

    def test_markdown_sanitizes_raw_html(self):
        html = render_markdown("# Hello\n<script>alert(1)</script>\n- **ok**")
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("<strong>ok</strong>", html)

    def test_risk_rules_and_no_report_promotion_model(self):
        save_plan(
            self.conn,
            self.project_id,
            {
                "objectives": "ship",
                "milestones": [{"title": "Late", "target_date": "2000-01-01", "status": "planned"}],
                "deliverables": [],
            },
        )
        save_outcomes(self.conn, self.project_id, {"outcomes": [{"title": "Blocked", "status": "blocked"}]})
        evaluate_risks(self.conn, self.project_id)
        rules = {row["rule"] for row in self.conn.execute("SELECT rule FROM risk_warnings")}
        self.assertIn("overdue_milestone", rules)
        self.assertIn("blocked_outcome", rules)
        self.assertEqual(progress_status(self.conn, self.project_id), "blocked")

    def test_risk_warning_resolves_when_condition_clears(self):
        evaluate_risks(self.conn, self.project_id)
        self.assertEqual(self.conn.execute("SELECT status FROM risk_warnings WHERE rule = 'missing_update'").fetchone()["status"], "active")
        save_weekly_update(self.conn, self.project_id, {"completed": "done"})
        evaluate_risks(self.conn, self.project_id)
        self.assertEqual(self.conn.execute("SELECT status FROM risk_warnings WHERE rule = 'missing_update'").fetchone()["status"], "resolved")

    def test_local_gh_disconnected_state_is_stored(self):
        with mock.patch("reports_app.server.check_repo") as mocked:
            mocked.return_value = {
                "status": "unauthenticated",
                "status_message": "login required",
                "activity_summary": "",
                "last_activity_at": None,
            }
            add_repo(self.conn, self.project_id, {"repo": "owner/repo"})
        row = self.conn.execute("SELECT status FROM github_repos").fetchone()
        self.assertEqual(row["status"], "unauthenticated")

    def test_system_source_errors_are_diagnostics_not_project_risks(self):
        week_key = current_week_key("Asia/Shanghai")
        save_weekly_update(self.conn, self.project_id, {"completed": "project work happened"})
        now = datetime.now(ZoneInfo("UTC")).isoformat()
        self.conn.execute(
            """
            INSERT INTO github_repos
            (project_id, repo, status, status_message, created_at, updated_at)
            VALUES (?, 'owner/repo', 'unauthenticated', 'login required', ?, ?)
            """,
            (self.project_id, now, now),
        )
        self.conn.execute(
            """
            INSERT INTO materials
            (project_id, filename, content_type, storage_path, size_bytes, checksum, source_type, extraction_status, extraction_error, created_at, updated_at)
            VALUES (?, 'broken.pdf', 'application/pdf', '/tmp/broken.pdf', 1, 'checksum', 'upload', 'failed', 'parse failed', ?, ?)
            """,
            (self.project_id, now, now),
        )
        self.conn.execute(
            """
            INSERT INTO generation_jobs
            (project_id, week_key, trigger_type, provider, status, failure_reason, started_at, completed_at)
            VALUES (?, ?, 'manual', 'codex', 'failed', 'provider failed', ?, ?)
            """,
            (self.project_id, week_key, now, now),
        )
        evaluate_risks(self.conn, self.project_id)
        rules = {row["rule"] for row in self.conn.execute("SELECT rule FROM risk_warnings WHERE status = 'active'")}
        self.assertNotIn("github_unavailable", rules)
        self.assertNotIn("material_extraction_failed", rules)
        self.assertNotIn("generation_failed", rules)
        self.assertEqual(progress_status(self.conn, self.project_id), "on track")
        data = workspace(self.conn, self.project_id)
        self.assertEqual(data["risks"], [])
        self.assertEqual({item["kind"] for item in data["source_diagnostics"]}, {"github", "material", "generation"})


if __name__ == "__main__":
    unittest.main()
