"""Insurance schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


class InsuranceCreate(BaseModel):
    policy_name: str
    provider: str
    policy_type: str
    policy_number: Optional[str] = None
    coverage_amount: Decimal
    annual_premium: Decimal
    premium_frequency: str = "yearly"
    start_date: date
    renewal_date: date
    nominee: Optional[str] = None
    notes: Optional[str] = None


class InsuranceUpdate(InsuranceCreate):
    status: Optional[str] = None


class ClaimCreate(BaseModel):
    claim_date: date
    claim_amount: Decimal
    description: Optional[str] = None
    status: str = "pending"


class InsuranceResponse(BaseModel):
    id: uuid.UUID
    policy_name: str
    provider: str
    policy_type: str
    policy_number: Optional[str] = None
    coverage_amount: Decimal
    annual_premium: Decimal
    premium_frequency: str
    start_date: date
    renewal_date: date
    status: str
    nominee: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Aliases matching API router import names
InsurancePolicyCreate = InsuranceCreate
InsurancePolicyUpdate = InsuranceUpdate
InsurancePolicyResponse = InsuranceResponse
InsuranceClaimCreate = ClaimCreate
