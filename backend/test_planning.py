import asyncio
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.user import User
from app.core.planning.planning_service import PlanningService
from decimal import Decimal

async def test():
    async with SessionLocal() as db:
        user = (await db.execute(select(User))).scalars().first()
        if user:
            res = await PlanningService.get_user_planning_overview(db, user.id)
            print("Overview return:", res["overview"]["portfolio_avg_return"])
        else:
            print("No user")

asyncio.run(test())
