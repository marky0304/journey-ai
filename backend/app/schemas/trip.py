from datetime import datetime

from pydantic import BaseModel


class GeoPoint(BaseModel):
    lat: float
    lng: float


class ActivityOut(BaseModel):
    id: str
    type: str
    name: str
    start_time: str
    end_time: str
    duration: int
    location: GeoPoint | None = None
    description: str | None = None
    tips: str | None = None
    image_url: str | None = None


class DayPlanOut(BaseModel):
    day_index: int
    date: str
    activities: list[ActivityOut]


class TripSummary(BaseModel):
    total_cost: int
    attraction_count: int


class TripOut(BaseModel):
    id: str
    destination: str
    dates: dict
    budget: dict
    preferences: list[str]
    travel_style: str
    days: list[DayPlanOut]
    summary: TripSummary


class AgentInfo(BaseModel):
    name: str
    status: str


class TaskStatusOut(BaseModel):
    task_id: str
    status: str
    progress: int
    agents: list[AgentInfo]
    trip_id: str | None = None
    error_message: str | None = None


class PlanResponse(BaseModel):
    task_id: str


class CancelResponse(BaseModel):
    success: bool
