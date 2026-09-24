"""Budget API router.

Endpoints:
  GET    /budget            – list all budgets for current user
  POST   /budget            – create a budget (prevents duplicate overall budgets per month)
  GET    /budget/current    – current month's budget with real spending calculation
  GET    /budget/{id}       – single budget with per-item spending
  PUT    /budget/{id}       – update a budget
  DELETE /budget/{id}       – soft-delete a budget
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.budget import Budget, BudgetItem
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.schemas.common import APIResponse

router = APIRouter()


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

async def _calculate_spending(
    db: AsyncSession,
    user_id: uuid.UUID,
    year: int,
    month: int,
) -> tuple[float, float, int]:
    """Return (spent_total, remaining_total, days_remaining) for a given month."""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.date >= start_date,
            Transaction.date < end_date,
            Transaction.deleted_at.is_(None),
        )
    )
    spent_total = float(result.scalar() or 0)
    today = date.today()
    days_remaining = max((end_date - today).days - 1, 0)
    return spent_total, days_remaining


def _enrich_budget_response(
    budget: Budget,
    spent_total: float,
    days_remaining: int,
) -> dict:
    """Build a BudgetResponse dict enriched with computed spending fields."""
    budget_limit = float(budget.total_limit or 0)
    remaining = budget_limit - spent_total
    pct_used = (spent_total / budget_limit * 100) if budget_limit > 0 else 0.0

    data = BudgetResponse.model_validate(budget).model_dump()
    data["total_spent"] = Decimal(str(spent_total))
    data["remaining_total"] = Decimal(str(remaining))
    data["days_remaining"] = days_remaining
    data["percentage_used"] = round(pct_used, 2)
    # Ensure month_str is present
    data["month_str"] = f"{budget.year:04d}-{budget.month:02d}"
    return data


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@router.get("/current")
async def get_current_budget(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current month's budget with real spending figures."""
    today = date.today()

    result = await db.execute(
        select(Budget)
        .options(
            selectinload(Budget.items).selectinload(BudgetItem.category)
        )
        .where(
            Budget.user_id == current_user.id,
            Budget.month == today.month,
            Budget.year == today.year,
            Budget.deleted_at.is_(None),
        )
        .order_by(desc(Budget.created_at))
    )
    budget = result.scalars().first()

    if not budget:
        return APIResponse(data=None, message="No budget set for this month")

    spent_total, days_remaining = await _calculate_spending(
        db, current_user.id, today.year, today.month
    )

    # Per-item spending
    start_date = date(today.year, today.month, 1)
    if today.month == 12:
        end_date = date(today.year + 1, 1, 1)
    else:
        end_date = date(today.year, today.month + 1, 1)

    budget_data = _enrich_budget_response(budget, spent_total, days_remaining)

    for item in budget_data["items"]:
        cat_id = item.get("category_id")
        if cat_id:
            spent_r = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0))
                .where(
                    Transaction.user_id == current_user.id,
                    Transaction.category_id == (
                        uuid.UUID(str(cat_id)) if not isinstance(cat_id, uuid.UUID) else cat_id
                    ),
                    Transaction.type == "expense",
                    Transaction.date >= start_date,
                    Transaction.date < end_date,
                    Transaction.deleted_at.is_(None),
                )
            )
            item["spent_amount"] = float(spent_r.scalar() or 0)
            alloc = float(item.get("allocated_amount") or 0)
            item["percentage_used"] = round(
                (item["spent_amount"] / alloc * 100) if alloc > 0 else 0.0, 2
            )
        else:
            item["spent_amount"] = 0.0
            item["percentage_used"] = 0.0

    return APIResponse(data=budget_data)


@router.get("")
async def get_budgets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Budget)
        .where(Budget.user_id == current_user.id, Budget.deleted_at.is_(None))
        .order_by(desc(Budget.year), desc(Budget.month))
    )
    budgets = result.scalars().all()
    return APIResponse(
        data=[BudgetResponse.model_validate(b).model_dump() for b in budgets]
    )


@router.post("", status_code=201)
async def create_budget(
    data: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a budget. Prevents duplicate overall (no category) budgets for the same month."""
    # Duplicate check: if creating an overall budget (no category items with all null category_ids)
    # check if one already exists for this month/year.
    all_items_have_no_category = all(
        item.category_id is None for item in data.items
    ) if data.items else True

    if all_items_have_no_category:
        existing = await db.execute(
            select(Budget).where(
                Budget.user_id == current_user.id,
                Budget.month == data.month,
                Budget.year == data.year,
                Budget.deleted_at.is_(None),
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=409,
                detail=(
                    f"A budget already exists for "
                    f"{data.year:04d}-{data.month:02d}. "
                    "Update the existing budget or delete it first."
                ),
            )

    budget = Budget(
        user_id=current_user.id,
        name=data.name,
        month=data.month,
        year=data.year,
        total_limit=data.total_limit,
        alert_threshold=data.alert_threshold,
    )
    db.add(budget)
    await db.flush()

    for item_data in data.items:
        item = BudgetItem(
            budget_id=budget.id,
            category_id=item_data.category_id,
            name=item_data.name,
            allocated_amount=item_data.allocated_amount,
        )
        db.add(item)

    await db.commit()
    await db.refresh(budget)

    result = await db.execute(
        select(Budget)
        .options(selectinload(Budget.items))
        .where(Budget.id == budget.id)
    )
    budget = result.scalar_one()

    return APIResponse(
        data=BudgetResponse.model_validate(budget).model_dump(),
        message="Budget created successfully",
    )


@router.get("/{id}")
async def get_budget(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Budget)
        .options(selectinload(Budget.items).selectinload(BudgetItem.category))
        .where(
            Budget.id == id,
            Budget.user_id == current_user.id,
            Budget.deleted_at.is_(None),
        )
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    spent_total, days_remaining = await _calculate_spending(
        db, current_user.id, budget.year, budget.month
    )

    # Per-item spending
    start_date = date(budget.year, budget.month, 1)
    if budget.month == 12:
        end_date = date(budget.year + 1, 1, 1)
    else:
        end_date = date(budget.year, budget.month + 1, 1)

    budget_data = _enrich_budget_response(budget, spent_total, days_remaining)

    for item in budget_data["items"]:
        cat_id = item.get("category_id")
        if cat_id:
            spent_r = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0))
                .where(
                    Transaction.user_id == current_user.id,
                    Transaction.category_id == (
                        uuid.UUID(str(cat_id)) if not isinstance(cat_id, uuid.UUID) else cat_id
                    ),
                    Transaction.type == "expense",
                    Transaction.date >= start_date,
                    Transaction.date < end_date,
                    Transaction.deleted_at.is_(None),
                )
            )
            item["spent_amount"] = float(spent_r.scalar() or 0)
            alloc = float(item.get("allocated_amount") or 0)
            item["percentage_used"] = round(
                (item["spent_amount"] / alloc * 100) if alloc > 0 else 0.0, 2
            )
        else:
            item["spent_amount"] = 0.0
            item["percentage_used"] = 0.0

    return APIResponse(data=budget_data)


@router.put("/{id}")
async def update_budget(
    id: uuid.UUID,
    data: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Budget)
        .options(selectinload(Budget.items))
        .where(
            Budget.id == id,
            Budget.user_id == current_user.id,
            Budget.deleted_at.is_(None),
        )
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"items"})
    for k, v in update_data.items():
        setattr(budget, k, v)

    if data.items is not None:
        for item in budget.items:
            await db.delete(item)
        for item_data in data.items:
            item = BudgetItem(
                budget_id=budget.id,
                category_id=item_data.category_id,
                name=item_data.name,
                allocated_amount=item_data.allocated_amount,
            )
            db.add(item)

    await db.commit()
    await db.refresh(budget)

    result = await db.execute(
        select(Budget)
        .options(selectinload(Budget.items))
        .where(Budget.id == budget.id)
    )
    budget = result.scalar_one()
    return APIResponse(
        data=BudgetResponse.model_validate(budget).model_dump(),
        message="Budget updated successfully",
    )


@router.delete("/{id}")
async def delete_budget(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Budget).where(
            Budget.id == id,
            Budget.user_id == current_user.id,
            Budget.deleted_at.is_(None),
        )
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    budget.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Budget deleted successfully")
