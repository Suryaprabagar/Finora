"""Loan schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class LoanCreate(BaseModel):
    name: str
    lender: str
    loan_type: str
    principal_amount: Decimal
    outstanding_balance: Decimal
    interest_rate: Decimal
    emi_amount: Decimal
    tenure_months: int
    start_date: date
    end_date: date
    emi_day: int = 1
    bank_account_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class LoanUpdate(LoanCreate):
    paid_months: Optional[int] = None
    is_active: Optional[bool] = None


class LoanResponse(BaseModel):
    id: uuid.UUID
    name: str
    lender: str
    loan_type: str
    principal_amount: Decimal
    outstanding_balance: Decimal
    interest_rate: Decimal
    emi_amount: Decimal
    tenure_months: int
    paid_months: int
    start_date: date
    end_date: date
    emi_day: int
    is_active: bool
    notes: Optional[str] = None
    progress_percentage: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True


class LoanPaymentCreate(BaseModel):
    payment_date: date
    amount_paid: Optional[Decimal] = None
    bank_account_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
