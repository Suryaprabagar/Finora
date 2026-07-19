"""Shared Pydantic schema primitives."""
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')


class Pagination(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    pagination: Optional[Pagination] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
