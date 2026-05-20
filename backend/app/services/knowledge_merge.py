from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import UserKnowledge, GlobalKnowledge
from app.schemas.learn import MergeReport


async def monthly_merge(db: AsyncSession) -> MergeReport:
    result = await db.execute(
        select(UserKnowledge)
        .where(
            UserKnowledge.status == "active",
            UserKnowledge.quality_score >= 0.6,
        )
        .order_by(UserKnowledge.quality_score.desc())
    )
    candidates = result.scalars().all()

    groups: dict[str, list[UserKnowledge]] = {}
    for item in candidates:
        key = _group_key(item)
        groups.setdefault(key, []).append(item)

    new_count = 0
    merged_count = 0

    for key, items in groups.items():
        best = items[0]
        others = items[1:]

        existing = await db.execute(
            select(GlobalKnowledge).where(GlobalKnowledge.location == best.location)
        )
        global_item = existing.scalar_one_or_none()

        if global_item:
            _merge_into_global(global_item, best, others)
            merged_count += 1
        else:
            global_item = GlobalKnowledge(
                id=uuid.uuid4(),
                source_user_ids=[str(best.user_id)],
                source_item_ids=[str(best.id)],
                title=best.title,
                summary=best.summary,
                knowledge_points=best.knowledge_points,
                tags=best.tags,
                location=best.location,
                practical_info=best.practical_info,
                quality_score=best.quality_score,
                merged_count=1,
            )
            db.add(global_item)
            new_count += 1

        for item in items:
            item.status = "merged"
            item.merged_at = datetime.now(timezone.utc)

    three_months_ago = datetime.now(timezone.utc)
    clean_result = await db.execute(
        select(UserKnowledge).where(
            UserKnowledge.status == "active",
            UserKnowledge.quality_score < 0.3,
            UserKnowledge.created_at < three_months_ago,
        )
    )
    old_items = clean_result.scalars().all()
    for item in old_items:
        item.status = "archived"

    await db.commit()

    return MergeReport(
        new_items=new_count,
        merged_items=merged_count,
        cleaned_items=len(old_items),
    )


def _group_key(item: UserKnowledge) -> str:
    loc = (item.location or "").strip()
    tags = sorted(item.tags.get("items", []))
    return f"{loc}|{','.join(tags[:3])}"


def _merge_into_global(
    target: GlobalKnowledge,
    best: UserKnowledge,
    others: list[UserKnowledge],
) -> None:
    target.updated_at = datetime.now(timezone.utc)
    target.merged_count += 1

    existing_ids = set(target.source_item_ids)
    existing_users = set(target.source_user_ids)

    if str(best.id) not in existing_ids:
        existing_ids.add(str(best.id))
        existing_users.add(str(best.user_id))
        target.quality_score = max(target.quality_score, best.quality_score)

    for item in others:
        if str(item.id) not in existing_ids:
            existing_ids.add(str(item.id))
            existing_users.add(str(item.user_id))

    target.source_item_ids = list(existing_ids)
    target.source_user_ids = list(existing_users)

    existing_points = {
        p.get("point", ""): p for p in target.knowledge_points.get("points", [])
    }
    for point in best.knowledge_points.get("points", []):
        key = point.get("point", "")
        if key and key not in existing_points:
            existing_points[key] = point
    target.knowledge_points = {"points": list(existing_points.values())}
