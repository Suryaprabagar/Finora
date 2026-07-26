from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.user import User
from app.models.insurance import InsurancePolicy, InsuranceClaim
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.insurance import InsurancePolicyCreate, InsurancePolicyUpdate, InsurancePolicyResponse, InsuranceClaimCreate
import uuid
from datetime import date, datetime, timezone

router = APIRouter()

@router.get("/")
async def get_insurance_policies(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(InsurancePolicy)
        .where(InsurancePolicy.user_id == current_user.id, InsurancePolicy.status == "active", InsurancePolicy.deleted_at.is_(None))
    )
    policies = result.scalars().all()
    return APIResponse(data=[InsurancePolicyResponse.model_validate(p).model_dump() for p in policies])

@router.get("/summary")
async def get_insurance_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(
            func.coalesce(func.sum(InsurancePolicy.coverage_amount), 0).label("total_coverage"),
            func.coalesce(func.sum(InsurancePolicy.annual_premium), 0).label("annual_premium"),
            func.count(InsurancePolicy.id).label("active_count"),
            func.min(InsurancePolicy.renewal_date).label("next_renewal")
        )
        .where(InsurancePolicy.user_id == current_user.id, InsurancePolicy.status == "active", InsurancePolicy.deleted_at.is_(None))
    )
    totals = result.one()
    
    claims_r = await db.execute(
        select(func.count(InsuranceClaim.id))
        .join(InsurancePolicy)
        .where(InsurancePolicy.user_id == current_user.id, InsuranceClaim.status == "pending", InsurancePolicy.deleted_at.is_(None))
    )
    open_claims = claims_r.scalar() or 0
    
    return APIResponse(data={
        "total_coverage": float(totals.total_coverage),
        "annual_premium": float(totals.annual_premium),
        "active_count": totals.active_count,
        "next_renewal": totals.next_renewal.isoformat() if totals.next_renewal else None,
        "open_claims_count": open_claims
    })

@router.post("/", status_code=201)
async def create_insurance_policy(data: InsurancePolicyCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    policy = InsurancePolicy(**data.model_dump(), user_id=current_user.id)
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return APIResponse(data=InsurancePolicyResponse.model_validate(policy).model_dump(), message="Insurance policy created")

@router.get("/{id}")
async def get_insurance_policy(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(InsurancePolicy)
        .options(selectinload(InsurancePolicy.claims))
        .where(InsurancePolicy.id == id, InsurancePolicy.user_id == current_user.id, InsurancePolicy.deleted_at.is_(None))
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Insurance policy not found")
    return APIResponse(data=InsurancePolicyResponse.model_validate(policy).model_dump())

@router.put("/{id}")
async def update_insurance_policy(id: uuid.UUID, data: InsurancePolicyUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(InsurancePolicy).where(InsurancePolicy.id == id, InsurancePolicy.user_id == current_user.id, InsurancePolicy.deleted_at.is_(None))
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Insurance policy not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(policy, k, v)
        
    await db.commit()
    await db.refresh(policy)
    return APIResponse(data=InsurancePolicyResponse.model_validate(policy).model_dump(), message="Insurance policy updated")

@router.delete("/{id}")
async def delete_insurance_policy(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(InsurancePolicy).where(InsurancePolicy.id == id, InsurancePolicy.user_id == current_user.id, InsurancePolicy.deleted_at.is_(None))
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Insurance policy not found")
        
    policy.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Insurance policy deleted")

@router.post("/{id}/claims")
async def file_claim(id: uuid.UUID, data: InsuranceClaimCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(InsurancePolicy).where(InsurancePolicy.id == id, InsurancePolicy.user_id == current_user.id, InsurancePolicy.deleted_at.is_(None))
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Insurance policy not found")
        
    claim = InsuranceClaim(**data.model_dump(), policy_id=policy.id)
    db.add(claim)
    await db.commit()
    return APIResponse(message="Insurance claim filed")

@router.get("/{id}/claims")
async def get_claims(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(InsuranceClaim)
        .join(InsurancePolicy)
        .where(InsurancePolicy.id == id, InsurancePolicy.user_id == current_user.id, InsurancePolicy.deleted_at.is_(None))
    )
    claims = result.scalars().all()
    # Assuming InsuranceClaimResponse schema exists, else manual dict mapping
    claims_list = [{
        "id": str(c.id),
        "claim_number": c.claim_number,
        "claim_date": c.claim_date.isoformat(),
        "amount_claimed": float(c.amount_claimed),
        "status": c.status,
        "description": c.description
    } for c in claims]
    return APIResponse(data=claims_list)
