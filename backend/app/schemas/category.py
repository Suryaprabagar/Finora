"""Category schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class CategoryCreate(BaseModel):
    name: str
    type: str  # income | expense
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryUpdate(CategoryCreate):
    pass


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    icon: Optional[str] = None
    color: Optional[str] = None
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True
