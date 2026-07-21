"""Credit card schemas."""
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class CreditCardCreate(BaseModel):
    name: str
    bank_name: str
    card_number: Optional[str] = None
    credit_limit: Decimal
    outstanding_balance: Decimal = Decimal("0")
    billing_cycle_day: int = 1
    due_day: int = 15
    interest_rate: Optional[Decimal] = None
    annual_fee: Optional[Decimal] = None
    color: Optional[str] = None


class CreditCardUpdate(CreditCardCreate):
    pass


class CreditCardResponse(BaseModel):
    id: uuid.UUID
    name: str
    bank_name: str
    card_number: Optional[str] = None
    credit_limit: Decimal
    outstanding_balance: Decimal
    billing_cycle_day: int
    due_day: int
    interest_rate: Optional[Decimal] = None
    annual_fee: Optional[Decimal] = None
    rewards_points: int
    is_active: bool
    color: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreditCardPaymentCreate(BaseModel):
    amount: Decimal
    date: str
    bank_account_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
