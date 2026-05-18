import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import PlanningTask, TaskStatus


async def create_task(db: AsyncSession, preferences: dict, celery_task_id: str) -> PlanningTask:
    task = PlanningTask(
        preferences=preferences,
        celery_task_id=celery_task_id,
        status=TaskStatus.processing,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> PlanningTask | None:
    result = await db.execute(select(PlanningTask).where(PlanningTask.id == task_id))
    return result.scalar_one_or_none()


async def update_task_status(
    db: AsyncSession,
    task: PlanningTask,
    status: TaskStatus,
    error_message: str | None = None,
) -> None:
    task.status = status
    if error_message:
        task.error_message = error_message
    if status in (TaskStatus.completed, TaskStatus.failed):
        task.completed_at = datetime.utcnow()
    await db.commit()


async def cancel_task(db: AsyncSession, task: PlanningTask) -> None:
    task.status = TaskStatus.failed
    task.error_message = "用户取消"
    task.completed_at = datetime.utcnow()
    await db.commit()
