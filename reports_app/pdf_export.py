import html
import re

from .markdown import render_markdown


def build_report_print_html(project, report):
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
      .print-actions {{
        position: sticky;
        top: 0;
        margin: -8px -8px 18px;
        padding: 10px 8px;
        background: #ffffff;
        border-bottom: 1px solid #d8dee6;
      }}
      .print-actions button {{
        border: 1px solid #b8c2cc;
        border-radius: 6px;
        background: #1f2933;
        color: #ffffff;
        padding: 8px 12px;
        cursor: pointer;
      }}
      @media print {{
        .print-actions {{
          display: none;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="print-actions">
      <button onclick="window.print()">导出 PDF</button>
    </div>
    <header>
      <h1>{html.escape(project["name"])}</h1>
      <p>{html.escape(report["week_key"])} · Weekly Report</p>
    </header>
    <main class="report">{rendered}</main>
    <script>
      window.addEventListener("load", () => setTimeout(() => window.print(), 250));
    </script>
  </body>
</html>
"""


def pdf_filename(project_name, week_key):
    safe_project = re.sub(r"[^A-Za-z0-9._-]+", "-", project_name).strip("-") or "project"
    safe_week = re.sub(r"[^A-Za-z0-9._-]+", "-", week_key).strip("-") or "week"
    return f"{safe_project}-{safe_week}-weekly-report.pdf"
