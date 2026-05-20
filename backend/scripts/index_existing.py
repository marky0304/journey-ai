"""One-shot script: index existing LearnHistory/GlobalKnowledge into ChromaDB.

Usage: python -m scripts.index_existing
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.knowledge import GlobalKnowledge, LearnHistory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_text(h: LearnHistory) -> str:
    parts = [h.title, h.summary]
    kps = h.knowledge_points.get("points", [])
    if kps:
        parts.append(" ".join(
            f"{kp.get('category', '')}: {kp.get('point', '')}" for kp in kps
        ))
    tags = h.tags.get("items", [])
    if tags:
        parts.append("标签: " + " ".join(tags))
    if h.location:
        parts.append("地点: " + h.location)
    return " | ".join(parts)


def _build_global_text(g: GlobalKnowledge) -> str:
    parts = [g.title, g.summary]
    kps = g.knowledge_points.get("points", [])
    if kps:
        parts.append(" ".join(
            f"{kp.get('category', '')}: {kp.get('point', '')}" for kp in kps
        ))
    tags = g.tags.get("items", [])
    if tags:
        parts.append("标签: " + " ".join(tags))
    if g.location:
        parts.append("地点: " + g.location)
    return " | ".join(parts)


async def index_existing() -> None:
    from app.services.vector_store import get_vector_store

    store = get_vector_store()
    logger.info("Vector store has %d documents before indexing", store.count())

    dbgen = get_db()
    db: AsyncSession = await dbgen.__anext__()

    # Index LearnHistory records
    result = await db.execute(select(LearnHistory))
    histories: List[LearnHistory] = result.scalars().all()
    logger.info("Found %d LearnHistory records", len(histories))

    for h in histories:
        text = _build_text(h)
        metadata = {
            "user_id": str(h.user_id),
            "platform": h.platform,
            "location": h.location or "",
            "quality_score": h.quality_score,
            "source": "learn_history",
        }
        store.index_knowledge(str(h.id), text, metadata)

    # Index GlobalKnowledge records
    result = await db.execute(select(GlobalKnowledge))
    globals_: List[GlobalKnowledge] = result.scalars().all()
    logger.info("Found %d GlobalKnowledge records", len(globals_))

    for g in globals_:
        text = _build_global_text(g)
        metadata: Dict = {
            "location": g.location or "",
            "quality_score": g.quality_score,
            "merged_count": g.merged_count,
            "source": "global_knowledge",
        }
        store.index_knowledge(f"global-{g.id}", text, metadata)

    indexed = len(histories) + len(globals_)
    logger.info("Indexed %d documents. Vector store count: %d", indexed, store.count())


if __name__ == "__main__":
    asyncio.run(index_existing())
