from typing import List, Optional

from pydantic import BaseModel


class InspireRequest(BaseModel):
    preferences: Optional[str] = None
    budget_min: Optional[int] = 0
    budget_max: Optional[int] = 10000
    days: Optional[int] = 3


class DestinationCard(BaseModel):
    name: str
    reason: str
    season: str
    budget_estimate: int
    highlights: List[str]
    tags: List[str]


class InspireResponse(BaseModel):
    destinations: List[DestinationCard]
