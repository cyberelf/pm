"""In-process internal agent: LLM calls through langchain-bound providers.

The internal agent replaces the Codex/Claude CLI handoff with direct chat
invocations. Which provider (openai or anthropic) serves the calls, its
endpoint, API key, and model come from app settings (with the provider's
standard API-key environment variable as fallback). langchain's provider
integration classes perform the actual binding so both providers share
one call surface. langchain imports stay lazy so the rest of the app
works without the optional dependency installed.
"""

import os

from .config import (
    DEFAULT_LLM_BASE_URLS,
    DEFAULT_LLM_PROVIDER,
    LLM_API_KEY_ENV_VARS,
    LLM_API_KEY_SETTING,
    LLM_BASE_URL_SETTING,
    LLM_MODEL_SETTING,
    LLM_PROVIDER_SETTING,
    LLM_REPORT_MAX_TOKENS,
    LLM_VOICE_MAX_TOKENS,
    SUPPORTED_LLM_PROVIDERS,
)
from .db import connect, get_setting
from .validation import ValidationError


def resolve_llm_settings(conn=None):
    """Read LLM provider settings; stored values win, the provider's
    standard API-key environment variable fills in a missing key."""
    own_conn = conn is None
    if own_conn:
        conn = connect()
    try:
        settings = {
            "provider": get_setting(conn, LLM_PROVIDER_SETTING, DEFAULT_LLM_PROVIDER),
            "base_url": (get_setting(conn, LLM_BASE_URL_SETTING, "") or "").strip(),
            "api_key": get_setting(conn, LLM_API_KEY_SETTING, ""),
            "model": (get_setting(conn, LLM_MODEL_SETTING, "") or "").strip(),
        }
    finally:
        if own_conn:
            conn.close()
    if settings["provider"] not in SUPPORTED_LLM_PROVIDERS:
        settings["provider"] = DEFAULT_LLM_PROVIDER
    if not settings["base_url"]:
        settings["base_url"] = DEFAULT_LLM_BASE_URLS[settings["provider"]]
    if not settings["api_key"]:
        env_var = LLM_API_KEY_ENV_VARS[settings["provider"]]
        settings["api_key"] = os.environ.get(env_var, "")
    return settings


def llm_api_key_configured(conn=None):
    settings = resolve_llm_settings(conn)
    return bool(settings["api_key"])


def validate_llm_settings(settings):
    if not settings["model"]:
        raise ValidationError("LLM model is not configured; set it in 全局设置")
    if not settings["api_key"]:
        env_var = LLM_API_KEY_ENV_VARS[settings["provider"]]
        raise ValidationError(f"LLM API key is not configured; set it in 全局设置 or export {env_var}")
    return settings


def build_chat_model(settings, timeout, max_tokens, temperature=None):
    kwargs = {
        "model": settings["model"],
        "api_key": settings["api_key"],
        "base_url": settings["base_url"],
        "timeout": timeout,
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    if settings["provider"] == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(**kwargs)
    if settings["provider"] == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(**kwargs)
    raise ValidationError("unsupported LLM provider; use openai or anthropic")


def response_text(response):
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content.strip()
    parts = []
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text") or ""))
        elif isinstance(block, str):
            parts.append(block)
    return "\n".join(parts).strip()


def internal_chat(prompt, settings, timeout=120, max_tokens=4096, temperature=None):
    """Run one chat completion through the configured provider and return
    the response text."""
    validate_llm_settings(settings)
    model = build_chat_model(settings, timeout=timeout, max_tokens=max_tokens, temperature=temperature)
    from langchain_core.messages import HumanMessage

    try:
        response = model.invoke([HumanMessage(content=prompt)])
    except Exception as exc:
        raise RuntimeError(f"internal agent LLM call failed: {exc}") from exc
    return response_text(response)


def internal_voice_todo_items(transcript, timeout=120):
    """Structure a voice transcript into TODO items with the internal agent."""
    from .voice_todos import build_voice_todo_prompt, parse_voice_todo_output

    prompt = build_voice_todo_prompt(transcript)
    settings = resolve_llm_settings()
    raw = internal_chat(prompt, settings, timeout=timeout, max_tokens=LLM_VOICE_MAX_TOKENS, temperature=0)
    return parse_voice_todo_output(raw)


def generate_internal_report(context, timeout=300):
    """Generate the weekly report with the internal agent; returns Markdown.

    The prompt carries the same bounded evidence the platform already
    assembled, so the internal agent needs no tool execution."""
    from .reports import build_internal_evidence_prompt

    settings = resolve_llm_settings()
    prompt = build_internal_evidence_prompt(context)
    output = internal_chat(prompt, settings, timeout=timeout, max_tokens=LLM_REPORT_MAX_TOKENS)
    if not output.strip():
        raise RuntimeError("internal agent returned an empty report")
    return output
