"""Redis memory service for chat session storage and user preferences.

All keys use the "tl:" namespace prefix and have a 30-day TTL.
Graceful degradation: all getters return None/empty when Redis is unavailable.
"""

import json
import logging
from typing import Optional

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

TTL_SECONDS = 30 * 24 * 3600  # 30 days
MAX_MESSAGES = 10


def _key_trip_meta(user_id: str, trip_id: str) -> str:
    return f"tl:user:{user_id}:trip:{trip_id}:meta"


def _key_trip_summary(user_id: str, trip_id: str) -> str:
    return f"tl:user:{user_id}:trip:{trip_id}:summary"


def _key_chat(user_id: str, trip_id: str, session_id: str) -> str:
    return f"tl:user:{user_id}:trip:{trip_id}:chat:{session_id}"


def _key_hot_prefs(user_id: str) -> str:
    return f"tl:user:{user_id}:preferences:hot"


def _key_pref_keywords(user_id: str) -> str:
    return f"tl:user:{user_id}:preferences:keywords"


# ─── Trip meta ────────────────────────────────────────────────────

async def set_trip_meta(user_id: str, trip_id: str, meta: dict) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        key = _key_trip_meta(user_id, trip_id)
        await r.hset(key, mapping={k: str(v) for k, v in meta.items()})
        await r.expire(key, TTL_SECONDS)
    except Exception:
        logger.warning("set_trip_meta failed", exc_info=True)


async def get_trip_meta(user_id: str, trip_id: str) -> Optional[dict]:
    r = await get_redis()
    if not r:
        return None
    try:
        key = _key_trip_meta(user_id, trip_id)
        data = await r.hgetall(key)
        return data if data else None
    except Exception:
        logger.warning("get_trip_meta failed", exc_info=True)
        return None


# ─── Session messages ─────────────────────────────────────────────

async def save_message(
    user_id: str, trip_id: str, session_id: str, role: str, content: str
) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        key = _key_chat(user_id, trip_id, session_id)
        msg = json.dumps({"role": role, "content": content}, ensure_ascii=False)
        await r.rpush(key, msg)
        await r.ltrim(key, -MAX_MESSAGES, -1)
        await r.expire(key, TTL_SECONDS)
    except Exception:
        logger.warning("save_message failed", exc_info=True)


async def save_messages_batch(
    user_id: str, trip_id: str, session_id: str, messages: list[dict]
) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        key = _key_chat(user_id, trip_id, session_id)
        await r.delete(key)
        for msg in messages[-MAX_MESSAGES:]:
            await r.rpush(key, json.dumps(msg, ensure_ascii=False))
        await r.expire(key, TTL_SECONDS)
    except Exception:
        logger.warning("save_messages_batch failed", exc_info=True)


async def get_session_messages(
    user_id: str, trip_id: str, session_id: str
) -> list[dict]:
    r = await get_redis()
    if not r:
        return []
    try:
        key = _key_chat(user_id, trip_id, session_id)
        raw = await r.lrange(key, 0, -1)
        return [json.loads(m) for m in raw]
    except Exception:
        logger.warning("get_session_messages failed", exc_info=True)
        return []


# ─── Trip summary ─────────────────────────────────────────────────

async def set_trip_summary(user_id: str, trip_id: str, summary: str) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        key = _key_trip_summary(user_id, trip_id)
        await r.set(key, summary)
        await r.expire(key, TTL_SECONDS)
    except Exception:
        logger.warning("set_trip_summary failed", exc_info=True)


async def get_trip_summary(user_id: str, trip_id: str) -> Optional[str]:
    r = await get_redis()
    if not r:
        return None
    try:
        key = _key_trip_summary(user_id, trip_id)
        return await r.get(key)
    except Exception:
        logger.warning("get_trip_summary failed", exc_info=True)
        return None


# ─── User preferences ─────────────────────────────────────────────

async def set_hot_preferences(user_id: str, prefs_by_category: dict[str, str]) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        key = _key_hot_prefs(user_id)
        await r.delete(key)
        await r.hset(key, mapping=prefs_by_category)
        await r.expire(key, TTL_SECONDS)
    except Exception:
        logger.warning("set_hot_preferences failed", exc_info=True)


async def get_hot_preferences(user_id: str) -> Optional[dict[str, str]]:
    r = await get_redis()
    if not r:
        return None
    try:
        key = _key_hot_prefs(user_id)
        data = await r.hgetall(key)
        return data if data else None
    except Exception:
        logger.warning("get_hot_preferences failed", exc_info=True)
        return None


async def set_preference_keywords(user_id: str, keywords: list[str]) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        key = _key_pref_keywords(user_id)
        await r.delete(key)
        if keywords:
            await r.sadd(key, *keywords)
        await r.expire(key, TTL_SECONDS)
    except Exception:
        logger.warning("set_preference_keywords failed", exc_info=True)


async def get_preference_keywords(user_id: str) -> set[str]:
    r = await get_redis()
    if not r:
        return set()
    try:
        key = _key_pref_keywords(user_id)
        members = await r.smembers(key)
        return members if members else set()
    except Exception:
        logger.warning("get_preference_keywords failed", exc_info=True)
        return set()


# ─── Session cleanup ──────────────────────────────────────────────

async def delete_session(user_id: str, trip_id: str, session_id: str) -> None:
    r = await get_redis()
    if not r:
        return
    try:
        key = _key_chat(user_id, trip_id, session_id)
        await r.delete(key)
    except Exception:
        logger.warning("delete_session failed", exc_info=True)
