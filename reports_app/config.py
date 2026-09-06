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
SUPPORTED_PROVIDERS = {"codex", "claude", "internal"}
INTERNAL_AGENT = "internal"
VOICE_AGENT_SETTING = "voice_agent"
DEFAULT_VOICE_AGENT = "codex"
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
ASR_ENDPOINT_SETTING = "asr_endpoint"
ASR_MODEL_SETTING = "asr_model"
DEFAULT_ASR_ENDPOINT = "http://127.0.0.1:8766/inference"
DEFAULT_ASR_MODEL = "whisper"
PROJECT_STATUS_ACTIVE = "active"
PROJECT_STATUS_PAUSED = "paused"
PROJECT_STATUS_ARCHIVED = "archived"
SUPPORTED_PROJECT_STATUSES = {PROJECT_STATUS_ACTIVE, PROJECT_STATUS_PAUSED, PROJECT_STATUS_ARCHIVED}
GIT_MODE_GITHUB = "github"
GIT_MODE_GITLAB = "gitlab"
SUPPORTED_GIT_MODES = {GIT_MODE_GITHUB, GIT_MODE_GITLAB}
DEFAULT_GITLAB_SERVER = "https://gitlab.com"
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
