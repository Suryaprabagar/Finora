import asyncio
from app.core.database import AsyncSessionLocal
from app.services.auth_service import authenticate_user
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT email FROM users LIMIT 1"))
        email = res.scalar()
        if not email:
            print("No users found")
            return
        print(f"Testing auth for {email}")
        try:
            # We don't have the password, but we can just see if querying user works.
            from app.models.user import User
            from sqlalchemy import select
            user = await db.execute(select(User).where(User.email == email))
            print("User fetch successful")
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
