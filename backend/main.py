from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router


# database module created in Task 1.1
# from app.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: DB tables created via Alembic migrations or Task 1.1
    yield
    # Shutdown: cleanup if needed


app = FastAPI(title="旅程AI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
