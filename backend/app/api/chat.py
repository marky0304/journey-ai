"""Chat API routes — context-aware chat with session management and preferences."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.chat import ChatSession, UserPreference
from app.models.trip import Trip
from app.models.user import User
from app.schemas.chat import (
    CloseSessionRequest,
    ContextResponse,
    HistoryResponse,
    PreferenceOut,
    RestoreRequest,
    RestoreResponse,
    SendMessageRequest,
    SendMessageResponse,
    SessionHistoryResponse,
    SessionItem,
    TripSessionGroup,
)
from app.services import redis_memory

router = APIRouter()


@router.get("/context", response_model=ContextResponse)
async def get_chat_context(
    tripId: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return trip metadata + suggested questions for a fresh chat dialog."""
    try:
        trip_uuid = uuid.UUID(tripId)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail="无效的行程ID")

    trip = await db.get(Trip, trip_uuid)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    meta = {
        "destination": trip.destination,
        "dates": trip.dates,
        "budget": trip.budget,
        "preferences": trip.preferences,
    }

    suggested_questions = [
        f"{trip.destination}有哪些必去景点？",
        "帮我推荐当地特色美食",
        "这趟行程需要注意什么？",
        "帮我调整一下行程安排",
    ]

    try:
        await redis_memory.set_trip_meta(
            str(user.id), tripId,
            {
                "destination": trip.destination,
                "dates": f"{trip.dates.get('start', '')} 至 {trip.dates.get('end', '')}",
                "budget": f"{trip.budget.get('min', 0)}-{trip.budget.get('max', 0)} {trip.budget.get('currency', 'CNY')}",
                "preferences": ", ".join(trip.preferences or []),
            },
        )
    except Exception:
        pass

    return ContextResponse(trip_meta=meta, suggested_questions=suggested_questions)


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    req: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get AI reply. Session is created on first message."""
    from app.agent.context_engine import chat_with_context

    try:
        trip_uuid = uuid.UUID(req.trip_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail="无效的行程ID")

    trip = await db.get(Trip, trip_uuid)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    trip_dict = {
        "destination": trip.destination,
        "dates": trip.dates,
        "budget": trip.budget,
        "preferences": trip.preferences,
        "days": trip.data.get("days", []) if trip.data else [],
    }

    history = await redis_memory.get_session_messages(
        str(user.id), req.trip_id, req.session_id
    )

    reply = await chat_with_context(
        user_id=str(user.id),
        trip_id=req.trip_id,
        session_id=req.session_id,
        user_question=req.message,
        trip_dict=trip_dict,
        history=history,
    )

    await redis_memory.save_message(
        str(user.id), req.trip_id, req.session_id, "user", req.message
    )
    await redis_memory.save_message(
        str(user.id), req.trip_id, req.session_id, "assistant", reply
    )

    existing = await db.execute(
        select(ChatSession).where(ChatSession.session_id == req.session_id)
    )
    session = existing.scalar_one_or_none()
    if session:
        session.message_count += 2
        session.last_active_at = datetime.now(timezone.utc)
    else:
        session = ChatSession(
            user_id=user.id,
            trip_id=trip_uuid if req.trip_id else None,
            session_id=req.session_id,
            first_message=req.message[:255],
            message_count=2,
        )
        db.add(session)
    await db.commit()

    return SendMessageResponse(reply=reply, suggestions=[])


@router.get("/history", response_model=HistoryResponse)
async def get_chat_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions grouped by trip."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id, ChatSession.is_deleted == False)
        .order_by(ChatSession.last_active_at.desc())
    )
    sessions = result.scalars().all()

    groups: dict[str, TripSessionGroup] = {}
    for s in sessions:
        tid = str(s.trip_id) if s.trip_id else "__no_trip__"
        if tid not in groups:
            trip_name = "独立对话"
            if s.trip_id:
                trip = await db.get(Trip, s.trip_id)
                if trip:
                    trip_name = trip.destination or "未命名行程"
            groups[tid] = TripSessionGroup(
                trip_id=tid if tid != "__no_trip__" else "",
                trip_name=trip_name,
                is_current_trip=False,
                sessions=[],
            )
        groups[tid].sessions.append(SessionItem(
            session_id=s.session_id,
            first_message=s.first_message,
            message_count=s.message_count,
            started_at=s.started_at,
            last_active_at=s.last_active_at,
        ))

    return HistoryResponse(groups=list(groups.values()))


@router.get("/session/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full message history for a single session."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user.id,
            ChatSession.is_deleted == False,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    trip_name = "独立对话"
    if session.trip_id:
        trip = await db.get(Trip, session.trip_id)
        if trip:
            trip_name = trip.destination or "未命名行程"

    tid = str(session.trip_id) if session.trip_id else ""
    messages = await redis_memory.get_session_messages(
        str(user.id), tid, session_id
    )

    return SessionHistoryResponse(
        session_id=session_id,
        trip_name=trip_name,
        messages=messages,
    )


@router.post("/restore", response_model=RestoreResponse)
async def restore_session(
    req: RestoreRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore a historical session by copying its messages to a new session."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == req.original_session_id,
            ChatSession.user_id == user.id,
            ChatSession.is_deleted == False,
        )
    )
    old_session = result.scalar_one_or_none()
    if not old_session:
        raise HTTPException(status_code=404, detail="原会话不存在")

    new_session_id = uuid.uuid4().hex[:16]
    old_messages = await redis_memory.get_session_messages(
        str(user.id), req.trip_id or "", req.original_session_id
    )

    if old_messages:
        await redis_memory.save_messages_batch(
            str(user.id), req.trip_id or "", new_session_id, old_messages
        )

    return RestoreResponse(
        new_session_id=new_session_id,
        messages=old_messages,
    )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a chat session."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    session.is_deleted = True
    await db.commit()

    tid = str(session.trip_id) if session.trip_id else ""
    await redis_memory.delete_session(str(user.id), tid, session_id)

    return {"success": True}


@router.post("/session/close")
async def close_session(
    req: CloseSessionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Close a session and trigger preference extraction."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == req.session_id,
            ChatSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        # Session was never created (no messages sent) — nothing to do
        return {"success": True}

    session.last_active_at = datetime.now(timezone.utc)
    await db.commit()

    tid = str(session.trip_id) if session.trip_id else ""

    messages = await redis_memory.get_session_messages(
        str(user.id), tid, req.session_id
    )

    if messages:
        from app.services.preference_service import extract_preferences, save_preferences
        from app.services.summarize import generate_summary

        prefs = await extract_preferences(str(user.id), messages)
        if prefs:
            await save_preferences(db, user.id, prefs)

        if len(messages) > 6:
            await generate_summary(str(user.id), tid, messages)

    return {"success": True}


@router.get("/preferences", response_model=list[PreferenceOut])
async def get_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List active user preferences."""
    result = await db.execute(
        select(UserPreference)
        .where(UserPreference.user_id == user.id, UserPreference.is_active == True)
        .order_by(UserPreference.confidence.desc())
    )
    rows = result.scalars().all()
    return [
        PreferenceOut(
            id=str(r.id),
            category=r.category,
            content=r.content,
            confidence=r.confidence,
        )
        for r in rows
    ]


@router.put("/preferences/{pref_id}", response_model=PreferenceOut)
async def update_preference(
    pref_id: str,
    content: str | None = None,
    confidence: float | None = None,
    is_active: bool | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a user preference."""
    pref = await db.get(UserPreference, uuid.UUID(pref_id))
    if not pref or pref.user_id != user.id:
        raise HTTPException(status_code=404, detail="偏好不存在")

    if content is not None:
        pref.content = content
    if confidence is not None:
        pref.confidence = confidence
    if is_active is not None:
        pref.is_active = is_active

    await db.commit()

    return PreferenceOut(
        id=str(pref.id),
        category=pref.category,
        content=pref.content,
        confidence=pref.confidence,
    )


@router.delete("/preferences/{pref_id}")
async def delete_preference(
    pref_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user preference."""
    pref = await db.get(UserPreference, uuid.UUID(pref_id))
    if not pref or pref.user_id != user.id:
        raise HTTPException(status_code=404, detail="偏好不存在")

    await db.delete(pref)
    await db.commit()

    return {"success": True}
