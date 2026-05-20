from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class ClarifyRequest(BaseModel):
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_min: int = 0
    budget_max: int = 100000
    currency: str = "CNY"
    preferences: List[str] = Field(default_factory=list)
    travel_style: str = "balanced"
    messages: List[dict] = Field(default_factory=list)


class ClarifyResponse(BaseModel):
    done: bool
    message: str
    questions_asked: int = 0
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    currency: Optional[str] = None
    preferences: Optional[List[str]] = None
    travel_style: Optional[str] = None
