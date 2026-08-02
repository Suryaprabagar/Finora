"""Investment model for portfolio tracking."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, ForeignKey, func, Numeric, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # Types: stocks | mutual_fund | gold | fd | ppf | nps | bonds | etf | real_estate
    symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)  # stock ticker
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("1"), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interest_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # for FD/PPF/NPS/Bonds
    coupon_frequency: Mapped[str | None] = mapped_column(String(20), nullable=True)  # monthly, quarterly, semi-annually, annually
    next_coupon_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    broker: Mapped[str | None] = mapped_column(String(100), nullable=True)
    folio_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="investments")
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True)
