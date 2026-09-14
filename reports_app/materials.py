import base64
import hashlib
import io
import json
import os
import re
from pathlib import Path

from html.parser import HTMLParser
from pypdf import PdfReader

from .config import SUPPORTED_HTML_EXTENSIONS, SUPPORTED_TEXT_EXTENSIONS, UPLOAD_DIR
from .timeutil import current_week_key, iso_now, parse_iso, week_key_for
from .validation import ValidationError, validate_material_filename


def safe_filename(name):
    base = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base) or "material"


def store_material(conn, project_id, payload):
    filename = original_filename(payload.get("filename") or "")
    ext = validate_material_filename(filename)
    raw = base64.b64decode(payload.get("content_base64") or "", validate=True)
    checksum = hashlib.sha256(raw).hexdigest()
    project_dir = UPLOAD_DIR / f"project_{project_id}"
    project_dir.mkdir(parents=True, exist_ok=True)
    storage_name = f"{checksum[:12]}_{safe_filename(filename)}"
    path = project_dir / storage_name
    path.write_bytes(raw)

    status = "pending"
    extracted = ""
    error = ""
    if ext in SUPPORTED_TEXT_EXTENSIONS:
        try:
            extracted = raw.decode("utf-8")
            status = "extracted"
        except UnicodeDecodeError as exc:
            status = "failed"
            error = f"text decode failed: {exc}"
    elif ext in SUPPORTED_HTML_EXTENSIONS:
        try:
            extracted = extract_html_text(raw)
            if not extracted.strip():
                raise ValueError("HTML contains no extractable text")
            status = "extracted"
        except Exception as exc:
            status = "failed"
            error = f"HTML text extraction failed: {exc}"
    elif ext == ".pdf":
        try:
            extracted = extract_pdf_text(raw)
            if not extracted.strip():
                raise ValueError("PDF contains no extractable text")
            status = "extracted"
        except Exception as exc:
            status = "failed"
            error = f"PDF text extraction failed: {exc}"

    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO materials
        (project_id, filename, content_type, storage_path, size_bytes, checksum,
         extraction_status, extracted_text, extraction_error, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            filename,
            payload.get("content_type") or "application/octet-stream",
            os.fspath(path),
            len(raw),
            checksum,
            status,
            extracted,
            error,
            now,
            now,
        ),
    )
    return cur.lastrowid


def original_filename(name):
    value = Path(name).name.strip()
    if not value:
        raise ValidationError("material filename is required")
    return value[:255]


def extract_pdf_text(raw):
    reader = PdfReader(io.BytesIO(raw))
    return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()

def decode_document_bytes(raw):
    """Decode an uploaded document to str: strict UTF-8 first, then the charset
    declared in the HTML meta tag, then gb18030 (superset of the gb2312/gbk
    encodings common in Chinese HTML exports). Raises UnicodeDecodeError."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    head = raw[:2048].decode("ascii", errors="ignore")
    match = re.search(r'charset\s*=\s*["\']?([A-Za-z0-9_.:-]+)', head, re.IGNORECASE)
    candidates = [match.group(1)] if match else []
    candidates.append("gb18030")
    for encoding in candidates:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    raise UnicodeDecodeError("utf-8", raw, 0, 1, "unsupported encoding and no usable charset declaration")


class _HTMLTextExtractor(HTMLParser):
    """Extract readable text from an uploaded HTML document (stdlib only)."""
    HEADINGS = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ", "h5": "#### ", "h6": "#### "}
    NEWLINE = {"p", "div", "br", "tr", "table", "ul", "ol", "section", "hr", "blockquote"}
    SKIP = {"script", "style"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1
        elif self.skip_depth:
            return
        elif tag in self.HEADINGS:
            self.parts.append("\n\n" + self.HEADINGS[tag])
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in {"td", "th"}:
            self.parts.append(" | ")
        elif tag in self.NEWLINE:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif self.skip_depth:
            return
        elif tag in self.HEADINGS or tag in self.NEWLINE or tag == "li":
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)


def extract_html_text(raw):
    parser = _HTMLTextExtractor()
    parser.feed(decode_document_bytes(raw))
    text = "".join(parser.parts)
    lines = [line.rstrip() for line in text.splitlines()]
    out, blank = [], 0
    for line in lines:
        if not line.strip():
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        out.append(line)
    return "\n".join(out).strip()


def summarize_uploaded_materials(conn, project_id, material_ids, timeout=120):
    if not material_ids:
        return
    placeholders = ",".join("?" for _ in material_ids)
    rows = conn.execute(
        f"SELECT id, filename, extracted_text FROM materials WHERE project_id = ? AND id IN ({placeholders}) ORDER BY id",
        (project_id, *material_ids),
    ).fetchall()
    items = [
        {"id": row["id"], "filename": row["filename"], "text_start": (row["extracted_text"] or "")[:4000]}
        for row in rows
    ]
    fallbacks = {item["id"]: fallback_summary(item["filename"], item["text_start"]) for item in items}
    try:
        generated = generate_ai_summaries(items, timeout)
    except Exception as exc:
        for item in items:
            conn.execute(
                "UPDATE materials SET summary = ?, summary_status = 'failed', summary_error = ? WHERE id = ?",
                (fallbacks[item["id"]], str(exc)[:2000], item["id"]),
            )
        return
    for item in items:
        summary = (generated.get(item["id"]) or "").strip()
        if summary:
            conn.execute(
                "UPDATE materials SET summary = ?, summary_status = 'generated', summary_error = '' WHERE id = ?",
                (summary[:1000], item["id"]),
            )
        else:
            conn.execute(
                "UPDATE materials SET summary = ?, summary_status = 'failed', summary_error = ? WHERE id = ?",
                (fallbacks[item["id"]], "AI summary output was missing for this file", item["id"]),
            )


def generate_ai_summaries(items, timeout=120):
    """Material summaries run through the internal agent; REPORTS_FAKE_PROVIDER
    keeps tests and dry runs offline."""
    from .reports import fake_provider_enabled

    if fake_provider_enabled():
        return {item["id"]: fallback_summary(item["filename"], item["text_start"]) for item in items}
    from .internal_agent import internal_chat, resolve_llm_settings

    raw = internal_chat(build_summary_prompt(items), resolve_llm_settings(), timeout=timeout, temperature=0)
    return parse_summary_output(raw, items)


def build_summary_prompt(items):
    evidence = json.dumps(items, ensure_ascii=False, indent=2)
    return (
        "为每份项目资料生成简洁、客观的摘要。只依据原始文件名和正文开头，不要补充未出现的事实。"
        "使用资料正文的主要语言，每条不超过120个汉字或同等长度。"
        "只输出 JSON 数组，每项严格使用 {\"id\": 数字, \"summary\": \"摘要\"}，不要 Markdown。\n\n"
        f"资料：\n{evidence}"
    )


def parse_summary_output(raw, items):
    value = (raw or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value, flags=re.IGNORECASE)
    data = json.loads(value)
    if not isinstance(data, list):
        raise ValueError("AI summary output must be a JSON array")
    allowed = {item["id"] for item in items}
    result = {}
    for item in data:
        if isinstance(item, dict) and item.get("id") in allowed and isinstance(item.get("summary"), str):
            result[item["id"]] = item["summary"]
    return result


def fallback_summary(filename, text):
    excerpt = re.sub(r"\s+", " ", text or "").strip()[:180]
    return f"{filename}：{excerpt}" if excerpt else f"{filename}：暂无可提取的正文内容"


def update_material_summary(conn, project_id, material_id, payload):
    row = conn.execute(
        "SELECT id FROM materials WHERE id = ? AND project_id = ? AND source_type = 'upload'",
        (material_id, project_id),
    ).fetchone()
    if not row:
        raise ValidationError("uploaded material not found")
    summary = (payload.get("summary") or "").strip()
    if not summary:
        raise ValidationError("material summary is required")
    conn.execute(
        "UPDATE materials SET summary = ?, summary_status = 'manual', summary_error = '', updated_at = ? WHERE id = ?",
        (summary[:1000], iso_now(), material_id),
    )


def store_manual_material(conn, project_id, payload):
    title = safe_manual_title(payload.get("title") or payload.get("filename") or "manual-note")
    content = payload.get("content") or ""
    if not content.strip():
        raise ValidationError("manual material content is required")
    raw = content.encode("utf-8")
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO materials
        (project_id, filename, content_type, storage_path, size_bytes, checksum,
         extraction_status, extracted_text, extraction_error, created_at, updated_at, source_type)
        VALUES (?, ?, 'text/markdown', '', ?, ?, 'extracted', ?, '', ?, ?, 'manual')
        """,
        (
            project_id,
            title,
            len(raw),
            hashlib.sha256(raw).hexdigest(),
            content,
            now,
            now,
        ),
    )
    return cur.lastrowid


def update_manual_material(conn, project_id, material_id, payload):
    row = conn.execute("SELECT * FROM materials WHERE id = ? AND project_id = ?", (material_id, project_id)).fetchone()
    if not row:
        raise ValidationError("material not found")
    if row["source_type"] != "manual":
        raise ValidationError("only manual materials can be edited")
    project = conn.execute("SELECT timezone FROM projects WHERE id = ?", (project_id,)).fetchone()
    created_at = parse_iso(row["created_at"])
    if not created_at or week_key_for(created_at, project["timezone"]) != current_week_key(project["timezone"]):
        raise ValidationError("previous-week materials are locked")
    title = safe_manual_title(payload.get("title") or row["filename"])
    content = payload.get("content") or ""
    if not content.strip():
        raise ValidationError("manual material content is required")
    raw = content.encode("utf-8")
    conn.execute(
        """
        UPDATE materials
        SET filename = ?, size_bytes = ?, checksum = ?, extracted_text = ?, updated_at = ?
        WHERE id = ? AND project_id = ?
        """,
        (title, len(raw), hashlib.sha256(raw).hexdigest(), content, iso_now(), material_id, project_id),
    )


def delete_material(conn, project_id, material_id):
    row = conn.execute(
        """
        SELECT materials.*, projects.timezone
        FROM materials
        JOIN projects ON projects.id = materials.project_id
        WHERE materials.id = ? AND materials.project_id = ?
        """,
        (material_id, project_id),
    ).fetchone()
    if not row:
        raise ValidationError("material not found")
    if not material_is_unlocked(row, row["timezone"]):
        raise ValidationError("previous-week materials are locked")
    conn.execute("DELETE FROM materials WHERE id = ? AND project_id = ?", (material_id, project_id))
    return row["storage_path"] if row["source_type"] == "upload" else ""


def remove_material_file(storage_path):
    if not storage_path:
        return
    path = Path(storage_path).resolve()
    try:
        path.relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        # The material record is already gone; leave an inaccessible orphan rather
        # than turning a successful logical deletion into an API failure.
        pass


def material_is_unlocked(row, timezone):
    created_at = parse_iso(row["created_at"])
    return bool(created_at and week_key_for(created_at, timezone) == current_week_key(timezone))


def material_is_editable(row, timezone):
    return row["source_type"] == "manual" and material_is_unlocked(row, timezone)


def safe_manual_title(title):
    value = (title or "").strip()
    if not value:
        raise ValidationError("manual material title is required")
    return value[:160]
