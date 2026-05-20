import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_admin
from app.models.user import User
from app.models.knowledge import UserKnowledge, GlobalKnowledge, LearnHistory
from app.schemas.learn import (
    LearnRequest,
    LearnItemOut,
    LearnListResponse,
    LearnHistoryOut,
    LearnHistoryListResponse,
    LearnAnalyzeResult,
    LearnSearchRequest,
    LearnSearchResult,
    LearnSearchResultItem,
    GlobalKnowledgeOut,
    GlobalKnowledgeListResponse,
    MergeReport,
    KnowledgeStats,
)
from app.services.scraper_service import fetch_and_extract
from app.agent.learn_agent import digest_content

router = APIRouter()


def _to_learn_item(item: UserKnowledge) -> LearnItemOut:
    return LearnItemOut(
        id=str(item.id),
        url=item.url,
        platform=item.platform,
        title=item.title,
        summary=item.summary,
        knowledge_points=item.knowledge_points.get("points", []),
        tags=item.tags.get("items", []),
        location=item.location,
        practical_info=item.practical_info,
        quality_score=item.quality_score,
        status=item.status,
        created_at=item.created_at.isoformat(),
        merged_at=item.merged_at.isoformat() if item.merged_at else None,
    )


def _to_history_out(h: LearnHistory) -> LearnHistoryOut:
    return LearnHistoryOut(
        id=str(h.id),
        url=h.url,
        platform=h.platform,
        title=h.title,
        summary=h.summary,
        knowledge_points=h.knowledge_points.get("points", []),
        tags=h.tags.get("items", []),
        location=h.location,
        quality_score=h.quality_score,
        learned_at=h.learned_at.isoformat(),
    )


def _build_index_text(h: LearnHistory) -> str:
    """Build a dense text representation for vector indexing."""
    parts = [h.title, h.summary]
    kps = h.knowledge_points.get("points", [])
    if kps:
        parts.append(" ".join(
            f"{kp.get('category', '')}: {kp.get('point', '')}"
            for kp in kps
        ))
    tags = h.tags.get("items", [])
    if tags:
        parts.append("标签: " + " ".join(tags))
    if h.location:
        parts.append("地点: " + h.location)
    return " | ".join(parts)


async def _index_async(doc_id: str, text: str, metadata: dict) -> None:
    """Index a document in the vector store via thread pool."""
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None,
            _sync_index,
            doc_id,
            text,
            metadata,
        )
    except Exception:
        logger.warning("Failed to index doc_id=%s", doc_id)


def _sync_index(doc_id: str, text: str, metadata: dict) -> None:
    from app.services.vector_store import get_vector_store
    get_vector_store().index_knowledge(doc_id, text, metadata)


async def _delete_index_async(doc_id: str) -> None:
    """Delete a document from the vector store via thread pool."""
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, _sync_delete, doc_id)
    except Exception:
        logger.warning("Failed to delete vector for doc_id=%s", doc_id)


def _sync_delete(doc_id: str) -> None:
    from app.services.vector_store import get_vector_store
    get_vector_store().delete(doc_id)


@router.post("/analyze", response_model=LearnAnalyzeResult)
async def analyze_url(
    data: LearnRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scraped = await fetch_and_extract(data.url)

    try:
        digested = await digest_content(data.url, scraped)
    except Exception:
        logger.warning("AI digest failed for %s, using fallback", data.url)
        digested = {
            "title": scraped.get("title", data.url),
            "summary": scraped.get("text", "")[:300] if scraped.get("text") else "",
            "knowledge_points": [],
            "tags": [],
            "location": None,
            "practical_info": None,
            "quality_score": 0.2,
        }

    history = LearnHistory(
        id=uuid.uuid4(),
        user_id=user.id,
        url=data.url,
        platform=scraped.get("platform", "generic"),
        title=digested.get("title", scraped.get("title", "")),
        summary=digested.get("summary", ""),
        knowledge_points={"points": digested.get("knowledge_points", [])},
        tags={"items": digested.get("tags", [])},
        location=digested.get("location"),
        quality_score=digested.get("quality_score", 0.3),
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    # Fire-and-forget: index into vector store via thread pool
    index_text = _build_index_text(history)
    index_meta = {
        "user_id": str(user.id),
        "platform": history.platform,
        "location": history.location or "",
        "quality_score": history.quality_score,
        "source": "learn_history",
    }
    asyncio.create_task(_index_async(str(history.id), index_text, index_meta))

    return LearnAnalyzeResult(
        history=_to_history_out(history),
        knowledge_points=digested.get("knowledge_points", []),
        summary=digested.get("summary", ""),
        practical_info=digested.get("practical_info"),
    )


@router.get("/recent", response_model=LearnHistoryListResponse)
async def list_recent(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=20),
):
    result = await db.execute(
        select(LearnHistory)
        .where(LearnHistory.user_id == user.id)
        .order_by(LearnHistory.learned_at.desc())
        .limit(limit)
    )
    items = result.scalars().all()
    return LearnHistoryListResponse(
        items=[_to_history_out(item) for item in items],
        total=len(items),
    )


@router.get("/history", response_model=LearnHistoryListResponse)
async def list_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    result = await db.execute(
        select(LearnHistory)
        .where(LearnHistory.user_id == user.id)
        .order_by(LearnHistory.learned_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).where(LearnHistory.user_id == user.id)
    )
    total = count_result.scalar() or 0

    return LearnHistoryListResponse(
        items=[_to_history_out(item) for item in items],
        total=total,
    )


@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history(
    history_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = uuid.UUID(history_id)
    result = await db.execute(
        select(LearnHistory).where(
            LearnHistory.id == uid,
            LearnHistory.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="学习记录不存在")
    await db.delete(item)
    await db.commit()
    asyncio.create_task(_delete_index_async(history_id))


@router.post("/search", response_model=LearnSearchResult)
async def search_knowledge(
    data: LearnSearchRequest,
    user: User = Depends(get_current_user),
):
    """Search the vector store for relevant knowledge (RAG endpoint)."""
    where = {"user_id": str(user.id)}
    if data.location:
        where["location"] = data.location

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(
        None,
        lambda: _sync_search(data.query, data.n_results, where),
    )
    items = [
        LearnSearchResultItem(
            id=r["id"],
            document=r["document"],
            distance=round(r["distance"], 4),
            metadata=r["metadata"],
        )
        for r in results
    ]
    return LearnSearchResult(items=items, query=data.query)


def _sync_search(query: str, n_results: int, where: dict) -> list:
    from app.services.vector_store import get_vector_store
    return get_vector_store().search(query, n_results=n_results, where=where)


# ── Legacy endpoints for backward compatibility ──────────────────

@router.get("/items", response_model=LearnListResponse)
async def list_items(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    result = await db.execute(
        select(UserKnowledge)
        .where(UserKnowledge.user_id == user.id)
        .order_by(UserKnowledge.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).where(UserKnowledge.user_id == user.id)
    )
    total = count_result.scalar() or 0

    return LearnListResponse(
        items=[_to_learn_item(item) for item in items],
        total=total,
    )


@router.get("/items/{item_id}", response_model=LearnItemOut)
async def get_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = uuid.UUID(item_id)
    result = await db.execute(
        select(UserKnowledge).where(
            UserKnowledge.id == uid,
            UserKnowledge.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="学习内容不存在")
    return _to_learn_item(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = uuid.UUID(item_id)
    result = await db.execute(
        select(UserKnowledge).where(
            UserKnowledge.id == uid,
            UserKnowledge.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="学习内容不存在")
    await db.delete(item)
    await db.commit()


# ── Global knowledge ─────────────────────────────────────────────

@router.get("/global", response_model=GlobalKnowledgeListResponse)
async def list_global_knowledge(
    db: AsyncSession = Depends(get_db),
    location: str = Query("", max_length=200),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = select(GlobalKnowledge).order_by(GlobalKnowledge.quality_score.desc())
    if location:
        query = query.where(GlobalKnowledge.location.ilike(f"%{location}%"))

    result = await db.execute(query.offset(offset).limit(limit))
    items = result.scalars().all()

    count_query = select(func.count())
    if location:
        count_query = count_query.where(GlobalKnowledge.location.ilike(f"%{location}%"))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    def _to_global(item: GlobalKnowledge) -> GlobalKnowledgeOut:
        return GlobalKnowledgeOut(
            id=str(item.id),
            title=item.title,
            summary=item.summary,
            knowledge_points=item.knowledge_points.get("points", []),
            tags=item.tags.get("items", []),
            location=item.location,
            practical_info=item.practical_info,
            quality_score=item.quality_score,
            merged_count=item.merged_count,
            updated_at=item.updated_at.isoformat(),
        )

    return GlobalKnowledgeListResponse(
        items=[_to_global(item) for item in items],
        total=total,
    )


# ── Admin ────────────────────────────────────────────────────────

@router.post("/admin/merge", response_model=MergeReport)
async def trigger_merge(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.services.knowledge_merge import monthly_merge
    report = await monthly_merge(db)
    return report


@router.get("/admin/stats", response_model=KnowledgeStats)
async def get_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    total = await db.execute(select(func.count()).select_from(UserKnowledge))
    active = await db.execute(
        select(func.count()).where(UserKnowledge.status == "active")
    )
    merged = await db.execute(
        select(func.count()).where(UserKnowledge.status == "merged")
    )
    global_count = await db.execute(select(func.count()).select_from(GlobalKnowledge))

    return KnowledgeStats(
        total_user_items=total.scalar() or 0,
        active_items=active.scalar() or 0,
        merged_items=merged.scalar() or 0,
        global_items=global_count.scalar() or 0,
    )
