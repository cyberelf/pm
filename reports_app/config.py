from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "reports.sqlite3"
STATIC_DIR = ROOT_DIR / "static"

WORKSPACE_USER = "local-user"
SUPPORTED_PROVIDERS = {"codex", "claude"}
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
