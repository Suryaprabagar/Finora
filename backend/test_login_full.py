import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.schemas.user import UserResponse

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user:
            print("Access token:", create_access_token({"sub": str(user.id)}))
            print("Refresh token:", create_refresh_token({"sub": str(user.id)}))
            try:
                res = UserResponse.model_validate(user).model_dump()
                print("User dump:", res)
            except Exception as e:
                import traceback
                traceback.print_exc()

asyncio.run(main())
