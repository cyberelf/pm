import json
import os
import re
import tempfile
from pathlib import Path

from .todos import create_todo
from .validation import ValidationError

MAX_VOICE_TEXT_LENGTH = 4000
MAX_VOICE_TODO_ITEMS = 10


def create_todos_from_voice(conn, text, provider, timeout=120):
    transcript = (text or "").strip()
    if not transcript:
        raise ValidationError("voice transcript is required")
    transcript = transcript[:MAX_VOICE_TEXT_LENGTH]
    items, error = convert_transcript_to_todos(transcript, provider, timeout)
    created = [create_todo(conn, item) for item in items]
    return {"ids": created, "fallback": bool(error), "error": error}


def convert_transcript_to_todos(transcript, provider, timeout=120):
    """Returns (items, error). When the agent CLI fails, error explains why and
    items fall back to TODOs built from the raw transcript so nothing is lost."""
    from .reports import fake_provider_enabled, provider_command, run_provider_command

    if fake_provider_enabled():
        return fallback_voice_items(transcript), ""
    prompt = build_voice_todo_prompt(transcript)
    try:
        with tempfile.TemporaryDirectory(prefix="voice-todo-") as tmp:
            tmp_path = Path(tmp)
            output_path = (tmp_path / "todos.json").resolve()
            command = provider_command(provider, prompt, tmp_path, output_path)
            if provider == "claude" and not os.environ.get("REPORTS_CLAUDE_CMD"):
                result = run_provider_command(command, tmp, timeout, input_text=prompt)
                raw = result.stdout
            else:
                result = run_provider_command(command, tmp, timeout)
                raw = output_path.read_text(encoding="utf-8") if output_path.exists() else result.stdout
        return parse_voice_todo_output(raw), ""
    except Exception as exc:
        return fallback_voice_items(transcript), str(exc)[:2000]


def build_voice_todo_prompt(transcript):
    return (
        "把下面的语音转写整理成待办事项（TODO）。"
        "每条 TODO 的标题简明扼要（不超过 50 个汉字，使用转写的主要语言），"
        "转写中的细节、背景和时间要求放进 description，保持原始含义，不要编造转写之外的事实。"
        "如果转写包含多个独立任务，拆分成多条 TODO；否则只输出一条。"
        "只输出 JSON 数组，每项严格使用 {\"title\": \"标题\", \"description\": \"补充说明\"}，不要 Markdown。\n\n"
        f"语音转写：\n{transcript}"
    )


def parse_voice_todo_output(raw):
    value = (raw or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value, flags=re.IGNORECASE)
    data = json.loads(value)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("voice TODO output must be a JSON object or array")
    items = []
    for entry in data[:MAX_VOICE_TODO_ITEMS]:
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title") or "").strip()
        if not title:
            continue
        items.append({
            "title": title[:200],
            "description": str(entry.get("description") or "").strip()[:4000],
        })
    if not items:
        raise ValueError("voice TODO output contained no usable items")
    return items


def fallback_voice_items(transcript):
    lines = [line.strip() for line in transcript.splitlines() if line.strip()]
    if len(lines) > 1:
        return [{"title": line[:200], "description": line} for line in lines]
    title = next((part.strip() for part in re.split(r"[。；;！!？?]", transcript) if part.strip()), "")
    if not title:
        title = transcript
    return [{"title": title[:200], "description": transcript}]
