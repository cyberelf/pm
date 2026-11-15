import base64
import io
import json
import tempfile
import threading
import unittest
from datetime import datetime
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

from openpyxl import Workbook
from reports_app import auth
from reports_app.backup import run_backup
from reports_app.cold_storage import evaluate_cold_storage, month_cutoff, validate_cold_target
from reports_app.db import connect, create_project, ensure_bootstrap_admin, init_db, set_setting
from reports_app.materials import extract_excel_text, store_material
from reports_app.server import Handler, material_detail
from reports_app.validation import ValidationError


class FileStorageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="zreport-storage-")
        self.root = Path(self.tmp.name)
        self.uploads = self.root / "uploads"
        self.cold = self.root / "cold"
        self.db = self.root / "reports.sqlite3"
        init_db(self.db)
        self.conn = connect(self.db)
        self.user = ensure_bootstrap_admin(self.conn)
        self.project = create_project(self.conn, {"name": "Storage", "start_date": "2026-01-01"}, self.user)
        self.token = auth.create_session(self.conn, self.user["id"])
        self.member = auth.create_user(self.conn, "other", "password123")
        self.other_token = auth.create_session(self.conn, self.member)
        self.conn.commit()
        for module in ("materials", "server", "cold_storage", "backup"):
            patch = mock.patch(f"reports_app.{module}.UPLOAD_DIR", self.uploads)
            patch.start()
            self.addCleanup(patch.stop)
        self.now = datetime(2026, 3, 31, 12, tzinfo=ZoneInfo("Asia/Shanghai"))

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def upload(self, name="资料.txt", raw=b"original content", created=None):
        material = store_material(self.conn, self.project, {"filename": name, "content_base64": base64.b64encode(raw).decode()})
        if created:
            self.conn.execute("UPDATE materials SET created_at = ? WHERE id = ?", (created, material))
        self.conn.commit()
        return material

    def row(self, material):
        return self.conn.execute("SELECT * FROM materials WHERE id = ?", (material,)).fetchone()

    def enable(self):
        set_setting(self.conn, "cold_storage_enabled", "1")
        set_setting(self.conn, "cold_storage_target_dir", str(self.cold))
        self.conn.commit()

    def start_api(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.db_path = self.db
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server.server_port

    def request(self, port, path, method="GET", token=None, payload=None):
        client = HTTPConnection("127.0.0.1", port, timeout=10)
        headers = {"Authorization": f"Bearer {token or self.token}"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        client.request(method, path, json.dumps(payload) if payload is not None else None, headers)
        response = client.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        client.close()
        return result

    def test_excel_multisheet_unicode_values_and_formulas(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "进度"
        sheet.append(["任务", "完成率", "验证"])
        sheet.append(["接口开发", 0.75, True])
        workbook.create_sheet("风险").append(["依赖延期", "=1+2"])
        stream = io.BytesIO()
        workbook.save(stream)
        material = self.upload("项目.xlsx", stream.getvalue())
        row = self.row(material)
        self.assertEqual(row["extraction_status"], "extracted")
        for value in ("## 进度", "接口开发\t0.75\tTrue", "## 风险", "=1+2"):
            self.assertIn(value, row["extracted_text"])
        self.assertEqual(material_detail(self.conn, self.project, material)["preview_kind"], "text")
        legacy = Path(__file__).with_name("fixtures") / "materials.xls"
        text = extract_excel_text(legacy.read_bytes(), ".xls")
        self.assertIn("接口开发\t0.75", text)
        self.assertIn("## 风险\n依赖延期", text)

    def test_invalid_and_empty_excel_keep_original(self):
        for name, raw in (("bad.xls", b"invalid"), ("bad.xlsx", b"invalid")):
            row = self.row(self.upload(name, raw))
            self.assertEqual(row["extraction_status"], "failed")
            self.assertEqual(Path(row["storage_path"]).read_bytes(), raw)
        stream = io.BytesIO()
        Workbook().save(stream)
        row = self.row(self.upload("empty.xlsx", stream.getvalue()))
        self.assertEqual(row["extraction_status"], "failed")

    def test_calendar_month_threshold_and_hourly_schedule(self):
        self.assertEqual(month_cutoff(self.now).isoformat(), "2026-02-28T12:00:00+08:00")
        old = self.upload(created="2026-02-28T11:59:59+08:00")
        exact = self.upload(created="2026-02-28T12:00:00+08:00")
        recent = self.upload(created="2026-03-01T00:00:00+08:00")
        source = Path(self.row(old)["storage_path"])
        self.enable()
        result = evaluate_cold_storage(self.conn, self.now)
        self.assertEqual(result["cold_storage_last_count"], 1)
        self.assertFalse(source.exists())
        self.assertEqual(Path(self.row(old)["storage_path"]).read_bytes(), b"original content")
        self.assertEqual(self.row(exact)["archive_root"], "")
        self.assertEqual(self.row(recent)["archive_root"], "")
        self.assertEqual(evaluate_cold_storage(self.conn, self.now), result)
        # Changing the target does not break previously archived paths.
        set_setting(self.conn, "cold_storage_target_dir", str(self.root / "other-cold"))
        self.conn.commit()
        self.assertEqual(material_detail(self.conn, self.project, old)["content"], "original content")

    def test_failed_transfer_preserves_original_and_database_path(self):
        material = self.upload(created="2026-01-01T00:00:00+08:00")
        source = Path(self.row(material)["storage_path"])
        self.enable()
        with mock.patch("reports_app.cold_storage._checksum", return_value="bad"):
            result = evaluate_cold_storage(self.conn, self.now)
        self.assertIn("校验失败", result["cold_storage_last_error"])
        self.assertTrue(source.exists())
        self.assertEqual(self.row(material)["storage_path"], str(source))
        self.assertEqual(list(self.cold.rglob(".transfer-*")), [])
        result = evaluate_cold_storage(self.conn, self.now, force=True)
        self.assertEqual(result["cold_storage_last_count"], 1)
        self.assertEqual(result["cold_storage_last_error"], "")

    def test_shared_legacy_path_not_deleted_until_all_references_move(self):
        first = self.upload(created="2026-01-01T00:00:00+08:00")
        recent = self.upload(created="2026-03-20T00:00:00+08:00")
        source = self.row(first)["storage_path"]
        self.conn.execute("UPDATE materials SET storage_path = ? WHERE id = ?", (source, recent))
        self.conn.commit()
        self.enable()
        evaluate_cold_storage(self.conn, self.now)
        self.assertTrue(Path(source).exists())
        self.assertTrue(Path(self.row(first)["storage_path"]).exists())

    def test_download_access_headers_and_archived_pdf_html(self):
        material = self.upload(raw=b"\x00original\xff", created="2026-01-01T00:00:00+08:00")
        html = self.upload("页面.html", "<h1>原文</h1>".encode(), created="2026-01-01T00:00:00+08:00")
        pdf = self.upload("file.pdf", b"%PDF-original", created="2026-01-01T00:00:00+08:00")
        port = self.start_api()
        path = f"/api/projects/{self.project}/materials/{material}/download"
        status, headers, body = self.request(port, path)
        self.assertEqual(status, 200)
        self.assertEqual(body, b"\x00original\xff")
        self.assertIn("filename*=UTF-8''%E8%B5%84%E6%96%99.txt", headers["Content-Disposition"])
        self.assertEqual(self.request(port, path, token=self.other_token)[0], 404)
        self.conn.execute("""INSERT INTO project_shares (project_id, user_id, role, created_at, updated_at)
                             VALUES (?, ?, 'read', ?, ?)""",
                          (self.project, self.member, self.now.isoformat(), self.now.isoformat()))
        self.conn.commit()
        self.assertEqual(self.request(port, path, token=self.other_token)[2], body)
        self.enable()
        evaluate_cold_storage(self.conn, self.now)
        self.assertEqual(self.request(port, path)[2], body)
        self.assertEqual(self.request(port, path, token=self.other_token)[2], body)
        status, _, content = self.request(port, f"/api/projects/{self.project}/materials/{pdf}/content")
        self.assertEqual((status, content), (200, b"%PDF-original"))
        self.assertEqual(material_detail(self.conn, self.project, html)["content_html"], "<h1>原文</h1>")
        Path(self.row(material)["storage_path"]).unlink()
        self.assertEqual(self.request(port, path)[0], 404)

    def test_admin_configuration_permissions_and_validation(self):
        port = self.start_api()
        payload = {"cold_storage_enabled": True, "cold_storage_target_dir": str(self.cold)}
        self.assertEqual(self.request(port, "/api/settings", "PUT", self.other_token, payload)[0], 403)
        self.assertEqual(self.request(port, "/api/cold-storage/run", "POST", self.other_token)[0], 403)
        self.assertEqual(self.request(port, "/api/settings", "PUT", payload={"cold_storage_enabled": True})[0], 400)
        self.assertEqual(self.request(port, "/api/settings", "PUT", payload=payload)[0], 200)
        self.assertEqual(self.request(port, "/api/cold-storage/run", "POST")[0], 200)
        self.assertEqual(self.request(port, "/api/settings", "PUT", payload={"cold_storage_target_dir": ""})[0], 400)
        self.assertEqual(self.request(port, "/api/settings", "PUT", payload={"backup_target_dir": str(self.cold / "backups")})[0], 400)
        for path in ("relative", str(Path(__file__).resolve().parents[1] / "data/uploads")):
            with self.assertRaises(ValidationError):
                validate_cold_target(path)

    def test_full_backup_includes_cold_original_and_manifest(self):
        material = self.upload(created="2026-01-01T00:00:00+08:00")
        self.enable()
        evaluate_cold_storage(self.conn, self.now)
        set_setting(self.conn, "backup_target_dir", str(self.root / "backups"))
        self.conn.commit()
        run = run_backup(self.conn, self.db)
        self.assertEqual(run["status"], "success", run["message"])
        folder = Path(run["backup_path"])
        manifest = json.loads((folder / "cold_uploads.json").read_text())
        self.assertEqual(manifest[0]["material_id"], material)
        self.assertEqual((folder / manifest[0]["backup_path"]).read_bytes(), b"original content")
        Path(self.row(material)["storage_path"]).unlink()
        run = run_backup(self.conn, self.db)
        self.assertEqual(run["status"], "failed")
