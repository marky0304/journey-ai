from fastapi import APIRouter

from app.api.trip import router as trip_router

api_router = APIRouter()
api_router.include_router(trip_router, prefix="/trip")
