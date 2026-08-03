"""Shared Pydantic schema primitives."""
from pydantic import BaseModel, model_validator
from typing import Generic, TypeVar, Optional

T = TypeVar('T')


class Pagination(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: Optional[int] = None

    @model_validator(mode='after')
    def set_total_pages(self) -> 'Pagination':
        if self.total_pages is None and self.per_page > 0:
            self.total_pages = (self.total + self.per_page - 1) // self.per_page
        return self


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
