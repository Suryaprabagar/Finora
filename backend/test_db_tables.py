import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        try:
            res = await db.execute(text("SELECT * FROM portfolio_snapshots LIMIT 1"))
            print("Snapshots OK")
        except Exception as e:
            print("Snapshots ERROR:", e)
            
        try:
            res = await db.execute(text("SELECT * FROM users LIMIT 1"))
            print("Users OK")
        except Exception as e:
            print("Users ERROR:", e)

asyncio.run(main())
