"""AssetAllocation and ObjectiveHistory models for the Financial Planning Engine."""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, func, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.core.database import Base


class AssetAllocation(Base):
    __tablename__ = "asset_allocations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    objective_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    objective_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    allocation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'fixed' or 'percentage'
    allocation_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ObjectiveHistory(Base):
    __tablename__ = "objective_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    objective_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    objective_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Examples: target_amount_changed, target_date_changed, asset_allocated, asset_reallocated, priority_changed, dependency_changed, monthly_contribution_updated
    old_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
