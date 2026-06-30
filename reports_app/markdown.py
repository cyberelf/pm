import html
import re

try:
    from markdown_it import MarkdownIt
except ImportError:
    MarkdownIt = None

try:
    import markdown as markdown_lib
except ImportError:
    markdown_lib = None

MARKDOWN_EXTENSIONS = ["extra", "sane_lists", "nl2br"]
MARKDOWN_IT = (
    MarkdownIt("gfm-like", {"html": False, "linkify": True}).enable("table")
    if MarkdownIt
    else None
)


def render_markdown(md: str) -> str:
    """Render Markdown while escaping raw HTML before conversion.

    The preferred path uses markdown-it-py for tables, nested lists,
    blockquotes, fenced code, and horizontal rules. Raw HTML is escaped before
    Markdown expansion, so generated reports cannot execute scripts.
    """
    safe_md = md or ""
    if MARKDOWN_IT:
        return MARKDOWN_IT.render(safe_md)
    safe_md = escape_raw_html(safe_md)
    if markdown_lib:
        return markdown_lib.markdown(
            safe_md,
            extensions=MARKDOWN_EXTENSIONS,
            output_format="html5",
        )
    return fallback_render_markdown(safe_md)


def escape_raw_html(md: str) -> str:
    return re.sub(r"</?[A-Za-z][^>\n]*>", lambda match: html.escape(match.group(0)), md)


def fallback_render_markdown(md: str) -> str:
    escaped_lines = [html.escape(line.rstrip()) for line in (md or "").splitlines()]
    out = []
    in_ul = False
    in_code = False
    code_lines = []
    for line in escaped_lines:
        if line.strip().startswith("```"):
            if in_code:
                out.append("<pre><code>" + "\n".join(code_lines) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                if in_ul:
                    out.append("</ul>")
                    in_ul = False
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            if in_ul:
                out.append("</ul>")
                in_ul = False
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            continue
        item = re.match(r"^[-*]\s+(.*)$", line)
        if item:
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(item.group(1))}</li>")
            continue
        if in_ul:
            out.append("</ul>")
            in_ul = False
        out.append(f"<p>{inline(line)}</p>")
    if in_code:
        out.append("<pre><code>" + "\n".join(code_lines) + "</code></pre>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def inline(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", value)
    return value
