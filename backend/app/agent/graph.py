from __future__ import annotations

import asyncio
import json
import re
import uuid
from typing import Awaitable, Callable, Dict, List, Optional

from langchain_core.messages import HumanMessage

from app.agent.accommodation import accommodation_node
from app.agent.attraction import attraction_node
from app.agent.coordinator import coordinator_node
from app.agent.dining import dining_node
from app.agent.state import AgentState
from app.agent.strategy import strategy_node
from app.agent.transport import transport_node

ProgressCallback = Callable[[int, List[dict]], Awaitable[None]]


def _default_agents(statuses: Dict[str, str]) -> List[dict]:
    names = ["coordinator", "transport", "accommodation", "attraction", "dining", "strategy"]
    return [{"name": n, "status": statuses.get(n, "idle")} for n in names]


async def aggregate_results(state: AgentState) -> dict:
    return {"messages": []}


async def run_trip_pipeline(
    initial_state: AgentState,
    on_progress: Optional[ProgressCallback] = None,
) -> dict:
    state = dict(initial_state)

    if on_progress:
        await on_progress(10, _default_agents({"coordinator": "working"}))

    state.update(await coordinator_node(state))

    budget_targets = state.get("constraints") or {}
    transport_budget = budget_targets.get("transport", state["budget_max"])
    accommodation_budget = budget_targets.get("accommodation", state["budget_max"])
    attraction_budget = budget_targets.get("attraction", state["budget_max"])
    dining_budget = budget_targets.get("dining", state["budget_max"])

    if on_progress:
        await on_progress(25, _default_agents({
            "coordinator": "done",
            "transport": "working",
            "accommodation": "working",
            "attraction": "working",
            "dining": "working",
        }))

    transport_result, accommodation_result, attraction_result, dining_result = (
        await asyncio.gather(
            transport_node(state, budget_target=transport_budget),
            accommodation_node(state, budget_target=accommodation_budget),
            attraction_node(state, budget_target=attraction_budget),
            dining_node(state, budget_target=dining_budget),
            return_exceptions=True,
        )
    )

    for key, result in [
        ("transport_plan", transport_result),
        ("accommodation_plan", accommodation_result),
        ("attraction_plan", attraction_result),
        ("dining_plan", dining_result),
    ]:
        if isinstance(result, Exception):
            state[key] = {"raw": "{}", "error": str(result)}
            state["messages"].append(
                HumanMessage(content=f"{key} 失败: {result}", name=key.split("_")[0])
            )
        else:
            state.update(result)

    if on_progress:
        await on_progress(60, _default_agents({
            "coordinator": "done",
            "transport": "done",
            "accommodation": "done",
            "attraction": "done",
            "dining": "done",
            "strategy": "working",
        }))

    state.update(await aggregate_results(state))
    try:
        state.update(await strategy_node(state))
    except Exception as e:
        state["final_plan"] = {"raw": "{}", "error": str(e)}
        state["messages"].append(
            HumanMessage(content=f"策略整合失败: {e}", name="strategy")
        )

    if on_progress:
        await on_progress(90, _default_agents({
            "coordinator": "done",
            "transport": "done",
            "accommodation": "done",
            "attraction": "done",
            "dining": "done",
            "strategy": "done",
        }))

    return state


def extract_trip_from_final_plan(final_plan: dict) -> dict:
    raw = final_plan.get("raw", "{}")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            parsed = json.loads(match.group())
        else:
            raise ValueError(f"无法解析 Agent 输出: {raw[:200]}")

    for day in parsed.get("days", []):
        for activity in day.get("activities", []):
            raw_id = activity.get("id")
            if not raw_id or not isinstance(raw_id, str):
                activity["id"] = str(uuid.uuid4())
            if isinstance(activity.get("duration"), float):
                activity["duration"] = int(round(activity["duration"]))
    if "summary" in parsed and isinstance(parsed["summary"], dict):
        for key in ("total_cost",):
            if key in parsed["summary"] and isinstance(parsed["summary"][key], float):
                parsed["summary"][key] = int(round(parsed["summary"][key]))
    return parsed
