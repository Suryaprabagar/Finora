from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.user import User
from app.models.budget import Budget, BudgetItem
from app.models.transaction import Transaction
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
import uuid
from datetime import date, datetime, timezone

router = APIRouter()

@router.get("")
async def get_budgets(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Budget)
        .where(Budget.user_id == current_user.id, Budget.deleted_at.is_(None))
        .order_by(desc(Budget.year), desc(Budget.month))
    )
    budgets = result.scalars().all()
    return APIResponse(data=[BudgetResponse.model_validate(b).model_dump() for b in budgets])

@router.post("", status_code=201)
async def create_budget(
    data: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = Budget(
        user_id=current_user.id,
        name=data.name,
        month=data.month,
        year=data.year,
        total_limit=data.total_limit
    )
    db.add(budget)
    await db.flush()
    
    for item_data in data.items:
        item = BudgetItem(
            budget_id=budget.id,
            category_id=item_data.category_id,
            name=item_data.name,
            allocated_amount=item_data.allocated_amount
        )
        db.add(item)
        
    await db.commit()
    await db.refresh(budget)
    
    result = await db.execute(
        select(Budget).options(selectinload(Budget.items)).where(Budget.id == budget.id)
    )
    budget = result.scalar_one()
    
    return APIResponse(data=BudgetResponse.model_validate(budget).model_dump(), message="Budget created")

@router.get("/current")
async def get_current_budget(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    result = await db.execute(
        select(Budget)
        .options(selectinload(Budget.items).selectinload(BudgetItem.category))
        .where(
            Budget.user_id == current_user.id,
            Budget.month == today.month,
            Budget.year == today.year,
            Budget.deleted_at.is_(None)
        )
        .order_by(desc(Budget.created_at))
    )
    budget = result.scalars().first()
    
    if not budget:
        return APIResponse(data=None)
        
    # Calculate spent amounts
    current_month_start = today.replace(day=1)
    if today.month == 12:
        next_month_start = date(today.year + 1, 1, 1)
    else:
        next_month_start = date(today.year, today.month + 1, 1)
        
    budget_data = BudgetResponse.model_validate(budget).model_dump()
    for item in budget_data["items"]:
        if item.get("category_id"):
            spent_r = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0))
                .where(
                    Transaction.user_id == current_user.id,
                    Transaction.category_id == uuid.UUID(item["category_id"]),
                    Transaction.type == "expense",
                    Transaction.date >= current_month_start,
                    Transaction.date < next_month_start,
                    Transaction.deleted_at.is_(None)
                )
            )
            item["spent_amount"] = float(spent_r.scalar() or 0)
        else:
            item["spent_amount"] = 0.0
            
    return APIResponse(data=budget_data)

@router.get("/{id}")
async def get_budget(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Budget)
        .options(selectinload(Budget.items).selectinload(BudgetItem.category))
        .where(Budget.id == id, Budget.user_id == current_user.id, Budget.deleted_at.is_(None))
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    # Calculate spent amounts
    start_date = date(budget.year, budget.month, 1)
    if budget.month == 12:
        end_date = date(budget.year + 1, 1, 1)
    else:
        end_date = date(budget.year, budget.month + 1, 1)
        
    budget_data = BudgetResponse.model_validate(budget).model_dump()
    for item in budget_data["items"]:
        if item.get("category_id"):
            spent_r = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0))
                .where(
                    Transaction.user_id == current_user.id,
                    Transaction.category_id == uuid.UUID(item["category_id"]),
                    Transaction.type == "expense",
                    Transaction.date >= start_date,
                    Transaction.date < end_date,
                    Transaction.deleted_at.is_(None)
                )
            )
            item["spent_amount"] = float(spent_r.scalar() or 0)
        else:
            item["spent_amount"] = 0.0
            
    return APIResponse(data=budget_data)

@router.put("/{id}")
async def update_budget(
    id: uuid.UUID,
    data: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Budget).options(selectinload(Budget.items)).where(Budget.id == id, Budget.user_id == current_user.id, Budget.deleted_at.is_(None))
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    update_data = data.model_dump(exclude_unset=True, exclude={"items"})
    for k, v in update_data.items():
        setattr(budget, k, v)
        
    if data.items is not None:
        # Delete old items
        for item in budget.items:
            await db.delete(item)
            
        # Add new items
        for item_data in data.items:
            item = BudgetItem(
                budget_id=budget.id,
                category_id=item_data.category_id,
                name=item_data.name,
                allocated_amount=item_data.allocated_amount
            )
            db.add(item)
            
    await db.commit()
    await db.refresh(budget)
    
    result = await db.execute(
        select(Budget).options(selectinload(Budget.items)).where(Budget.id == budget.id)
    )
    budget = result.scalar_one()
    return APIResponse(data=BudgetResponse.model_validate(budget).model_dump(), message="Budget updated")

@router.delete("/{id}")
async def delete_budget(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Budget).where(Budget.id == id, Budget.user_id == current_user.id, Budget.deleted_at.is_(None))
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    budget.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Budget deleted")
