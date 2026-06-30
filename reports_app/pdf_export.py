import hashlib
import html
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from .config import DATA_DIR
from .markdown import render_markdown


CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
)
PDF_CACHE_DIR = DATA_DIR / "pdf_cache"


def find_chrome():
    for candidate in CHROME_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return str(path)
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def report_pdf_bytes(project_id, project, report):
    path = cached_pdf_path(project_id, report)
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    chrome = find_chrome()
    if not chrome:
        raise RuntimeError("Chrome or Chromium is required for server-side PDF export")
    html_text = build_report_pdf_html(project, report)
    pdf = render_pdf_with_chrome(chrome, html_text)
    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf)
    return pdf


def cached_pdf_path(project_id, report):
    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    identity = f"{project_id}:{report['id']}:{report['week_key']}:{report['updated_at']}:{report['latest_job_id']}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    safe_week = re.sub(r"[^A-Za-z0-9._-]+", "-", report["week_key"]).strip("-") or "week"
    return PDF_CACHE_DIR / f"project-{project_id}-{safe_week}-{digest}.pdf"


def render_pdf_with_chrome(chrome, html_text, timeout=30):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "report.html"
        pdf_path = tmp_path / "report.pdf"
        profile_path = tmp_path / "chrome-profile"
        html_path.write_text(html_text, encoding="utf-8")
        command = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-component-update",
            "--disable-dev-shm-usage",
            "--remote-debugging-port=0",
            f"--user-data-dir={profile_path}",
            f"--print-to-pdf={pdf_path}",
            f"file://{html_path}",
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            wait_for_pdf(pdf_path, process, timeout)
            return pdf_path.read_bytes()
        finally:
            stop_process_group(process)


def wait_for_pdf(pdf_path, process, timeout):
    deadline = time.monotonic() + timeout
    last_size = -1
    stable_since = None
    while time.monotonic() < deadline:
        if pdf_path.exists():
            size = pdf_path.stat().st_size
            if size > 0 and size == last_size:
                stable_since = stable_since or time.monotonic()
                if time.monotonic() - stable_since >= 0.6:
                    return
            elif size > 0:
                last_size = size
                stable_since = time.monotonic()
        if process.poll() is not None:
            break
        time.sleep(0.2)
    if pdf_path.exists() and pdf_path.stat().st_size > 0:
        return
    stdout, stderr = process.communicate(timeout=1)
    detail = (stderr or stdout or "unknown PDF export failure").strip()
    raise RuntimeError(detail)


def stop_process_group(process):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return


def build_report_pdf_html(project, report):
    title = f"{project['name']} {report['week_key']} 周报"
    rendered = render_markdown(report["content_md"])
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <title>{html.escape(title)}</title>
    <style>
      @page {{
        size: A4;
        margin: 18mm 16mm;
      }}
      * {{
        box-sizing: border-box;
      }}
      body {{
        margin: 0;
        color: #1f2933;
        background: #ffffff;
        font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif;
        font-size: 12.5pt;
        line-height: 1.62;
      }}
      header {{
        border-bottom: 1px solid #d8dee6;
        margin-bottom: 18px;
        padding-bottom: 12px;
      }}
      header h1 {{
        margin: 0 0 6px;
        font-size: 22pt;
        line-height: 1.2;
      }}
      header p {{
        margin: 0;
        color: #667085;
        font-size: 10.5pt;
      }}
      h1, h2, h3, h4, h5, h6 {{
        color: #17202a;
        page-break-after: avoid;
      }}
      h1 {{ font-size: 20pt; margin: 24px 0 10px; }}
      h2 {{ font-size: 16pt; margin: 22px 0 8px; }}
      h3 {{ font-size: 13.5pt; margin: 18px 0 6px; }}
      p {{ margin: 8px 0; }}
      ul {{ margin: 8px 0 8px 20px; padding: 0; }}
      li {{ margin: 4px 0; }}
      code {{
        font-family: Menlo, Consolas, monospace;
        font-size: 10.5pt;
        background: #eef2f6;
        padding: 1px 4px;
        border-radius: 4px;
      }}
      pre {{
        white-space: pre-wrap;
        background: #f4f6f8;
        border: 1px solid #d8dee6;
        border-radius: 6px;
        padding: 10px;
        overflow-wrap: anywhere;
      }}
      .report {{
        max-width: 100%;
      }}
    </style>
  </head>
  <body>
    <header>
      <h1>{html.escape(project["name"])}</h1>
      <p>{html.escape(report["week_key"])} · Weekly Report</p>
    </header>
    <main class="report">{rendered}</main>
  </body>
</html>
"""


def pdf_filename(project_name, week_key):
    safe_project = re.sub(r"[^A-Za-z0-9._-]+", "-", project_name).strip("-") or "project"
    safe_week = re.sub(r"[^A-Za-z0-9._-]+", "-", week_key).strip("-") or "week"
    return f"{safe_project}-{safe_week}-weekly-report.pdf"
