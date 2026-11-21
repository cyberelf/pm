"""In-process internal agent: LLM calls through the official OpenAI and
Anthropic SDKs.

The internal agent replaces the Codex/Claude CLI handoff with direct chat
invocations. Which provider (openai or anthropic) serves the calls, its
endpoint, API key, and model come from app settings (with the provider's
standard API-key environment variable as fallback). Both SDK imports stay
lazy so the rest of the app works without the optional dependencies
installed.
"""

import base64
import json
import os
import time

from .config import (
    DEFAULT_LLM_BASE_URLS,
    DEFAULT_LLM_PROVIDER,
    LLM_ANTHROPIC_MAX_OUTPUT_TOKENS,
    LLM_VISION_MAX_OUTPUT_TOKENS,
    LLM_API_KEY_ENV_VARS,
    LLM_API_KEY_SETTING,
    LLM_BASE_URL_SETTING,
    LLM_MODEL_SETTING,
    LLM_PROVIDER_SETTING,
    LLM_VISION_BASE_URL_SETTING,
    LLM_VISION_MODEL_SETTING,
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
            "vision_model": (get_setting(conn, LLM_VISION_MODEL_SETTING, "") or "").strip(),
            "vision_base_url": (get_setting(conn, LLM_VISION_BASE_URL_SETTING, "") or "").strip(),
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


def build_client(settings, timeout):
    """Build the provider SDK client for one chat-completion surface."""
    if settings["provider"] == "openai":
        from openai import OpenAI

        return OpenAI(api_key=settings["api_key"], base_url=settings["base_url"], timeout=timeout)
    if settings["provider"] == "anthropic":
        from anthropic import Anthropic

        return Anthropic(api_key=settings["api_key"], base_url=settings["base_url"], timeout=timeout)
    raise ValidationError("unsupported LLM provider; use openai or anthropic")


def user_content(prompt, provider, image=None):
    """User message content; image is (media_type, raw bytes) and rides
    along inline as base64 in the provider's own image block format."""
    if image is None:
        return prompt
    media_type, raw = image
    data = base64.b64encode(raw).decode("ascii")
    if provider == "openai":
        return [
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{data}"}},
            {"type": "text", "text": prompt},
        ]
    return [
        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
        {"type": "text", "text": prompt},
    ]


def internal_chat(prompt, settings, timeout=120, temperature=None, image=None, max_tokens=None,
                  system=None, history=None):
    """Run one chat completion through the configured provider and return
    the response text. The configured model must accept images when
    image is given. history is an optional list of earlier
    {"role": "user"|"assistant", "content": str} turns placed before the
    prompt; system rides in the provider's own system slot."""
    validate_llm_settings(settings)
    client = build_client(settings, timeout=timeout)
    content = user_content(prompt, settings["provider"], image)
    messages = [{"role": item["role"], "content": item["content"]} for item in (history or [])]
    messages.append({"role": "user", "content": content})
    try:
        if settings["provider"] == "openai":
            # No max_tokens cap: reasoning models spend part of a capped
            # budget on hidden thinking blocks and can come back empty.
            if system:
                messages.insert(0, {"role": "system", "content": system})
            kwargs = {"model": settings["model"], "messages": messages}
            if temperature is not None:
                kwargs["temperature"] = temperature
            response = client.chat.completions.create(**kwargs)
            return (response.choices[0].message.content or "").strip()
        kwargs = {
            "model": settings["model"],
            # The Messages API mandates max_tokens; keep it far above the
            # report so thinking models retain budget for the visible answer.
            "max_tokens": max_tokens or LLM_ANTHROPIC_MAX_OUTPUT_TOKENS,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if temperature is not None:
            kwargs["temperature"] = temperature
        response = client.messages.create(**kwargs)
        return "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        ).strip()
    except Exception as exc:
        raise RuntimeError(f"internal agent LLM call failed: {exc}") from exc


def _anthropic_block(block):
    """Echo an assistant content block back on the next request. model_dump
    keeps thinking signatures intact; None fields are dropped because some
    compatible endpoints reject unknown nulls."""
    if hasattr(block, "model_dump"):
        return block.model_dump(exclude_none=True)
    return dict(block)


def internal_tool_chat(prompt, settings, tools, run_tool, system=None, history=None, timeout=120,
                       max_rounds=6, temperature=None):
    """Chat with on-demand tool calls. tools are provider-neutral
    {name, description, parameters} specs; run_tool(name, args) returns the
    result text. The loop ends when the model answers without calling a
    tool; the final round forbids tools so it always ends with text.
    Returns (answer_text, trace) where trace lists each executed call."""
    validate_llm_settings(settings)
    client = build_client(settings, timeout=timeout)
    messages = [{"role": item["role"], "content": item["content"]} for item in (history or [])]
    messages.append({"role": "user", "content": prompt})
    trace = []

    def execute(name, args):
        started = time.monotonic()
        result = run_tool(name, args)
        trace.append({
            "name": name,
            "args": args,
            "ms": int((time.monotonic() - started) * 1000),
            "chars": len(result),
            "error": result.startswith('{"error"'),
        })
        return result

    try:
        if settings["provider"] == "openai":
            if system:
                messages.insert(0, {"role": "system", "content": system})
            specs = [{"type": "function", "function": spec} for spec in tools]
            for round_index in range(max_rounds + 1):
                kwargs = {"model": settings["model"], "messages": messages, "tools": specs}
                if round_index == max_rounds:
                    kwargs["tool_choice"] = "none"
                if temperature is not None:
                    kwargs["temperature"] = temperature
                message = client.chat.completions.create(**kwargs).choices[0].message
                calls = list(message.tool_calls or [])
                if not calls:
                    return (message.content or "").strip(), trace
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments or "{}"}}
                        for c in calls
                    ],
                })
                for call in calls:
                    try:
                        args = json.loads(call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": execute(call.function.name, args)})
            return "", trace
        specs = [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in tools]
        for round_index in range(max_rounds + 1):
            kwargs = {
                "model": settings["model"],
                "max_tokens": LLM_ANTHROPIC_MAX_OUTPUT_TOKENS,
                "messages": messages,
                "tools": specs,
            }
            if round_index == max_rounds:
                kwargs["tool_choice"] = {"type": "none"}
            if system:
                kwargs["system"] = system
            if temperature is not None:
                kwargs["temperature"] = temperature
            response = client.messages.create(**kwargs)
            calls = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
            text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()
            if not calls:
                return text, trace
            messages.append({"role": "assistant", "content": [_anthropic_block(b) for b in response.content]})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": c.id, "content": execute(c.name, dict(c.input or {}))}
                    for c in calls
                ],
            })
        return "", trace
    except Exception as exc:
        raise RuntimeError(f"internal agent LLM call failed: {exc}") from exc


IMAGE_RECOGNITION_PROMPT = (
    "请如实转写这张图片中所有可辨认的文字（保持原有结构，表格用 Markdown 表格），"
    "然后用一段话客观描述你实际看到的内容（如截图的界面、图表的数据趋势、照片的场景）。"
    "只描述图片中可见的信息，不要推测用途或补充背景；没有文字时在“图片文字”下写“无”，内容无法辨认时直接说明。"
    "使用图片文字的主要语言，没有文字时使用中文。"
    "只输出 Markdown：先写“## 图片文字”，再写“## 图片描述”。"
)


def internal_image_text(raw, media_type, timeout=120):
    """Recognise an uploaded image (text + description) with the configured
    vision model. Text-only report models often answer "I cannot see the
    image", which would land in report evidence, so recognition only runs
    when an image-capable model is named explicitly."""
    settings = resolve_llm_settings()
    if not settings["vision_model"]:
        raise ValidationError("image recognition model is not configured; set 图片识别模型 in 全局设置")
    settings = {**settings, "model": settings["vision_model"]}
    if settings["vision_base_url"]:
        # a dedicated vision endpoint always speaks the OpenAI-compatible protocol
        settings.update(provider="openai", base_url=settings["vision_base_url"])
    output = internal_chat(IMAGE_RECOGNITION_PROMPT, settings, timeout=timeout, temperature=0, image=(media_type, raw),
                           max_tokens=LLM_VISION_MAX_OUTPUT_TOKENS)
    if not output.strip():
        raise RuntimeError("internal agent returned no image description")
    return output


def internal_voice_todo_items(transcript, timeout=120):
    """Structure a voice transcript into TODO items with the internal agent."""
    from .voice_todos import build_voice_todo_prompt, parse_voice_todo_output

    prompt = build_voice_todo_prompt(transcript)
    settings = resolve_llm_settings()
    raw = internal_chat(prompt, settings, timeout=timeout, temperature=0)
    return parse_voice_todo_output(raw)


def generate_internal_report(context, timeout=300):
    """Generate the weekly report with the internal agent; returns Markdown.

    The prompt carries the same bounded evidence the platform already
    assembled, so the internal agent needs no tool execution."""
    from .reports import build_internal_evidence_prompt

    settings = resolve_llm_settings()
    prompt = build_internal_evidence_prompt(context)
    output = internal_chat(prompt, settings, timeout=timeout)
    if not output.strip():
        raise RuntimeError("internal agent returned an empty report")
    return output
