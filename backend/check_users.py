import asyncio, sys
sys.path.append('.')
from app.core.database import AsyncSessionLocal
from app.models import User
from sqlalchemy import select

async def main():
    db = AsyncSessionLocal()
    users = (await db.execute(select(User))).scalars().all()
    print([(str(u.id), u.email, u.full_name) for u in users])
    await db.close()

if __name__ == '__main__':
    asyncio.run(main())
