"""Transaction schemas."""
import uuid
import datetime as dt
from decimal import Decimal
from pydantic import BaseModel, model_validator
from typing import Optional


class TransactionCreate(BaseModel):
    type: str
    amount: Decimal
    description: str
    merchant: Optional[str] = None
    date: dt.date
    category_id: Optional[uuid.UUID] = None
    bank_account_id: Optional[uuid.UUID] = None
    credit_card_id: Optional[uuid.UUID] = None
    status: str = "cleared"
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    is_recurring: bool = False
    recurrence_frequency: Optional[str] = None
    recurring_interval: Optional[str] = None
    next_due_date: Optional[dt.date] = None
    recurrence_end_date: Optional[dt.date] = None
    recurring_parent_id: Optional[uuid.UUID] = None
    tags: Optional[str] = None

    @model_validator(mode="after")
    def validate_recurrence(self) -> "TransactionCreate":
        freq = self.recurrence_frequency or self.recurring_interval
        if self.is_recurring:
            if not freq:
                raise ValueError("recurrence_frequency is required when is_recurring=True")
            freq_clean = freq.lower()
            if freq_clean not in {"weekly", "monthly", "yearly"}:
                raise ValueError(f"Invalid recurrence frequency '{freq}'. Must be 'weekly', 'monthly', or 'yearly'")
            self.recurrence_frequency = freq_clean
            self.recurring_interval = freq_clean

            if not self.next_due_date:
                raise ValueError("next_due_date is required when is_recurring=True")

            if self.recurrence_end_date and self.recurrence_end_date < self.next_due_date:
                raise ValueError("recurrence_end_date cannot be before next_due_date")
        else:
            if freq:
                self.recurring_interval = freq.lower()
                self.recurrence_frequency = freq.lower()
        return self


class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    date: Optional[dt.date] = None
    category_id: Optional[uuid.UUID] = None
    bank_account_id: Optional[uuid.UUID] = None
    credit_card_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_frequency: Optional[str] = None
    recurring_interval: Optional[str] = None
    next_due_date: Optional[dt.date] = None
    recurrence_end_date: Optional[dt.date] = None
    recurring_parent_id: Optional[uuid.UUID] = None
    tags: Optional[str] = None

    @model_validator(mode="after")
    def validate_recurrence(self) -> "TransactionUpdate":
        freq = self.recurrence_frequency or self.recurring_interval
        if self.is_recurring is True:
            if not freq:
                raise ValueError("recurrence_frequency is required when is_recurring=True")
            freq_clean = freq.lower()
            if freq_clean not in {"weekly", "monthly", "yearly"}:
                raise ValueError(f"Invalid recurrence frequency '{freq}'. Must be 'weekly', 'monthly', or 'yearly'")
            self.recurrence_frequency = freq_clean
            self.recurring_interval = freq_clean

            if not self.next_due_date:
                raise ValueError("next_due_date is required when is_recurring=True")

            if self.recurrence_end_date and self.recurrence_end_date < self.next_due_date:
                raise ValueError("recurrence_end_date cannot be before next_due_date")
        elif freq:
            self.recurring_interval = freq.lower()
            self.recurrence_frequency = freq.lower()
        return self


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
    date: dt.date
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
    recurrence_frequency: Optional[str] = None
    recurring_interval: Optional[str] = None
    next_due_date: Optional[dt.date] = None
    recurrence_end_date: Optional[dt.date] = None
    recurring_parent_id: Optional[uuid.UUID] = None
    tags: Optional[str] = None
    created_at: dt.datetime

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def populate_frequency(self) -> "TransactionResponse":
        if not self.recurrence_frequency and self.recurring_interval:
            self.recurrence_frequency = self.recurring_interval
        elif not self.recurring_interval and self.recurrence_frequency:
            self.recurring_interval = self.recurrence_frequency
        return self


class RecurringExpenseResponse(BaseModel):
    id: uuid.UUID
    merchant: Optional[str] = None
    description: str
    amount: Decimal
    frequency: str
    next_due_date: Optional[dt.date] = None
    recurrence_end_date: Optional[dt.date] = None
    days_until_due: Optional[int] = None
    category_id: Optional[uuid.UUID] = None
    category: Optional[CategoryBasic] = None
    category_name: Optional[str] = None
    bank_account_id: Optional[uuid.UUID] = None
    bank_account: Optional[BankAccountBasic] = None
    status: str = "cleared"
    is_recurring: bool = True
    created_at: dt.datetime

    class Config:
        from_attributes = True


class BulkDeleteRequest(BaseModel):
    ids: list[uuid.UUID]
