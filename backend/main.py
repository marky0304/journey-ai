from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router


from app.core.database import engine, Base, async_session
from app.models.task import PlanningTask, TaskStatus


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Clean up orphaned processing tasks (async tasks don't survive restarts)
    try:
        from sqlalchemy import select

        async with async_session() as db:
            result = await db.execute(
                select(PlanningTask).where(PlanningTask.status == TaskStatus.processing)
            )
            orphans = result.scalars().all()
            for task in orphans:
                task.status = TaskStatus.failed
                task.error_message = "服务重启，任务中断"
            if orphans:
                await db.commit()
    except Exception:
        pass

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
