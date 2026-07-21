import asyncio
from app.core.database import async_session_maker
from app.core.analytics.analytics_service import AnalyticsService
import uuid
from sqlalchemy import text

async def main():
    async with async_session_maker() as db:
        res = await db.execute(text("SELECT id FROM users LIMIT 1"))
        u_id_str = res.scalar()
        if not u_id_str:
            print("No users found")
            return
        u_id = uuid.UUID(u_id_str)
        try:
            data = await AnalyticsService.get_dashboard_analytics(db, u_id)
            print("SUCCESS")
            # print(data)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
