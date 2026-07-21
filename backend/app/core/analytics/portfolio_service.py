from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.portfolio_snapshot import PortfolioSnapshot
from app.models.investment import Investment
from datetime import date, timedelta
from decimal import Decimal
import uuid

class PortfolioService:
    @staticmethod
    async def get_growth_history(db: AsyncSession, user_id: uuid.UUID):
        """Fetches historical portfolio snapshots for the growth chart."""
        result = await db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.user_id == user_id)
            .order_by(PortfolioSnapshot.date)
        )
        snapshots = result.scalars().all()
        
        # If no snapshots exist (new user), we create a baseline estimation point based on total invested
        if not snapshots:
            return await PortfolioService._estimate_growth(db, user_id)
            
        history = []
        for snap in snapshots:
            history.append({
                "date": snap.date.isoformat(),
                "value": float(snap.total_value),
                "invested": float(snap.invested_amount),
                "return_pct": float(snap.total_return_pct)
            })
            
        return history

    @staticmethod
    async def _estimate_growth(db: AsyncSession, user_id: uuid.UUID):
        # Fallback estimation for brand new users with no snapshots yet
        # Fetch current investments
        result = await db.execute(
            select(Investment).where(Investment.user_id == user_id, Investment.is_active.is_(True), Investment.deleted_at.is_(None))
        )
        investments = result.scalars().all()
        if not investments:
            return []
            
        total_invested = sum(inv.purchase_price * inv.quantity for inv in investments)
        total_value = sum(inv.current_price * inv.quantity for inv in investments)
        
        # Find oldest investment date
        oldest_date = min(inv.purchase_date for inv in investments)
        today = date.today()
        
        # Just return 2 points: Start and Today
        history = [
            {
                "date": oldest_date.isoformat(),
                "value": float(total_invested), # Assume value was equal to invested at start
                "invested": float(total_invested),
                "return_pct": 0.0
            },
            {
                "date": today.isoformat(),
                "value": float(total_value),
                "invested": float(total_invested),
                "return_pct": float(((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0)
            }
        ]
        return history

    @staticmethod
    async def create_snapshot(db: AsyncSession, user_id: uuid.UUID, total_value: Decimal, invested_amount: Decimal, todays_gain: Decimal = Decimal('0')):
        """Creates or updates a snapshot for today."""
        today = date.today()
        
        # Check if snapshot exists for today
        result = await db.execute(
            select(PortfolioSnapshot).where(PortfolioSnapshot.user_id == user_id, PortfolioSnapshot.date == today)
        )
        existing = result.scalar_one_or_none()
        
        unrealized_gain = total_value - invested_amount
        return_pct = float(((total_value - invested_amount) / invested_amount * 100) if invested_amount > 0 else 0)
        
        if existing:
            existing.total_value = total_value
            existing.invested_amount = invested_amount
            existing.unrealized_gain = unrealized_gain
            existing.todays_gain = todays_gain
            existing.total_return_pct = return_pct
        else:
            new_snap = PortfolioSnapshot(
                user_id=user_id,
                date=today,
                total_value=total_value,
                invested_amount=invested_amount,
                unrealized_gain=unrealized_gain,
                todays_gain=todays_gain,
                total_return_pct=return_pct
            )
            db.add(new_snap)
        
        await db.commit()
