"""Extract user preferences from chat history using DeepSeek.

Triggered on session close. Batches last 6 exchanges, asks LLM to extract
structured preferences, persists to DB + Redis cache.
"""

from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

EXTRACTION_PROMPT = """分析以下旅行对话，提取用户明确提到的个人偏好。

分类：diet（饮食）/ schedule（作息）/ transport（交通）/ accommodation（住宿）/ taboo（禁忌）/ other（其他）

规则：
- 只提取明确提到的事实，不要推测
- 若无偏好返回空数组
- confidence 取值 0.1-1.0，根据确定性评估

输出纯 JSON 数组：
[{"category": "diet", "content": "...", "confidence": 0.8}]"""


async def extract_preferences(user_id: str, messages: list[dict]) -> list[dict]:
    recent = messages[-12:]
    if not recent:
        return []
    try:
        lines = []
        for m in recent:
            role = "用户" if m.get("role") == "user" else "AI"
            lines.append(f"{role}: {m.get('content', '')[:300]}")
        conv = "\n".join(lines)

        resp = await _get_client().chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": conv},
            ],
            temperature=0.1,
            max_tokens=400,
        )
        raw = (resp.choices[0].message.content or "").strip()
        try:
            prefs = json.loads(raw)
        except json.JSONDecodeError:
            import re
            m = re.search(r"\[[\s\S]*\]", raw)
            prefs = json.loads(m.group()) if m else []

        if not isinstance(prefs, list):
            return []
        return [p for p in prefs if isinstance(p, dict) and "category" in p]
    except Exception:
        logger.warning("extract_preferences failed", exc_info=True)
        return []


async def save_preferences(
    db: AsyncSession,
    user_id: uuid.UUID,
    prefs: list[dict],
) -> dict[str, str]:
    """Persist extracted preferences to DB and update Redis cache.

    Returns a dict mapping category → content for the Redis hot-preferences hash.
    """
    from app.models.chat import UserPreference
    from datetime import datetime, timezone

    hot: dict[str, str] = {}
    try:
        existing_hot = await redis_memory.get_hot_preferences(str(user_id)) or {}
    except Exception:
        existing_hot = {}

    keywords_to_add: set[str] = set()

    for p in prefs:
        category = p.get("category", "other")
        content = p.get("content", "")
        confidence = float(p.get("confidence", 0.5))

        if not content.strip():
            continue

        existing = await db.execute(
            select(UserPreference).where(
                UserPreference.user_id == user_id,
                UserPreference.category == category,
                UserPreference.content == content,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.mention_count += 1
            row.confidence = min(1.0, row.confidence + 0.1)
            row.last_mentioned_at = datetime.now(timezone.utc)
            row.is_active = True
        else:
            db.add(UserPreference(
                user_id=user_id,
                category=category,
                content=content,
                confidence=confidence,
                mention_count=1,
            ))

        hot[category] = content
        for word in content.replace("，", ",").replace("、", ",").split(","):
            w = word.strip()
            if w and len(w) >= 2:
                keywords_to_add.add(f"{category}:{w}")

    await db.commit()

    if hot:
        try:
            await redis_memory.set_hot_preferences(str(user_id), hot)
        except Exception:
            logger.warning("Redis hot prefs update failed", exc_info=True)

    if keywords_to_add:
        try:
            existing_kw = await redis_memory.get_preference_keywords(str(user_id))
            all_kw = existing_kw | keywords_to_add
            await redis_memory.set_preference_keywords(str(user_id), list(all_kw))
        except Exception:
            logger.warning("Redis keywords update failed", exc_info=True)

    return hot
