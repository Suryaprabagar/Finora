"""Loan and LoanPayment models."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, ForeignKey, func, Numeric, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    lender: Mapped[str] = mapped_column(String(100), nullable=False)
    loan_type: Mapped[str] = mapped_column(String(30), nullable=False)  # home | vehicle | personal | education | business
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # annual %
    emi_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    paid_months: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    emi_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("bank_accounts.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="loans")
    payments: Mapped[list["LoanPayment"]] = relationship(back_populates="loan", cascade="all, delete-orphan")


class LoanPayment(Base):
    __tablename__ = "loan_payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    loan_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("loans.id", ondelete="CASCADE"), index=True, nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    emi_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    principal_component: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    interest_component: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="paid", nullable=False)  # paid | pending | overdue
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    loan: Mapped["Loan"] = relationship(back_populates="payments")
