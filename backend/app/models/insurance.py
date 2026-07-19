"""Insurance policy and claims models."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, ForeignKey, func, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    policy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # Types: life | health | vehicle | property | term | accident
    policy_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    coverage_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    annual_premium: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    premium_frequency: Mapped[str] = mapped_column(String(20), default="yearly", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    renewal_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    # Status: active | expired | cancelled | pending_renewal
    nominee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="insurance_policies")
    claims: Mapped[list["InsuranceClaim"]] = relationship(back_populates="policy", cascade="all, delete-orphan")


class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("insurance_policies.id", ondelete="CASCADE"), index=True, nullable=False)
    claim_date: Mapped[date] = mapped_column(Date, nullable=False)
    claim_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending | approved | rejected
    settlement_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    policy: Mapped["InsurancePolicy"] = relationship(back_populates="claims")
