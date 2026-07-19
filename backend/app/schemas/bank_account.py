"""Bank account schemas."""
import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class BankAccountCreate(BaseModel):
    name: str
    account_type: str
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    balance: Decimal = Decimal("0")
    interest_rate: Optional[Decimal] = None
    color: Optional[str] = None
    notes: Optional[str] = None


class BankAccountUpdate(BankAccountCreate):
    pass


class BankAccountResponse(BaseModel):
    id: uuid.UUID
    name: str
    account_type: str
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    balance: Decimal
    interest_rate: Optional[Decimal] = None
    is_active: bool
    color: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransferRequest(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: Decimal
    description: str
    date: str
