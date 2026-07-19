"""Investment schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class InvestmentCreate(BaseModel):
    name: str
    type: str
    symbol: Optional[str] = None
    purchase_price: Decimal
    current_price: Decimal
    quantity: Decimal = Decimal("1")
    purchase_date: date
    maturity_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None
    broker: Optional[str] = None
    folio_number: Optional[str] = None
    notes: Optional[str] = None


class InvestmentUpdate(InvestmentCreate):
    is_active: Optional[bool] = None


class InvestmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    symbol: Optional[str] = None
    purchase_price: Decimal
    current_price: Decimal
    quantity: Decimal
    purchase_date: date
    maturity_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None
    broker: Optional[str] = None
    folio_number: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    current_value: Decimal = Decimal("0")
    gain_loss: Decimal = Decimal("0")
    gain_loss_percent: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True
