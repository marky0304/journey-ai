from typing import Dict, List, Optional, TypedDict
from typing_extensions import Annotated


def add_messages(existing: list, new: list) -> list:
    return existing + new


class AgentState(TypedDict):
    start_location: str
    destination: str
    start_date: str
    end_date: str
    budget_min: int
    budget_max: int
    currency: str
    preferences: List[str]
    travel_style: str

    messages: Annotated[list, add_messages]

    constraints: Optional[dict]

    transport_plan: Optional[dict]
    accommodation_plan: Optional[dict]
    attraction_plan: Optional[dict]
    dining_plan: Optional[dict]

    final_plan: Optional[dict]
    error: Optional[str]
