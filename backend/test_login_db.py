import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def main():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            print("Successfully queried user:", user.email if user else None)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
