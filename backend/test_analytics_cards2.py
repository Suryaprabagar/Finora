import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.investment import Investment
from app.core.analytics.analytics_service import AnalyticsService
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        for user in users:
            inv_result = await db.execute(select(Investment).where(Investment.user_id == user.id))
            invs = inv_result.scalars().all()
            if invs:
                print(f"User: {user.email} (ID: {user.id}) has {len(invs)} investments")
                try:
                    analytics = await AnalyticsService.get_dashboard_analytics(db, user.id)
                    print("  Analytics generated successfully!")
                    print("  Keys:", analytics.keys())
                except Exception as e:
                    print("  ERROR generating analytics:", repr(e))
                    import traceback
                    traceback.print_exc()

asyncio.run(main())
