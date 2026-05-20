from fastapi import APIRouter

from app.api.trip import router as trip_router
from app.api.auth import router as auth_router
from app.api.learn import router as learn_router
from app.api.chat import router as chat_router

api_router = APIRouter()
api_router.include_router(trip_router, prefix="/trip")
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(learn_router, prefix="/learn")
api_router.include_router(chat_router, prefix="/v1/chat")
