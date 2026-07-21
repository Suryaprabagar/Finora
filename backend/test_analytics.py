import asyncio
from app.core.database import SessionLocal
from app.core.analytics.analytics_service import AnalyticsService
import uuid

async def main():
    async with SessionLocal() as db:
        user_id = uuid.UUID('e8029d2b-c567-464a-97ab-9c17e0abfc1f') # Hardcoded or use db to find a user
        # Actually I can just select first user
        from sqlalchemy import text
        res = await db.execute(text("SELECT id FROM users LIMIT 1"))
        u_id_str = res.scalar()
        if not u_id_str:
            print("No users found")
            return
        u_id = uuid.UUID(u_id_str)
        data = await AnalyticsService.get_dashboard_analytics(db, u_id)
        print("Summary:", data['summary'])
        print("Allocation:", data['allocation']['total_value'])
        print("Risk:", data['risk_profile']['profile'])

asyncio.run(main())
