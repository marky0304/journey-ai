from datetime import date
from typing import List

from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    start_location: str = Field(..., min_length=1, max_length=100)
    destination: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: date
    budget_min: int = Field(0, ge=0)
    budget_max: int = Field(100000, ge=0)
    currency: str = Field(default="CNY")
    preferences: List[str] = Field(default_factory=list)
    travel_style: str = Field(default="balanced")
