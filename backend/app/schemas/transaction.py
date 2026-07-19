"""Transaction schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class TransactionCreate(BaseModel):
    type: str
    amount: Decimal
    description: str
    merchant: Optional[str] = None
    date: date
    category_id: Optional[uuid.UUID] = None
    bank_account_id: Optional[uuid.UUID] = None
    credit_card_id: Optional[uuid.UUID] = None
    status: str = "cleared"
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    is_recurring: bool = False
    recurring_interval: Optional[str] = None
    tags: Optional[str] = None


class TransactionUpdate(TransactionCreate):
    pass


class CategoryBasic(BaseModel):
    id: uuid.UUID
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


class BankAccountBasic(BaseModel):
    id: uuid.UUID
    name: str
    bank_name: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    id: uuid.UUID
    type: str
    amount: Decimal
    description: str
    merchant: Optional[str] = None
    date: date
    status: str
    payment_method: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    category: Optional[CategoryBasic] = None
    bank_account_id: Optional[uuid.UUID] = None
    bank_account: Optional[BankAccountBasic] = None
    credit_card_id: Optional[uuid.UUID] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    is_recurring: bool
    recurring_interval: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BulkDeleteRequest(BaseModel):
    ids: list[uuid.UUID]
