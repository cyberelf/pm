import html
import re


def render_markdown(md: str) -> str:
    """Small sanitized Markdown renderer for the local MVP.

    Raw HTML is escaped before Markdown expansion, so generated reports cannot
    execute scripts through the report view.
    """
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

