"""Portfolio Snapshot model for analytics."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    total_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    invested_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unrealized_gain: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    todays_gain: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_return_pct: Mapped[float] = mapped_column(nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="portfolio_snapshots")
