import json

from app.agent.graph import extract_trip_from_final_plan, trip_graph
from app.agent.state import AgentState
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

        result = trip_graph.invoke(initial_state)

        if result.get("final_plan"):
            trip_data = extract_trip_from_final_plan(result["final_plan"])
            redis.hset(
                f"task:{task_id}",
                mapping={
                    "status": "completed",
                    "progress": "100",
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
