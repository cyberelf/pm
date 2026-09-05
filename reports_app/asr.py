import base64
import json
import uuid
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .config import DEFAULT_ASR_ENDPOINT, DEFAULT_ASR_MODEL
from .validation import ValidationError

ASR_ENDPOINT_SETTING = "asr_endpoint"
ASR_MODEL_SETTING = "asr_model"
ALLOWED_ASR_AUDIO_TYPES = {"audio/wav", "audio/x-wav", "audio/wave", "audio/mpeg", "audio/mp3", "audio/flac"}
MAX_ASR_AUDIO_BYTES = 25 * 1024 * 1024


def normalize_asr_endpoint(endpoint):
    value = (endpoint or "").strip() or DEFAULT_ASR_ENDPOINT
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError("invalid ASR endpoint; use an http(s) URL of an OpenAI-compatible transcription endpoint")
    return value


def validate_asr_audio(payload):
    """Decodes and validates an uploaded voice recording. Returns (raw_bytes, content_type)."""
    content_type = (payload.get("content_type") or "audio/wav").split(";")[0].strip().lower()
    if content_type not in ALLOWED_ASR_AUDIO_TYPES:
        raise ValidationError("unsupported voice recording format; use wav, mp3, or flac")
    try:
        raw = base64.b64decode(payload.get("audio_base64") or "", validate=True)
    except Exception as exc:
        raise ValidationError("voice recording is not valid base64") from exc
    if not raw:
        raise ValidationError("voice recording is empty")
    if len(raw) > MAX_ASR_AUDIO_BYTES:
        raise ValidationError("voice recording is too long")
    return raw, content_type


def transcribe_audio(raw, content_type, endpoint, model, timeout=120):
    """Sends audio to an OpenAI-compatible /v1/audio/transcriptions service
    and returns the transcript text."""
    boundary = f"----reports-asr-{uuid.uuid4().hex}"
    parts = []
    for name, value in (("model", model), ("response_format", "json")):
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8")
        )
    filename = "voice.wav" if content_type.endswith("wav") else f"voice{content_type.split('/')[1]}"
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
        + raw
        + b"\r\n"
    )
    body = b"".join(parts) + f"--{boundary}--\r\n".encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    text = ""
    if isinstance(result, dict):
        text = str(result.get("text") or "")
    elif isinstance(result, list):
        text = "".join(str(segment.get("text") or "") for segment in result if isinstance(segment, dict))
    return text.strip()
