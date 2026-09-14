import base64
import gzip
import io
import json
import os
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import unittest
from http.client import HTTPConnection, HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, StreamObject

from reports_app.config import (
    APP_VERSION,
    DEFAULT_ASR_LANGUAGE,
    DEFAULT_LLM_BASE_URLS,
    DEFAULT_SYSTEM_PROMPT,
    LLM_API_KEY_SETTING,
    LLM_BASE_URL_SETTING,
    LLM_MODEL_SETTING,
    LLM_PROVIDER_SETTING,
    load_env_file,
)
from reports_app.internal_agent import (
    generate_internal_report,
    internal_voice_todo_items,
    resolve_llm_settings,
    validate_llm_settings,
)
from reports_app.asr import normalize_asr_endpoint, transcribe_audio, validate_asr_audio
from reports_app import auth
from reports_app.db import create_project, ensure_bootstrap_admin, init_db, connect, set_setting, set_user_setting
from reports_app import git_sources
from reports_app.gitlab import check_repo as gitlab_check_repo
from reports_app.gitlab import list_branches as gitlab_list_branches
from reports_app.gitlab import weekly_commits as gitlab_weekly_commits
from reports_app.github import check_repo as github_check_repo, token_kind
from reports_app.github import list_branches, weekly_commits
from reports_app.markdown import render_markdown
from reports_app.materials import (
    build_summary_prompt,
    decode_document_bytes,
    delete_material,
    extract_html_text,
    material_is_unlocked,
    parse_summary_output,
    store_manual_material,
    store_material,
    summarize_uploaded_materials,
    update_manual_material,
    update_material_summary,
)
from reports_app.pdf_export import build_report_pdf_html, pdf_filename
from reports_app.reports import FAKE_SUGGESTED_TEMPLATE, assemble_context, get_effective_prompt, build_internal_evidence_prompt, build_template_suggestion_prompt, collect_template_sources, compact_previous_report, fail_stale_generation_jobs, generate_report, changed_since_last_success, fake_provider_enabled, input_summary, invoke_provider, latest_report_markdown, suggest_report_template, strip_template_fences
from reports_app.task_queue import get_task_queue, queue_capacity, queue_parallelism
from reports_app.risks import evaluate_risks, progress_status
from reports_app.server import Handler, LoginRateLimiter, MAX_BODY_BYTES, add_repo, build_tls_server, delete_repo, evaluate_schedules, material_detail, save_plan, save_weekly_update, schedule_due, source_diagnostics, update_repo_notes, update_settings, workspace
from reports_app.timeutil import current_week_key, iso_now
import time
from reports_app.todos import close_todo, create_todo, delete_todo, todo_rows, update_todo
from reports_app.voice_todos import (
    build_voice_todo_prompt,
    create_todos_from_voice,
    create_todos_from_voice_audio,
    fail_stale_voice_jobs,
    fallback_voice_items,
    parse_voice_todo_output,
)
from reports_app.validation import ValidationError, validate_branches, validate_git_mode, validate_gitlab_server, validate_llm_base_url, validate_llm_provider, validate_material_filename, validate_provider, validate_repo, validate_schedule_item


class CoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        init_db(self.db_path)
        self.conn = connect(self.db_path)
        self.user = ensure_bootstrap_admin(self.conn)
        self.user_id = self.user["id"]
        self.conn.commit()
        self.project_id = create_project(
            self.conn,
            {
                "name": "Demo",
                "start_date": "2026-06-27",
                "timezone": "Asia/Shanghai",
                "report_provider": "internal",
            },
            self.user,
        )
        self.conn.commit()
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"

    def session_token(self):
        if not getattr(self, "_session_token", None):
            self._session_token = auth.create_session(self.conn, self.user_id)
            self.conn.commit()
        return self._session_token

    def api_request(self, client, method, path, body=None, headers=None):
        merged = dict(headers or {})
        merged.setdefault("Cookie", f"reports_session={self.session_token()}")
        if body is not None:
            merged.setdefault("Content-Type", "application/json")
        client.request(method, path, body=body, headers=merged)

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
        self.assertEqual(validate_material_filename("page.html"), ".html")
        self.assertEqual(validate_material_filename("page.htm"), ".htm")
        self.assertEqual(validate_branches(["main", "release/1.0", "main", ""]), ["main", "release/1.0"])
        self.assertEqual(validate_branches(["main", "*", "develop"]), ["*"])
        with self.assertRaises(ValidationError):
            validate_branches(["bad branch"])

    def test_git_mode_and_gitlab_validation(self):
        self.assertEqual(validate_repo("group/proj", "gitlab"), "group/proj")
        self.assertEqual(validate_repo("https://gitlab.example.com/group/sub/proj.git/", "gitlab"), "group/sub/proj")
        self.assertEqual(validate_repo("https://github.com/owner/repo/", "github"), "owner/repo")
        with self.assertRaises(ValidationError):
            validate_repo("group", "gitlab")
        with self.assertRaises(ValidationError):
            validate_repo("owner/repo", "gitea")
        self.assertEqual(validate_git_mode(None), "github")
        self.assertEqual(validate_git_mode("gitlab"), "gitlab")
        self.assertEqual(validate_gitlab_server("gitlab.example.com/"), "https://gitlab.example.com")
        self.assertEqual(validate_gitlab_server(""), "")
        self.assertEqual(validate_gitlab_server("http://10.0.0.2:8080"), "http://10.0.0.2:8080")
        with self.assertRaises(ValidationError):
            validate_gitlab_server("ftp://gitlab.example.com")

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
                "report_provider": "internal",
                "system_prompt": "prompt",
                "report_template": "# T",
                "schedules": [{"weekday": 5, "local_time": "18:00", "timezone": "Asia/Shanghai"}],
            },
        )
        row = self.conn.execute("SELECT report_provider, system_prompt FROM projects WHERE id = ?", (self.project_id,)).fetchone()
        self.assertEqual(row["report_provider"], "internal")
        # per-project system prompts are frozen: settings saves ignore the field
        self.assertNotEqual(row["system_prompt"], "prompt")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM update_schedules").fetchone()["n"], 1)

    def test_todo_open_workflow_requires_valid_title_and_status(self):
        with self.assertRaises(ValidationError):
            create_todo(self.conn, {"title": "  "}, self.user_id)
        todo_id = create_todo(self.conn, {"title": "Ship board", "description": "Build the flow"}, self.user_id)
        update_todo(self.conn, todo_id, {"status": "doing"}, self.user_id)
        todo = todo_rows(self.conn, self.user_id)[0]
        self.assertEqual(todo["status"], "doing")
        self.assertEqual(todo["description"], "Build the flow")
        update_todo(self.conn, todo_id, {"status": "doing", "description": "**bold** <script>bad()</script>"}, self.user_id)
        todo = todo_rows(self.conn, self.user_id)[0]
        self.assertIn("<strong>bold</strong>", todo["description_html"])
        self.assertNotIn("<script>", todo["description_html"])
        with self.assertRaises(ValidationError):
            update_todo(self.conn, todo_id, {"status": "closed"}, self.user_id)

    def _live_server(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def _raw_request(self, client, method, path, body=None, headers=None):
        """Request without the default session cookie (device-flow clients,
        Bearer-token checks)."""
        client.request(
            method,
            path,
            body=body,
            headers=dict(headers or {}, **({"Content-Type": "application/json"} if body else {})),
        )
        response = client.getresponse()
        return response.status, json.loads(response.read())

    def test_device_auth_flow_issues_bearer_session(self):
        server, thread = self._live_server()
        try:
            port = server.server_port
            client = HTTPConnection("127.0.0.1", port, timeout=10)
            status, payload = self._raw_request(client, "POST", "/api/device/auth/start", body="{}")
            self.assertEqual(status, 200)
            self.assertEqual(payload["interval"], 5)
            self.assertLessEqual(payload["expires_in"], 900)
            device_code, user_code = payload["device_code"], payload["user_code"]

            status, payload = self._raw_request(client, "POST", "/api/device/auth/poll", body=json.dumps({"device_code": device_code}))
            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "pending")

            status, _ = self._raw_request(client, "POST", "/api/device/auth/approve", body=json.dumps({"user_code": user_code}))
            self.assertEqual(status, 401)

            status, _ = self._raw_request(
                client,
                "POST",
                "/api/device/auth/approve",
                body=json.dumps({"user_code": user_code.lower().replace("-", "")}),
                headers={"Cookie": f"reports_session={self.session_token()}"},
            )
            self.assertEqual(status, 200)

            status, payload = self._raw_request(client, "POST", "/api/device/auth/poll", body=json.dumps({"device_code": device_code}))
            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "approved")
            token = payload["access_token"]
            self.assertEqual(payload["user"]["username"], self.user["username"])
            client.close()

            client = HTTPConnection("127.0.0.1", port, timeout=10)
            status, payload = self._raw_request(client, "GET", "/api/todos", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(status, 200)
            self.assertIn("todos", payload)
            client.close()

            client = HTTPConnection("127.0.0.1", port, timeout=10)
            status, _ = self._raw_request(client, "POST", "/api/auth/logout", body="{}", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(status, 200)
            client.close()

            client = HTTPConnection("127.0.0.1", port, timeout=10)
            status, _ = self._raw_request(client, "GET", "/api/todos", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(status, 401)
            client.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_device_auth_deny_expiry_and_unknown_codes(self):
        server, thread = self._live_server()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            status, payload = self._raw_request(client, "POST", "/api/device/auth/start", body="{}")
            self.assertEqual(status, 200)
            device_code, user_code = payload["device_code"], payload["user_code"]

            status, _ = self._raw_request(
                client,
                "POST",
                "/api/device/auth/approve",
                body=json.dumps({"user_code": "ZZZZ-ZZZZ"}),
                headers={"Cookie": f"reports_session={self.session_token()}"},
            )
            self.assertEqual(status, 400)

            status, _ = self._raw_request(
                client,
                "POST",
                "/api/device/auth/deny",
                body=json.dumps({"user_code": user_code}),
                headers={"Cookie": f"reports_session={self.session_token()}"},
            )
            self.assertEqual(status, 200)
            status, payload = self._raw_request(client, "POST", "/api/device/auth/poll", body=json.dumps({"device_code": device_code}))
            self.assertEqual(payload["status"], "denied")

            status, payload = self._raw_request(client, "POST", "/api/device/auth/poll", body=json.dumps({"device_code": "missing"}))
            self.assertEqual(payload["status"], "expired")

            # an expired code is cleaned up on the next start and cannot be approved
            row = self.conn.execute("SELECT * FROM device_auth_codes WHERE user_code = ?", (user_code,)).fetchone()
            self.assertIsNone(row)

            status, payload = self._raw_request(client, "POST", "/api/device/auth/start", body="{}")
            device_code, user_code = payload["device_code"], payload["user_code"]
            self.conn.execute(
                "UPDATE device_auth_codes SET expires_at = ? WHERE device_code = ?",
                ("2000-01-01T00:00:00+00:00", device_code),
            )
            self.conn.commit()
            status, _ = self._raw_request(
                client,
                "POST",
                "/api/device/auth/approve",
                body=json.dumps({"user_code": user_code}),
                headers={"Cookie": f"reports_session={self.session_token()}"},
            )
            self.assertEqual(status, 400)
            status, payload = self._raw_request(client, "POST", "/api/device/auth/poll", body=json.dumps({"device_code": device_code}))
            self.assertEqual(payload["status"], "expired")
            client.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_tls_listener_serves_api_for_secure_context_clients(self):
        openssl = shutil.which("openssl")
        if not openssl:
            self.skipTest("openssl is required to generate a test certificate")
        cert = Path(self.tmp.name) / "service.crt"
        key = Path(self.tmp.name) / "service.key"
        subprocess.run(
            [openssl, "req", "-x509", "-newkey", "rsa:2048", "-sha256", "-days", "1", "-nodes",
             "-keyout", str(key), "-out", str(cert), "-subj", "/CN=weeklyreports"],
            check=True, capture_output=True,
        )
        self.assertIsNone(build_tls_server("127.0.0.1", None, self.db_path, cert, key))
        tls_server = build_tls_server("127.0.0.1", 0, self.db_path, cert, key)
        thread = threading.Thread(target=tls_server.serve_forever, daemon=True)
        thread.start()
        try:
            context = ssl._create_unverified_context()
            client = HTTPSConnection("127.0.0.1", tls_server.server_port, timeout=10, context=context)
            self.api_request(client, "GET", "/api/state")
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
        finally:
            tls_server.shutdown()
            tls_server.server_close()
            thread.join(timeout=2)

    def test_load_env_file_fills_missing_values_only(self):
        env_file = Path(self.tmp.name) / "custom.env"
        env_file.write_text(
            "# service binding\n"
            "\n"
            "REPORTS_TEST_A=alpha\n"
            'REPORTS_TEST_B="beta"\n'
            "REPORTS_TEST_C='gam ma'\n"
            "REPORTS_TEST_A=second\n"
            "MALFORMED_LINE\n"
            "REPORTS_TEST_D=\n",
            encoding="utf-8",
        )
        with mock.patch.dict(os.environ, {"REPORTS_TEST_A": "existing"}):
            applied = load_env_file(env_file)
            self.assertEqual(applied, {"REPORTS_TEST_B": "beta", "REPORTS_TEST_C": "gam ma", "REPORTS_TEST_D": ""})
            self.assertEqual(os.environ["REPORTS_TEST_B"], "beta")
            self.assertEqual(os.environ["REPORTS_TEST_C"], "gam ma")
            self.assertEqual(os.environ["REPORTS_TEST_A"], "existing")
        self.assertEqual(load_env_file(Path(self.tmp.name) / "missing.env"), {})

    def test_asr_audio_validation_and_endpoint_normalization(self):
        raw, content_type = validate_asr_audio({"audio_base64": base64.b64encode(b"RIFF....").decode(), "content_type": "audio/wav; codecs=0"})
        self.assertEqual(raw, b"RIFF....")
        self.assertEqual(content_type, "audio/wav")
        with self.assertRaises(ValidationError):
            validate_asr_audio({"audio_base64": base64.b64encode(b"x").decode(), "content_type": "video/mp4"})
        with self.assertRaises(ValidationError):
            validate_asr_audio({"audio_base64": "not-base64!!", "content_type": "audio/wav"})
        with self.assertRaises(ValidationError):
            validate_asr_audio({"audio_base64": "", "content_type": "audio/wav"})
        self.assertEqual(normalize_asr_endpoint(" http://127.0.0.1:8766/inference "), "http://127.0.0.1:8766/inference")
        with self.assertRaises(ValidationError):
            normalize_asr_endpoint("ftp://127.0.0.1:8766/inference")
        with self.assertRaises(ValidationError):
            normalize_asr_endpoint("not-a-url")

    def test_transcribe_audio_posts_multipart_and_parses_text(self):
        captured = {}

        class MockAsrHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                captured["body"] = self.rfile.read(length)
                captured["path"] = self.path
                payload = json.dumps({"text": "明天上午十点开评审会，给王老师发周报初稿"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, fmt, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), MockAsrHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            audio = b"RIFFfake-wav-bytes"
            text = transcribe_audio(
                audio,
                "audio/wav",
                f"http://127.0.0.1:{server.server_port}/inference",
                "whisper",
            )
            self.assertEqual(text, "明天上午十点开评审会，给王老师发周报初稿")
            self.assertTrue(captured["path"].endswith("/inference"))
            self.assertIn(b'name="file"', captured["body"])
            self.assertIn(audio, captured["body"])
            self.assertIn(b'name="model"', captured["body"])
            self.assertIn(b'name="language"\r\n\r\nzh\r\n', captured["body"])

            transcribe_audio(audio, "audio/wav", f"http://127.0.0.1:{server.server_port}/inference", "whisper", language="en")
            self.assertIn(b'name="language"\r\n\r\nen\r\n', captured["body"])
            transcribe_audio(audio, "audio/wav", f"http://127.0.0.1:{server.server_port}/inference", "whisper", language="auto")
            self.assertNotIn(b'name="language"', captured["body"], "auto must omit the field so the service decides")
            transcribe_audio(audio, "audio/wav", f"http://127.0.0.1:{server.server_port}/inference", "whisper", language="  ")
            self.assertNotIn(b'name="language"', captured["body"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_voice_todo_audio_flow_uses_configured_asr_service(self):
        class MockAsrHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(length)
                payload = json.dumps({"text": "盘点线上集群状态"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, fmt, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), MockAsrHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "1"}):
                result, transcript = create_todos_from_voice_audio(
                    self.conn,
                    {"audio_base64": base64.b64encode(b"RIFFfake").decode(), "content_type": "audio/wav"},
                    "codex",
                    f"http://127.0.0.1:{server.server_port}/inference",
                    "whisper",
                    user_id=self.user_id,
                )
            self.assertEqual(transcript, "盘点线上集群状态")
            self.assertFalse(result["fallback"])
            todo = next(row for row in todo_rows(self.conn, self.user_id) if row["id"] == result["ids"][0])
            self.assertEqual(todo["title"], "盘点线上集群状态")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_voice_todo_prompt_and_json_parser(self):
        transcript = "明天上午十点开评审会，然后给王老师发周报初稿"
        prompt = build_voice_todo_prompt(transcript)
        self.assertIn(transcript, prompt)
        self.assertIn('"title"', prompt)
        parsed = parse_voice_todo_output(
            '```json\n[{"title": "开评审会", "description": "明天上午十点"}, {"title": "发周报初稿", "description": ""}]\n```'
        )
        self.assertEqual(
            parsed,
            [
                {"title": "开评审会", "description": "明天上午十点"},
                {"title": "发周报初稿", "description": ""},
            ],
        )
        single = parse_voice_todo_output('{"title": "唯一任务", "description": "细节"}')
        self.assertEqual(single, [{"title": "唯一任务", "description": "细节"}])
        with self.assertRaises(ValueError):
            parse_voice_todo_output("这不是 JSON")
        with self.assertRaises(ValueError):
            parse_voice_todo_output('[{"description": "缺少标题"}]')

    def test_voice_todo_fallback_splits_raw_transcript(self):
        items = fallback_voice_items("明天上午十点开评审会。下午给王老师发周报初稿")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "明天上午十点开评审会")
        self.assertEqual(items[0]["description"], "明天上午十点开评审会。下午给王老师发周报初稿")
        multi = fallback_voice_items("第一行任务\n第二行任务")
        self.assertEqual([item["title"] for item in multi], ["第一行任务", "第二行任务"])

    def test_create_todos_from_voice_with_fake_provider(self):
        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "1"}):
            result = create_todos_from_voice(self.conn, "给后端日志加上脱敏处理", "internal", user_id=self.user_id)
        self.assertFalse(result["fallback"])
        self.assertEqual(len(result["ids"]), 1)
        todo = next(row for row in todo_rows(self.conn, self.user_id) if row["id"] == result["ids"][0])
        self.assertEqual(todo["title"], "给后端日志加上脱敏处理")
        self.assertEqual(todo["status"], "todo")

    def test_create_todos_from_voice_falls_back_when_provider_fails(self):
        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}):
            with mock.patch(
                "reports_app.internal_agent.internal_voice_todo_items",
                side_effect=RuntimeError("provider exploded"),
            ):
                result = create_todos_from_voice(self.conn, "盘点仓库权限", "internal", user_id=self.user_id)
        self.assertTrue(result["fallback"])
        self.assertIn("provider exploded", result["error"])
        todo = next(row for row in todo_rows(self.conn, self.user_id) if row["id"] == result["ids"][0])
        self.assertEqual(todo["title"], "盘点仓库权限")
        with self.assertRaises(ValidationError):
            create_todos_from_voice(self.conn, "   ", "internal")

    def _poll_voice_job(self, server_port, job_id, timeout=30):
        deadline = time.time() + timeout
        while time.time() < deadline:
            client = HTTPConnection("127.0.0.1", server_port, timeout=10)
            self.api_request(client, "GET", f"/api/voice-jobs/{job_id}")
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            if payload["status"] in {"completed", "failed", "cancelled"}:
                return response.status, payload
            time.sleep(0.1)
        raise AssertionError("voice job did not finish in time")

    def _wait_voice_status(self, server_port, job_id, expected, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            client = HTTPConnection("127.0.0.1", server_port, timeout=10)
            self.api_request(client, "GET", f"/api/voice-jobs/{job_id}")
            payload = json.loads(client.getresponse().read())
            client.close()
            if payload["status"] in expected:
                return payload["status"]
            time.sleep(0.05)
        raise AssertionError(f"voice job {job_id} never reached {expected}")

    def test_voice_jobs_queue_cancel_and_capacity(self):
        release = threading.Event()

        class BlockingAsrHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(length)
                release.wait(timeout=5)
                payload = json.dumps({"text": "迟到的转写内容"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, fmt, *args):
                return

        asr_server = ThreadingHTTPServer(("127.0.0.1", 0), BlockingAsrHandler)
        asr_thread = threading.Thread(target=asr_server.serve_forever, daemon=True)
        asr_thread.start()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({"asr_endpoint": f"http://127.0.0.1:{asr_server.server_port}/inference", "queue_capacity": 2, "queue_parallelism": 1}),
                headers={"Content-Type": "application/json"},
            )
            settings = json.loads(client.getresponse().read())
            client.close()
            self.assertEqual(settings["queue_capacity"], 2)
            self.assertEqual(settings["queue_parallelism"], 1)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "POST",
                "/api/todos/voice",
                body=json.dumps({"audio_base64": base64.b64encode(b"RIFFfake").decode(), "content_type": "audio/wav"}),
                headers={"Content-Type": "application/json"},
            )
            first = json.loads(client.getresponse().read())
            client.close()
            self.assertEqual(first["status"], "queued")
            self._wait_voice_status(server.server_port, first["id"], {"transcribing"})

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "POST", "/api/todos/voice", body=json.dumps({"text": "第二个任务"}), headers={"Content-Type": "application/json"})
            response = client.getresponse()
            second = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 202)
            self.assertEqual(second["status"], "queued")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "POST", "/api/todos/voice", body=json.dumps({"text": "第三个任务"}), headers={"Content-Type": "application/json"})
            response = client.getresponse()
            third = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 409)
            self.assertIn("task queue is full", third["error"])

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/task-queue")
            queue_state = json.loads(client.getresponse().read())
            client.close()
            self.assertEqual(queue_state["capacity"], 2)
            self.assertEqual(queue_state["parallelism"], 1)
            self.assertEqual(queue_state["active"], 2)
            voice_statuses = {task["id"]: task["status"] for task in queue_state["tasks"] if task["kind"] == "voice"}
            self.assertEqual(voice_statuses[first["id"]], "transcribing")
            self.assertEqual(voice_statuses[second["id"]], "queued")

            # cancelling works for queued and running tasks alike
            for job_id in (second["id"], first["id"]):
                client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                self.api_request(client, "POST", f"/api/voice-jobs/{job_id}/cancel", body="{}", headers={"Content-Type": "application/json"})
                response = client.getresponse()
                cancelled = json.loads(response.read())
                client.close()
                self.assertEqual(response.status, 200)
                self.assertEqual(cancelled["status"], "cancelled")

            release.set()
            status, job = self._poll_voice_job(server.server_port, first["id"])
            self.assertEqual(job["status"], "cancelled")
            status, job = self._poll_voice_job(server.server_port, second["id"])
            self.assertEqual(job["status"], "cancelled")
            time.sleep(0.3)
            created_titles = [row["title"] for row in todo_rows(self.conn, self.user_id)]
            self.assertNotIn("迟到的转写内容", created_titles)
            self.assertNotIn("第二个任务", created_titles)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/voice-jobs/active")
            active = json.loads(client.getresponse().read())
            client.close()
            self.assertIsNone(active["job"])

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "POST", "/api/todos/voice", body=json.dumps({"text": "取消后新建任务"}), headers={"Content-Type": "application/json"})
            fourth = json.loads(client.getresponse().read())
            client.close()
            self.assertEqual(fourth["status"], "queued")
            status, job = self._poll_voice_job(server.server_port, fourth["id"])
            self.assertEqual(job["status"], "completed")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "POST", f"/api/voice-jobs/{fourth['id']}/cancel", body="{}", headers={"Content-Type": "application/json"})
            response = client.getresponse()
            response.read()
            client.close()
            self.assertEqual(response.status, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            asr_server.shutdown()
            asr_server.server_close()
            asr_thread.join(timeout=2)

    def test_stale_voice_jobs_fail_on_startup(self):
        now = iso_now()
        for status in ("queued", "transcribing", "structuring"):
            self.conn.execute(
                "INSERT INTO voice_jobs (status, created_at, updated_at) VALUES (?, ?, ?)",
                (status, now, now),
            )
        self.conn.commit()
        fail_stale_voice_jobs(self.db_path)
        rows = self.conn.execute("SELECT status, error FROM voice_jobs").fetchall()
        self.assertEqual([row["status"] for row in rows], ["failed", "failed", "failed"])
        for row in rows:
            self.assertEqual(row["error"], "interrupted by service restart")

    def test_stale_generation_jobs_fail_on_startup(self):
        now = iso_now()
        for status in ("queued", "running"):
            self.conn.execute(
                "INSERT INTO generation_jobs (project_id, week_key, trigger_type, provider, status, queued_at, started_at) VALUES (?, '2026-W36', 'manual', 'codex', ?, ?, ?)",
                (self.project_id, status, now, now),
            )
        self.conn.commit()
        fail_stale_generation_jobs(self.db_path)
        rows = self.conn.execute("SELECT status, failure_reason FROM generation_jobs").fetchall()
        self.assertEqual([row["status"] for row in rows], ["failed", "failed"])
        for row in rows:
            self.assertEqual(row["failure_reason"], "interrupted by service restart")

    def test_manual_generation_queues_and_completes_asynchronously(self):
        save_weekly_update(self.conn, self.project_id, {"completed": "A"})
        self.conn.commit()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "POST",
                f"/api/projects/{self.project_id}/generate",
                body=json.dumps({"force": True}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 202)
            self.assertEqual(payload["status"], "queued")

            deadline = time.time() + 15
            job_status = None
            while time.time() < deadline:
                row = self.conn.execute("SELECT status FROM generation_jobs WHERE id = ?", (payload["id"],)).fetchone()
                if row and row["status"] in {"success", "failed", "skipped"}:
                    job_status = row["status"]
                    break
                time.sleep(0.05)
            self.assertEqual(job_status, "success")
            week_key = current_week_key("Asia/Shanghai")
            report = self.conn.execute(
                "SELECT content_md FROM weekly_reports WHERE project_id = ? AND week_key = ?",
                (self.project_id, week_key),
            ).fetchone()
            self.assertIsNotNone(report)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/task-queue")
            queue_state = json.loads(client.getresponse().read())
            client.close()
            self.assertEqual(queue_state["capacity"], 5, "defaults come from settings, not the environment")
            self.assertEqual(queue_state["parallelism"], 2)
            self.assertEqual(queue_state["active"], 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_generation_enqueue_rejects_duplicate_and_full_queue(self):
        week_key = current_week_key("Asia/Shanghai")
        now = iso_now()
        self.conn.execute(
            "INSERT INTO generation_jobs (project_id, week_key, trigger_type, provider, status, queued_at, started_at) VALUES (?, ?, 'manual', 'codex', 'running', ?, ?)",
            (self.project_id, week_key, now, now),
        )
        set_setting(self.conn, "queue_capacity", "1")
        self.conn.commit()
        other_project = create_project(
            self.conn,
            {"name": "Other", "start_date": "2026-06-27", "timezone": "Asia/Shanghai", "report_provider": "internal"},
            self.user,
        )
        self.conn.commit()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "POST",
                f"/api/projects/{self.project_id}/generate",
                body=json.dumps({"force": True}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            duplicate = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 400)
            self.assertIn("already has a generation job", duplicate["error"])

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "POST",
                f"/api/projects/{other_project}/generate",
                body=json.dumps({"force": True}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            full = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 409)
            self.assertIn("task queue is full", full["error"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_queue_settings_validation_and_clamping(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({"queue_capacity": 3, "queue_parallelism": 2}),
                headers={"Content-Type": "application/json"},
            )
            payload = json.loads(client.getresponse().read())
            client.close()
            self.assertEqual(payload["queue_capacity"], 3)
            self.assertEqual(payload["queue_parallelism"], 2)

            for bad_payload in (
                {"queue_capacity": 0},
                {"queue_capacity": 99},
                {"queue_capacity": "abc"},
                {"queue_parallelism": 0},
                {"queue_parallelism": 99},
                {"queue_parallelism": "abc"},
            ):
                client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                self.api_request(client, "PUT", "/api/settings", body=json.dumps(bad_payload), headers={"Content-Type": "application/json"})
                response = client.getresponse()
                response.read()
                client.close()
                self.assertEqual(response.status, 400, f"expected 400 for {bad_payload}")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/state")
            state_payload = json.loads(client.getresponse().read())
            client.close()
            self.assertEqual(state_payload["queue_capacity"], 3)
            self.assertEqual(state_payload["queue_parallelism"], 2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        set_setting(self.conn, "queue_capacity", "999")
        set_setting(self.conn, "queue_parallelism", "-4")
        self.assertEqual(queue_capacity(self.conn), 20)
        self.assertEqual(queue_parallelism(self.conn), 1)

    def test_settings_roundtrip_gitlab_url_and_skip_verify(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(
                client,
                "PUT",
                "/api/settings",
                body=json.dumps({"gitlab_url": "gitlab.example.com:8443", "gitlab_skip_verify": True}),
                headers={"Content-Type": "application/json"},
            )
            settings = json.loads(client.getresponse().read())
            client.close()
            self.assertEqual(settings["gitlab_url"], "https://gitlab.example.com:8443")
            self.assertTrue(settings["gitlab_skip_verify"])

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(
                client,
                "PUT",
                "/api/settings",
                body=json.dumps({"gitlab_url": "", "gitlab_skip_verify": False}),
                headers={"Content-Type": "application/json"},
            )
            settings = json.loads(client.getresponse().read())
            client.close()
            self.assertEqual(settings["gitlab_url"], "")
            self.assertFalse(settings["gitlab_skip_verify"])

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(
                client, "PUT", "/api/settings", body=json.dumps({"gitlab_url": "ftp://gitlab.example.com"}), headers={"Content-Type": "application/json"}
            )
            response = client.getresponse()
            response.read()
            client.close()
            self.assertEqual(response.status, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        set_setting(self.conn, "queue_capacity", "not-a-number")
        set_setting(self.conn, "queue_parallelism", "")
        self.assertEqual(queue_capacity(self.conn), 5)
        self.assertEqual(queue_parallelism(self.conn), 2)
        with mock.patch.dict(os.environ, {"REPORTS_QUEUE_CAPACITY": "3", "REPORTS_QUEUE_PARALLELISM": "2"}):
            self.assertEqual(queue_capacity(self.conn), 3)
            self.assertEqual(queue_parallelism(self.conn), 2)

    def test_task_queue_dispatch_respects_parallelism(self):
        set_setting(self.conn, "queue_parallelism", "2")
        self.conn.commit()
        queue = get_task_queue(self.db_path)
        lock = threading.Lock()
        counters = {"active": 0, "max": 0, "done": 0}
        done = threading.Event()

        def runner():
            with lock:
                counters["active"] += 1
                counters["max"] = max(counters["max"], counters["active"])
            time.sleep(0.15)
            with lock:
                counters["active"] -= 1
                counters["done"] += 1
                if counters["done"] == 4:
                    done.set()

        for _ in range(4):
            queue.submit(runner)
        self.assertTrue(done.wait(timeout=5), "queued runners did not all finish in time")
        self.assertEqual(counters["done"], 4)
        self.assertEqual(counters["max"], 2, "parallelism setting must cap concurrent runners")

    def test_voice_todo_settings_and_api_endpoints(self):
        class MockAsrHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(length)
                payload = json.dumps({"text": "给官网更换证书"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, fmt, *args):
                return

        asr_server = ThreadingHTTPServer(("127.0.0.1", 0), MockAsrHandler)
        asr_thread = threading.Thread(target=asr_server.serve_forever, daemon=True)
        asr_thread.start()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({
                    "asr_endpoint": f"http://127.0.0.1:{asr_server.server_port}/inference",
                    "asr_model": "whisper",
                }),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["asr_endpoint"], f"http://127.0.0.1:{asr_server.server_port}/inference")
            self.assertEqual(payload["asr_model"], "whisper")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "PUT", "/api/settings", body=json.dumps({"asr_endpoint": "not-a-url"}), headers={"Content-Type": "application/json"})
            response = client.getresponse()
            response.read()
            client.close()
            self.assertEqual(response.status, 400)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/state")
            response = client.getresponse()
            state_payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(state_payload["asr_endpoint"], f"http://127.0.0.1:{asr_server.server_port}/inference")
            self.assertEqual(state_payload["asr_model"], "whisper")

            with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "1"}):
                client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                self.api_request(client, "POST", "/api/todos/voice", body=json.dumps({"text": "巡检线上集群状态"}), headers={"Content-Type": "application/json"})
                response = client.getresponse()
                payload = json.loads(response.read())
                client.close()
            self.assertEqual(response.status, 202)
            self.assertEqual(payload["status"], "queued")
            status, job = self._poll_voice_job(server.server_port, payload["id"])
            self.assertEqual(status, 200)
            self.assertEqual(job["status"], "completed")
            self.assertFalse(job["fallback"])
            self.assertEqual(job["transcript"], "巡检线上集群状态")
            self.assertEqual(job["todo_ids"], [todo["id"] for todo in todo_rows(self.conn, self.user_id) if todo["title"] == "巡检线上集群状态"])

            with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "1"}):
                client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                self.api_request(client, 
                    "POST",
                    "/api/todos/voice",
                    body=json.dumps({"audio_base64": base64.b64encode(b"RIFFfake").decode(), "content_type": "audio/wav"}),
                    headers={"Content-Type": "application/json"},
                )
                response = client.getresponse()
                payload = json.loads(response.read())
                client.close()
            self.assertEqual(response.status, 202)
            status, job = self._poll_voice_job(server.server_port, payload["id"])
            self.assertEqual(job["status"], "completed")
            self.assertEqual(job["transcript"], "给官网更换证书")
            created = todo_rows(self.conn, self.user_id)[0]
            self.assertEqual(created["title"], "给官网更换证书")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "POST", "/api/todos/voice", body=json.dumps({"text": "  "}), headers={"Content-Type": "application/json"})
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 202)
            status, job = self._poll_voice_job(server.server_port, payload["id"])
            self.assertEqual(job["status"], "failed")
            self.assertIn("voice transcript is required", job["error"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            asr_server.shutdown()
            asr_server.server_close()
            asr_thread.join(timeout=2)

    def test_todo_card_links_open_in_new_tab(self):
        todo_id = create_todo(self.conn, {"title": "Link card", "description": "See [guide](https://example.com/docs) and https://example.com"}, self.user_id)
        close_todo(self.conn, todo_id, {"reason": "Done via https://example.com/done"}, self.user_id)
        todo = todo_rows(self.conn, self.user_id)[0]
        for html_field in ("description_html", "close_reason_html"):
            rendered = todo[html_field]
            self.assertIn('target="_blank"', rendered)
            self.assertIn('rel="noopener noreferrer"', rendered)
            self.assertNotIn('<a href=', rendered)

    def test_todo_delete_only_removes_closed_todo_and_keeps_material(self):
        todo_id = create_todo(self.conn, {"title": "Temporary card", "description": "Delete me"}, self.user_id)
        with self.assertRaises(ValidationError):
            delete_todo(self.conn, todo_id, self.user_id)
        material_id = close_todo(self.conn, todo_id, {"reason": "Archived first", "project_id": self.project_id}, self.user_id)
        material = self.conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        self.assertIsNotNone(material)

        delete_todo(self.conn, todo_id, self.user_id)

        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM todos WHERE id = ?", (todo_id,)).fetchone()["n"], 0)
        kept = self.conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        self.assertIsNotNone(kept)
        self.assertEqual(kept["extracted_text"], material["extracted_text"])
        with self.assertRaises(ValidationError):
            delete_todo(self.conn, todo_id, self.user_id)

    def test_todo_close_requires_reason_and_optionally_archives_project_material(self):
        todo_id = create_todo(self.conn, {"title": "Finish release", "description": "Validate TODO board"}, self.user_id)
        with self.assertRaises(ValidationError):
            close_todo(self.conn, todo_id, {"reason": "   ", "project_id": self.project_id}, self.user_id)
        open_row = self.conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        self.assertEqual(open_row["status"], "todo")
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM materials").fetchone()["n"], 0)

        material_id = close_todo(self.conn, todo_id,
            {"reason": "Acceptance checks passed", "project_id": self.project_id}, self.user_id)
        closed = todo_rows(self.conn, self.user_id)[0]
        self.assertEqual(closed["status"], "closed")
        self.assertEqual(closed["close_reason"], "Acceptance checks passed")
        self.assertEqual(closed["project_name"], "Demo")
        self.assertEqual(closed["material_id"], material_id)
        material = self.conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        self.assertEqual(material["source_type"], "manual")
        self.assertIn("Finish release", material["extracted_text"])
        self.assertIn("Acceptance checks passed", material["extracted_text"])

        update_todo(self.conn, todo_id,
            {"status": "closed", "title": "Finish polished release", "description": "**Verified** board"}, self.user_id)
        material = self.conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        self.assertIn("Finish polished release", material["extracted_text"])
        self.assertIn("**Verified** board", material["extracted_text"])
        self.assertIn("Acceptance checks passed", material["extracted_text"])
        with self.assertRaises(ValidationError):
            update_todo(self.conn, todo_id, {"status": "doing"}, self.user_id)

        with self.assertRaises(ValidationError):
            close_todo(self.conn, todo_id, {"reason": "again", "project_id": self.project_id}, self.user_id)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM materials").fetchone()["n"], 1)

    def test_todo_close_without_project_does_not_create_material(self):
        todo_id = create_todo(self.conn, {"title": "Personal reminder"}, self.user_id)
        self.assertIsNone(close_todo(self.conn, todo_id, {"reason": "No longer needed"}, self.user_id))
        row = self.conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        self.assertEqual(row["status"], "closed")
        self.assertIsNone(row["project_id"])
        self.assertIsNone(row["material_id"])

    def test_update_closed_todo_rejected_once_archived_material_locks(self):
        todo_id = create_todo(self.conn, {"title": "Ship board", "description": "original"}, self.user_id)
        material_id = close_todo(self.conn, todo_id, {"reason": "shipped", "project_id": self.project_id}, self.user_id)

        update_todo(self.conn, todo_id, {"status": "closed", "description": "fresh details"}, self.user_id)
        material = self.conn.execute(
            "SELECT extracted_text FROM materials WHERE id = ?", (material_id,)
        ).fetchone()
        self.assertIn("fresh details", material["extracted_text"])

        self.conn.execute(
            "UPDATE materials SET created_at = '2026-06-01T00:00:00+00:00' WHERE id = ?",
            (material_id,),
        )
        with self.assertRaises(ValidationError) as ctx:
            update_todo(self.conn, todo_id, {"status": "closed", "title": "Locked edit"}, self.user_id)
        self.assertIn("locked", str(ctx.exception))
        material = self.conn.execute(
            "SELECT extracted_text FROM materials WHERE id = ?", (material_id,)
        ).fetchone()
        self.assertNotIn("Locked edit", material["extracted_text"])

        # Autosave fires even when nothing changed; an unchanged payload must stay allowed.
        update_todo(self.conn, todo_id,
            {"status": "closed", "title": "Ship board", "description": "fresh details"}, self.user_id)
        row = self.conn.execute("SELECT title, description FROM todos WHERE id = ?", (todo_id,)).fetchone()
        self.assertEqual(row["title"], "Ship board")
        self.assertEqual(row["description"], "fresh details")

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
                "report_provider": "internal",
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
        self.assertNotIn("background", context["project_profile"])
        self.assertNotIn("objectives", context["project_profile"])
        self.assertNotIn("constraints", context["project_profile"])
        self.assertEqual(context["plan"]["objectives"], "plan objective")
        self.assertEqual(context["plan"]["milestones"][0]["title"], "M1")
        self.assertIn("profile=yes", input_summary(context))
        self.assertIn("plan=yes", input_summary(context))

    def test_fixed_report_system_prompt(self):
        self.conn.execute("UPDATE projects SET system_prompt = 'legacy prompt' WHERE id = ?", (self.project_id,))
        context, _hash = assemble_context(self.conn, self.project_id)
        self.assertEqual(context["system_prompt"], DEFAULT_SYSTEM_PROMPT)
        self.assertEqual(get_effective_prompt({"system_prompt": "legacy prompt"}), DEFAULT_SYSTEM_PROMPT)

    def test_material_upload_and_pdf_extraction(self):
        txt = base64.b64encode(b"hello").decode()
        material_id = store_material(self.conn, self.project_id, {"filename": "notes.txt", "content_base64": txt})
        row = self.conn.execute("SELECT source_type, extraction_status, extracted_text FROM materials WHERE id = ?", (material_id,)).fetchone()
        self.assertEqual(row["source_type"], "upload")
        self.assertEqual(row["extraction_status"], "extracted")
        self.assertEqual(row["extracted_text"], "hello")
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})
        })
        contents = StreamObject()
        contents.set_data(b"BT /F1 12 Tf 72 720 Td (PDF hello) Tj ET")
        page[NameObject("/Contents")] = writer._add_object(contents)
        output = io.BytesIO()
        writer.write(output)
        material_id = store_material(
            self.conn,
            self.project_id,
            {"filename": "项目 简报.pdf", "content_base64": base64.b64encode(output.getvalue()).decode()},
        )
        row = self.conn.execute(
            "SELECT filename, extraction_status, extracted_text FROM materials WHERE id = ?", (material_id,)
        ).fetchone()
        self.assertEqual(row["filename"], "项目 简报.pdf")
        self.assertEqual(row["extraction_status"], "extracted")
        self.assertIn("PDF hello", row["extracted_text"])

        broken_id = store_material(
            self.conn,
            self.project_id,
            {"filename": "broken.pdf", "content_base64": base64.b64encode(b"%PDF").decode()},
        )
        broken = self.conn.execute("SELECT extraction_status FROM materials WHERE id = ?", (broken_id,)).fetchone()
        self.assertEqual(broken["extraction_status"], "failed")

        data = workspace(self.conn, self.project_id)
        self.assertNotIn("broken.pdf", {item["filename"] for item in data["materials"]})
        self.assertIn(
            "broken.pdf",
            {item["details"].split(":", 1)[0] for item in data["source_diagnostics"] if item["kind"] == "material"},
        )

    def test_html_material_extraction_charset_and_failure(self):
        doc = (
            "<!DOCTYPE html><html><head><title>周报资料</title>"
            '<meta charset="utf-8"><style>body { color: red; }</style>'
            "<script>console.log('secret script');</script></head>"
            "<body><h1>项目周报</h1><p>第一段：登录模块上线。</p>"
            "<ul><li>完成 A</li><li>完成 B</li></ul>"
            "<table><tr><th>模块</th><th>状态</th></tr><tr><td>登录</td><td>完成</td></tr></table>"
            "</body></html>"
        )
        material_id = store_material(
            self.conn,
            self.project_id,
            {"filename": "简报.html", "content_base64": base64.b64encode(doc.encode("utf-8")).decode()},
        )
        row = self.conn.execute(
            "SELECT extraction_status, extracted_text FROM materials WHERE id = ?", (material_id,)
        ).fetchone()
        self.assertEqual(row["extraction_status"], "extracted")
        text = row["extracted_text"]
        self.assertIn("# 项目周报", text)
        self.assertIn("第一段：登录模块上线。", text)
        self.assertIn("- 完成 A", text)
        self.assertIn("模块 | 状态", text)
        self.assertIn("登录 | 完成", text)
        self.assertNotIn("<h1>", text)
        self.assertNotIn("secret script", text)
        self.assertNotIn("color: red", text)

        htm_id = store_material(
            self.conn,
            self.project_id,
            {"filename": "manual.htm", "content_base64": base64.b64encode(b"<p>plain body</p>").decode()},
        )
        row = self.conn.execute(
            "SELECT extraction_status, extracted_text FROM materials WHERE id = ?", (htm_id,)
        ).fetchone()
        self.assertEqual(row["extraction_status"], "extracted")
        self.assertEqual(row["extracted_text"], "plain body")

        gb_doc = (
            '<html><head><meta charset="gb2312"></head><body><h1>项目进展</h1>'
            "<p>本周完成了登录模块。</p></body></html>"
        )
        gb_id = store_material(
            self.conn,
            self.project_id,
            {"filename": "gb.html", "content_base64": base64.b64encode(gb_doc.encode("gb2312")).decode()},
        )
        row = self.conn.execute(
            "SELECT extraction_status, extracted_text FROM materials WHERE id = ?", (gb_id,)
        ).fetchone()
        self.assertEqual(row["extraction_status"], "extracted")
        self.assertIn("项目进展", row["extracted_text"])
        self.assertIn("本周完成了登录模块。", row["extracted_text"])

        empty_id = store_material(
            self.conn,
            self.project_id,
            {
                "filename": "empty.html",
                "content_base64": base64.b64encode("<html><head></head><body></body></html>".encode()).decode(),
            },
        )
        row = self.conn.execute(
            "SELECT extraction_status, extraction_error FROM materials WHERE id = ?", (empty_id,)
        ).fetchone()
        self.assertEqual(row["extraction_status"], "failed")
        self.assertIn("HTML text extraction failed", row["extraction_error"])

        data = workspace(self.conn, self.project_id)
        self.assertNotIn("empty.html", {item["filename"] for item in data["materials"]})
        self.assertIn(
            "empty.html",
            {item["details"].split(":", 1)[0] for item in data["source_diagnostics"] if item["kind"] == "material"},
        )

    def test_html_material_preview_kind_and_fallback(self):
        doc = "<html><body><h1>原始页面</h1><p>正文</p></body></html>"
        material_id = store_material(
            self.conn,
            self.project_id,
            {"filename": "page.html", "content_base64": base64.b64encode(doc.encode("utf-8")).decode()},
        )
        row = self.conn.execute("SELECT storage_path FROM materials WHERE id = ?", (material_id,)).fetchone()
        detail = material_detail(self.conn, self.project_id, material_id)
        self.assertEqual(detail["preview_kind"], "html")
        self.assertIn("<h1>原始页面</h1>", detail["content_html"])
        self.assertNotIn("storage_path", detail)

        os.unlink(row["storage_path"])
        detail = material_detail(self.conn, self.project_id, material_id)
        self.assertEqual(detail["preview_kind"], "text")
        self.assertIn("原始页面", detail["content"])

        txt_id = store_material(
            self.conn, self.project_id, {"filename": "a.txt", "content_base64": base64.b64encode(b"hi").decode()}
        )
        self.assertEqual(material_detail(self.conn, self.project_id, txt_id)["preview_kind"], "text")
        md_id = store_material(
            self.conn, self.project_id, {"filename": "a.md", "content_base64": base64.b64encode(b"# hi").decode()}
        )
        self.assertEqual(material_detail(self.conn, self.project_id, md_id)["preview_kind"], "markdown")

    def test_decode_document_bytes_charset_fallback(self):
        self.assertEqual(decode_document_bytes("中文".encode("utf-8")), "中文")
        declared = '<html><head><meta charset="gb18030"></head><body>会议纪要</body></html>'.encode("gb18030")
        self.assertIn("会议纪要", decode_document_bytes(declared))
        # gb2312/gbk bytes without a meta declaration still decode via the
        # gb18030 superset fallback
        self.assertIn("会议纪要", decode_document_bytes("会议纪要".encode("gb2312")))
        with self.assertRaises(UnicodeDecodeError):
            decode_document_bytes(b"\xff\xfe")
        self.assertEqual(extract_html_text(b"<p>caf&eacute;</p>"), "café")

    def test_template_suggestion_prompt_bundles_requirements_sources_and_last_report(self):
        store_material(
            self.conn,
            self.project_id,
            {"filename": "weekly-notes.md", "content_base64": base64.b64encode(b"# notes").decode()},
        )
        add_repo(self.conn, self.project_id, {"repo": "acme/server", "git_mode": "github", "notes": "核心服务"})
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
            VALUES (?, '2026-W30', '# Latest Report\n\n风险预测要点', 2, '2026-07-26T00:00:00+00:00', '2026-07-26T00:00:00+00:00')
            """,
            (self.project_id,),
        )

        sources = collect_template_sources(self.conn, self.project_id)
        self.assertEqual(sources["material_count"], 1)
        self.assertEqual(sources["materials"][0]["filename"], "weekly-notes.md")
        self.assertEqual(sources["repositories"][0]["repo"], "acme/server")
        self.assertEqual(sources["report_history_weeks"], ["2026-W30", "2026-W25"])
        self.assertFalse(sources["weekly_update_present"])
        self.assertNotIn("commits", sources)

        self.assertEqual(latest_report_markdown(self.conn, self.project_id), "# Latest Report\n\n风险预测要点")

        prompt = build_template_suggestion_prompt("突出风险预测和里程碑", sources, latest_report_markdown(self.conn, self.project_id))
        self.assertIn("突出风险预测和里程碑", prompt)
        self.assertIn("weekly-notes.md", prompt)
        self.assertIn("acme/server", prompt)
        self.assertIn("# Latest Report", prompt)
        self.assertIn("只输出模板本身的 Markdown", prompt)

    def test_suggest_report_template_fake_provider_and_fences(self):
        template = suggest_report_template(self.conn, self.project_id, "突出风险预测")
        self.assertEqual(template, FAKE_SUGGESTED_TEMPLATE.strip())
        self.assertTrue(template.startswith("#"))
        self.assertIn("##", template)
        saved = self.conn.execute("SELECT report_template FROM projects WHERE id = ?", (self.project_id,)).fetchone()
        self.assertEqual(saved["report_template"], "")

        # fake provider is on in setUp; turn it off to exercise the real path
        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": ""}):
            with mock.patch("reports_app.internal_agent.internal_chat", return_value="```markdown\n# Styled Template\n```") as chat:
                template = suggest_report_template(self.conn, self.project_id, "", timeout=5)
            self.assertEqual(template, "# Styled Template")
            self.assertEqual(chat.call_args.kwargs["max_tokens"], 4096)
            self.assertEqual(chat.call_args.kwargs["temperature"], 0)

            with mock.patch("reports_app.internal_agent.internal_chat", side_effect=RuntimeError("provider down")):
                with self.assertRaises(ValidationError) as ctx:
                    suggest_report_template(self.conn, self.project_id, "")
            self.assertIn("模板生成失败", str(ctx.exception))

            with mock.patch("reports_app.internal_agent.internal_chat", return_value="   "):
                with self.assertRaises(ValidationError):
                    suggest_report_template(self.conn, self.project_id, "")

    def test_suggest_template_endpoint_returns_template_without_saving(self):
        self.conn.execute(
            "UPDATE projects SET report_template = '# Existing Template' WHERE id = ?", (self.project_id,)
        )
        self.conn.commit()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(
                client,
                "POST",
                f"/api/projects/{self.project_id}/suggest-template",
                body=json.dumps({"requirements": "突出风险预测"}, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            result = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertTrue(result["template"].startswith("#"))

            saved = self.conn.execute(
                "SELECT report_template FROM projects WHERE id = ?", (self.project_id,)
            ).fetchone()
            self.assertEqual(saved["report_template"], "# Existing Template")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "POST", "/api/projects/999999/suggest-template", body="{}", headers={"Content-Type": "application/json"})
            response = client.getresponse()
            client.close()
            self.assertEqual(response.status, 404)
        finally:
            server.shutdown()
            server.server_close()

    def test_batch_ai_summaries_and_manual_summary_edit(self):
        ids = [
            store_material(
                self.conn,
                self.project_id,
                {"filename": name, "content_base64": base64.b64encode(content.encode()).decode()},
            )
            for name, content in (("第一份.txt", "alpha details"), ("second.md", "beta details"))
        ]
        summarize_uploaded_materials(self.conn, self.project_id, ids)
        rows = self.conn.execute(
            "SELECT id, summary, summary_status FROM materials WHERE id IN (?, ?) ORDER BY id", ids
        ).fetchall()
        self.assertEqual([row["summary_status"] for row in rows], ["generated", "generated"])
        self.assertIn("第一份.txt", rows[0]["summary"])
        self.assertIn("alpha details", rows[0]["summary"])

        update_material_summary(self.conn, self.project_id, ids[0], {"summary": "手工修订摘要"})
        edited = self.conn.execute(
            "SELECT summary, summary_status FROM materials WHERE id = ?", (ids[0],)
        ).fetchone()
        self.assertEqual(dict(edited), {"summary": "手工修订摘要", "summary_status": "manual"})

    def test_ai_summary_prompt_and_json_parser_keep_files_separate(self):
        items = [
            {"id": 7, "filename": "原始 名称.pdf", "text_start": "正文开头"},
            {"id": 8, "filename": "notes.txt", "text_start": "leading text"},
        ]
        prompt = build_summary_prompt(items)
        self.assertIn("原始 名称.pdf", prompt)
        parsed = parse_summary_output(
            '```json\n[{"id": 7, "summary": "摘要一"}, {"id": 8, "summary": "Summary two"}]\n```',
            items,
        )
        self.assertEqual(parsed, {7: "摘要一", 8: "Summary two"})

    def test_material_api_accepts_multiple_files_in_one_request(self):
        manual_id = store_manual_material(
            self.conn, self.project_id, {"title": "Manual preview", "content": "complete manual content"}
        )
        pdf_buffer = io.BytesIO()
        pdf_writer = PdfWriter()
        pdf_writer.add_blank_page(width=200, height=200)
        pdf_writer.write(pdf_buffer)
        pdf_id = store_material(
            self.conn,
            self.project_id,
            {
                "filename": "preview.pdf",
                "content_type": "application/pdf",
                "content_base64": base64.b64encode(pdf_buffer.getvalue()).decode(),
            },
        )
        pdf_path = Path(self.conn.execute("SELECT storage_path FROM materials WHERE id = ?", (pdf_id,)).fetchone()["storage_path"])
        self.conn.commit()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/state")
            response = client.getresponse()
            state_payload = json.loads(response.read())
            client.close()
            state_project = next(project for project in state_payload["projects"] if project["id"] == self.project_id)
            self.assertEqual(state_project["progress_status"], progress_status(self.conn, self.project_id))

            payload = json.dumps({
                "files": [
                    {"filename": "one.txt", "content_base64": base64.b64encode(b"first body").decode()},
                    {"filename": "two.md", "content_base64": base64.b64encode(b"second body").decode()},
                ]
            })
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "POST",
                f"/api/projects/{self.project_id}/materials",
                body=payload,
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            result = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 201)
            self.assertEqual(len(result["ids"]), 2)
            rows = self.conn.execute(
                "SELECT filename, summary_status FROM materials WHERE id IN (?, ?) ORDER BY id", result["ids"]
            ).fetchall()
            self.assertEqual([row["filename"] for row in rows], ["one.txt", "two.md"])
            self.assertEqual([row["summary_status"] for row in rows], ["generated", "generated"])

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", f"/api/projects/{self.project_id}/materials/{result['ids'][1]}")
            response = client.getresponse()
            markdown_detail = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(markdown_detail["preview_kind"], "markdown")
            self.assertIn("<p>second body</p>", markdown_detail["content_html"])

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", f"/api/projects/{self.project_id}/materials/{pdf_id}/content")
            response = client.getresponse()
            pdf_content = response.read()
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("Content-Type"), "application/pdf")
            self.assertTrue(pdf_content.startswith(b"%PDF"))

            for material_id, expected_content in (
                (result["ids"][0], "first body"),
                (manual_id, "complete manual content"),
            ):
                client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                self.api_request(client, "GET", f"/api/projects/{self.project_id}/materials/{material_id}")
                response = client.getresponse()
                detail = json.loads(response.read())
                client.close()
                self.assertEqual(response.status, 200)
                self.assertEqual(detail["content"], expected_content)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", f"/api/projects/999/materials/{result['ids'][0]}")
            response = client.getresponse()
            response.read()
            client.close()
            self.assertEqual(response.status, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            pdf_path.unlink(missing_ok=True)

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

    def test_material_delete_allows_current_week_and_rejects_locked_history(self):
        current_id = store_material(
            self.conn,
            self.project_id,
            {
                "filename": "delete-me.txt",
                "content_base64": base64.b64encode(b"temporary current-week material").decode(),
            },
        )
        current_row = self.conn.execute("SELECT * FROM materials WHERE id = ?", (current_id,)).fetchone()
        current_path = Path(current_row["storage_path"])
        project_timezone = self.conn.execute(
            "SELECT timezone FROM projects WHERE id = ?", (self.project_id,)
        ).fetchone()["timezone"]
        self.assertTrue(material_is_unlocked(current_row, project_timezone))

        locked_id = store_manual_material(
            self.conn,
            self.project_id,
            {"title": "Historical note", "content": "must remain"},
        )
        self.conn.execute(
            "UPDATE materials SET created_at = '2026-06-01T00:00:00+00:00' WHERE id = ?",
            (locked_id,),
        )
        self.conn.commit()

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "DELETE", f"/api/projects/{self.project_id}/materials/{current_id}")
            response = client.getresponse()
            deleted_workspace = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertNotIn(current_id, {item["id"] for item in deleted_workspace["materials"]})
            self.assertIsNone(self.conn.execute("SELECT id FROM materials WHERE id = ?", (current_id,)).fetchone())
            self.assertFalse(current_path.exists())

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "DELETE", f"/api/projects/{self.project_id}/materials/{locked_id}")
            response = client.getresponse()
            error = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 400)
            self.assertIn("locked", error["error"])
            self.assertIsNotNone(self.conn.execute("SELECT id FROM materials WHERE id = ?", (locked_id,)).fetchone())

            with self.assertRaises(ValidationError):
                delete_material(self.conn, self.project_id + 999, locked_id)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            current_path.unlink(missing_ok=True)

    def test_report_context_includes_current_week_materials_and_commits(self):
        txt = base64.b64encode(b"weekly context").decode()
        store_material(self.conn, self.project_id, {"filename": "week.md", "content_base64": txt})
        store_manual_material(self.conn, self.project_id, {"title": "manual", "content": "manual context"})
        self.conn.execute(
            """
            INSERT INTO github_repos
            (project_id, repo, tracked_branches_json, status, status_message, activity_summary, created_at, updated_at)
            VALUES (?, 'owner/repo', '["main", "release"]', 'connected', 'ok', 'summary', '2026-06-27T00:00:00+00:00', '2026-06-27T00:00:00+00:00')
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
        commits.assert_called_once()
        self.assertEqual(commits.call_args.args[3], ["main", "release"])
        material_names = {item["filename"] for item in context["new_materials_this_week"]}
        self.assertIn("week.md", material_names)
        self.assertIn("manual", material_names)
        manual = next(item for item in context["new_materials_this_week"] if item["filename"] == "manual")
        self.assertEqual(manual["source_type"], "manual")
        self.assertEqual(manual["excerpt"], "manual context")
        self.assertEqual(context["git_commits_this_week"][0]["commits"][0]["message"], "ship")
        self.assertEqual(context["github_activity"][0]["tracked_branches"], ["main", "release"])

    def test_previous_report_compaction_does_not_inline_body(self):
        compacted = compact_previous_report({"updated_at": "t", "content_md": "sentinel body"})
        self.assertEqual(compacted, {"available": True, "updated_at": "t"})

    def test_github_repo_is_unique_and_notes_enter_report_context(self):
        with mock.patch("reports_app.server.check_repo") as mocked:
            mocked.return_value = {
                "status": "connected",
                "status_message": "ok",
                "activity_summary": "summary",
                "last_activity_at": "2026-06-27T00:00:00Z",
                "default_branch": "main",
            }
            first = add_repo(self.conn, self.project_id, {"repo": "owner/repo", "notes": "first note"})
            second = add_repo(self.conn, self.project_id, {"repo": "owner/repo", "notes": "reporting name", "branches": ["main", "develop"]})
        self.assertEqual(first, second)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM github_repos").fetchone()["n"], 1)
        row = self.conn.execute("SELECT tracked_branches_json FROM github_repos WHERE id = ?", (first,)).fetchone()
        self.assertEqual(json.loads(row["tracked_branches_json"]), ["main", "develop"])
        update_repo_notes(self.conn, self.project_id, first, {"notes": "repo purpose"})
        with mock.patch("reports_app.reports.weekly_commits") as commits:
            commits.return_value = {"repo": "owner/repo", "status": "ok", "status_message": "0 commits", "commits": []}
            context, _hash = assemble_context(self.conn, self.project_id)
        self.assertEqual(context["github_activity"][0]["notes"], "repo purpose")
        self.assertEqual(context["git_commits_this_week"][0]["notes"], "repo purpose")
        update_repo_notes(self.conn, self.project_id, first, {"notes": "all branches", "branches": ["*"]})
        row = self.conn.execute("SELECT tracked_branches_json FROM github_repos WHERE id = ?", (first,)).fetchone()
        self.assertEqual(json.loads(row["tracked_branches_json"]), ["*"])

    def test_repo_enable_disable_and_delete_control_report_sources(self):
        with mock.patch("reports_app.server.check_repo") as mocked:
            mocked.return_value = {
                "status": "connected",
                "status_message": "ok",
                "activity_summary": "summary",
                "last_activity_at": "2026-06-27T00:00:00Z",
                "default_branch": "main",
            }
            active_id = add_repo(self.conn, self.project_id, {"repo": "owner/active", "notes": "active"})
            paused_id = add_repo(self.conn, self.project_id, {"repo": "owner/paused", "notes": "paused"})

        update_repo_notes(self.conn, self.project_id, paused_id, {"enabled": False})
        row = self.conn.execute("SELECT enabled, notes FROM github_repos WHERE id = ?", (paused_id,)).fetchone()
        self.assertEqual(row["enabled"], 0)
        self.assertEqual(row["notes"], "paused")
        update_repo_notes(self.conn, self.project_id, active_id, {})
        row = self.conn.execute("SELECT enabled, tracked_branches_json FROM github_repos WHERE id = ?", (active_id,)).fetchone()
        self.assertEqual(row["enabled"], 1)
        self.assertEqual(json.loads(row["tracked_branches_json"]), ["main"])

        with mock.patch("reports_app.reports.weekly_commits") as commits:
            commits.return_value = {"repo": "owner/active", "status": "ok", "status_message": "0 commits", "commits": []}
            context, _hash = assemble_context(self.conn, self.project_id)
        self.assertEqual([item["repo"] for item in context["github_activity"]], ["owner/active"])

        self.conn.execute("UPDATE github_repos SET status = 'inaccessible' WHERE id = ?", (paused_id,))
        self.conn.commit()
        self.assertEqual(
            [item["source_ref"] for item in source_diagnostics(self.conn, self.project_id, "2026-W27") if item["kind"] == "github"],
            [],
        )

        payload = workspace(self.conn, self.project_id)
        repo_flags = {item["repo"]: item["enabled"] for item in payload["repos"]}
        self.assertEqual(repo_flags, {"owner/active": 1, "owner/paused": 0})

        add_repo(self.conn, self.project_id, {"repo": "owner/paused", "notes": "paused"})
        row = self.conn.execute("SELECT enabled FROM github_repos WHERE id = ?", (paused_id,)).fetchone()
        self.assertEqual(row["enabled"], 1)

        update_repo_notes(self.conn, self.project_id, paused_id, {"enabled": False})
        update_repo_notes(self.conn, self.project_id, active_id, {"enabled": False})
        evaluate_risks(self.conn, self.project_id)
        warning = self.conn.execute(
            "SELECT status FROM risk_warnings WHERE project_id = ? AND rule = 'missing_update'",
            (self.project_id,),
        ).fetchone()
        self.assertEqual(warning["status"], "active")
        self.conn.commit()
        delete_repo(self.conn, self.project_id, paused_id)
        self.assertIsNone(self.conn.execute("SELECT id FROM github_repos WHERE id = ?", (paused_id,)).fetchone())
        with self.assertRaises(ValidationError):
            delete_repo(self.conn, self.project_id, paused_id)

    def test_repo_delete_api_route_removes_repo(self):
        with mock.patch("reports_app.server.check_repo") as mocked:
            mocked.return_value = {
                "status": "connected",
                "status_message": "ok",
                "activity_summary": "summary",
                "last_activity_at": "2026-06-27T00:00:00Z",
                "default_branch": "main",
            }
            repo_id = add_repo(self.conn, self.project_id, {"repo": "owner/route", "notes": "route"})
        self.conn.commit()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "DELETE", f"/api/projects/{self.project_id}/repos/{repo_id}")
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual([item["repo"] for item in payload["repos"]], [])

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "DELETE", f"/api/projects/{self.project_id}/repos/{repo_id}")
            response = client.getresponse()
            error = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 400)
            self.assertEqual(error["error"], "repository not found")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_gitlab_check_repo_uses_configured_token(self):
        def fake_request(server, path, token, timeout, skip_verify=False):
            self.assertEqual(server, "gitlab.example.com")
            self.assertEqual(token, "glpat-x")
            if "merge_requests" in path:
                return [{"iid": 1}, {"iid": 2}], 200, None
            if "issues" in path:
                return [{"iid": 1}], 200, None
            if path.startswith("projects/group%2Fproj"):
                return (
                    {
                        "path_with_namespace": "group/proj",
                        "description": "infra",
                        "default_branch": "trunk",
                        "last_activity_at": "2026-06-30T10:00:00.000+08:00",
                    },
                    200,
                    None,
                )
            return {}, 200, None

        with mock.patch("reports_app.gitlab._request", side_effect=fake_request) as request:
            result = gitlab_check_repo("group/proj", server="gitlab.example.com", token="glpat-x")

        self.assertEqual(result["status"], "connected")
        self.assertEqual(result["default_branch"], "trunk")
        self.assertEqual(result["last_activity_at"], "2026-06-30T10:00:00.000+08:00")
        self.assertIn("Recent merge requests: 2", result["activity_summary"])
        self.assertIn("Recent issues: 1", result["activity_summary"])
        self.assertEqual(request.call_count, 3, "project + merge requests + issues, no separate auth call")
        self.assertTrue(request.call_args_list[0].args[1].startswith("projects/group%2Fproj"))

    def test_gitlab_check_repo_reports_unreachable_and_bad_auth(self):
        with mock.patch("reports_app.gitlab._request", return_value=(None, None, "connection refused")):
            result = gitlab_check_repo("group/proj")
        self.assertEqual(result["status"], "disconnected")
        self.assertIn("unreachable", result["status_message"])

        with mock.patch("reports_app.gitlab._request", return_value=(None, 401, "401 Unauthorized")):
            result = gitlab_check_repo("group/proj", server="gitlab.example.com", token="bad")
        self.assertEqual(result["status"], "unauthenticated")

    def test_github_404_distinguishes_missing_repo_from_token_access(self):
        # token rejected for a PRIVATE repo but the repo is public: anonymous probe succeeds
        def probe_ok(path, token, timeout):
            return ({}, 200, None) if not token else (None, 404, '{"status":"404"}')

        with mock.patch("reports_app.github._request", side_effect=probe_ok):
            result = github_check_repo("owner/private", token="ghp_x")
        self.assertEqual(result["status"], "inaccessible")
        self.assertIn("令牌无权访问", result["status_message"])

        # anonymous probe also 404: the path itself is wrong (or fully inaccessible)
        def always_404(path, token, timeout):
            return None, 404, '{"status":"404"}'

        with mock.patch("reports_app.github._request", side_effect=always_404):
            result = github_check_repo("owner/ghost", token="ghp_x")
        self.assertEqual(result["status"], "inaccessible")
        self.assertIn("路径有误", result["status_message"])

        result = github_check_repo("owner/ghost", token="")
        self.assertEqual(result["status"], "inaccessible")
        self.assertIn("路径有误", result["status_message"])

    def test_github_404_org_repo_reports_org_requirements(self):
        def org_scoped(path, token, timeout):
            if path.startswith("/repos/") and token:
                return None, 404, '{"status":"404"}'
            if path.startswith("/repos/"):
                return None, 404, '{"status":"404"}'
            if path.startswith("/orgs/"):
                return {"login": "acme"}, 200, None
            return None, 404, ""

        with mock.patch("reports_app.github._request", side_effect=org_scoped):
            result = github_check_repo("acme/infra", token="ghp_x")
        self.assertEqual(result["status"], "inaccessible")
        self.assertIn("acme 是组织", result["status_message"])
        self.assertIn("SAML SSO", result["status_message"], "classic tokens get the SSO hint")

        with mock.patch("reports_app.github._request", side_effect=org_scoped):
            result = github_check_repo("acme/infra", token="github_pat_x")
        self.assertIn("Resource owner", result["status_message"], "fine-grained tokens get the resource-owner hint")

    def test_gitlab_404_reports_path_or_permission(self):
        with mock.patch("reports_app.gitlab._request", return_value=(None, 404, '{"message":"404 Project Not Found"}')):
            result = gitlab_check_repo("group/ghost", server="https://gitlab.example.com", token="glpat_x")
        self.assertEqual(result["status"], "inaccessible")
        self.assertIn("路径有误", result["status_message"])
        self.assertIn("404", result["status_message"])

    def test_gitlab_weekly_commits_reads_selected_branches_and_dedupes(self):
        shared = {
            "id": "aaa1112223334445",
            "title": "shared change",
            "author_name": "A",
            "committed_date": "2026-06-30T08:00:00.000+08:00",
            "web_url": "https://gitlab.example.com/group/proj/-/commit/aaa1112223334445",
        }

        def fake_request(server, path, token, timeout, skip_verify=False):
            self.assertEqual(token, "glpat-x")
            self.assertIn("projects/group%2Fsub%2Fproj/repository/commits", path)
            self.assertIn("per_page=100&page=1", path)
            if "ref_name=main" in path:
                items = [shared]
            elif "ref_name=develop" in path:
                items = [
                    shared,
                    {
                        "id": "bbb2223334445566",
                        "title": "develop only",
                        "author_name": "B",
                        "authored_date": "2026-07-01T00:00:00Z",
                        "web_url": "https://gitlab.example.com/group/proj/-/commit/bbb2223334445566",
                    },
                ]
            else:
                items = []
            return items, 200, None

        start = datetime(2026, 6, 29, tzinfo=ZoneInfo("UTC"))
        end = datetime(2026, 7, 6, tzinfo=ZoneInfo("UTC"))
        with mock.patch("reports_app.gitlab._request", side_effect=fake_request) as request:
            result = gitlab_weekly_commits(
                "group/sub/proj",
                start,
                end,
                ["main", "develop"],
                server="https://gitlab.example.com",
                token="glpat-x",
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["branches"], ["main", "develop"])
        self.assertEqual(len(result["commits"]), 2)
        self.assertIn("since=2026-06-29T00%3A00%3A00Z", request.call_args_list[0].args[1])
        shared_commit = next(item for item in result["commits"] if item["sha"] == "aaa111222333")
        self.assertEqual(shared_commit["branches"], ["main", "develop"])
        self.assertEqual(shared_commit["date"], "2026-06-30T00:00:00Z")
        self.assertEqual(shared_commit["author"], "A")
        develop_commit = next(item for item in result["commits"] if item["sha"] == "bbb222333444")
        self.assertEqual(develop_commit["message"], "develop only")

    def test_gitlab_list_branches_stops_at_short_page(self):
        def fake_request(server, path, token, timeout, skip_verify=False):
            self.assertIn("projects/group%2Fproj/repository/branches", path)
            items = [{"name": f"feature/{index}"} for index in range(100)] if path.endswith("page=1") else [{"name": "release/next"}]
            return items, 200, None

        with mock.patch("reports_app.gitlab._request", side_effect=fake_request) as request:
            result = gitlab_list_branches("group/proj", server="gitlab.example.com")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["branches"]), 101)
        self.assertEqual(result["branches"][-1], "release/next")
        self.assertEqual(request.call_count, 2)

    def test_git_sources_dispatch_routes_by_mode(self):
        with mock.patch("reports_app.git_sources.gitlab_check_repo") as glab_check, mock.patch(
            "reports_app.git_sources.github_check_repo"
        ) as gh_check:
            glab_check.return_value = {"status": "connected"}
            git_sources.check_repo(
                "group/proj",
                "gitlab",
                auth_info={"gitlab_url": "https://gitlab.example.com", "gitlab_skip_verify": True},
            )
        glab_check.assert_called_once_with(
            "group/proj", server="https://gitlab.example.com", token="", timeout=20, skip_verify=True
        )
        gh_check.assert_not_called()

        with mock.patch("reports_app.git_sources.gitlab_weekly_commits") as glab_commits, mock.patch(
            "reports_app.git_sources.github_weekly_commits"
        ) as gh_commits:
            start = datetime(2026, 6, 29, tzinfo=ZoneInfo("UTC"))
            end = datetime(2026, 7, 6, tzinfo=ZoneInfo("UTC"))
            git_sources.weekly_commits("owner/repo", start, end, ["main"], git_mode="github")
        gh_commits.assert_called_once_with("owner/repo", start, end, ["main"], token="", timeout=30)
        glab_commits.assert_not_called()

    def test_git_sources_honors_disabled_integrations_and_user_tokens(self):
        with mock.patch("reports_app.git_sources.github_check_repo") as gh_check:
            result = git_sources.check_repo(
                "owner/repo", "github", auth_info={"github_enabled": False, "github_token": "t"}
            )
        self.assertEqual(result["status"], "disabled")
        gh_check.assert_not_called()

        with mock.patch("reports_app.git_sources.gitlab_weekly_commits") as glab_commits:
            glab_commits.return_value = {"status": "ok", "commits": []}
            start = datetime(2026, 6, 29, tzinfo=ZoneInfo("UTC"))
            end = datetime(2026, 7, 6, tzinfo=ZoneInfo("UTC"))
            git_sources.weekly_commits(
                "group/proj",
                start,
                end,
                ["main"],
                git_mode="gitlab",
                auth_info={"gitlab_token": "glpat-y", "gitlab_enabled": True},
            )
        glab_commits.assert_called_once_with("group/proj", start, end, ["main"], server="", token="glpat-y", timeout=30, skip_verify=False)

        auth_info = git_sources.git_auth_for_user(self.conn, self.user_id)
        self.assertTrue(auth_info["github_enabled"])
        self.assertEqual(auth_info["github_token"], "")
        set_user_setting(self.conn, self.user_id, "github_token", "ghp-secret")
        set_setting(self.conn, "github_enabled", "0")
        auth_info = git_sources.git_auth_for_user(self.conn, self.user_id)
        self.assertEqual(auth_info["github_token"], "ghp-secret")
        self.assertFalse(auth_info["github_enabled"])

    def test_token_kind_detection_and_automatic_fallback(self):
        self.assertEqual(token_kind("github_pat_ABCD1234"), "fine-grained")
        self.assertEqual(token_kind("ghp_ABCD1234"), "classic")
        self.assertEqual(token_kind("gho_ABCD1234"), "classic")
        self.assertEqual(token_kind("weird-custom-token"), "unknown")

        # refresh path: the org-matched token fails, the general token connects
        info = {
            "github_tokens": [
                {"label": "acme", "owner": "acme", "token": "github_pat_ORG"},
                {"label": "general", "owner": "", "token": "ghp_ALL"},
            ],
            "github_enabled": True,
        }

        def fake_check(repo, token="", timeout=20):
            if token == "github_pat_ORG":
                return {"status": "inaccessible", "status_message": "404", "activity_summary": "", "last_activity_at": None}
            return {
                "status": "connected",
                "status_message": "connected through GitHub API",
                "activity_summary": "ok",
                "last_activity_at": "2026-09-08T00:00:00Z",
                "default_branch": "main",
            }

        with mock.patch("reports_app.git_sources.github_check_repo", side_effect=fake_check) as check:
            result = git_sources.check_repo("acme/infra", "github", auth_info=info)
        self.assertEqual(check.call_count, 2)
        self.assertEqual(result["status"], "connected")
        self.assertIn("自动改用「general」", result["status_message"])

        # candidates: org entry first, then ownerless, then the legacy token
        info_legacy = {"github_tokens": [], "github_token": "ghp_LEGACY", "github_enabled": True}
        candidates = git_sources.github_token_candidates(info_legacy, "acme/infra")
        self.assertEqual([entry["token"] for entry in candidates], ["ghp_LEGACY"])

    def test_github_token_selection_prefers_matching_org_entry(self):
        set_user_setting(
            self.conn,
            self.user_id,
            "github_tokens",
            json.dumps([
                {"label": "acme", "owner": "Acme", "token": "ghp_org"},
                {"label": "general", "owner": "", "token": "ghp_all"},
            ]),
        )
        info = git_sources.git_auth_for_user(self.conn, self.user_id)
        self.assertEqual(git_sources.github_token_for(info, "acme/infra"), "ghp_org")
        self.assertEqual(git_sources.github_token_for(info, "ACME/web"), "ghp_org", "owner matching is case-insensitive")
        self.assertEqual(git_sources.github_token_for(info, "alice/pet"), "ghp_all", "ownerless entry is the fallback")
        # legacy single token is the deepest fallback
        set_user_setting(self.conn, self.user_id, "github_tokens", "")
        set_user_setting(self.conn, self.user_id, "github_token", "ghp_legacy")
        info = git_sources.git_auth_for_user(self.conn, self.user_id)
        self.assertEqual(git_sources.load_github_tokens(self.conn, self.user_id)[0]["token"], "ghp_legacy")
        self.assertEqual(git_sources.github_token_for(info, "acme/infra"), "ghp_legacy")

    def test_gitlab_url_from_user_settings_is_the_only_server(self):
        set_user_setting(self.conn, self.user_id, "gitlab_url", "https://gitlab.example.com")
        with mock.patch("reports_app.git_sources.gitlab_check_repo") as glab_check:
            glab_check.return_value = {"status": "connected"}
            git_sources.check_repo("group/proj", "gitlab", auth_info={"gitlab_url": "https://gitlab.example.com"})
        glab_check.assert_called_once_with(
            "group/proj", server="https://gitlab.example.com", token="", timeout=20, skip_verify=False
        )
        # without a configured URL the request goes out empty and gitlab.resolve_server falls back to gitlab.com
        with mock.patch("reports_app.git_sources.gitlab_check_repo") as glab_check:
            glab_check.return_value = {"status": "connected"}
            git_sources.check_repo("group/proj", "gitlab", auth_info={})
        glab_check.assert_called_once_with(
            "group/proj", server="", token="", timeout=20, skip_verify=False
        )

        auth_info = git_sources.git_auth_for_user(self.conn, self.user_id)
        self.assertFalse(auth_info["gitlab_skip_verify"])
        set_user_setting(self.conn, self.user_id, "gitlab_skip_verify", "1")
        auth_info = git_sources.git_auth_for_user(self.conn, self.user_id)
        self.assertTrue(auth_info["gitlab_skip_verify"])

    def test_gitlab_skip_verify_uses_unverified_tls_context(self):
        project_payload = json.dumps({"default_branch": "main", "path_with_namespace": "group/proj"}).encode()

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return project_payload

        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value = FakeResponse()
            gitlab_check_repo("group/proj", server="https://gitlab.example.com", skip_verify=True)
        context = urlopen.call_args.kwargs["context"]
        self.assertEqual(context.verify_mode, ssl.CERT_NONE)
        self.assertFalse(context.check_hostname)

        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value = FakeResponse()
            gitlab_check_repo("group/proj", server="https://gitlab.example.com")
        self.assertIsNone(urlopen.call_args.kwargs["context"])

    def test_gitlab_ssl_verify_failure_suggests_skip_verify(self):
        weak_key_error = "[SSL: certificate verify failed] EE certificate key too weak (_ssl.c:1000)"
        with mock.patch("reports_app.gitlab._request", return_value=(None, None, weak_key_error)):
            result = gitlab_check_repo("group/proj")
        self.assertEqual(result["status"], "disconnected")
        self.assertIn("跳过 SSL 证书校验", result["status_message"])

        with mock.patch("reports_app.gitlab._request", return_value=(None, None, "connection refused")):
            result = gitlab_list_branches("group/proj")
        self.assertIn("connection refused", result["status_message"])
        self.assertNotIn("跳过 SSL 证书校验", result["status_message"])

    def test_gitlab_repo_mode_is_persisted_and_unique_per_mode(self):
        connected = {
            "status": "connected",
            "status_message": "ok",
            "activity_summary": "summary",
            "last_activity_at": "2026-06-27T00:00:00Z",
            "default_branch": "main",
        }
        with mock.patch("reports_app.server.check_repo") as mocked:
            mocked.return_value = connected
            gh_id = add_repo(self.conn, self.project_id, {"repo": "group/proj", "notes": "mirror", "git_mode": "github"})
            gl_id = add_repo(
                self.conn,
                self.project_id,
                {
                    "repo": "https://gitlab.example.com/group/proj.git",
                    "notes": "primary",
                    "git_mode": "gitlab",
                },
            )
            again = add_repo(
                self.conn,
                self.project_id,
                {"repo": "group/proj", "git_mode": "gitlab"},
            )
        self.assertNotEqual(gh_id, gl_id)
        self.assertEqual(gl_id, again)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM github_repos").fetchone()["n"], 2)
        row = self.conn.execute("SELECT git_mode, gitlab_server, repo FROM github_repos WHERE id = ?", (gl_id,)).fetchone()
        self.assertEqual(row["git_mode"], "gitlab")
        self.assertEqual(row["gitlab_server"], "", "the per-repo GitLab server address is gone; 全局设置 holds the URL")
        self.assertEqual(row["repo"], "group/proj")

        with self.assertRaises(ValidationError):
            update_repo_notes(
                self.conn,
                self.project_id,
                gh_id,
                {"git_mode": "gitlab"},
            )

        other_id = None
        with mock.patch("reports_app.server.check_repo") as mocked:
            mocked.return_value = connected
            other_id = add_repo(self.conn, self.project_id, {"repo": "other/proj", "git_mode": "github"})
            update_repo_notes(
                self.conn,
                self.project_id,
                other_id,
                {"git_mode": "gitlab"},
            )
        row = self.conn.execute("SELECT git_mode, status FROM github_repos WHERE id = ?", (other_id,)).fetchone()
        self.assertEqual(row["git_mode"], "gitlab")
        self.assertEqual(row["status"], "connected")

        self.conn.execute("UPDATE github_repos SET status = 'inaccessible' WHERE id = ?", (gl_id,))
        titles = {
            item["source_ref"]: item["title"]
            for item in source_diagnostics(self.conn, self.project_id, "2026-W27")
        }
        self.assertEqual(titles[str(gl_id)], "GitLab source unavailable")

    def test_report_context_passes_git_mode_to_weekly_commits(self):
        self.conn.execute(
            """
            INSERT INTO github_repos
            (project_id, repo, git_mode, gitlab_server, tracked_branches_json, status, status_message, activity_summary, created_at, updated_at)
            VALUES (?, 'group/proj', 'gitlab', 'https://gitlab.example.com', '["main"]', 'connected', 'ok', 'summary', '2026-06-27T00:00:00+00:00', '2026-06-27T00:00:00+00:00')
            """,
            (self.project_id,),
        )
        with mock.patch("reports_app.reports.weekly_commits") as commits:
            commits.return_value = {"repo": "group/proj", "status": "ok", "status_message": "0 commits", "commits": []}
            context, _hash = assemble_context(self.conn, self.project_id)
        self.assertEqual(commits.call_args.kwargs["git_mode"], "gitlab")
        self.assertNotIn("gitlab_server", commits.call_args.kwargs, "the stored per-repo server value is ignored")
        self.assertEqual(context["github_activity"][0]["git_mode"], "gitlab")

    def test_schedule_enable_disable_and_skipped_run_recording(self):
        weekday = datetime.now(ZoneInfo("Asia/Shanghai")).isoweekday()

        def insert_schedule(enabled):
            cur = self.conn.execute(
                "INSERT INTO update_schedules (project_id, weekday, local_time, timezone, enabled, created_at) VALUES (?, ?, '00:00', 'Asia/Shanghai', ?, ?)",
                (self.project_id, weekday, enabled, iso_now()),
            )
            return cur.lastrowid

        disabled_id = insert_schedule(0)
        evaluate_schedules(self.conn, self.project_id)
        row = self.conn.execute("SELECT last_checked_at FROM update_schedules WHERE id = ?", (disabled_id,)).fetchone()
        self.assertIsNone(row["last_checked_at"])

        enabled_id = insert_schedule(1)
        evaluate_schedules(self.conn, self.project_id)
        disabled_row = self.conn.execute("SELECT last_checked_at FROM update_schedules WHERE id = ?", (disabled_id,)).fetchone()
        enabled_row = self.conn.execute("SELECT last_checked_at FROM update_schedules WHERE id = ?", (enabled_id,)).fetchone()
        self.assertIsNone(disabled_row["last_checked_at"])
        self.assertIsNotNone(enabled_row["last_checked_at"])
        jobs = self.conn.execute("SELECT status FROM generation_jobs WHERE project_id = ? ORDER BY id", (self.project_id,)).fetchall()
        self.assertEqual([job["status"] for job in jobs], ["success"])

        self.conn.execute("UPDATE update_schedules SET last_checked_at = NULL WHERE id = ?", (enabled_id,))
        evaluate_schedules(self.conn, self.project_id)
        jobs = self.conn.execute("SELECT status FROM generation_jobs WHERE project_id = ? ORDER BY id", (self.project_id,)).fetchall()
        self.assertEqual([job["status"] for job in jobs], ["success", "skipped"])

        update_settings(
            self.conn,
            self.project_id,
            {
                "name": "Demo",
                "start_date": "2026-06-27",
                "schedules": [{"weekday": 6, "local_time": "09:00", "timezone": "Asia/Shanghai", "enabled": False}],
            },
        )
        rows = self.conn.execute(
            "SELECT weekday, local_time, enabled FROM update_schedules WHERE project_id = ?", (self.project_id,)
        ).fetchall()
        self.assertEqual([(row["weekday"], row["local_time"], row["enabled"]) for row in rows], [(6, "09:00", 0)])

    def test_weekly_commits_reads_selected_branches_and_deduplicates(self):
        main_commit = {
            "sha": "abc1234567890",
            "html_url": "https://example.test/a",
            "commit": {"message": "shared", "author": {"name": "A", "date": "2026-06-30T00:00:00Z"}},
        }

        def fake_request(path, token, timeout):
            if "sha=main" in path:
                return [main_commit], 200, None
            if "sha=develop" in path:
                return [
                    main_commit,
                    {
                        "sha": "def1234567890",
                        "html_url": "https://example.test/b",
                        "commit": {"message": "develop only", "author": {"name": "B", "date": "2026-07-01T00:00:00Z"}},
                    },
                ], 200, None
            return [], 200, None

        start = datetime(2026, 6, 29, tzinfo=ZoneInfo("UTC"))
        end = datetime(2026, 7, 6, tzinfo=ZoneInfo("UTC"))
        with mock.patch("reports_app.github._request", side_effect=fake_request) as request:
            result = weekly_commits("owner/repo", start, end, ["main", "develop"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["branches"], ["main", "develop"])
        self.assertEqual(len(result["commits"]), 2)
        shared = next(item for item in result["commits"] if item["sha"] == "abc123456789")
        self.assertEqual(shared["branches"], ["main", "develop"])
        self.assertEqual(request.call_count, 2)

    def test_github_weekly_commits_maps_api_errors(self):
        def fake_request(path, token, timeout):
            if "sha=main" in path:
                return None, 401, "401 Unauthorized"
            return [
                {
                    "sha": "def1234567890",
                    "html_url": "https://example.test/b",
                    "commit": {"message": "develop only", "author": {"name": "B", "date": "2026-07-01T00:00:00Z"}},
                }
            ], 200, None

        start = datetime(2026, 6, 29, tzinfo=ZoneInfo("UTC"))
        end = datetime(2026, 7, 6, tzinfo=ZoneInfo("UTC"))
        with mock.patch("reports_app.github._request", side_effect=fake_request):
            result = weekly_commits("owner/repo", start, end, ["main", "develop"])
        self.assertEqual(result["status"], "partial", "one failed branch plus one successful branch")
        self.assertIn("401", result["status_message"])
        self.assertEqual(len(result["commits"]), 1)

        def unreachable(path, token, timeout):
            return None, None, "getaddrinfo failed"

        with mock.patch("reports_app.github._request", side_effect=unreachable):
            result = weekly_commits("owner/repo", start, end, ["main"])
        self.assertEqual(result["status"], "failed")

    def test_list_branches_loads_all_paginated_remote_branches(self):
        first_page = [{"name": f"feature/{index}"} for index in range(100)]
        second_page = [{"name": "release/next"}]

        def fake_request(path, token, timeout):
            self.assertIn("repos/owner/repo/branches", path)
            return (first_page, 200, None) if path.endswith("page=1") else (second_page, 200, None)

        with mock.patch("reports_app.github._request", side_effect=fake_request) as request:
            result = list_branches("owner/repo")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["branches"]), 101)
        self.assertEqual(result["branches"][-1], "release/next")
        self.assertEqual(request.call_count, 2)

    def test_weekly_commits_resolves_all_remote_branches_at_collection_time(self):
        def fake_request(path, token, timeout):
            branch = "main" if "sha=main" in path else "develop"
            item = {
                "sha": f"{branch}-sha",
                "html_url": f"https://example.test/{branch}",
                "commit": {
                    "message": f"{branch} change",
                    "author": {"name": "A", "date": "2026-07-01T00:00:00Z"},
                },
            }
            return [item], 200, None

        start = datetime(2026, 6, 29, tzinfo=ZoneInfo("UTC"))
        end = datetime(2026, 7, 6, tzinfo=ZoneInfo("UTC"))
        branch_result = {"status": "ok", "status_message": "2 branches", "branches": ["main", "develop"]}
        with mock.patch("reports_app.github.list_branches", return_value=branch_result) as branches, mock.patch(
            "reports_app.github._request", side_effect=fake_request
        ):
            result = weekly_commits("owner/repo", start, end, ["*"])

        branches.assert_called_once_with("owner/repo", token="", timeout=30)
        self.assertEqual(result["branches"], ["*"])
        self.assertEqual(result["resolved_branches"], ["main", "develop"])
        self.assertEqual(len(result["commits"]), 2)

    def test_fake_provider_flag_requires_truthy_value(self):
        os.environ["REPORTS_FAKE_PROVIDER"] = "0"
        self.assertFalse(fake_provider_enabled())
        os.environ["REPORTS_FAKE_PROVIDER"] = "false"
        self.assertFalse(fake_provider_enabled())
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"
        self.assertTrue(fake_provider_enabled())

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

    def test_api_responses_are_gzipped_only_when_client_accepts(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            # app.js is large enough to cross the compression threshold
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/app.js", headers={"Accept-Encoding": "gzip"})
            response = client.getresponse()
            body = response.read()
            client.close()
            self.assertEqual(response.headers.get("Content-Encoding"), "gzip")
            self.assertGreater(len(gzip.decompress(body)), 1024)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/app.js")
            response = client.getresponse()
            body = response.read()
            client.close()
            self.assertIsNone(response.headers.get("Content-Encoding"))
            self.assertGreater(len(body), 1024)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

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
        self.assertNotIn("content_html", data["report_history"][1], "archived bodies must load on demand")
        self.assertNotIn("content_md", data["report_history"][1])

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
                "report_provider": "internal",
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
                    "report_provider": "internal",
                    "schedules": [{"weekday": 5, "local_time": "18:00", "timezone": "Asia/Shanghai"}],
                },
            )
            save_weekly_update(self.conn, self.project_id, {"completed": "scheduled"})
            evaluate_schedules(self.conn, self.project_id)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM generation_jobs WHERE trigger_type = 'scheduled'").fetchone()["n"], 1)

    def test_paused_project_skips_scheduled_generation_and_status_toggle(self):
        update_settings(
            self.conn,
            self.project_id,
            {
                "name": "Demo",
                "start_date": "2026-06-27",
                "timezone": "Asia/Shanghai",
                "status": "paused",
                "report_provider": "internal",
                "schedules": [{"weekday": 5, "local_time": "18:00", "timezone": "Asia/Shanghai"}],
            },
        )
        with mock.patch("reports_app.server.schedule_due", return_value=True):
            evaluate_schedules(self.conn, self.project_id)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM generation_jobs").fetchone()["n"], 0)

        with self.assertRaises(ValidationError):
            update_settings(
                self.conn,
                self.project_id,
                {"name": "Demo", "start_date": "2026-06-27", "status": "sleeping"},
            )

        self.conn.commit()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "POST",
                f"/api/projects/{self.project_id}/status",
                body=json.dumps({"enabled": True}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["status"], "active")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        with mock.patch("reports_app.server.schedule_due", return_value=True):
            evaluate_schedules(self.conn, self.project_id)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) AS n FROM generation_jobs").fetchone()["n"], 1)

    def test_markdown_sanitizes_raw_html(self):
        html = render_markdown("# Hello\n<script>alert(1)</script>\n- **ok**")
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("<strong>ok</strong>", html)
        nested = render_markdown("- parent\n  - child\n\n---\n\n> quote\n\n| A | B |\n| - | - |\n| 1 | 2 |")
        self.assertIn("<ul>", nested)
        self.assertIn("<hr", nested)
        self.assertIn("<blockquote>", nested)
        self.assertIn("<table>", nested)

    def test_pdf_export_html_and_filename(self):
        html = build_report_pdf_html(
            {"name": "项目 A"},
            {"id": 1, "latest_job_id": 1, "updated_at": "2026-06-30T00:00:00+00:00", "week_key": "2026-W27", "content_md": "# 周报\n\n<script>alert(1)</script>\n\n- 完成"},
        )
        self.assertIn("项目 A", html)
        self.assertIn("2026-W27", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("window.print()", html)
        self.assertEqual(pdf_filename("项目 A", "2026-W27"), "A-2026-W27-weekly-report.pdf")

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
        evaluate_risks(self.conn, self.project_id)
        rules = {row["rule"] for row in self.conn.execute("SELECT rule FROM risk_warnings")}
        self.assertIn("overdue_milestone", rules)
        self.assertNotIn("blocked_outcome", rules)
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

    def test_session_cookie_flags(self):
        header = auth.session_cookie_header("token1")
        self.assertIn("HttpOnly", header)
        self.assertIn("SameSite=Lax", header)
        self.assertNotIn("Secure", header)
        self.assertIn("Secure", auth.session_cookie_header("token1", secure=True))
        self.assertNotIn("Secure", auth.clear_cookie_header())
        self.assertIn("Secure", auth.clear_cookie_header(secure=True))

    def test_login_rate_limiter_window(self):
        limiter = LoginRateLimiter(max_per_ip=3, max_per_username=2, window_seconds=60)
        for _ in range(2):
            limiter.record_failure("10.0.0.1", "darren")
        # per-username budget exhausted; other usernames and IPs are unaffected
        self.assertTrue(limiter.blocked("10.0.0.1", "darren"))
        self.assertFalse(limiter.blocked("10.0.0.1", "member"))
        self.assertFalse(limiter.blocked("10.0.0.2", "other"))
        # the per-IP budget trips once three failures accumulate on one IP
        limiter.record_failure("10.0.0.1", "member")
        self.assertTrue(limiter.blocked("10.0.0.1", "third"))
        self.assertFalse(limiter.blocked("10.0.0.2", "member"))

    def test_static_serving_confined_to_static_dir(self):
        server, thread = self._live_server()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            client.request("GET", "/app.js")
            response = client.getresponse()
            self.assertEqual(response.status, 200)
            response.read()
            client.close()
            for path in ("/../.env", "/../../etc/passwd", "/../data/reports.sqlite3"):
                client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                client.request("GET", path)
                response = client.getresponse()
                body = response.read()
                client.close()
                self.assertEqual(response.status, 404, path)
                self.assertNotIn(b"REPORTS_ADMIN_PASSWORD", body)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_request_body_size_limit_rejected(self):
        server, thread = self._live_server()
        try:
            sock = socket.create_connection(("127.0.0.1", server.server_port), timeout=10)
            try:
                request = (
                    "POST /api/auth/login HTTP/1.1\r\n"
                    f"Host: 127.0.0.1:{server.server_port}\r\n"
                    f"Content-Length: {MAX_BODY_BYTES + 1}\r\n"
                    "Content-Type: application/json\r\n"
                    "\r\n"
                )
                sock.sendall(request.encode("ascii"))
                response = sock.recv(4096).decode("utf-8", "replace")
            finally:
                sock.close()
            self.assertTrue(response.startswith("HTTP/1.1 413"), response)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_login_rate_limited_after_repeated_failures(self):
        server, thread = self._live_server()
        try:
            statuses = []
            for _ in range(6):
                client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
                client.request(
                    "POST",
                    "/api/auth/login",
                    body=json.dumps({"username": "darren", "password": "wrong-password"}),
                    headers={"Content-Type": "application/json"},
                )
                response = client.getresponse()
                statuses.append(response.status)
                response.read()
                client.close()
            self.assertEqual(statuses[:5], [400] * 5)
            self.assertEqual(statuses[5], 429)
            # a different username from the same IP still gets a clean 400
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            client.request(
                "POST",
                "/api/auth/login",
                body=json.dumps({"username": "ghost", "password": "wrong-password"}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            self.assertEqual(response.status, 400)
            response.read()
            client.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_non_numeric_entity_ids_return_404(self):
        server, thread = self._live_server()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/projects/abc/workspace")
            response = client.getresponse()
            self.assertEqual(response.status, 404)
            response.read()
            client.close()
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "POST", "/api/risks/xyz/dismissed", body="{}")
            response = client.getresponse()
            self.assertEqual(response.status, 404)
            response.read()
            client.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class InternalAgentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        init_db(self.db_path)
        self.conn = connect(self.db_path)
        self.user = ensure_bootstrap_admin(self.conn)
        self.user_id = self.user["id"]
        self.conn.commit()
        self.project_id = create_project(
            self.conn,
            {
                "name": "Demo",
                "start_date": "2026-06-27",
                "timezone": "Asia/Shanghai",
                "report_provider": "internal",
            },
            self.user,
        )
        self.conn.commit()
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"

    def session_token(self):
        if not getattr(self, "_session_token", None):
            self._session_token = auth.create_session(self.conn, self.user_id)
            self.conn.commit()
        return self._session_token

    def api_request(self, client, method, path, body=None, headers=None):
        merged = dict(headers or {})
        merged.setdefault("Cookie", f"reports_session={self.session_token()}")
        if body is not None:
            merged.setdefault("Content-Type", "application/json")
        client.request(method, path, body=body, headers=merged)

    def tearDown(self):
        self.conn.close()
        os.environ.pop("REPORTS_FAKE_PROVIDER", None)
        self.tmp.cleanup()

    def test_internal_agent_is_the_only_supported_provider(self):
        validate_provider("internal")
        with self.assertRaises(ValidationError):
            validate_provider("codex")
        with self.assertRaises(ValidationError):
            validate_provider("claude")
        with self.assertRaises(ValidationError):
            validate_provider("gpt")
        validate_llm_provider("openai")
        validate_llm_provider("anthropic")
        with self.assertRaises(ValidationError):
            validate_llm_provider("gpt")
        self.assertEqual(validate_llm_base_url("api.openai.com/v1"), "https://api.openai.com/v1")
        self.assertEqual(validate_llm_base_url("http://127.0.0.1:1234/v1/"), "http://127.0.0.1:1234/v1")
        with self.assertRaises(ValidationError):
            validate_llm_base_url("http://")

    def test_resolve_llm_settings_defaults_stored_values_and_env_fallback(self):
        settings = resolve_llm_settings(self.conn)
        self.assertEqual(settings["provider"], "openai")
        self.assertEqual(settings["base_url"], DEFAULT_LLM_BASE_URLS["openai"])
        self.assertEqual(settings["model"], "")
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            self.assertEqual(resolve_llm_settings(self.conn)["api_key"], "env-key")

        set_setting(self.conn, LLM_PROVIDER_SETTING, "anthropic")
        set_setting(self.conn, LLM_BASE_URL_SETTING, "https://gateway.internal/anthropic")
        set_setting(self.conn, LLM_MODEL_SETTING, "claude-opus-5")
        set_setting(self.conn, LLM_API_KEY_SETTING, "stored-key")
        settings = resolve_llm_settings(self.conn)
        self.assertEqual(settings["provider"], "anthropic")
        self.assertEqual(settings["base_url"], "https://gateway.internal/anthropic")
        self.assertEqual(settings["model"], "claude-opus-5")
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            self.assertEqual(resolve_llm_settings(self.conn)["api_key"], "stored-key")
        self.assertTrue(validate_llm_settings(settings))

    def test_validate_llm_settings_requires_model_and_key(self):
        with self.assertRaises(ValidationError):
            validate_llm_settings({"provider": "openai", "base_url": "https://x", "model": "", "api_key": "k"})
        with self.assertRaises(ValidationError):
            validate_llm_settings({"provider": "openai", "base_url": "https://x", "model": "gpt-4o", "api_key": ""})

    def test_internal_evidence_prompt_carries_bounded_evidence(self):
        store_manual_material(self.conn, self.project_id, {"title": "manual", "content": "internal context"})
        context, _hash = assemble_context(self.conn, self.project_id)
        prompt = build_internal_evidence_prompt(context)
        self.assertIn("Evidence JSON", prompt)
        self.assertIn("internal context", prompt)
        self.assertIn("# Weekly Report", prompt)
        self.assertIn("Do not invent facts", prompt)
        self.assertNotIn("Claude Code CLI", prompt)
        self.assertNotIn("`gh` or `glab`", prompt)

    def test_generate_internal_report_invokes_chat_and_rejects_empty_output(self):
        settings = {"provider": "openai", "base_url": DEFAULT_LLM_BASE_URLS["openai"], "api_key": "k", "model": "gpt-4o-mini"}
        context = {"system_prompt": "s", "report_template": "# Weekly Report", "week_key": "2026-W36"}
        with mock.patch("reports_app.internal_agent.resolve_llm_settings", return_value=settings):
            with mock.patch("reports_app.internal_agent.internal_chat", return_value="# Weekly Report") as chat:
                output = generate_internal_report(context, timeout=30)
        self.assertEqual(output, "# Weekly Report")
        self.assertIn("Evidence JSON", chat.call_args[0][0])
        self.assertEqual(chat.call_args[1].get("timeout"), 30)
        with mock.patch("reports_app.internal_agent.resolve_llm_settings", return_value=settings):
            with mock.patch("reports_app.internal_agent.internal_chat", return_value="   "):
                with self.assertRaises(RuntimeError):
                    generate_internal_report(context)

    def test_generate_report_with_internal_provider_records_success_and_failure(self):
        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}):
            with mock.patch("reports_app.internal_agent.generate_internal_report", return_value="# Internal Report") as gen:
                job_id = generate_report(self.conn, self.project_id, "manual", force=True)
        row = self.conn.execute(
            "SELECT status, provider, failure_reason FROM generation_jobs WHERE id = ?", (job_id,)
        ).fetchone()
        self.assertEqual(row["status"], "success")
        self.assertEqual(row["provider"], "internal")
        report = self.conn.execute(
            "SELECT content_md FROM weekly_reports WHERE project_id = ?", (self.project_id,)
        ).fetchone()
        self.assertEqual(report["content_md"], "# Internal Report")
        self.assertEqual(gen.call_args[0][0]["project_profile"]["name"], "Demo")

        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}):
            with mock.patch(
                "reports_app.internal_agent.generate_internal_report",
                side_effect=RuntimeError("LLM API key is not configured"),
            ):
                failed_job = generate_report(self.conn, self.project_id, "manual", force=True)
        row = self.conn.execute(
            "SELECT status, failure_reason FROM generation_jobs WHERE id = ?", (failed_job,)
        ).fetchone()
        self.assertEqual(row["status"], "failed")
        self.assertIn("LLM API key is not configured", row["failure_reason"])

    def test_internal_provider_still_uses_fake_report_when_fake_mode_on(self):
        context = {
            "project": {"name": "Demo"},
            "week_key": "2026-W36",
            "weekly_update": None,
            "github_activity": [],
            "git_commits_this_week": [],
            "new_materials_this_week": [],
        }
        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "1"}):
            with mock.patch("reports_app.internal_agent.generate_internal_report") as gen:
                output = invoke_provider("internal", context)
        gen.assert_not_called()
        self.assertIn("Weekly Report", output)

    def test_voice_internal_agent_structures_and_falls_back(self):
        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}):
            with mock.patch(
                "reports_app.internal_agent.internal_voice_todo_items",
                return_value=[{"title": "买牛奶", "description": "两盒"}],
            ) as items_fn:
                result = create_todos_from_voice(self.conn, "买牛奶 两盒", "internal", user_id=self.user_id)
        self.assertFalse(result["fallback"])
        self.assertEqual(result["error"], "")
        self.assertEqual(len(result["ids"]), 1)
        items_fn.assert_called_once_with("买牛奶 两盒", timeout=120)

        with mock.patch.dict(os.environ, {"REPORTS_FAKE_PROVIDER": "0"}):
            with mock.patch(
                "reports_app.internal_agent.internal_voice_todo_items",
                side_effect=RuntimeError("internal agent LLM call failed: boom"),
            ):
                result = create_todos_from_voice(self.conn, "买牛奶 两盒", "internal", user_id=self.user_id)
        self.assertTrue(result["fallback"])
        self.assertIn("boom", result["error"])
        titles = [row["title"] for row in todo_rows(self.conn, self.user_id)]
        self.assertIn("买牛奶 两盒", titles)

    def test_internal_agent_end_to_end_with_local_openai_compatible_server(self):
        try:
            import langchain_core  # noqa: F401
            import langchain_openai  # noqa: F401
        except ImportError:
            self.skipTest("langchain is not installed")

        seen_requests = []

        class MockOpenAIHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length))
                seen_requests.append({"path": self.path, "model": body.get("model"), "messages": body.get("messages")})
                payload = json.dumps({
                    "id": "chatcmpl-test",
                    "object": "chat.completion",
                    "created": 1,
                    "model": body.get("model", "test-model"),
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": '[{"title": "买牛奶", "description": "两盒"}]'},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, fmt, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), MockOpenAIHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            settings = {
                "provider": "openai",
                "base_url": f"http://127.0.0.1:{server.server_port}/v1",
                "api_key": "sk-test",
                "model": "test-model",
            }
            # httpx reads proxy variables when the client is built; keep
            # loopback traffic direct even on proxied dev machines.
            with mock.patch.dict(os.environ), mock.patch("reports_app.internal_agent.resolve_llm_settings", return_value=settings):
                for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
                    os.environ.pop(var, None)
                os.environ["NO_PROXY"] = "127.0.0.1,localhost"
                items = internal_voice_todo_items("买牛奶 两盒", timeout=20)
            self.assertEqual(items, [{"title": "买牛奶", "description": "两盒"}])
            self.assertEqual(seen_requests[0]["path"], "/v1/chat/completions")
            self.assertEqual(seen_requests[0]["model"], "test-model")
            self.assertIn("买牛奶", seen_requests[0]["messages"][-1]["content"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_llm_provider_settings_api_round_trip(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({
                    "llm_provider": "openai",
                    "llm_base_url": "http://127.0.0.1:1234/v1",
                    "llm_model": "gpt-4o-mini",
                    "llm_api_key": "sk-test-123",
                }),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["llm_provider"], "openai")
            self.assertEqual(payload["llm_base_url"], "http://127.0.0.1:1234/v1")
            self.assertEqual(payload["llm_model"], "gpt-4o-mini")
            self.assertTrue(payload["llm_api_key_set"])
            self.assertNotIn("llm_api_key", payload)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({
                    "llm_provider": "anthropic",
                    "llm_base_url": "",
                    "llm_model": "claude-opus-5",
                }),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["llm_provider"], "anthropic")
            self.assertEqual(payload["llm_base_url"], DEFAULT_LLM_BASE_URLS["anthropic"])
            self.assertTrue(payload["llm_api_key_set"], "empty llm_api_key must keep the stored key")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({"llm_provider": "gpt"}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            response.read()
            client.close()
            self.assertEqual(response.status, 400)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({"llm_base_url": "http://"}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            response.read()
            client.close()
            self.assertEqual(response.status, 400)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/state")
            response = client.getresponse()
            state_payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(state_payload["llm_provider"], "anthropic")
            self.assertEqual(state_payload["llm_model"], "claude-opus-5")
            self.assertTrue(state_payload["llm_api_key_set"])
            self.assertNotIn("llm_api_key", state_payload)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


    def test_asr_language_defaults_to_chinese_and_is_configurable(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({"asr_language": "en"}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["asr_language"], "en")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/state")
            response = client.getresponse()
            state_payload = json.loads(response.read())
            client.close()
            self.assertEqual(state_payload["asr_language"], "en")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({"asr_language": "  "}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(payload["asr_language"], DEFAULT_ASR_LANGUAGE, "blank asr_language resets to the Chinese default")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(payload["asr_language"], DEFAULT_ASR_LANGUAGE, "PUT without asr_language keeps the Chinese default")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


    def test_write_request_body_is_drained_for_keep_alive_reuse(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
        try:
            # The cancel endpoint never reads its body; before the drain fix
            # the leftover "{}" was parsed as the next request line and the
            # browser saw 501 Unsupported method ('{}POST').
            self.api_request(client, "POST", "/api/voice-jobs/999/cancel", body="{}", headers={"Content-Type": "application/json"})
            response = client.getresponse()
            response.read()
            self.assertEqual(response.status, 400)

            self.api_request(client, "POST", "/api/todos/voice", body=json.dumps({"text": "keepalive 下一条"}), headers={"Content-Type": "application/json"})
            response = client.getresponse()
            payload = json.loads(response.read())
            self.assertEqual(response.status, 202, "the next request on a reused connection must not see the previous body")
            self.assertEqual(payload["status"], "queued")
        finally:
            client.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_settings_put_updates_only_provided_keys(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({
                    "asr_language": "zh",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4o-mini",
                    "llm_api_key": "sk-stored",
                    "ui_theme": "Green",
                    "ui_mode": "dark",
                }),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["ui_theme"], "green", "theme names are stored lowercased")
            self.assertEqual(payload["ui_mode"], "dark")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({"asr_model": "whisper-medium"}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["asr_model"], "whisper-medium")
            self.assertEqual(payload["llm_model"], "gpt-4o-mini")
            self.assertTrue(payload["llm_api_key_set"])
            self.assertEqual(payload["asr_language"], "zh")
            self.assertEqual(payload["ui_theme"], "green")
            self.assertEqual(payload["ui_mode"], "dark")

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, 
                "PUT",
                "/api/settings",
                body=json.dumps({"ui_theme": "not a theme!"}),
                headers={"Content-Type": "application/json"},
            )
            response = client.getresponse()
            response.read()
            client.close()
            self.assertEqual(response.status, 400)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", "/api/state")
            response = client.getresponse()
            state_payload = json.loads(response.read())
            client.close()
            self.assertEqual(state_payload["ui_theme"], "green")
            self.assertEqual(state_payload["ui_mode"], "dark")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


    def test_archived_report_endpoint_renders_body_on_demand(self):
        self.conn.execute(
            """
            INSERT INTO weekly_reports (project_id, week_key, content_md, latest_job_id, created_at, updated_at)
            VALUES (?, '2026-W25', '# Old Report\n\n归档正文', 1, '2026-06-21T00:00:00+00:00', '2026-06-21T00:00:00+00:00')
            """,
            (self.project_id,),
        )
        self.conn.commit()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", f"/api/projects/{self.project_id}/reports/2026-W25")
            response = client.getresponse()
            payload = json.loads(response.read())
            client.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["week_key"], "2026-W25")
            self.assertIn("<h1>Old Report</h1>", payload["content_html"])
            self.assertNotIn("content_md", payload)

            client = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            self.api_request(client, "GET", f"/api/projects/{self.project_id}/reports/1999-W01")
            response = client.getresponse()
            response.read()
            client.close()
            self.assertEqual(response.status, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()


class UserAuthTest(unittest.TestCase):
    """Login, admin user management, and per-user data isolation."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        # production bootstraps a random admin password when this env var is
        # unset; the login tests need the known value, and it must be pinned
        # before init_db because schema migration already creates the admin
        os.environ["REPORTS_ADMIN_PASSWORD"] = "changeme"
        init_db(self.db_path)
        self.conn = connect(self.db_path)
        self.admin = ensure_bootstrap_admin(self.conn)
        self.project_id = create_project(
            self.conn,
            {
                "name": "Admin Project",
                "start_date": "2026-06-27",
                "timezone": "Asia/Shanghai",
            },
            self.admin,
        )
        self.conn.commit()
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"

    def tearDown(self):
        self.conn.close()
        os.environ.pop("REPORTS_FAKE_PROVIDER", None)
        os.environ.pop("REPORTS_ADMIN_PASSWORD", None)
        self.tmp.cleanup()

    def start_server(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def login(self, port, username, password):
        client = HTTPConnection("127.0.0.1", port, timeout=10)
        client.request(
            "POST",
            "/api/auth/login",
            body=json.dumps({"username": username, "password": password}),
            headers={"Content-Type": "application/json"},
        )
        response = client.getresponse()
        payload = json.loads(response.read())
        set_cookie = response.getheader("Set-Cookie") or ""
        client.close()
        return response.status, payload, set_cookie

    def api(self, port, method, path, token, body=None):
        client = HTTPConnection("127.0.0.1", port, timeout=10)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Cookie"] = f"reports_session={token}"
        client.request(method, path, body=body, headers=headers)
        response = client.getresponse()
        payload = json.loads(response.read())
        client.close()
        return response.status, payload

    def test_login_sets_cookie_and_rejects_bad_credentials(self):
        server, thread = self.start_server()
        try:
            status, payload, set_cookie = self.login(server.server_port, "darren", "changeme")
            self.assertEqual(status, 200)
            self.assertTrue(payload["current_user"]["is_admin"])
            self.assertIn("reports_session=", set_cookie)
            self.assertIn("HttpOnly", set_cookie)

            status, payload, _ = self.login(server.server_port, "darren", "wrong")
            self.assertEqual(status, 400)
            status, payload, _ = self.login(server.server_port, "ghost", "changeme")
            self.assertEqual(status, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_api_requires_authentication(self):
        server, thread = self.start_server()
        try:
            status, payload = self.api(server.server_port, "GET", "/api/state", None)
            self.assertEqual(status, 401)
            status, payload = self.api(server.server_port, "GET", "/api/todos", None)
            self.assertEqual(status, 401)
            status, payload = self.api(server.server_port, "GET", "/api/auth/state", None)
            self.assertEqual(status, 200)
            self.assertFalse(payload["authenticated"])
            self.assertEqual(payload["version"], APP_VERSION)
            status, payload = self.api(server.server_port, "GET", "/api/state", "bogus-token")
            self.assertEqual(status, 401)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_user_management_requires_admin_and_guards_last_admin(self):
        server, thread = self.start_server()
        try:
            _, payload, _ = self.login(server.server_port, "darren", "changeme")
            admin_token = None
            # pull the session token straight from the database for the cookie
            row = self.conn.execute("SELECT token FROM sessions ORDER BY created_at DESC LIMIT 1").fetchone()
            admin_token = row["token"]

            status, payload = self.api(server.server_port, "GET", "/api/users", admin_token)
            self.assertEqual(status, 200)
            self.assertEqual([u["username"] for u in payload["users"]], ["darren"])

            # create a plain member
            status, payload = self.api(
                server.server_port,
                "POST",
                "/api/users",
                admin_token,
                body=json.dumps({"username": "alice", "password": "secret1", "is_admin": False}),
            )
            self.assertEqual(status, 201)
            alice_id = payload["user"]["id"]

            # alice logs in with her own cookie
            _, _, cookie = self.login(server.server_port, "alice", "secret1")
            alice_token = cookie.split("reports_session=")[1].split(";")[0]
            status, payload = self.api(server.server_port, "GET", "/api/users", alice_token)
            self.assertEqual(status, 403)
            status, payload = self.api(
                server.server_port,
                "POST",
                "/api/users",
                alice_token,
                body=json.dumps({"username": "bob", "password": "secret2"}),
            )
            self.assertEqual(status, 403)

            # alice cannot demote or delete herself, nor the last admin
            status, payload = self.api(
                server.server_port,
                "PUT",
                f"/api/users/{alice_id}",
                admin_token,
                body=json.dumps({"is_admin": True}),
            )
            self.assertEqual(status, 200)
            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/users/1",
                admin_token,
                body=json.dumps({"is_admin": False}),
            )
            self.assertEqual(status, 400)
            status, payload = self.api(server.server_port, "DELETE", "/api/users/1", admin_token)
            self.assertEqual(status, 400)

            # demote alice again, then disable her; her sessions must be revoked
            status, payload = self.api(
                server.server_port,
                "PUT",
                f"/api/users/{alice_id}",
                admin_token,
                body=json.dumps({"is_admin": False}),
            )
            self.assertEqual(status, 200)
            status, payload = self.api(server.server_port, "GET", "/api/users", alice_token)
            self.assertEqual(status, 403)
            status, payload = self.api(
                server.server_port,
                "PUT",
                f"/api/users/{alice_id}",
                admin_token,
                body=json.dumps({"enabled": False}),
            )
            self.assertEqual(status, 200)
            status, payload = self.api(server.server_port, "GET", "/api/state", alice_token)
            self.assertEqual(status, 401)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_delete_user_blocked_while_user_still_owns_data(self):
        other = auth.create_user(self.conn, "carol", "secret1", is_admin=False)
        create_project(
            self.conn,
            {"name": "Carol Project", "start_date": "2026-06-27", "timezone": "Asia/Shanghai"},
            {"id": other, "username": "carol"},
        )
        self.conn.commit()
        server, thread = self.start_server()
        try:
            self.login(server.server_port, "darren", "changeme")
            row = self.conn.execute("SELECT token FROM sessions ORDER BY created_at DESC LIMIT 1").fetchone()
            admin_token = row["token"]
            status, payload = self.api(server.server_port, "DELETE", f"/api/users/{other}", admin_token)
            self.assertEqual(status, 400)
            self.assertIn("projects", payload["error"])
            self.assertIsNotNone(self.conn.execute("SELECT id FROM users WHERE id = ?", (other,)).fetchone())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_project_data_is_isolated_per_user(self):
        other_id = auth.create_user(self.conn, "dave", "secret1", is_admin=False)
        self.conn.commit()
        other_project = create_project(
            self.conn,
            {"name": "Dave Project", "start_date": "2026-06-27", "timezone": "Asia/Shanghai"},
            {"id": other_id, "username": "dave"},
        )
        self.conn.commit()

        server, thread = self.start_server()
        try:
            _, _, cookie = self.login(server.server_port, "dave", "secret1")
            dave_token = cookie.split("reports_session=")[1].split(";")[0]

            status, payload = self.api(server.server_port, "GET", "/api/state", dave_token)
            self.assertEqual(status, 200)
            self.assertEqual([p["name"] for p in payload["projects"]], ["Dave Project"])

            status, payload = self.api(server.server_port, "GET", f"/api/projects/{other_project}/workspace", dave_token)
            self.assertEqual(status, 200)
            status, payload = self.api(server.server_port, "GET", f"/api/projects/{self.project_id}/workspace", dave_token)
            self.assertEqual(status, 404)

            status, payload = self.api(server.server_port, "GET", "/api/todos", dave_token)
            self.assertEqual(status, 200)
            self.assertEqual(payload["todos"], [])

            # the admin does not see dave's project either
            self.login(server.server_port, "darren", "changeme")
            row = self.conn.execute("SELECT token FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (self.admin["id"],)).fetchone()
            admin_token = row["token"]
            status, payload = self.api(server.server_port, "GET", f"/api/projects/{other_project}/workspace", admin_token)
            self.assertEqual(status, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_legacy_rows_are_migrated_to_bootstrap_admin(self):
        # simulate a pre-multiuser database: rows without an owner
        now = iso_now()
        cur = self.conn.execute(
            "INSERT INTO projects (name, start_date, status, timezone, created_at, updated_at) VALUES ('Legacy', '2026-06-27', 'active', 'Asia/Shanghai', ?, ?)",
            (now, now),
        )
        legacy_project = cur.lastrowid
        self.conn.execute(
            "INSERT INTO todos (title, status, created_at, updated_at) VALUES ('Legacy todo', 'todo', ?, ?)",
            (now, now),
        )
        self.conn.execute(
            "INSERT INTO voice_jobs (status, created_at, updated_at) VALUES ('failed', ?, ?)",
            (now, now),
        )
        self.conn.commit()

        init_db(self.db_path)

        for table in ("projects", "todos", "voice_jobs"):
            row = self.conn.execute(f"SELECT user_id FROM {table} WHERE user_id IS NULL LIMIT 1").fetchone()
            self.assertIsNone(row, f"{table} rows must be assigned after migration")
        row = self.conn.execute("SELECT user_id, owner FROM projects WHERE id = ?", (legacy_project,)).fetchone()
        self.assertEqual(row["user_id"], self.admin["id"])
        self.assertEqual(row["owner"], self.admin["username"])

    def test_change_own_password(self):
        server, thread = self.start_server()
        try:
            _, _, cookie = self.login(server.server_port, "darren", "changeme")
            token = cookie.split("reports_session=")[1].split(";")[0]

            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/auth/password",
                token,
                body=json.dumps({"old_password": "wrong", "new_password": "newpass1"}),
            )
            self.assertEqual(status, 400)
            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/auth/password",
                token,
                body=json.dumps({"old_password": "changeme", "new_password": "newpass1"}),
            )
            self.assertEqual(status, 200)
            self.assertIsNotNone(auth.authenticate(self.conn, "darren", "newpass1"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class GitSettingsApiTest(unittest.TestCase):
    """Global GitHub/GitLab switches are admin-only; git tokens are per user."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.sqlite3"
        # see UserAuthTest.setUp: pin the bootstrap admin password for logins
        os.environ["REPORTS_ADMIN_PASSWORD"] = "changeme"
        init_db(self.db_path)
        self.conn = connect(self.db_path)
        self.admin = ensure_bootstrap_admin(self.conn)
        self.member_id = auth.create_user(self.conn, "member", "secret1", is_admin=False)
        self.conn.commit()
        os.environ["REPORTS_FAKE_PROVIDER"] = "1"

    def tearDown(self):
        self.conn.close()
        os.environ.pop("REPORTS_FAKE_PROVIDER", None)
        os.environ.pop("REPORTS_ADMIN_PASSWORD", None)
        self.tmp.cleanup()

    def start_server(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db_path
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def token_for(self, port, username, password):
        client = HTTPConnection("127.0.0.1", port, timeout=10)
        client.request(
            "POST",
            "/api/auth/login",
            body=json.dumps({"username": username, "password": password}),
            headers={"Content-Type": "application/json"},
        )
        response = client.getresponse()
        response.read()
        cookie = response.getheader("Set-Cookie") or ""
        client.close()
        return cookie.split("reports_session=")[1].split(";")[0]

    def api(self, port, method, path, token, body=None):
        client = HTTPConnection("127.0.0.1", port, timeout=10)
        headers = {"Content-Type": "application/json", "Cookie": f"reports_session={token}"}
        client.request(method, path, body=body, headers=headers)
        response = client.getresponse()
        payload = json.loads(response.read())
        client.close()
        return response.status, payload

    def test_git_switches_are_admin_only_and_tokens_stay_per_user(self):
        server, thread = self.start_server()
        try:
            admin_token = self.token_for(server.server_port, "darren", "changeme")
            member_token = self.token_for(server.server_port, "member", "secret1")

            # a member can store their own token but cannot flip the switches
            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/settings",
                member_token,
                body=json.dumps({"github_token": "ghp-member", "github_enabled": False}),
            )
            self.assertEqual(status, 403)
            row = self.conn.execute(
                "SELECT value FROM user_settings WHERE user_id = ? AND key = 'github_token'", (self.member_id,)
            ).fetchone()
            self.assertIsNone(row, "the whole request must be rejected, not just the admin key")

            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/settings",
                member_token,
                body=json.dumps({"github_token": "ghp-member"}),
            )
            self.assertEqual(status, 200)
            self.assertTrue(payload["github_token_set"])
            self.assertIsNone(
                self.conn.execute("SELECT value FROM app_settings WHERE key = 'github_token'").fetchone(),
                "git tokens must not leak into the global app_settings table",
            )

            # the admin can flip the switch and the flag is visible to everyone
            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/settings",
                admin_token,
                body=json.dumps({"github_enabled": False}),
            )
            self.assertEqual(status, 200)
            self.assertFalse(payload["github_enabled"])

            status, payload = self.api(server.server_port, "GET", "/api/state", member_token)
            self.assertEqual(status, 200)
            self.assertFalse(payload["github_enabled"])
            self.assertTrue(payload["github_token_set"])
            self.assertNotIn("llm_api_key_set", payload, "LLM configuration is admin-only")
            self.assertNotIn("queue_capacity", payload, "queue configuration is admin-only")

            status, payload = self.api(server.server_port, "GET", "/api/state", admin_token)
            self.assertTrue(payload["llm_api_key_set"] is not None)
            self.assertIn("queue_capacity", payload)

            # GitHub token list: per-org entries plus a general fallback
            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/settings",
                member_token,
                body=json.dumps({"github_tokens": [
                    {"label": "acme", "owner": "@Acme", "token": "ghp_org1"},
                    {"label": "general", "owner": "", "token": "ghp_all1"},
                ]}),
            )
            self.assertEqual(status, 200)
            self.assertEqual(len(payload["github_tokens"]), 2)
            self.assertEqual(payload["github_tokens"][0]["owner"], "acme", "owner is normalized (lowercase, no @)")
            self.assertTrue(all(entry["hint"].startswith("····") for entry in payload["github_tokens"]))
            self.assertEqual(payload["github_tokens"][0]["kind"], "classic")
            self.assertEqual(payload["github_tokens"][1]["kind"], "classic")
            self.assertNotIn("ghp_org1", json.dumps(payload), "raw tokens never leave the server")
            row = self.conn.execute(
                "SELECT value FROM user_settings WHERE user_id = ? AND key = 'github_tokens'", (self.member_id,)
            ).fetchone()
            self.assertIn("ghp_org1", row["value"])

            # resubmitting with empty tokens keeps the stored values by index
            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/settings",
                member_token,
                body=json.dumps({"github_tokens": [
                    {"label": "acme", "owner": "acme", "token": ""},
                    {"label": "general", "owner": "", "token": ""},
                ]}),
            )
            self.assertEqual(status, 200)
            stored = json.loads(
                self.conn.execute(
                    "SELECT value FROM user_settings WHERE user_id = ? AND key = 'github_tokens'", (self.member_id,)
                ).fetchone()["value"]
            )
            self.assertEqual([entry["token"] for entry in stored], ["ghp_org1", "ghp_all1"])

            # a repo whose owner matches uses the org token
            auth_info = git_sources.git_auth_for_user(self.conn, self.member_id)
            self.assertEqual(git_sources.github_token_for(auth_info, "acme/infra"), "ghp_org1")
            self.assertEqual(git_sources.github_token_for(auth_info, "alice/pet"), "ghp_all1")

            # per-user GitLab server address: stored, returned, and validated
            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/settings",
                member_token,
                body=json.dumps({"gitlab_url": "https://gitlab.self.example.com"}),
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["gitlab_url"], "https://gitlab.self.example.com")
            status, payload = self.api(server.server_port, "GET", "/api/state", member_token)
            self.assertEqual(payload["gitlab_url"], "https://gitlab.self.example.com")
            status, payload = self.api(
                server.server_port,
                "PUT",
                "/api/settings",
                member_token,
                body=json.dumps({"gitlab_url": "ftp://bad"}),
            )
            self.assertEqual(status, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
