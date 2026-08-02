import sys
import asyncio
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token
from sqlalchemy import select

async def main():
    db = AsyncSessionLocal()
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user:
        token = create_access_token({'sub': str(user.id)})
        print(token)
    else:
        print("NO_USERS")
    await db.close()

if __name__ == '__main__':
    asyncio.run(main())
