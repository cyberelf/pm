import re
import shutil
from pathlib import Path

from .config import SUPPORTED_MATERIAL_EXTENSIONS, SUPPORTED_PROVIDERS
from .timeutil import get_zone


REPO_RE = re.compile(r"^(?:https://github\.com/)?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class ValidationError(ValueError):
    pass


def require_project_name(data):
    if not (data.get("name") or "").strip():
        raise ValidationError("project name is required")


def validate_provider(provider):
    if provider not in SUPPORTED_PROVIDERS:
        raise ValidationError("unsupported report provider")


def validate_timezone(tz_name):
    get_zone(tz_name)


def validate_schedule_item(item):
    weekday = int(item.get("weekday", 0))
    if weekday < 1 or weekday > 7:
        raise ValidationError("weekday must be 1-7")
    local_time = item.get("local_time", "")
    if not TIME_RE.match(local_time):
        raise ValidationError("local_time must be HH:MM")
    validate_timezone(item.get("timezone") or "Asia/Shanghai")


def validate_repo(repo):
    value = (repo or "").strip()
    if not REPO_RE.match(value):
        raise ValidationError("invalid GitHub repository; use owner/name")
    return value.replace("https://github.com/", "").rstrip("/")


def validate_material_filename(filename):
    ext = Path(filename or "").suffix.lower()
    if ext not in SUPPORTED_MATERIAL_EXTENSIONS:
        raise ValidationError("unsupported file type; upload Markdown, plain text, or PDF")
    return ext


def gh_status():
    if not shutil.which("gh"):
        return "missing", "local GitHub CLI (`gh`) is not installed"
    return "available", "local GitHub CLI is available"

