"""Context Engine — layered assembly with 800-token hard cap.

Priority tiers:
  P0: System role prompt (≤150 tokens)
  P1: Relevant user preferences — keyword-matched (≤150 tokens)
  P2: Trip metadata — Redis or DB fallback (≤200 tokens)
  P3: Session history or AI summary — Redis (≤300 tokens)

When session messages exceed 6 rounds, a summary is generated and cached.
All Redis keys carry a 30-day TTL, set by redis_memory.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.config import settings
from app.core.llm import LLM_MAX_RETRIES, LLM_TIMEOUT, _get_http_client
from app.services import redis_memory

logger = logging.getLogger(__name__)

_client: Optional[object] = None


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

TOKEN_BUDGET = 800
TOKENS_PER_CHAR = 0.3
SUMMARY_ROUND_THRESHOLD = 6

SYSTEM_PROMPT = """你是"小智"，一位AI旅行伙伴。

## 性格
热情友好，博学多才，细心周到，幽默风趣。

## 能力
旅行规划、知识问答、实时建议、行程调整、文化讲解、美食推荐。

## 回答规范
- 简洁实用，优先使用已学知识和当前行程中的真实信息
- 可以给出旅行建议和方向性指导，但绝对禁止编造具体的价格、时间、地址、电话
- 不确定的信息必须诚实说明"建议出发前查询最新信息"，不要装作知道
- 适当使用emoji

{knowledge_section}
{preferences_section}
{context_section}"""
SYSTEM_PROMPT_NO_CTX = """你是"小智"，一位AI旅行伙伴。

## 性格
热情友好，博学多才，细心周到，幽默风趣。

## 能力
旅行规划、知识问答、实时建议、行程调整、文化讲解、美食推荐。

## 回答规范
- 简洁实用，可以给出旅行建议和方向性指导，但绝对禁止编造具体的价格、时间、地址、电话
- 不确定的信息必须诚实说明"建议出发前查询最新信息"，不要装作知道
- 适当使用emoji"""


def _estimate_tokens(text: str) -> int:
    return int(len(text) * TOKENS_PER_CHAR)


def _truncate_to_budget(text: str, max_tokens: int) -> str:
    if not text:
        return ""
    if _estimate_tokens(text) <= max_tokens:
        return text

    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if _estimate_tokens(text[:mid]) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1

    cut = lo
    if cut < len(text):
        last_period = text.rfind("。", max(0, cut - 60), cut)
        if last_period > 0:
            cut = last_period + 1
        else:
            last_newline = text.rfind("\n", max(0, cut - 60), cut)
            if last_newline > 0:
                cut = last_newline
    return text[:cut].rstrip()


async def _build_preferences_text(user_id: str, user_question: str) -> str:
    """Keyword-match user preferences from Redis, format ≤150 chars."""
    if not user_question.strip():
        return ""
    try:
        keywords = await redis_memory.get_preference_keywords(user_id)
        if not keywords:
            return ""
        matched_cats: set[str] = set()
        q_lower = user_question.lower()
        for kw in keywords:
            if kw.lower() in q_lower:
                cat = kw.split(":", 1)[0] if ":" in kw else "other"
                matched_cats.add(cat)
        if not matched_cats:
            return ""

        hot = await redis_memory.get_hot_preferences(user_id) or {}
        lines = []
        for cat in matched_cats:
            if cat in hot:
                lines.append(f"- {cat}: {hot[cat]}")
        if not lines:
            return ""
        raw = "已知用户偏好：\n" + "\n".join(lines)
        return _truncate_to_budget(raw, 150)
    except Exception:
        logger.warning("_build_preferences_text failed", exc_info=True)
        return ""


async def _build_meta_text(
    user_id: str, trip_id: str, trip_dict: Optional[dict] = None
) -> str:
    """Trip metadata from Redis cache or DB fallback, ≤200 tokens."""
    try:
        meta = await redis_memory.get_trip_meta(user_id, trip_id)
        if meta:
            parts = []
            if meta.get("destination"):
                parts.append(f"目的地：{meta['destination']}")
            if meta.get("dates"):
                parts.append(f"日期：{meta['dates']}")
            if meta.get("budget"):
                parts.append(f"预算：{meta['budget']}")
            if meta.get("preferences"):
                parts.append(f"偏好：{meta['preferences']}")
            raw = "\n".join(parts)
            if raw:
                return _truncate_to_budget(raw, 200)
    except Exception:
        logger.warning("Redis meta read failed", exc_info=True)

    if trip_dict:
        parts = []
        if trip_dict.get("destination"):
            parts.append(f"目的地：{trip_dict['destination']}")
        dates = trip_dict.get("dates", {})
        if dates.get("start") and dates.get("end"):
            parts.append(f"日期：{dates['start']} 至 {dates['end']}")
        budget = trip_dict.get("budget", {})
        if budget:
            parts.append(f"预算：{budget.get('min', 0)}-{budget.get('max', 0)} {budget.get('currency', 'CNY')}")
        prefs = trip_dict.get("preferences", [])
        if prefs:
            parts.append(f"偏好：{', '.join(prefs)}")
        return _truncate_to_budget("\n".join(parts), 200)
    return ""


async def _build_history_text(
    user_id: str, trip_id: str, session_id: str
) -> str:
    """Return cached summary (preferred) or recent messages, ≤300 tokens."""
    try:
        summary = await redis_memory.get_trip_summary(user_id, trip_id)
        if summary:
            return _truncate_to_budget(f"对话摘要：{summary}", 300)

        messages = await redis_memory.get_session_messages(user_id, trip_id, session_id)
        if not messages:
            return ""

        if len(messages) > SUMMARY_ROUND_THRESHOLD * 2:
            new_summary = await _generate_summary(user_id, trip_id, messages)
            if new_summary:
                await redis_memory.set_trip_summary(user_id, trip_id, new_summary)
                return _truncate_to_budget(f"对话摘要：{new_summary}", 300)

        recent = messages[-8:]
        lines = []
        for m in recent:
            role_label = "用户" if m.get("role") == "user" else "小智"
            content = m.get("content", "")[:120]
            lines.append(f"{role_label}: {content}")
        return _truncate_to_budget("\n".join(lines), 300)
    except Exception:
        logger.warning("_build_history_text failed", exc_info=True)
        return ""


async def _retrieve_knowledge(query: str, user_id: str, destination: str) -> str:
    """Retrieve relevant knowledge chunks from the vector store."""
    try:
        from app.services.vector_store import get_vector_store

        store = get_vector_store()
        if store.count() == 0:
            return ""

        search_query = query
        if destination and destination not in query:
            search_query = f"{destination} {query}"

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            lambda: store.search(search_query, n_results=3, where={"user_id": user_id}),
        )

        if not results:
            results = await loop.run_in_executor(
                None,
                lambda: store.search(search_query, n_results=2),
            )

        if not results:
            return ""

        lines = [f"{i}. {r['document'][:200]}" for i, r in enumerate(results, 1)]
        return "## 相关知识\n" + "\n".join(lines)
    except Exception:
        logger.warning("_retrieve_knowledge failed", exc_info=True)
        return ""


async def _generate_summary(
    user_id: str, trip_id: str, messages: list[dict]
) -> Optional[str]:
    """Ask DeepSeek to summarise the last 6 exchanges into ≤200 chars."""
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
                {"role": "system", "content": "你是对话摘要助手。用≤200字中文概括以下旅行对话的关键信息：目的地、日期、偏好、已确认事项。只输出摘要。"},
                {"role": "user", "content": conv},
            ],
            temperature=0.1,
            max_tokens=200,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        logger.warning("_generate_summary failed", exc_info=True)
        return None


async def build_context(
    user_id: str,
    trip_id: str,
    session_id: str,
    user_question: str,
    trip_dict: Optional[dict] = None,
) -> str:
    """Assemble P0-P4 context tiers within 800-token budget."""
    destination = trip_dict.get("destination", "") if trip_dict else ""

    p1, p2, p3, knowledge = await asyncio.gather(
        _build_preferences_text(user_id, user_question),
        _build_meta_text(user_id, trip_id, trip_dict),
        _build_history_text(user_id, trip_id, session_id),
        _retrieve_knowledge(user_question, user_id, destination),
    )

    p0_tokens = _estimate_tokens(SYSTEM_PROMPT)
    p1_tokens = _estimate_tokens(p1)
    p2_tokens = _estimate_tokens(p2)
    knowledge_tokens = _estimate_tokens(knowledge)
    remaining = TOKEN_BUDGET - p0_tokens - p1_tokens - p2_tokens - knowledge_tokens
    if remaining < 0:
        remaining = 100
    p3 = _truncate_to_budget(p3, remaining)

    context_section = f"## 当前行程\n{p2}" if p2 else ""
    preferences_section = p1 if p1 else ""
    knowledge_section = knowledge if knowledge else ""

    final_system = SYSTEM_PROMPT.format(
        knowledge_section=knowledge_section,
        preferences_section=preferences_section,
        context_section=context_section,
    )

    total = _estimate_tokens(final_system) + _estimate_tokens(p3)
    if total > TOKEN_BUDGET:
        overhead = total - TOKEN_BUDGET + 50
        if len(p3) > overhead:
            p3 = _truncate_to_budget(p3, max(50, _estimate_tokens(p3) - overhead))

    context_section = f"## 当前行程\n{p2}" if p2 else ""
    preferences_section = p1 if p1 else ""
    knowledge_section = knowledge if knowledge else ""
    final_system = SYSTEM_PROMPT.format(
        knowledge_section=knowledge_section,
        preferences_section=preferences_section,
        context_section=context_section,
    )

    return final_system


def format_chat_messages(
    system_prompt: str,
    user_id: str,
    trip_id: str,
    session_id: str,
    user_question: str,
    history: list[dict],
) -> list[dict]:
    """Format messages for the DeepSeek chat API."""
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    recent = history[-8:] if history else []
    for m in recent:
        messages.append({"role": m.get("role", "user"), "content": m.get("content", "")[:500]})
    messages.append({"role": "user", "content": user_question})
    return messages


def estimate_total_tokens(
    messages: list[dict],
    system_prompt: str,
) -> int:
    total = _estimate_tokens(system_prompt)
    for m in messages:
        total += _estimate_tokens(m.get("content", ""))
    return total


async def chat_with_context(
    user_id: str,
    trip_id: str,
    session_id: str,
    user_question: str,
    trip_dict: Optional[dict] = None,
    history: Optional[list[dict]] = None,
) -> str:
    """Full chat pipeline: build context → format messages → call LLM."""
    system_prompt = await build_context(
        user_id=user_id,
        trip_id=trip_id,
        session_id=session_id,
        user_question=user_question,
        trip_dict=trip_dict,
    )

    messages = format_chat_messages(
        system_prompt=system_prompt,
        user_id=user_id,
        trip_id=trip_id,
        session_id=session_id,
        user_question=user_question,
        history=history or [],
    )

    resp = await _get_client().chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=0.3,
        max_tokens=800,
    )

    return resp.choices[0].message.content or ""
