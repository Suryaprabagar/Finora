"""Budget schemas."""
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
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
    month: int
    year: int
    total_limit: Decimal
    alert_threshold: int = 80
    items: list[BudgetItemCreate] = []


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
    total_limit: Decimal
    alert_threshold: int
    total_spent: Decimal = Decimal("0")
    items: list[BudgetItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True
