"""User profile schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    currency: str
    currency_symbol: str
    theme: str
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    currency: Optional[str] = None
    currency_symbol: Optional[str] = None
    theme: Optional[str] = None
    phone: Optional[str] = None
