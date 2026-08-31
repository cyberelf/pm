import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

from .config import (
    GIT_MODE_GITHUB,
    GIT_MODE_GITLAB,
    SUPPORTED_GIT_MODES,
    SUPPORTED_MATERIAL_EXTENSIONS,
    SUPPORTED_PROVIDERS,
    TRACK_ALL_BRANCHES,
)
from .timeutil import get_zone


REPO_RE = re.compile(r"^(?:https://github\.com/)?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$")
GITLAB_REPO_RE = re.compile(r"^(?:https?://[^/]+/)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+){1,4}/?$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
BRANCH_RE = re.compile(r"^[^\s~^:?*\[\\\]\x00-\x1f\x7f]+(?:/[^\s~^:?*\[\\\]\x00-\x1f\x7f]+)*$")


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


def validate_git_mode(git_mode):
    value = (git_mode or GIT_MODE_GITHUB).strip() or GIT_MODE_GITHUB
    if value not in SUPPORTED_GIT_MODES:
        raise ValidationError("invalid git mode; use github or gitlab")
    return value


def validate_repo(repo, git_mode=GIT_MODE_GITHUB):
    value = (repo or "").strip()
    git_mode = validate_git_mode(git_mode)
    if git_mode == GIT_MODE_GITLAB:
        if not GITLAB_REPO_RE.match(value):
            raise ValidationError("invalid GitLab repository; use group/project or group/sub-group/project")
        value = re.sub(r"^[A-Za-z][A-Za-z0-9+.-]*://[^/]+/", "", value)
        return value.rstrip("/").removesuffix(".git")
    if not REPO_RE.match(value):
        raise ValidationError("invalid GitHub repository; use owner/name")
    return value.replace("https://github.com/", "").rstrip("/")


def gitlab_server_from_url(repo):
    match = re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://([^/]+?)/", (repo or "").strip())
    if not match:
        return ""
    return validate_gitlab_server(match.group(1))


def validate_gitlab_server(server):
    value = (server or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError("invalid GitLab server address; use http(s)://host[:port]")
    return f"{parsed.scheme}://{parsed.netloc}"


def validate_branches(branches):
    result = []
    for branch in branches or []:
        value = str(branch or "").strip()
        if not value:
            continue
        if value != TRACK_ALL_BRANCHES and (
            len(value) > 200 or not BRANCH_RE.match(value) or value.endswith(".") or ".." in value
        ):
            raise ValidationError("invalid branch name")
        if value not in result:
            result.append(value)
    return [TRACK_ALL_BRANCHES] if TRACK_ALL_BRANCHES in result else result


def validate_material_filename(filename):
    ext = Path(filename or "").suffix.lower()
    if ext not in SUPPORTED_MATERIAL_EXTENSIONS:
        raise ValidationError("unsupported file type; upload Markdown, plain text, or PDF")
    return ext


def gh_status():
    if not shutil.which("gh"):
        return "missing", "local GitHub CLI (`gh`) is not installed"
    return "available", "local GitHub CLI is available"
