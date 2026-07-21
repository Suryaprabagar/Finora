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
            print(f"User: {user.email}")
            inv_result = await db.execute(select(Investment).where(Investment.user_id == user.id))
            invs = inv_result.scalars().all()
            print(f"  Investments count: {len(invs)}")
            if invs:
                try:
                    analytics = await AnalyticsService.get_dashboard_analytics(db, user.id)
                    print(f"  Analytics: summary total_value={analytics.get('summary', {}).get('total_value')}")
                    print(f"  Allocation distribution length={len(analytics.get('allocation', {}).get('distribution', []))}")
                    print(f"  Risk Profile score={analytics.get('risk_profile', {}).get('score')}")
                    print(f"  Growth History length={len(analytics.get('growth_history', []))}")
                except Exception as e:
                    print(f"  Analytics error: {e}")
                    import traceback
                    traceback.print_exc()
            print("-" * 20)

asyncio.run(main())
