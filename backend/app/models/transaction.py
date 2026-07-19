"""Transaction model - the core financial event."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, ForeignKey, func, Numeric, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("categories.id"), nullable=True, index=True)
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("bank_accounts.id"), nullable=True, index=True)
    credit_card_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("credit_cards.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # income | expense | transfer
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    merchant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="cleared", nullable=False)  # cleared | pending | reconciled
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)  # cash | card | upi | netbanking | cheque
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurring_interval: Mapped[str | None] = mapped_column(String(20), nullable=True)  # daily | weekly | monthly | yearly
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True)  # comma-separated
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="transactions")
    category: Mapped["Category | None"] = relationship(back_populates="transactions")
    bank_account: Mapped["BankAccount | None"] = relationship(
        back_populates="transactions",
        foreign_keys=[bank_account_id],
    )
    credit_card: Mapped["CreditCard | None"] = relationship(back_populates="transactions")
