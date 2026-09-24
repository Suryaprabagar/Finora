"""Budget schemas."""
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator
from typing import Optional


class BudgetItemCreate(BaseModel):
    name: str
    allocated_amount: Decimal
    category_id: Optional[uuid.UUID] = None


class BudgetItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    allocated_amount: Decimal
    category_id: Optional[uuid.UUID] = None
    spent_amount: Decimal = Decimal("0")
    percentage_used: float = 0.0

    class Config:
        from_attributes = True


class BudgetCreate(BaseModel):
    name: str
    month: int          # 1-12
    year: int           # e.g. 2026
    total_limit: Decimal
    alert_threshold: int = 80
    items: list[BudgetItemCreate] = []

    @field_validator("total_limit")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("total_limit must be greater than 0")
        return v

    @field_validator("month")
    @classmethod
    def month_valid(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("month must be between 1 and 12")
        return v


class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    total_limit: Optional[Decimal] = None
    alert_threshold: Optional[int] = None
    items: Optional[list[BudgetItemCreate]] = None


class BudgetResponse(BaseModel):
    id: uuid.UUID
    name: str
    month: int
    year: int
    # YYYY-MM convenience string for frontend
    month_str: str = ""
    total_limit: Decimal
    alert_threshold: int
    # Computed spending fields (populated by API endpoints, not ORM)
    total_spent: Decimal = Decimal("0")
    remaining_total: Decimal = Decimal("0")
    days_remaining: int = 0
    percentage_used: float = 0.0
    items: list[BudgetItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

    def model_post_init(self, __context: object) -> None:
        """Auto-compute month_str if not set."""
        if not self.month_str:
            # bypass frozen validation by using object.__setattr__
            object.__setattr__(self, "month_str", f"{self.year:04d}-{self.month:02d}")
