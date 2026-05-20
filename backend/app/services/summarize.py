"""Summarize chat history using DeepSeek, cache in Redis with 30d TTL."""

from __future__ import annotations

import logging

from app.config import settings
from app.core.llm import LLM_MAX_RETRIES, LLM_TIMEOUT, _get_http_client
from app.services import redis_memory

logger = logging.getLogger(__name__)

_client: object | None = None


def _get_client():
    global _client
    if _client is None:
        from openai import AsyncOpenAI

        _client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            max_retries=LLM_MAX_RETRIES,
            timeout=LLM_TIMEOUT,
            http_client=_get_http_client(),
        )
    return _client


async def generate_summary(user_id: str, trip_id: str, messages: list[dict]) -> str | None:
    recent = messages[-12:]
    if not recent:
        return None
    try:
        lines = []
        for m in recent:
            role = "用户" if m.get("role") == "user" else "AI"
            lines.append(f"{role}: {m.get('content', '')[:200]}")
        conv = "\n".join(lines)

        resp = await _get_client().chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": "你是对话摘要助手。用≤200字中文概括旅行对话关键信息：目的地、日期、偏好、已确认事项。只输出摘要。"},
                {"role": "user", "content": conv},
            ],
            temperature=0.1,
            max_tokens=200,
        )
        summary = (resp.choices[0].message.content or "").strip()
        if summary:
            await redis_memory.set_trip_summary(user_id, trip_id, summary)
        return summary
    except Exception:
        logger.warning("generate_summary failed", exc_info=True)
        return None
