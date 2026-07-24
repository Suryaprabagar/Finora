"""Goal schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class GoalCreate(BaseModel):
    name: str
    goal_type: str
    strategy: str = "Savings Only"
    risk_profile: str = "Moderate"
    importance: str = "Medium"
    priority_override: Optional[int] = None
    target_amount: Decimal
    target_date: Optional[date] = None
    monthly_contribution: Decimal = Decimal("0")
    notes: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None


class GoalUpdate(BaseModel):
    name: Optional[str] = None
    goal_type: Optional[str] = None
    strategy: Optional[str] = None
    risk_profile: Optional[str] = None
    importance: Optional[str] = None
    priority_override: Optional[int] = None
    target_amount: Optional[Decimal] = None
    target_date: Optional[date] = None
    monthly_contribution: Optional[Decimal] = None
    notes: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None


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
    user_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    name: str
    goal_type: str
    strategy: str
    risk_profile: str
    importance: str
    priority_override: Optional[int] = None
    target_amount: Decimal
    target_date: Optional[date] = None
    monthly_contribution: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # We omit current_amount, progress_percentage, etc from the base response
    # because they are generated dynamically by PlanningService.

    class Config:
        from_attributes = True
