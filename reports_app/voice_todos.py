import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

from .asr import transcribe_audio, validate_asr_audio
from .db import connect
from .todos import create_todo
from .timeutil import iso_now
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


def create_todos_from_voice_audio(conn, payload, provider, asr_endpoint, asr_model, timeout=180):
    """Transcribes an uploaded recording through the configured ASR service,
    then structures the transcript into TODO items. Returns (result, transcript)."""
    raw, content_type = validate_asr_audio(payload)
    try:
        transcript = transcribe_audio(raw, content_type, asr_endpoint, asr_model, timeout)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"voice transcription failed: {exc}") from exc
    return create_todos_from_voice(conn, transcript, provider, timeout), transcript


def create_voice_job(conn):
    now = iso_now()
    cur = conn.execute(
        "INSERT INTO voice_jobs (status, created_at, updated_at) VALUES ('transcribing', ?, ?)",
        (now, now),
    )
    return cur.lastrowid


def get_voice_job(conn, job_id):
    row = conn.execute("SELECT * FROM voice_jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise ValidationError("voice job not found")
    item = dict(row)
    item["todo_ids"] = json.loads(item.pop("todo_ids_json") or "[]")
    return item


def get_active_voice_job(conn):
    row = conn.execute(
        "SELECT id FROM voice_jobs WHERE status IN ('transcribing', 'structuring') ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return get_voice_job(conn, row["id"]) if row else None


def cancel_voice_job(conn, job_id):
    cur = conn.execute(
        "UPDATE voice_jobs SET status = 'cancelled', updated_at = ? WHERE id = ? AND status IN ('transcribing', 'structuring')",
        (iso_now(), job_id),
    )
    if cur.rowcount != 1:
        row = conn.execute("SELECT status FROM voice_jobs WHERE id = ?", (job_id,)).fetchone()
        state = row["status"] if row else "not found"
        raise ValidationError(f"voice job is {state}; only running jobs can be cancelled")
    return job_id


def fail_stale_voice_jobs(db_path):
    """Jobs stuck mid-flight belong to worker threads from a previous
    process; after a restart they can never finish, so the single-task
    lock must not keep blocking new submissions."""
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE voice_jobs SET status = 'failed', error = 'interrupted by service restart', updated_at = ? WHERE status IN ('transcribing', 'structuring')",
            (iso_now(),),
        )
        conn.commit()


def _log_voice_job(job_id, message):
    print(f"voice job {job_id}: {message}", file=sys.stdout, flush=True)


def _voice_job_status(conn, job_id):
    row = conn.execute("SELECT status FROM voice_jobs WHERE id = ?", (job_id,)).fetchone()
    return row["status"] if row else None


def _update_voice_job(conn, job_id, **fields):
    if not fields:
        return
    assignments = ", ".join(f"{name} = ?" for name in fields)
    conn.execute(
        f"UPDATE voice_jobs SET {assignments}, updated_at = ? WHERE id = ?",
        (*fields.values(), iso_now(), job_id),
    )


def run_voice_job(db_path, job_id, payload, voice_agent, asr_endpoint, asr_model):
    """Background worker: transcribe the recording, structure it into TODO
    items, and record stage timings so failures are diagnosable from
    server.log. Opens its own database connection."""
    started = time.monotonic()
    try:
        if payload.get("audio_base64"):
            raw, content_type = validate_asr_audio(payload)
            _log_voice_job(job_id, f"transcribing {len(raw)} bytes via {asr_endpoint}")
            transcript_started = time.monotonic()
            transcript = transcribe_audio(raw, content_type, asr_endpoint, asr_model, timeout=120)
            _log_voice_job(
                job_id,
                f"transcript ready in {time.monotonic() - transcript_started:.1f}s ({len(transcript)} chars): {transcript[:120]}",
            )
        else:
            transcript = (payload.get("text") or "").strip()[:MAX_VOICE_TEXT_LENGTH]
            if not transcript:
                raise ValidationError("voice transcript is required")
            _log_voice_job(job_id, f"using submitted text transcript ({len(transcript)} chars)")
        if not transcript:
            raise ValidationError("voice transcript is required")
        with connect(db_path) as conn:
            if _voice_job_status(conn, job_id) == "cancelled":
                _log_voice_job(job_id, "cancelled after transcription; discarding transcript")
                _update_voice_job(conn, job_id, transcript=transcript)
                conn.commit()
                return
            _update_voice_job(conn, job_id, status="structuring", transcript=transcript)
            conn.commit()
        structure_started = time.monotonic()
        items, error = convert_transcript_to_todos(transcript[:MAX_VOICE_TEXT_LENGTH], voice_agent)
        with connect(db_path) as conn:
            if _voice_job_status(conn, job_id) == "cancelled":
                _log_voice_job(job_id, "cancelled during structuring; discarding results")
                conn.commit()
                return
            created = [create_todo(conn, item) for item in items]
            _update_voice_job(
                conn,
                job_id,
                status="completed",
                fallback=1 if error else 0,
                error=error[:2000],
                todo_ids_json=json.dumps(created),
            )
            conn.commit()
        _log_voice_job(
            job_id,
            f"completed in {time.monotonic() - started:.1f}s, created {len(created)} todo(s)"
            + (f" with fallback ({error[:200]})" if error else ""),
        )
    except Exception as exc:
        _log_voice_job(job_id, f"failed after {time.monotonic() - started:.1f}s: {exc}")
        try:
            with connect(db_path) as conn:
                if _voice_job_status(conn, job_id) != "cancelled":
                    _update_voice_job(conn, job_id, status="failed", error=str(exc)[:2000])
                    conn.commit()
        except Exception:
            pass


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
