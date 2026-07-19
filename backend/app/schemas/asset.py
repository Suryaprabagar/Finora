"""Asset schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class AssetCreate(BaseModel):
    name: str
    asset_type: str
    purchase_price: Decimal
    current_value: Decimal
    purchase_date: date
    description: Optional[str] = None
    location: Optional[str] = None
    serial_number: Optional[str] = None
    depreciation_rate: Optional[Decimal] = None
    is_insured: bool = False


class AssetUpdate(AssetCreate):
    pass


class AssetResponse(BaseModel):
    id: uuid.UUID
    name: str
    asset_type: str
    purchase_price: Decimal
    current_value: Decimal
    purchase_date: date
    description: Optional[str] = None
    location: Optional[str] = None
    serial_number: Optional[str] = None
    depreciation_rate: Optional[Decimal] = None
    is_insured: bool
    appreciation_loss: Decimal = Decimal("0")
    appreciation_percent: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True
