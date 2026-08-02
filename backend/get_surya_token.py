import asyncio, sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token
from sqlalchemy import select

async def main():
    db = AsyncSessionLocal()
    user = (await db.execute(select(User).where(User.email=='surya1332005@gmail.com'))).scalar_one()
    print(create_access_token({'sub': str(user.id)}))
    await db.close()

if __name__ == '__main__':
    asyncio.run(main())
