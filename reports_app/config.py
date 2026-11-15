import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
# 平台（服务端 + UI）版本号，独立于 PyPI 的 CLI 版本（zreport.__version__）
APP_VERSION = "1.3.13"
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
# When REPORTS_ADMIN_PASSWORD is unset at first startup the bootstrap admin
# gets a random one-time password (db.ensure_bootstrap_admin); there is no
# built-in default password on purpose.
SUPPORTED_PROVIDERS = {"internal"}
INTERNAL_AGENT = "internal"
REPORT_PROVIDER = INTERNAL_AGENT
SUPPORTED_LLM_PROVIDERS = {"openai", "anthropic"}
LLM_PROVIDER_SETTING = "llm_provider"
LLM_BASE_URL_SETTING = "llm_base_url"
LLM_API_KEY_SETTING = "llm_api_key"
LLM_MODEL_SETTING = "llm_model"
# OpenAI 兼容 /embeddings 端点用的嵌入模型；留空则 search 只做关键字检索。
# 嵌入地址默认复用 llm_base_url；LLM 走远程、嵌入走本地（如 LM Studio）时单独设置。
LLM_EMBEDDING_MODEL_SETTING = "llm_embedding_model"
# image recognition model on the same provider/endpoint/key; empty disables it
LLM_VISION_MODEL_SETTING = "llm_vision_model"
# optional OpenAI-compatible endpoint for image recognition; some Anthropic-
# compatible gateways (Zhipu /api/anthropic) silently drop image blocks
LLM_VISION_BASE_URL_SETTING = "llm_vision_base_url"
LLM_EMBEDDING_BASE_URL_SETTING = "llm_embedding_base_url"
DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_LLM_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
}
LLM_API_KEY_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}
# The Anthropic Messages API requires max_tokens (there is no unlimited
# option), and reasoning models burn budget on hidden thinking blocks.
# Keep the request at the practical output ceiling so the visible answer
# never starves.
LLM_ANTHROPIC_MAX_OUTPUT_TOKENS = 32768
# vision models cap output lower (glm-4.5v rejects anything above 16384)
LLM_VISION_MAX_OUTPUT_TOKENS = 8192
QUEUE_CAPACITY_SETTING = "queue_capacity"
QUEUE_PARALLELISM_SETTING = "queue_parallelism"
DEFAULT_QUEUE_CAPACITY = 5
DEFAULT_QUEUE_PARALLELISM = 2
MAX_QUEUE_CAPACITY = 20
MAX_QUEUE_PARALLELISM = 4
QUEUE_CAPACITY_ENV_VAR = "REPORTS_QUEUE_CAPACITY"
QUEUE_PARALLELISM_ENV_VAR = "REPORTS_QUEUE_PARALLELISM"
# 数据备份：目标目录 + 定时调度（每天 HH:MM 或每 N 小时）+ 保留份数，全部存
# app_settings，修改即时生效；调度按北京时间计算，复用 server 的分钟级调度循环。
BACKUP_ENABLED_SETTING = "backup_enabled"
BACKUP_TARGET_DIR_SETTING = "backup_target_dir"
BACKUP_SCHEDULE_TYPE_SETTING = "backup_schedule_type"
BACKUP_SCHEDULE_TIME_SETTING = "backup_schedule_time"
BACKUP_INTERVAL_HOURS_SETTING = "backup_interval_hours"
BACKUP_KEEP_SETTING = "backup_keep"
BACKUP_SCHEDULE_DAILY = "daily"
BACKUP_SCHEDULE_INTERVAL = "interval"
SUPPORTED_BACKUP_SCHEDULE_TYPES = {BACKUP_SCHEDULE_DAILY, BACKUP_SCHEDULE_INTERVAL}
DEFAULT_BACKUP_SCHEDULE_TYPE = BACKUP_SCHEDULE_DAILY
DEFAULT_BACKUP_SCHEDULE_TIME = "03:00"
DEFAULT_BACKUP_INTERVAL_HOURS = 24
DEFAULT_BACKUP_KEEP = 14
MAX_BACKUP_INTERVAL_HOURS = 168
MAX_BACKUP_KEEP = 100
# 备份子目录统一前缀，保留清理只删除匹配该命名规则的目录，不动目标目录里的其他文件
BACKUP_DIR_PREFIX = "zreport-backup-"
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
GITHUB_TOKENS_SETTING = "github_tokens"
GITLAB_TOKEN_SETTING = "gitlab_token"
GITLAB_URL_SETTING = "gitlab_url"
GITLAB_SKIP_VERIFY_SETTING = "gitlab_skip_verify"
MAX_GITLAB_PAGES = 5
# raster images only: SVG can carry script, so it is never accepted
SUPPORTED_IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
SUPPORTED_IMAGE_EXTENSIONS = set(SUPPORTED_IMAGE_TYPES)
# vision recognition is skipped above this size (Anthropic caps images at 5 MB)
MAX_IMAGE_RECOGNITION_BYTES = 5 * 1024 * 1024
SUPPORTED_MATERIAL_EXTENSIONS = {".md", ".markdown", ".txt", ".html", ".htm", ".pdf", ".xlsx", ".xls"} | SUPPORTED_IMAGE_EXTENSIONS
SUPPORTED_TEXT_EXTENSIONS = {".md", ".markdown", ".txt"}
# uploaded HTML documents get tag-stripping extraction, not the raw text decode
SUPPORTED_HTML_EXTENSIONS = {".html", ".htm"}
DEFAULT_TIMEZONE = "Asia/Shanghai"
TRACK_ALL_BRANCHES = "*"

DEFAULT_REPORT_TEMPLATE = """# 周报

## 本周总结

## 已完成工作

## 进行中

## 阻塞与风险

## 风险预测

## 下周计划

## Git 活动摘要

## 资料来源与依据
"""

DEFAULT_SYSTEM_PROMPT = (
    "你是周报生成器。严格按照用户消息中 Required Markdown structure 给出的模板生成周报："
    "保留模板中的全部章节标题、顺序与层级，不得新增、删除或重命名任何章节；"
    "周报正文必须使用模板本身的语言书写；"
    "只依据 Evidence JSON 中的证据填写内容，不要编造事实；证据不足时在对应小节如实说明。"
)
