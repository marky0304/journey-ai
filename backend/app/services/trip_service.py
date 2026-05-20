import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip


async def create_trip(db: AsyncSession, task_id: uuid.UUID, trip_data: dict) -> Trip:
    trip = Trip(
        task_id=task_id,
        destination=trip_data["destination"],
        dates=trip_data["dates"],
        budget=trip_data["budget"],
        preferences=trip_data.get("preferences", []),
        travel_style=trip_data.get("travel_style", "balanced"),
        data={"days": trip_data.get("days", [])},
        summary=trip_data.get("summary", {}),
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)
    return trip


async def get_trip(db: AsyncSession, trip_id: uuid.UUID) -> Optional[Trip]:
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    return result.scalar_one_or_none()
