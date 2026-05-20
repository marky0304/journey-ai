from app.models.task import PlanningTask
from app.models.trip import Trip
from app.models.user import User
from app.models.knowledge import UserKnowledge, GlobalKnowledge, LearnHistory
from app.models.chat import ChatSession, UserPreference
from app.core.database import Base

__all__ = ["Base", "PlanningTask", "Trip", "User", "UserKnowledge", "GlobalKnowledge", "LearnHistory", "ChatSession", "UserPreference"]
