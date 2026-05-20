from typing import List, Optional

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
    location: Optional[GeoPoint] = None
    description: Optional[str] = None
    tips: Optional[str] = None
    image_url: Optional[str] = None


class DayPlanOut(BaseModel):
    day_index: int
    date: str
    activities: List[ActivityOut]


class TripSummary(BaseModel):
    total_cost: int
    attraction_count: int


class TripOut(BaseModel):
    id: str
    destination: str
    dates: dict
    budget: dict
    preferences: List[str]
    travel_style: str
    days: List[DayPlanOut]
    summary: TripSummary


class AgentInfo(BaseModel):
    name: str
    status: str


class TaskStatusOut(BaseModel):
    task_id: str
    status: str
    progress: int
    agents: List[AgentInfo]
    trip_id: Optional[str] = None
    error_message: Optional[str] = None


class PlanResponse(BaseModel):
    task_id: str


class WeatherDay(BaseModel):
    date: str
    temp_max: int
    temp_min: int
    text_day: str
    text_night: str
    humidity: int = 0
    wind_dir: str = ""
    wind_scale: str = ""


class WeatherInfo(BaseModel):
    city: str
    forecast: List[WeatherDay]


class OutfitSuggestion(BaseModel):
    date: str
    suggestion: str


class WeatherResponse(BaseModel):
    weather: Optional[WeatherInfo] = None
    outfits: List[OutfitSuggestion] = []


class CancelResponse(BaseModel):
    success: bool
