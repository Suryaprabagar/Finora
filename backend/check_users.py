import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User.email, User.is_active)
        )

        for email, is_active in result.all():
            print(f"{email} | active={is_active}")


if __name__ == "__main__":
    asyncio.run(main())