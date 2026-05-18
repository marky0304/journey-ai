from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    destination: str
    start_date: str
    end_date: str
    budget_min: int
    budget_max: int
    currency: str
    preferences: list[str]
    travel_style: str

    messages: Annotated[list, add_messages]

    transport_plan: dict | None
    accommodation_plan: dict | None
    attraction_plan: dict | None
    dining_plan: dict | None

    final_plan: dict | None
    error: str | None
