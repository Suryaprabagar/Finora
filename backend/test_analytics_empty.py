import asyncio
import json
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.analytics.analytics_service import AnalyticsService
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "surya1332005@gmail.com"))
        user = result.scalars().first()
        if user:
            analytics = await AnalyticsService.get_dashboard_analytics(db, user.id)
            print(json.dumps(analytics, indent=2))

asyncio.run(main())
