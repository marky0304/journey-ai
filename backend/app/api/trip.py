import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.request import PlanRequest
from app.schemas.trip import CancelResponse, PlanResponse, TaskStatusOut, TripOut
from app.services.task_service import cancel_task, create_task, get_task
from app.services.trip_service import create_trip as create_trip_record
from app.services.trip_service import get_trip
from app.tasks.planning_task import run_trip_planning

router = APIRouter()


@router.post("/plan", response_model=PlanResponse)
async def plan_trip(req: PlanRequest, db: AsyncSession = Depends(get_db)):
    celery_task = run_trip_planning.delay(
        str(uuid.uuid4()), req.model_dump(mode="json")
    )
    task = await create_task(db, req.model_dump(mode="json"), celery_task.id)

    redis = await get_redis()
    await redis.hset(
        f"task:{task.id}",
        mapping={
            "status": "pending",
            "progress": "0",
            "agents": json.dumps([
                {"name": "coordinator", "status": "idle"},
                {"name": "transport", "status": "idle"},
                {"name": "accommodation", "status": "idle"},
                {"name": "attraction", "status": "idle"},
                {"name": "dining", "status": "idle"},
                {"name": "strategy", "status": "idle"},
            ]),
        },
    )
    return PlanResponse(task_id=str(task.id))


@router.get("/planning/{task_id}", response_model=TaskStatusOut)
async def get_planning_status(task_id: uuid.UUID):
    redis = await get_redis()
    data = await redis.hgetall(f"task:{task_id}")
    if not data:
        raise HTTPException(status_code=404, detail="任务不存在")
    agents = json.loads(data.get("agents", "[]"))
    return TaskStatusOut(
        task_id=str(task_id),
        status=data.get("status", "pending"),
        progress=int(data.get("progress", 0)),
        agents=agents,
        trip_id=data.get("trip_id"),
        error_message=data.get("error"),
    )


@router.get("/{trip_id}", response_model=TripOut)
async def get_trip_result(trip_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    return TripOut(
        id=str(trip.id),
        destination=trip.destination,
        dates=trip.dates,
        budget=trip.budget,
        preferences=trip.preferences,
        travel_style=trip.travel_style,
        days=trip.data.get("days", []),
        summary=trip.summary,
    )


@router.post("/{task_id}/cancel", response_model=CancelResponse)
async def cancel_planning(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    await cancel_task(db, task)
    return CancelResponse(success=True)
