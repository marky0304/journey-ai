from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


class SendMessageRequest(BaseModel):
    trip_id: str
    session_id: str
    message: str = Field(..., min_length=1, max_length=2000)


class SendMessageResponse(BaseModel):
    reply: str
    suggestions: list[str] = []


class SessionItem(BaseModel):
    session_id: str
    first_message: str
    message_count: int
    started_at: datetime
    last_active_at: datetime


class TripSessionGroup(BaseModel):
    trip_id: str
    trip_name: str
    is_current_trip: bool
    sessions: list[SessionItem]


class HistoryResponse(BaseModel):
    groups: list[TripSessionGroup]


class SessionHistoryResponse(BaseModel):
    session_id: str
    trip_name: str
    messages: list[dict]


class RestoreRequest(BaseModel):
    trip_id: str
    original_session_id: str


class RestoreResponse(BaseModel):
    new_session_id: str
    messages: list[dict]


class CloseSessionRequest(BaseModel):
    session_id: str


class PreferenceOut(BaseModel):
    id: str
    category: str
    content: str
    confidence: float


class ContextResponse(BaseModel):
    trip_meta: Optional[dict] = None
    suggested_questions: list[str] = []
