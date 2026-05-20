from __future__ import annotations

import json
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.core.redis import get_redis
from app.schemas.request import PlanRequest
from app.schemas.swap import SwapRequest, SwapResponse
from app.schemas.clarify import ClarifyRequest, ClarifyResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.inspire import InspireRequest, InspireResponse
from app.schemas.trip import CancelResponse, PlanResponse, TaskStatusOut, TripOut, WeatherResponse, OutfitSuggestion
from app.services.task_service import cancel_task, create_task, get_task
from app.services.trip_service import create_trip as create_trip_record
from app.services.trip_service import get_trip
from app.tasks.planning_task import run_trip_planning

router = APIRouter()


@router.post("/clarify", response_model=ClarifyResponse)
async def clarify_trip(req: ClarifyRequest):
    from app.agent.clarify import clarify_node

    result = await clarify_node(req.model_dump(mode="json"))
    return ClarifyResponse(**result)


@router.post("/inspire", response_model=InspireResponse)
async def inspire_trip(req: InspireRequest):
    from app.agent.inspire import inspire_destinations

    destinations = await inspire_destinations(
        preferences=req.preferences or "",
        budget_min=req.budget_min or 0,
        budget_max=req.budget_max or 10000,
        days=req.days or 3,
    )
    return InspireResponse(destinations=destinations)


async def _run_planning_background(task_id: str, req_dict: dict):
    """Run the AI planning pipeline in the background with its own DB session."""
    from app.agent.graph import extract_trip_from_final_plan, run_trip_pipeline
    from app.agent.state import AgentState
    from app.core.database import async_session
    from app.models.task import TaskStatus
    from app.services.geo_service import enrich_trip_geolocations
    from app.services.task_service import update_task_progress, update_task_status
    from app.services.trip_service import create_trip as create_trip_record

    async with async_session() as db:
        task = await get_task(db, uuid.UUID(task_id))
        if not task:
            return
        try:
            await update_task_status(db, task, TaskStatus.processing)
            await update_task_progress(db, task, 10, [
                {"name": "coordinator", "status": "working"},
                {"name": "transport", "status": "idle"},
                {"name": "accommodation", "status": "idle"},
                {"name": "attraction", "status": "idle"},
                {"name": "dining", "status": "idle"},
                {"name": "strategy", "status": "idle"},
            ])

            async def on_progress(progress: int, agents: list[dict]):
                await update_task_progress(db, task, progress, agents)

            start_location = req_dict.get("start_location", "北京")
            import logging
            _logger = logging.getLogger("trip.planning")
            _logger.info(f"Task {task_id}: start_location={start_location} destination={req_dict['destination']}")

            initial_state: AgentState = {
                "start_location": start_location,
                "destination": req_dict["destination"],
                "start_date": req_dict["start_date"],
                "end_date": req_dict["end_date"],
                "budget_min": req_dict["budget_min"],
                "budget_max": req_dict["budget_max"],
                "currency": req_dict.get("currency", "CNY"),
                "preferences": req_dict.get("preferences", []),
                "travel_style": req_dict.get("travel_style", "balanced"),
                "messages": [],
                "constraints": None,
                "transport_plan": None,
                "accommodation_plan": None,
                "attraction_plan": None,
                "dining_plan": None,
                "final_plan": None,
                "error": None,
            }
            result = await run_trip_pipeline(initial_state, on_progress=on_progress)

            if result.get("final_plan"):
                trip_data = extract_trip_from_final_plan(result["final_plan"])
                # Normalize float→int for monetary fields
                if "summary" in trip_data and "total_cost" in trip_data["summary"]:
                    trip_data["summary"]["total_cost"] = int(round(trip_data["summary"]["total_cost"]))
                await enrich_trip_geolocations(trip_data)
                await create_trip_record(db, uuid.UUID(task_id), trip_data)
                await update_task_progress(db, task, 100, [
                    {"name": "coordinator", "status": "done"},
                    {"name": "transport", "status": "done"},
                    {"name": "accommodation", "status": "done"},
                    {"name": "attraction", "status": "done"},
                    {"name": "dining", "status": "done"},
                    {"name": "strategy", "status": "done"},
                ])
                await update_task_status(db, task, TaskStatus.completed)
            else:
                await update_task_status(
                    db, task, TaskStatus.failed,
                    error_message=result.get("error", "Agent 规划未产生结果")
                )
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            task = await get_task(db, uuid.UUID(task_id))
            if task:
                await update_task_status(db, task, TaskStatus.failed, error_message=str(e))


@router.post("/plan", response_model=PlanResponse)
async def plan_trip(req: PlanRequest, db: AsyncSession = Depends(get_db)):
    redis = await get_redis()
    task = await create_task(db, req.model_dump(mode="json"), "sync-dev")

    if redis:
        celery_task = run_trip_planning.delay(
            str(task.id), req.model_dump(mode="json")
        )
        task.celery_task_id = celery_task.id
        await db.commit()
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
    else:
        await db.commit()
        import asyncio
        asyncio.create_task(_run_planning_background(str(task.id), req.model_dump(mode="json")))

    return PlanResponse(task_id=str(task.id))


@router.get("/planning/{task_id}", response_model=TaskStatusOut)
async def get_planning_status(
    task_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    redis = await get_redis()
    if redis:
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

    # Dev mode: check DB instead of Redis
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    # Look up the associated trip
    trip_id = None
    if task.status.value == "completed":
        from sqlalchemy import select
        from app.models.trip import Trip
        result = await db.execute(
            select(Trip.id).where(Trip.task_id == task_id)
        )
        trip_row = result.scalar_one_or_none()
        if trip_row:
            trip_id = str(trip_row)
    return TaskStatusOut(
        task_id=str(task_id),
        status=task.status.value,
        progress=task.progress,
        agents=json.loads(task.agents_json) if task.agents_json else [],
        trip_id=trip_id,
        error_message=task.error_message,
    )


@router.get("/{trip_id}/weather", response_model=WeatherResponse)
async def get_trip_weather(trip_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    api_key = settings.seniverse_api_key
    weather = None
    outfits: List[OutfitSuggestion] = []

    from app.services.weather_service import get_weather

    weather = await get_weather(trip.destination, api_key)

    if weather and weather.get("forecast"):
        try:
            from app.core.llm import get_llm
            forecast_text = "\n".join(
                f"{d['date']}: {d['text_day']}，{d['temp_min']}~{d['temp_max']}°C，"
                f"{d['wind_dir']}{d['wind_scale']}级"
                for d in weather["forecast"][:3]
            )
            llm = get_llm(temperature=0.4)
            prompt = (
                f"目的地: {trip.destination}\n"
                f"天气预报:\n{forecast_text}\n\n"
                "基于以上天气，为旅行者生成每日穿搭建议（简短1-2句，口语化）。"
                "输出纯 JSON 数组: [{\"date\": \"2025-01-01\", \"suggestion\": \"...\"}]"
            )
            response = await llm.ainvoke(prompt)
            import json, re
            raw = response.content
            try:
                raw_outfits = json.loads(raw)
            except json.JSONDecodeError:
                match = re.search(r"\[[\s\S]*\]", raw)
                raw_outfits = json.loads(match.group()) if match else []

            outfits = [
                OutfitSuggestion(date=o.get("date", ""), suggestion=o.get("suggestion", ""))
                for o in raw_outfits
            ]
        except Exception:
            pass

    from app.schemas.trip import WeatherInfo, WeatherDay
    weather_info = None
    if weather:
        weather_info = WeatherInfo(
            city=weather["city"],
            forecast=[WeatherDay(**d) for d in weather["forecast"]],
        )

    return WeatherResponse(weather=weather_info, outfits=outfits)


@router.post("/{trip_id}/chat", response_model=ChatResponse)
async def chat_with_trip(
    trip_id: uuid.UUID, req: ChatRequest, db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    from app.agent.context_engine import chat_with_context

    trip_dict = {
        "destination": trip.destination,
        "dates": trip.dates,
        "budget": trip.budget,
        "preferences": trip.preferences,
        "days": trip.data.get("days", []),
    }

    session_id = uuid.uuid4().hex[:16]
    user_question = req.messages[-1].content if req.messages else ""
    history = [m.model_dump() for m in req.messages[:-1]] if len(req.messages) > 1 else []

    reply = await chat_with_context(
        user_id=str(user.id),
        trip_id=str(trip_id),
        session_id=session_id,
        user_question=user_question,
        trip_dict=trip_dict,
        history=history,
    )
    return ChatResponse(reply=reply)


def _normalize_activity_ids(days: list) -> list:
    import json
    normalized = json.loads(json.dumps(days))
    for day in normalized:
        for act in day.get("activities", []):
            if isinstance(act.get("id"), int):
                act["id"] = str(act["id"])
    return normalized


@router.get("/{trip_id}", response_model=TripOut)
async def get_trip_result(trip_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    summary = dict(trip.summary) if trip.summary else {"total_cost": 0, "attraction_count": 0}
    if "total_cost" in summary and isinstance(summary["total_cost"], float):
        summary["total_cost"] = int(round(summary["total_cost"]))
    if "attraction_count" not in summary:
        summary["attraction_count"] = 0
    return TripOut(
        id=str(trip.id),
        destination=trip.destination,
        dates=trip.dates,
        budget=trip.budget,
        preferences=trip.preferences,
        travel_style=trip.travel_style,
        days=_normalize_activity_ids(trip.data.get("days", [])),
        summary=summary,
    )


@router.post("/{trip_id}/swap", response_model=SwapResponse)
async def swap_trip_activity(
    trip_id: uuid.UUID, req: SwapRequest, db: AsyncSession = Depends(get_db)
):
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    try:
        from app.agent.swap import swap_activity

        result = await swap_activity(
            destination=req.destination,
            day_index=req.day_index,
            activity_type=req.type,
            activity_name=req.name,
            preferences=req.preferences,
            context=req.context,
        )
        import uuid as _uuid
        return SwapResponse(
            id=result.get("id", str(uuid.uuid4())),
            type=result.get("type", req.type),
            name=result.get("name", ""),
            start_time=result.get("start_time", ""),
            end_time=result.get("end_time", ""),
            duration=result.get("duration", 0),
            description=result.get("description"),
            tips=result.get("tips"),
            reason=result.get("reason", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"替换失败: {str(e)}")


@router.post("/{task_id}/cancel", response_model=CancelResponse)
async def cancel_planning(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    await cancel_task(db, task)
    return CancelResponse(success=True)
