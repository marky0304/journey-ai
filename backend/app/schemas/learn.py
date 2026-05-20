from typing import List, Optional

from pydantic import BaseModel, Field


class LearnRequest(BaseModel):
    url: str = Field(..., max_length=2000)


class KnowledgePoint(BaseModel):
    point: str
    category: str


class LearnItemOut(BaseModel):
    id: str
    url: str
    platform: str
    title: str
    summary: str
    knowledge_points: List[KnowledgePoint] = []
    tags: List[str] = []
    location: Optional[str] = None
    practical_info: Optional[dict] = None
    quality_score: float = 0.0
    status: str = "active"
    created_at: str
    merged_at: Optional[str] = None


class LearnListResponse(BaseModel):
    items: List[LearnItemOut]
    total: int


class LearnHistoryOut(BaseModel):
    id: str
    url: str
    platform: str
    title: str
    summary: str
    knowledge_points: List[KnowledgePoint] = []
    tags: List[str] = []
    location: Optional[str] = None
    quality_score: float = 0.0
    learned_at: str


class LearnHistoryListResponse(BaseModel):
    items: List[LearnHistoryOut]
    total: int


class LearnAnalyzeResult(BaseModel):
    history: LearnHistoryOut
    knowledge_points: List[KnowledgePoint]
    summary: str
    practical_info: Optional[dict] = None


class GlobalKnowledgeOut(BaseModel):
    id: str
    title: str
    summary: str
    knowledge_points: List[KnowledgePoint] = []
    tags: List[str] = []
    location: Optional[str] = None
    practical_info: Optional[dict] = None
    quality_score: float
    merged_count: int
    updated_at: str


class GlobalKnowledgeListResponse(BaseModel):
    items: List[GlobalKnowledgeOut]
    total: int


class LearnSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    n_results: int = Field(5, ge=1, le=20)


class LearnSearchResultItem(BaseModel):
    id: str
    document: str
    distance: float
    metadata: dict = {}


class LearnSearchResult(BaseModel):
    items: List[LearnSearchResultItem]
    query: str


class MergeReport(BaseModel):
    new_items: int = 0
    merged_items: int = 0
    cleaned_items: int = 0


class KnowledgeStats(BaseModel):
    total_user_items: int
    active_items: int
    merged_items: int
    global_items: int
