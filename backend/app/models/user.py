"""User model - core authentication and profile."""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    currency_symbol: Mapped[str] = mapped_column(String(5), default="\u20b9", nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="light", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    categories: Mapped[list["Category"]] = relationship(back_populates="user", lazy="select")
    bank_accounts: Mapped[list["BankAccount"]] = relationship(back_populates="user", lazy="select")
    credit_cards: Mapped[list["CreditCard"]] = relationship(back_populates="user", lazy="select")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", lazy="select")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="user", lazy="select")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", lazy="select")
    bills: Mapped[list["Bill"]] = relationship(back_populates="user", lazy="select")
    investments: Mapped[list["Investment"]] = relationship(back_populates="user", lazy="select")
    loans: Mapped[list["Loan"]] = relationship(back_populates="user", lazy="select")
    assets: Mapped[list["Asset"]] = relationship(back_populates="user", lazy="select")
    insurance_policies: Mapped[list["InsurancePolicy"]] = relationship(back_populates="user", lazy="select")
    portfolio_snapshots: Mapped[list["PortfolioSnapshot"]] = relationship(back_populates="user", lazy="select")

