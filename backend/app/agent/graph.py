import json
import re
import uuid

from langgraph.graph import END, StateGraph

from app.agent.accommodation import accommodation_node
from app.agent.attraction import attraction_node
from app.agent.coordinator import coordinator_node
from app.agent.dining import dining_node
from app.agent.state import AgentState
from app.agent.strategy import strategy_node
from app.agent.transport import transport_node


async def aggregate_results(state: AgentState) -> dict:
    return {"messages": []}


def build_trip_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("transport", transport_node)
    workflow.add_node("accommodation", accommodation_node)
    workflow.add_node("attraction", attraction_node)
    workflow.add_node("dining", dining_node)
    workflow.add_node("aggregate", aggregate_results)
    workflow.add_node("strategy", strategy_node)

    workflow.set_entry_point("coordinator")

    workflow.add_edge("coordinator", "transport")
    workflow.add_edge("coordinator", "accommodation")
    workflow.add_edge("coordinator", "attraction")
    workflow.add_edge("coordinator", "dining")

    workflow.add_edge("transport", "aggregate")
    workflow.add_edge("accommodation", "aggregate")
    workflow.add_edge("attraction", "aggregate")
    workflow.add_edge("dining", "aggregate")

    workflow.add_edge("aggregate", "strategy")
    workflow.add_edge("strategy", END)

    return workflow.compile()


trip_graph = build_trip_graph()


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
            if not activity.get("id"):
                activity["id"] = str(uuid.uuid4())
    return parsed
