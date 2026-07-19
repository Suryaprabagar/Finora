"""Bill schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class BillCreate(BaseModel):
    name: str
    category: str
    amount: Decimal
    due_day: int
    is_recurring: bool = True
    frequency: str = "monthly"
    auto_pay: bool = False
    bank_account_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    icon: Optional[str] = None


class BillUpdate(BillCreate):
    status: Optional[str] = None


class BillPaymentCreate(BaseModel):
    amount_paid: Decimal
    paid_date: date
    status: str = "paid"
    notes: Optional[str] = None


class BillResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    amount: Decimal
    due_day: int
    is_recurring: bool
    frequency: str
    auto_pay: bool
    status: str
    last_paid_date: Optional[date] = None
    next_due_date: Optional[date] = None
    notes: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
