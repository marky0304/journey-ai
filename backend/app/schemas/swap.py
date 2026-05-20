from typing import List, Optional

from pydantic import BaseModel

from app.schemas.trip import ActivityOut


class SwapRequest(BaseModel):
    day_index: int
    activity_id: str
    type: str
    name: str
    destination: str
    preferences: List[str] = []
    context: Optional[str] = None


class SwapResponse(ActivityOut):
    reason: str = ""
