import base64
import hashlib
import io
import json
import os
import re
import struct
import uuid
from zipfile import ZipFile
from pathlib import Path

from html.parser import HTMLParser
from xml.etree import ElementTree
from pypdf import PdfReader

from .config import (
    MAX_IMAGE_RECOGNITION_BYTES,
    SUPPORTED_HTML_EXTENSIONS,
    SUPPORTED_IMAGE_TYPES,
    SUPPORTED_TEXT_EXTENSIONS,
    UPLOAD_DIR,
)
from .timeutil import current_week_key, iso_now, parse_iso, week_key_for
from .validation import ValidationError, validate_material_filename


def safe_filename(name):
    base = Path(name).name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", base) or "material"


def add_uploaded_materials(conn, project_id, files, workstream_id=None, timeout=120):
    """Store uploaded files with their summaries and workstream links.

    Every slow step (image recognition, the summary/classification model
    call) runs before the first write, so this request never holds the
    SQLite write lock while waiting on the model; the rows land in one short
    burst of inserts that the caller commits. An explicit workstream_id is a
    manual link for every file, so the model is not asked to classify them."""
    prepared = []
    try:
        for payload in files:
            prepared.append(prepare_material(project_id, payload))
        from .workstreams import auto_link_material, set_material_links, workstreams_for_prompt

        workstreams = [] if workstream_id else workstreams_for_prompt(conn, project_id)
        summaries, assignments = summarize_prepared(prepared, timeout, workstreams)
        ids = []
        for index, item in enumerate(prepared):
            material_id = insert_material(conn, project_id, item, summaries[index])
            ids.append(material_id)
            if workstream_id:
                set_material_links(conn, project_id, material_id, workstream_id)
            elif assignments.get(index) is not None:
                auto_link_material(conn, project_id, material_id, assignments[index])
        return ids
    except BaseException:
        for item in prepared:
            remove_material_file(item["storage_path"])
        raise


def store_material(conn, project_id, payload):
    """Single file without a summary (summary_status stays pending)."""
    return insert_material(conn, project_id, prepare_material(project_id, payload))


def prepare_material(project_id, payload):
    """Validate, save and extract one upload without touching the database
    (image recognition is a model call)."""
    filename = original_filename(payload.get("filename") or "")
    ext = validate_material_filename(filename)
    raw = base64.b64decode(payload.get("content_base64") or "", validate=True)
    content_type = payload.get("content_type") or "application/octet-stream"
    if ext in SUPPORTED_IMAGE_TYPES:
        # images are served inline, so the stored type comes from the bytes,
        # never from the client
        content_type = sniff_image_type(raw)
        if not content_type:
            raise ValidationError(f"{filename}: file content is not a PNG, JPEG, GIF, or WebP image")
    checksum = hashlib.sha256(raw).hexdigest()
    project_dir = UPLOAD_DIR / f"project_{project_id}"
    project_dir.mkdir(parents=True, exist_ok=True)
    storage_name = f"{uuid.uuid4().hex}_{safe_filename(filename)}"
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
    elif ext in {".xlsx", ".xls"}:
        try:
            extracted = extract_excel_text(raw, ext)
            status = "extracted"
        except Exception as exc:
            status = "failed"
            error = f"Excel text extraction failed: {exc}"
    elif ext in {".docx", ".doc"}:
        try:
            extracted = extract_docx_text(raw) if ext == ".docx" else extract_doc_text(raw)
            status = "extracted"
        except Exception as exc:
            status = "failed"
            error = f"Word text extraction failed: {exc}"
    elif ext in SUPPORTED_IMAGE_TYPES:
        try:
            if len(raw) > MAX_IMAGE_RECOGNITION_BYTES:
                raise ValueError(f"image exceeds {MAX_IMAGE_RECOGNITION_BYTES // (1024 * 1024)} MiB recognition limit")
            extracted = recognize_image_text(filename, raw, content_type)
            status = "extracted"
        except Exception as exc:
            status = "failed"
            error = f"image recognition failed: {exc}"
    elif ext == ".pdf":
        try:
            extracted = extract_pdf_text(raw)
            if not extracted.strip():
                raise ValueError("PDF contains no extractable text")
            status = "extracted"
        except Exception as exc:
            status = "failed"
            error = f"PDF text extraction failed: {exc}"

    return {
        "filename": filename,
        "content_type": content_type,
        "storage_path": os.fspath(path),
        "size_bytes": len(raw),
        "checksum": checksum,
        "extraction_status": status,
        "extracted_text": extracted,
        "extraction_error": error,
    }


def insert_material(conn, project_id, item, summary=None):
    """summary: (text, status, error) from summarize_prepared, or None."""
    text, summary_status, summary_error = summary or ("", "pending", "")
    now = iso_now()
    cur = conn.execute(
        """
        INSERT INTO materials
        (project_id, filename, content_type, storage_path, size_bytes, checksum,
         extraction_status, extracted_text, extraction_error,
         summary, summary_status, summary_error, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            item["filename"],
            item["content_type"],
            item["storage_path"],
            item["size_bytes"],
            item["checksum"],
            item["extraction_status"],
            item["extracted_text"],
            item["extraction_error"],
            text,
            summary_status,
            summary_error,
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


def extract_excel_text(raw, ext):
    """Keep sheet/row context, with bounded extraction; never evaluate formulas."""
    parts = []
    cells = 0
    characters = 0

    def append_sheet(name, rows):
        nonlocal cells, characters
        lines = []
        for row in rows:
            cells += len(row)
            if cells > 200000:
                raise ValueError("Excel exceeds 200000 cells")
            values = ["" if value is None else str(value) for value in row]
            while values and not values[-1]:
                values.pop()
            if not any(values):
                continue
            line = "\t".join(values)
            characters += len(line)
            if characters > 2000000:
                raise ValueError("Excel text exceeds 2000000 characters")
            lines.append(line)
        if lines:
            parts.append(f"## {name}\n" + "\n".join(lines))

    if ext == ".xlsx":
        from openpyxl import load_workbook
        with ZipFile(io.BytesIO(raw)) as archive:
            if sum(item.file_size for item in archive.infolist()) > 64 * 1024 * 1024:
                raise ValueError("Excel uncompressed data exceeds 64 MiB")
        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=False, keep_links=False)
        try:
            for sheet in workbook:
                if (sheet.max_row or 0) * (sheet.max_column or 0) > 200000:
                    raise ValueError("Excel exceeds 200000 cells")
                append_sheet(sheet.title, sheet.iter_rows(values_only=True))
        finally:
            workbook.close()
    else:
        import xlrd
        workbook = xlrd.open_workbook(file_contents=raw, on_demand=True, ragged_rows=True)
        try:
            for sheet in workbook.sheets():
                if sheet.nrows * sheet.ncols > 200000:
                    raise ValueError("Excel exceeds 200000 cells")
                def rows():
                    for index in range(sheet.nrows):
                        values = []
                        for cell in sheet.row(index):
                            value = cell.value
                            if cell.ctype == xlrd.XL_CELL_DATE:
                                value = xlrd.xldate_as_datetime(value, workbook.datemode).isoformat(sep=" ")
                            elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                                value = bool(value)
                            values.append(value)
                        yield values
                append_sheet(sheet.name, rows())
        finally:
            workbook.release_resources()
    if not parts:
        raise ValueError("Excel contains no extractable cells")
    return "\n\n".join(parts)


MAX_WORD_TEXT_CHARACTERS = 2000000
MAX_WORD_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _parse_docx_xml(data):
    # stdlib ElementTree is not hardened against entity expansion; OOXML
    # parts never carry a DTD, so refuse any that do
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise ValueError("Word XML must not contain a DTD")
    return ElementTree.fromstring(data)


def _docx_heading_levels(styles_xml):
    """styleId -> heading level from styles.xml: 'heading N'/'Title' names or
    an outline level (Chinese Word names heading styles by number IDs)."""
    levels = {}
    if not styles_xml:
        return levels
    for style in _parse_docx_xml(styles_xml).iter(f"{_W}style"):
        style_id = style.get(f"{_W}styleId") or ""
        name_el = style.find(f"{_W}name")
        name = (name_el.get(f"{_W}val") if name_el is not None else "") or ""
        outline = style.find(f"{_W}pPr/{_W}outlineLvl")
        match = re.fullmatch(r"heading\s*([1-9])", name.strip(), re.IGNORECASE)
        if match:
            levels[style_id] = int(match.group(1))
        elif name.strip().lower() == "title":
            levels[style_id] = 1
        elif outline is not None and (outline.get(f"{_W}val") or "").isdigit() and int(outline.get(f"{_W}val")) < 9:
            levels[style_id] = int(outline.get(f"{_W}val")) + 1
    return levels


def _docx_blocks(container):
    """Paragraphs and tables in document order, unwrapping content controls."""
    for child in container:
        if child.tag in {f"{_W}p", f"{_W}tbl"}:
            yield child
        elif child.tag in {f"{_W}sdt", f"{_W}customXml"}:
            content = child.find(f"{_W}sdtContent") if child.tag == f"{_W}sdt" else child
            if content is not None:
                yield from _docx_blocks(content)


def _docx_paragraph_text(paragraph):
    parts = []
    for el in paragraph.iter():
        if el.tag == f"{_W}t":
            parts.append(el.text or "")
        elif el.tag == f"{_W}tab":
            parts.append("\t")
        elif el.tag in {f"{_W}br", f"{_W}cr"}:
            parts.append("\n")
        elif el.tag == f"{_W}noBreakHyphen":
            parts.append("-")
    return "".join(parts).strip()


def _docx_table_rows(table):
    rows = []
    for tr in table.findall(f"{_W}tr"):
        cells = []
        for tc in tr.findall(f"{_W}tc"):
            texts = []
            for block in _docx_blocks(tc):
                if block.tag == f"{_W}p":
                    text = _docx_paragraph_text(block)
                    if text:
                        texts.append(text)
                else:
                    texts.extend(" / ".join(row.split("\t")) for row in _docx_table_rows(block))
            cells.append(" ".join(texts).replace("\t", " ").replace("\n", " "))
        while cells and not cells[-1]:
            cells.pop()
        if any(cells):
            rows.append("\t".join(cells))
    return rows


def extract_docx_text(raw):
    """Word .docx body text: headings as Markdown '#', list items as '- ',
    table rows tab-separated (like Excel extraction). Bounded."""
    with ZipFile(io.BytesIO(raw)) as archive:
        if sum(item.file_size for item in archive.infolist()) > MAX_WORD_UNCOMPRESSED_BYTES:
            raise ValueError("Word uncompressed data exceeds 64 MiB")
        names = set(archive.namelist())
        if "word/document.xml" not in names:
            raise ValueError("not a Word document (word/document.xml missing)")
        document_xml = archive.read("word/document.xml")
        styles_xml = archive.read("word/styles.xml") if "word/styles.xml" in names else b""
    levels = _docx_heading_levels(styles_xml)
    body = _parse_docx_xml(document_xml).find(f"{_W}body")
    lines = []
    characters = 0
    for block in _docx_blocks(body if body is not None else []):
        if block.tag == f"{_W}tbl":
            entry = "\n".join(_docx_table_rows(block))
        else:
            entry = _docx_paragraph_text(block)
            if entry:
                props = block.find(f"{_W}pPr")
                level = 0
                if props is not None:
                    outline = props.find(f"{_W}outlineLvl")
                    style = props.find(f"{_W}pStyle")
                    if outline is not None and (outline.get(f"{_W}val") or "").isdigit() and int(outline.get(f"{_W}val")) < 9:
                        level = int(outline.get(f"{_W}val")) + 1
                    elif style is not None:
                        level = levels.get(style.get(f"{_W}val") or "", 0)
                    if level:
                        entry = "#" * min(level, 6) + " " + entry.replace("\n", " ")
                    elif props.find(f"{_W}numPr") is not None:
                        entry = "- " + entry
        if not entry:
            continue
        characters += len(entry)
        if characters > MAX_WORD_TEXT_CHARACTERS:
            raise ValueError("Word text exceeds 2000000 characters")
        lines.append(entry)
    if not lines:
        raise ValueError("Word document contains no extractable text")
    return "\n\n".join(lines)


_CFB_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_CFB_NOSTREAM = 0xFFFFFFFF


def _cfb_root_streams(raw):
    """Top-level streams of an OLE compound file (MS-CFB), stdlib only.
    Sector chains are cycle-checked; returns {name: bytes}."""
    if raw[:8] != _CFB_SIGNATURE or len(raw) < 512:
        raise ValueError("not an OLE compound document")
    sector_shift, mini_shift = struct.unpack_from("<HH", raw, 0x1E)
    if sector_shift not in (9, 12) or mini_shift != 6:
        raise ValueError("unsupported compound document sector size")
    size = 1 << sector_shift
    (num_fat, first_dir, _transaction, cutoff, first_minifat, _num_minifat,
     first_difat, num_difat) = struct.unpack_from("<8I", raw, 0x2C)
    sector_count = max(0, (len(raw) - size) // size + (1 if (len(raw) - size) % size else 0))

    def sector(index):
        if index >= sector_count:
            raise ValueError("compound document sector out of range")
        start = (index + 1) * size
        return raw[start:start + size].ljust(size, b"\0")

    fat_sectors = [value for value in struct.unpack_from("<109I", raw, 0x4C)]
    next_difat, seen = first_difat, set()
    while next_difat < 0xFFFFFFFA and len(fat_sectors) < num_fat + 109:
        if next_difat in seen:
            raise ValueError("compound document DIFAT loop")
        seen.add(next_difat)
        values = struct.unpack(f"<{size // 4}I", sector(next_difat))
        fat_sectors.extend(values[:-1])
        next_difat = values[-1]
    fat = []
    for index in fat_sectors[:num_fat]:
        if index >= 0xFFFFFFFA:
            break
        fat.extend(struct.unpack(f"<{size // 4}I", sector(index)))

    def chain(start, table):
        ids, seen = [], set()
        while start < 0xFFFFFFFA:
            if start in seen or start >= len(table):
                raise ValueError("corrupt compound document sector chain")
            seen.add(start)
            ids.append(start)
            start = table[start]
        return ids

    directory = b"".join(sector(index) for index in chain(first_dir, fat))
    entries = []
    for offset in range(0, len(directory) - 127, 128):
        name_len, kind = struct.unpack_from("<HB", directory, offset + 64)
        left, right, child = struct.unpack_from("<III", directory, offset + 68)
        start, stream_size = struct.unpack_from("<IQ", directory, offset + 116)
        if sector_shift == 9:
            stream_size &= 0xFFFFFFFF
        name = directory[offset:offset + max(0, min(name_len, 64) - 2)].decode("utf-16-le", errors="replace")
        entries.append((name, kind, left, right, child, start, stream_size))
    if not entries or entries[0][1] != 5:
        raise ValueError("compound document has no root entry")
    root = entries[0]
    mini_stream = b"".join(sector(index) for index in chain(root[5], fat))[:root[6]] if root[6] else b""
    minifat = []
    for index in chain(first_minifat, fat) if first_minifat < 0xFFFFFFFA else []:
        minifat.extend(struct.unpack(f"<{size // 4}I", sector(index)))

    def read(start, stream_size):
        if stream_size < cutoff:
            data = b"".join(mini_stream[i * 64:(i + 1) * 64] for i in chain(start, minifat))
        else:
            data = b"".join(sector(i) for i in chain(start, fat))
        return data[:stream_size]

    streams, pending, visited = {}, [root[4]], set()
    while pending:
        index = pending.pop()
        if index == _CFB_NOSTREAM or index in visited or index >= len(entries):
            continue
        visited.add(index)
        name, kind, left, right, _child, start, stream_size = entries[index]
        pending.extend((left, right))
        if kind == 2:
            streams[name] = (start, stream_size)
    return {name: read(*location) for name, location in streams.items() if name in {"WordDocument", "0Table", "1Table"}}


def _clean_doc_text(text):
    """Drop field instructions (keep displayed results) and map Word's
    control characters: paragraph/line/page marks to newlines, cell marks to tabs."""
    out, fields = [], []
    for char in text:
        if char == "\x13":
            fields.append(False)
        elif char == "\x14":
            if fields:
                fields[-1] = True
        elif char == "\x15":
            if fields:
                fields.pop()
        elif all(fields):
            out.append(char)
    text = "".join(out).replace("\r\x07", "\x07").replace("\x07\x07", "\n").replace("\x07", "\t")
    text = re.sub(r"[\r\x0b\x0c\x0e]", "\n", text).replace("\x1e", "-").replace("\x1f", "")
    text = re.sub(r"[\x00-\x08\x10-\x1f]", "", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_doc_text(raw):
    """Word 97-2003 .doc main-document text from the piece table (MS-DOC).
    Encrypted and pre-97 (Word 6/95) files are rejected."""
    streams = _cfb_root_streams(raw)
    word = streams.get("WordDocument") or b""
    if len(word) < 0x200:
        raise ValueError("not a Word 97-2003 document")
    ident, nfib = struct.unpack_from("<HH", word, 0)
    flags = struct.unpack_from("<H", word, 0x0A)[0]
    if ident != 0xA5EC:
        raise ValueError("not a Word 97-2003 document")
    if nfib < 0xC0:
        raise ValueError("Word 6/95 documents are not supported; save as .docx")
    if flags & 0x0100:
        raise ValueError("encrypted Word documents are not supported")
    table = streams.get("1Table" if flags & 0x0200 else "0Table") or b""
    csw = struct.unpack_from("<H", word, 32)[0]
    lw = 34 + csw * 2
    cslw = struct.unpack_from("<H", word, lw)[0]
    ccp_text = struct.unpack_from("<i", word, lw + 2 + 12)[0]
    rg = lw + 2 + cslw * 4
    cb_rg = struct.unpack_from("<H", word, rg)[0]
    if cb_rg < 34 or rg + 2 + 34 * 8 > len(word):
        raise ValueError("Word file information block is truncated")
    fc_clx, lcb_clx = struct.unpack_from("<II", word, rg + 2 + 33 * 8)
    clx = table[fc_clx:fc_clx + lcb_clx]
    if not clx or len(clx) < lcb_clx:
        raise ValueError("Word piece table is missing")
    pos, plc = 0, b""
    while pos < len(clx):
        if clx[pos] == 1:
            pos += 3 + struct.unpack_from("<H", clx, pos + 1)[0]
        elif clx[pos] == 2:
            length = struct.unpack_from("<I", clx, pos + 1)[0]
            plc = clx[pos + 5:pos + 5 + length]
            break
        else:
            raise ValueError("Word piece table is corrupt")
    count = (len(plc) - 4) // 12
    if count <= 0:
        raise ValueError("Word piece table is empty")
    cps = struct.unpack_from(f"<{count + 1}I", plc, 0)
    pieces, characters = [], 0
    for index in range(count):
        start, end = cps[index], min(cps[index + 1], max(ccp_text, 0))
        if start >= end:
            continue
        fc = struct.unpack_from("<I", plc, 4 * (count + 1) + 8 * index + 2)[0]
        length = end - start
        characters += length
        if characters > MAX_WORD_TEXT_CHARACTERS:
            raise ValueError("Word text exceeds 2000000 characters")
        if fc & 0x40000000:
            offset = (fc & 0x3FFFFFFF) // 2
            pieces.append(word[offset:offset + length].decode("cp1252", errors="replace"))
        else:
            offset = fc & 0x3FFFFFFF
            pieces.append(word[offset:offset + 2 * length].decode("utf-16-le", errors="replace"))
    text = _clean_doc_text("".join(pieces))
    if not text:
        raise ValueError("Word document contains no extractable text")
    return text


def sniff_image_type(raw):
    """Media type from the file signature, or "" when it is not a supported image."""
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw[:6] in {b"GIF87a", b"GIF89a"}:
        return "image/gif"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return ""


def recognize_image_text(filename, raw, media_type, timeout=120):
    """Image text + description through the internal agent's vision call;
    REPORTS_FAKE_PROVIDER keeps tests and dry runs offline."""
    from .reports import fake_provider_enabled

    if fake_provider_enabled():
        return f"## 图片文字\n\n（离线模式未识别）\n\n## 图片描述\n\n图片 {filename}（{media_type}，{len(raw)} 字节）"
    from .internal_agent import internal_image_text

    return internal_image_text(raw, media_type, timeout=timeout)


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


def summarize_prepared(prepared, timeout=120, workstreams=None):
    """One model call for a batch of prepared uploads, keyed by list index.
    Returns ({index: (summary, status, error)}, {index: workstream_id}); a
    failed call falls back to a text-start summary per file."""
    items = [
        {"id": index, "filename": item["filename"], "text_start": (item["extracted_text"] or "")[:4000]}
        for index, item in enumerate(prepared)
    ]
    if not items:
        return {}, {}
    fallbacks = {item["id"]: fallback_summary(item["filename"], item["text_start"]) for item in items}
    try:
        generated, assignments = generate_ai_summaries_and_workstreams(items, timeout, workstreams)
    except Exception as exc:
        return {key: (fallbacks[key], "failed", str(exc)[:2000]) for key in fallbacks}, {}
    summaries = {}
    for key, fallback in fallbacks.items():
        summary = (generated.get(key) or "").strip()
        if summary:
            summaries[key] = (summary[:1000], "generated", "")
        else:
            summaries[key] = (fallback, "failed", "AI summary output was missing for this file")
    return summaries, assignments


def generate_ai_summaries(items, timeout=120):
    return generate_ai_summaries_and_workstreams(items, timeout)[0]


def generate_ai_summaries_and_workstreams(items, timeout=120, workstreams=None):
    """Material summaries (and, when the project has active workstreams, a
    workstream per file) in one internal-agent call; REPORTS_FAKE_PROVIDER
    keeps tests and dry runs offline."""
    from .reports import fake_provider_enabled

    if fake_provider_enabled():
        from .workstream_agent import fake_classify

        summaries = {item["id"]: fallback_summary(item["filename"], item["text_start"]) for item in items}
        assignments = {}
        if workstreams:
            for item in items:
                assignments[item["id"]] = fake_classify(f"{item['filename']} {item['text_start']}", workstreams)
        return summaries, assignments
    from .internal_agent import internal_chat, resolve_llm_settings

    raw = internal_chat(build_summary_prompt(items, workstreams), resolve_llm_settings(), timeout=timeout, temperature=0)
    return parse_summary_output(raw, items), (parse_summary_assignments(raw, items) if workstreams else {})


def build_summary_prompt(items, workstreams=None):
    evidence = json.dumps(items, ensure_ascii=False, indent=2)
    if workstreams:
        return (
            "为每份项目资料生成简洁、客观的摘要，并归到最相关的一条工作线。只依据原始文件名和正文开头，不要补充未出现的事实。"
            "使用资料正文的主要语言，每条摘要不超过120个汉字或同等长度。无法判断工作线时 workstream_id 填 null。"
            "只输出 JSON 数组，每项严格使用 {\"id\": 数字, \"summary\": \"摘要\", \"workstream_id\": 工作线ID或null}，不要 Markdown。\n\n"
            f"工作线：\n{json.dumps(workstreams, ensure_ascii=False, indent=2)}\n\n"
            f"资料：\n{evidence}"
        )
    return (
        "为每份项目资料生成简洁、客观的摘要。只依据原始文件名和正文开头，不要补充未出现的事实。"
        "使用资料正文的主要语言，每条不超过120个汉字或同等长度。"
        "只输出 JSON 数组，每项严格使用 {\"id\": 数字, \"summary\": \"摘要\"}，不要 Markdown。\n\n"
        f"资料：\n{evidence}"
    )


def parse_summary_assignments(raw, items):
    """{material_id: workstream_id} from the summary output; entries without
    a usable id are left out."""
    value = (raw or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value, flags=re.IGNORECASE)
    try:
        data = json.loads(value)
    except ValueError:
        return {}
    if not isinstance(data, list):
        return {}
    allowed = {item["id"] for item in items}
    result = {}
    for entry in data:
        if isinstance(entry, dict) and entry.get("id") in allowed and isinstance(entry.get("workstream_id"), int):
            result[entry["id"]] = entry["workstream_id"]
    return result


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
