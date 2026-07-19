"""Goal schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class GoalCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "savings"
    target_amount: Decimal
    current_amount: Decimal = Decimal("0")
    monthly_contribution: Decimal = Decimal("0")
    deadline: Optional[date] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class GoalUpdate(GoalCreate):
    status: Optional[str] = None


class GoalContributionCreate(BaseModel):
    amount: Decimal
    date: date
    notes: Optional[str] = None


class GoalContributionResponse(BaseModel):
    id: uuid.UUID
    amount: Decimal
    date: date
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GoalResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    category: str
    target_amount: Decimal
    current_amount: Decimal
    monthly_contribution: Decimal
    deadline: Optional[date] = None
    status: str
    color: Optional[str] = None
    icon: Optional[str] = None
    progress_percentage: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True
