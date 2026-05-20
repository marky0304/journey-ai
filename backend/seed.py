"""Seed script: creates a test user account."""
import asyncio
import uuid

from app.core.database import engine, async_session, Base
from app.models.user import User
from app.core.auth import get_password_hash


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.username == "test"))
        if result.scalar_one_or_none():
            print("Test user already exists. Skipping.")
            return

        user = User(
            id=uuid.uuid4(),
            username="test",
            email="test@test.com",
            password_hash=get_password_hash("123456"),
            is_admin=True,
        )
        session.add(user)
        await session.commit()
        print("Test user created:")
        print("  Username: test")
        print("  Password: 123456")
        print("  Admin:    true")


if __name__ == "__main__":
    asyncio.run(seed())
