"""Bill and BillPayment models."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, ForeignKey, func, Numeric, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # utilities, subscriptions, insurance, rent, emi, internet, etc.
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)  # day of month (1-31)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)  # monthly | quarterly | yearly
    auto_pay: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("bank_accounts.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active | paused | cancelled
    last_paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="bills")
    payments: Mapped[list["BillPayment"]] = relationship(back_populates="bill", cascade="all, delete-orphan")


class BillPayment(Base):
    __tablename__ = "bill_payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    bill_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("bills.id", ondelete="CASCADE"), index=True, nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    paid_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="paid", nullable=False)  # paid | partial | overdue
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    bill: Mapped["Bill"] = relationship(back_populates="payments")
