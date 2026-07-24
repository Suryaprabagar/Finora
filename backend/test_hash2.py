import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
from app.core.security import verify_password

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user:
            print("Hash:", user.hashed_password)
            try:
                res = verify_password('password', user.hashed_password)
                print("Verify result:", res)
            except Exception as e:
                import traceback
                traceback.print_exc()

asyncio.run(main())
