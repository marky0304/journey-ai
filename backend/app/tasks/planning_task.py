import asyncio
import json
import uuid

from app.agent.graph import extract_trip_from_final_plan, run_trip_pipeline
from app.agent.state import AgentState
from app.core.database import async_session
from app.models.task import TaskStatus as TStatus
from app.services.geo_service import enrich_trip_geolocations
from app.services.task_service import get_task as svc_get_task, update_task_status
from app.services.trip_service import create_trip
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=1)
def run_trip_planning(self, task_id: str, preferences: dict):
    redis = celery_app.backend.client

    initial_state: AgentState = {
        "destination": preferences["destination"],
        "start_date": str(preferences["start_date"]),
        "end_date": str(preferences["end_date"]),
        "budget_min": preferences.get("budget_min", 0),
        "budget_max": preferences.get("budget_max", 100000),
        "currency": preferences.get("currency", "CNY"),
        "preferences": preferences.get("preferences", []),
        "travel_style": preferences.get("travel_style", "balanced"),
        "messages": [],
        "constraints": None,
        "transport_plan": None,
        "accommodation_plan": None,
        "attraction_plan": None,
        "dining_plan": None,
        "final_plan": None,
        "error": None,
    }

    try:
        redis.hset(
            f"task:{task_id}",
            mapping={
                "status": "processing",
                "progress": "10",
                "agents": json.dumps([
                    {"name": "coordinator", "status": "working"},
                    {"name": "transport", "status": "idle"},
                    {"name": "accommodation", "status": "idle"},
                    {"name": "attraction", "status": "idle"},
                    {"name": "dining", "status": "idle"},
                    {"name": "strategy", "status": "idle"},
                ]),
            },
        )

        result = asyncio.run(run_trip_pipeline(initial_state))

        if result.get("final_plan"):
            trip_data = extract_trip_from_final_plan(result["final_plan"])

            async def save_trip_to_db():
                await enrich_trip_geolocations(trip_data)
                async with async_session() as db:
                    task = await svc_get_task(db, uuid.UUID(task_id))
                    trip = await create_trip(db, uuid.UUID(task_id), trip_data)
                    await update_task_status(db, task, TStatus.completed)
                    return trip.id

            trip_uuid = asyncio.run(save_trip_to_db())

            redis.hset(
                f"task:{task_id}",
                mapping={
                    "status": "completed",
                    "progress": "100",
                    "trip_id": str(trip_uuid),
                    "trip_data": json.dumps(trip_data, ensure_ascii=False),
                    "agents": json.dumps([
                        {"name": "coordinator", "status": "done"},
                        {"name": "transport", "status": "done"},
                        {"name": "accommodation", "status": "done"},
                        {"name": "attraction", "status": "done"},
                        {"name": "dining", "status": "done"},
                        {"name": "strategy", "status": "done"},
                    ]),
                },
            )
        else:
            redis.hset(
                f"task:{task_id}",
                mapping={
                    "status": "failed",
                    "progress": "0",
                    "error": "Agent 规划未产生结果",
                },
            )
    except Exception as e:
        redis.hset(
            f"task:{task_id}",
            mapping={
                "status": "failed",
                "progress": "0",
                "error": str(e),
            },
        )
        raise
