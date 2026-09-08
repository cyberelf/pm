import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "reports.sqlite3"
STATIC_DIR = ROOT_DIR / "static"
ENV_FILE = ROOT_DIR / ".env"


def load_env_file(path=None):
    """Load KEY=VALUE pairs from a .env file into os.environ.

    Variables already present in the environment always win, so a real
    environment (LaunchAgent plist, shell export) overrides the file.
    Returns the mapping of variables applied from the file.
    """
    applied = {}
    try:
        lines = Path(path or ENV_FILE).read_text(encoding="utf-8").splitlines()
    except OSError:
        return applied
    for line in lines:
        entry = line.strip()
        if not entry or entry.startswith("#") or "=" not in entry:
            continue
        key, _, value = entry.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if not key or key in os.environ:
            continue
        os.environ[key] = value
        applied[key] = value
    return applied

WORKSPACE_USER = "local-user"
BOOTSTRAP_ADMIN_USERNAME = "darren"
ADMIN_PASSWORD_ENV_VAR = "REPORTS_ADMIN_PASSWORD"
DEFAULT_ADMIN_PASSWORD = "changeme"
SUPPORTED_PROVIDERS = {"internal"}
INTERNAL_AGENT = "internal"
REPORT_PROVIDER = INTERNAL_AGENT
SUPPORTED_LLM_PROVIDERS = {"openai", "anthropic"}
LLM_PROVIDER_SETTING = "llm_provider"
LLM_BASE_URL_SETTING = "llm_base_url"
LLM_API_KEY_SETTING = "llm_api_key"
LLM_MODEL_SETTING = "llm_model"
DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_LLM_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
}
LLM_API_KEY_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}
LLM_REPORT_MAX_TOKENS = 16000
LLM_VOICE_MAX_TOKENS = 4096
QUEUE_CAPACITY_SETTING = "queue_capacity"
QUEUE_PARALLELISM_SETTING = "queue_parallelism"
DEFAULT_QUEUE_CAPACITY = 5
DEFAULT_QUEUE_PARALLELISM = 2
MAX_QUEUE_CAPACITY = 20
MAX_QUEUE_PARALLELISM = 4
QUEUE_CAPACITY_ENV_VAR = "REPORTS_QUEUE_CAPACITY"
QUEUE_PARALLELISM_ENV_VAR = "REPORTS_QUEUE_PARALLELISM"
UI_THEME_SETTING = "ui_theme"
UI_MODE_SETTING = "ui_mode"
ASR_ENDPOINT_SETTING = "asr_endpoint"
ASR_MODEL_SETTING = "asr_model"
ASR_LANGUAGE_SETTING = "asr_language"
DEFAULT_ASR_ENDPOINT = "http://127.0.0.1:8766/inference"
DEFAULT_ASR_MODEL = "whisper"
DEFAULT_ASR_LANGUAGE = "zh"
PROJECT_STATUS_ACTIVE = "active"
PROJECT_STATUS_PAUSED = "paused"
PROJECT_STATUS_ARCHIVED = "archived"
SUPPORTED_PROJECT_STATUSES = {PROJECT_STATUS_ACTIVE, PROJECT_STATUS_PAUSED, PROJECT_STATUS_ARCHIVED}
GIT_MODE_GITHUB = "github"
GIT_MODE_GITLAB = "gitlab"
SUPPORTED_GIT_MODES = {GIT_MODE_GITHUB, GIT_MODE_GITLAB}
DEFAULT_GITLAB_SERVER = "https://gitlab.com"
GITHUB_ENABLED_SETTING = "github_enabled"
GITLAB_ENABLED_SETTING = "gitlab_enabled"
GITHUB_TOKEN_SETTING = "github_token"
GITLAB_TOKEN_SETTING = "gitlab_token"
GITLAB_URL_SETTING = "gitlab_url"
MAX_GITLAB_PAGES = 5
SUPPORTED_MATERIAL_EXTENSIONS = {".md", ".markdown", ".txt", ".pdf"}
SUPPORTED_TEXT_EXTENSIONS = {".md", ".markdown", ".txt"}
DEFAULT_TIMEZONE = "Asia/Shanghai"
TRACK_ALL_BRANCHES = "*"

DEFAULT_REPORT_TEMPLATE = """# Weekly Report

## This Week's Summary

## Completed Work

## In Progress

## Blockers and Risks

## Risk Forecast

## Next Week Plan

## GitHub Activity Summary

## Source/Input References
"""

DEFAULT_SYSTEM_PROMPT = (
    "Generate a factual weekly project report in Markdown. Use only evidence "
    "retrieved through the platform context CLI. Include observed risks and a "
    "cautious risk forecast when the evidence supports it. Do not invent facts."
)
