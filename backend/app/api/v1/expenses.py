from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc, func, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.bank_account import BankAccount
from app.dependencies import get_current_user
from app.schemas.common import APIResponse, Pagination
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    CategoryBasic,
)
from app.services.recurring_service import (
    process_due_recurring_expenses,
    calculate_recurring_monthly_commitment,
)
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Optional

router = APIRouter()


@router.get("")
async def get_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category_id: Optional[uuid.UUID] = None,
    merchant: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    # Process any due recurring expenses so newly generated transactions appear
    await process_due_recurring_expenses(db, user_id=current_user.id)

    # Exclude recurring templates from the transaction history ledger
    query = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.deleted_at.is_(None),
        or_(Transaction.is_recurring.is_(False), Transaction.recurring_parent_id.isnot(None))
    ).options(selectinload(Transaction.category), selectinload(Transaction.bank_account))

    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if merchant:
        query = query.where(Transaction.merchant.ilike(f"%{merchant}%"))
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Transaction.description.ilike(search_filter),
                Transaction.merchant.ilike(search_filter)
            )
        )

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    page_val = int(getattr(page, "default", page) if not isinstance(page, int) else page)
    per_page_val = int(getattr(per_page, "default", per_page) if not isinstance(per_page, int) else per_page)

    query = query.order_by(desc(Transaction.date), desc(Transaction.created_at)).offset((page_val - 1) * per_page_val).limit(per_page_val)
    result = await db.execute(query)
    transactions = result.scalars().all()

    return APIResponse(
        data=[TransactionResponse.model_validate(t).model_dump() for t in transactions],
        pagination=Pagination(page=page_val, per_page=per_page_val, total=total)
    )


@router.get("/summary")
async def get_expenses_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await process_due_recurring_expenses(db, user_id=current_user.id)

    today = date.today()
    current_month_start = today.replace(day=1)
    
    if today.month == 1:
        last_month_start = date(today.year - 1, 12, 1)
        last_month_end = date(today.year - 1, 12, 31)
    else:
        last_month_start = date(today.year, today.month - 1, 1)
        last_month_end = current_month_start - timedelta(days=1)
        
    monthly_r = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= current_month_start,
            Transaction.deleted_at.is_(None),
            or_(Transaction.is_recurring.is_(False), Transaction.recurring_parent_id.isnot(None))
        )
    )
    monthly_total = float(monthly_r.scalar() or 0)
    
    last_r = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= last_month_start,
            Transaction.date <= last_month_end,
            Transaction.deleted_at.is_(None),
            or_(Transaction.is_recurring.is_(False), Transaction.recurring_parent_id.isnot(None))
        )
    )
    last_month_total = float(last_r.scalar() or 0)
    
    change_pct = ((monthly_total - last_month_total) / last_month_total * 100) if last_month_total > 0 else 0
    
    days_in_month = today.day
    avg_daily = monthly_total / days_in_month if days_in_month > 0 else 0
    
    top_cat_r = await db.execute(
        select(Category.name)
        .join(Transaction)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= current_month_start,
            Transaction.deleted_at.is_(None),
            or_(Transaction.is_recurring.is_(False), Transaction.recurring_parent_id.isnot(None))
        )
        .group_by(Category.name)
        .order_by(desc(func.sum(Transaction.amount)))
        .limit(1)
    )
    top_category = top_cat_r.scalar_one_or_none() or "None"

    largest_expense_r = await db.execute(
        select(
            Transaction.amount,
            Transaction.description,
            Transaction.merchant,
            Category.name.label("category")
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= current_month_start,
            Transaction.deleted_at.is_(None),
            or_(Transaction.is_recurring.is_(False), Transaction.recurring_parent_id.isnot(None))
        )
        .order_by(desc(Transaction.amount))
        .limit(1)
    )

    largest_expense_row = largest_expense_r.first()

    if largest_expense_row:
        largest_expense = {
            "amount": float(largest_expense_row.amount or 0),
            "description": largest_expense_row.description or "",
            "merchant": largest_expense_row.merchant or "",
            "category": largest_expense_row.category or "Uncategorized"
        }
    else:
        largest_expense = {
            "amount": 0,
            "description": "",
            "merchant": "",
            "category": "None"
        }

    # Query active recurring expense schedules
    active_recurring_r = await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.is_recurring.is_(True),
            Transaction.recurring_parent_id.is_(None),
            Transaction.deleted_at.is_(None),
        )
    )
    active_recurring = active_recurring_r.scalars().all()
    recurring_count = len(active_recurring)
    recurring_total = calculate_recurring_monthly_commitment(active_recurring)

    return APIResponse(data={
        "monthly_total": monthly_total,
        "last_month_total": last_month_total,
        "change_pct": change_pct,
        "avg_daily": avg_daily,
        "recurring_count": recurring_count,
        "recurring_total": recurring_total,
        "top_category": top_category,
        "largest_expense": largest_expense
    })


@router.get("/recurring")
async def get_recurring_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all recurring expense templates for the current user."""
    await process_due_recurring_expenses(db, user_id=current_user.id)
    query = (
        select(Transaction)
        .options(selectinload(Transaction.category), selectinload(Transaction.bank_account))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.is_recurring.is_(True),
            Transaction.recurring_parent_id.is_(None),
            Transaction.deleted_at.is_(None),
        )
        .order_by(desc(Transaction.created_at))
    )
    result = await db.execute(query)
    schedules = result.scalars().all()
    return APIResponse(
        data=[TransactionResponse.model_validate(s).model_dump() for s in schedules]
    )


@router.get("/upcoming-recurring")
async def get_upcoming_recurring_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List upcoming recurring expenses sorted by next due date with days until due."""
    await process_due_recurring_expenses(db, user_id=current_user.id)
    today = date.today()
    query = (
        select(Transaction)
        .options(selectinload(Transaction.category), selectinload(Transaction.bank_account))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.is_recurring.is_(True),
            Transaction.recurring_parent_id.is_(None),
            Transaction.deleted_at.is_(None),
        )
        .order_by(asc(Transaction.next_due_date))
    )
    result = await db.execute(query)
    schedules = result.scalars().all()

    data = []
    for s in schedules:
        days_until = (s.next_due_date - today).days if s.next_due_date else None
        data.append({
            "id": str(s.id),
            "merchant": s.merchant,
            "description": s.description,
            "amount": float(s.amount),
            "frequency": s.recurrence_frequency or s.recurring_interval or "monthly",
            "next_due_date": s.next_due_date.isoformat() if s.next_due_date else None,
            "recurrence_end_date": s.recurrence_end_date.isoformat() if s.recurrence_end_date else None,
            "days_until_due": days_until,
            "category_id": str(s.category_id) if s.category_id else None,
            "category": CategoryBasic.model_validate(s.category).model_dump() if s.category else None,
            "category_name": s.category.name if s.category else "Uncategorized",
            "bank_account_id": str(s.bank_account_id) if s.bank_account_id else None,
            "status": s.status,
            "is_recurring": s.is_recurring,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return APIResponse(data=data)


@router.get("/by-category")
async def get_expenses_by_category(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    current_month_start = today.replace(day=1)
    
    result = await db.execute(
        select(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= current_month_start,
            Transaction.deleted_at.is_(None),
            or_(Transaction.is_recurring.is_(False), Transaction.recurring_parent_id.isnot(None))
        )
        .group_by(Category.name)
    )
    rows = result.all()
    
    total_exp = sum(float(r.total) for r in rows)
    data = []
    for r in rows:
        amount = float(r.total)
        data.append({
            "category": r.name,
            "amount": amount,
            "percentage": round((amount / total_exp * 100), 1) if total_exp > 0 else 0
        })
        
    return APIResponse(data=data)


@router.get("/by-merchant")
async def get_expenses_by_merchant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    current_month_start = today.replace(day=1)

    result = await db.execute(
        select(
            Transaction.merchant,
            func.sum(Transaction.amount).label("total")
        )
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= current_month_start,
            Transaction.deleted_at.is_(None),
            Transaction.merchant.isnot(None),
            Transaction.merchant != "",
            or_(Transaction.is_recurring.is_(False), Transaction.recurring_parent_id.isnot(None))
        )
        .group_by(Transaction.merchant)
        .order_by(desc(func.sum(Transaction.amount)))
        .limit(5)
    )

    rows = result.all()
    max_amount = float(rows[0].total or 0) if rows else 0

    data = [
        {
            "merchant": merchant,
            "amount": float(total or 0),
            "percentage": round((float(total or 0) / max_amount) * 100, 1)
            if max_amount > 0 else 0
        }
        for merchant, total in rows
    ]

    return APIResponse(data=data)


@router.get("/trends")
async def get_expenses_trends(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    trends = []
    
    prev_amount = 0
    for i in range(5, -1, -1):
        month_offset = today.month - i
        year_offset = today.year
        while month_offset <= 0:
            month_offset += 12
            year_offset -= 1
            
        m_start = date(year_offset, month_offset, 1)
        if month_offset == 12:
            m_end = date(year_offset + 1, 1, 1)
        else:
            m_end = date(year_offset, month_offset + 1, 1)
            
        exp_r = await db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                Transaction.date >= m_start,
                Transaction.date < m_end,
                Transaction.deleted_at.is_(None),
                or_(Transaction.is_recurring.is_(False), Transaction.recurring_parent_id.isnot(None))
            )
        )
        amount = float(exp_r.scalar() or 0)
        
        vs_prev = ((amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0
        
        trends.append({
            "month": m_start.strftime("%b %Y"),
            "amount": amount,
            "vs_prev_month_pct": vs_prev
        })
        
        prev_amount = amount
        
    return APIResponse(data=trends)


@router.post("", status_code=201)
async def create_expense(data: TransactionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    dump = data.model_dump()
    dump["type"] = "expense"
    
    if dump.get("is_recurring"):
        freq = (
            dump.get("recurrence_frequency")
            or dump.get("recurring_interval")
            or "monthly"
        )

        dump["recurrence_frequency"] = freq
        dump["recurring_interval"] = freq

        transaction = Transaction(**dump, user_id=current_user.id)
        db.add(transaction)

        await db.commit()

        # Process immediately when the recurring expense is already due.
        if transaction.next_due_date and transaction.next_due_date <= date.today():
            await process_due_recurring_expenses(
                db,
                user_id=current_user.id
            )

        # Reload with relationships eagerly loaded.
        result = await db.execute(
            select(Transaction)
            .options(
                selectinload(Transaction.category),
                selectinload(Transaction.bank_account)
            )
            .where(
                Transaction.id == transaction.id,
                Transaction.user_id == current_user.id
            )
        )

        transaction = result.scalar_one()

        return APIResponse(
            data=TransactionResponse.model_validate(transaction).model_dump(),
            message="Recurring expense created"
        )
    else:
        # Regular one-time expense
        transaction = Transaction(**dump, user_id=current_user.id)
        db.add(transaction)
        
        if data.bank_account_id:
            acc = await db.get(BankAccount, data.bank_account_id)
            if acc and acc.user_id == current_user.id:
                acc.balance -= data.amount
                
        await db.commit()
        await db.refresh(transaction)
        return APIResponse(data=TransactionResponse.model_validate(transaction).model_dump(), message="Expense created")


@router.get("/{id}")
async def get_expense(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category), selectinload(Transaction.bank_account))
        .where(Transaction.id == id, Transaction.user_id == current_user.id, Transaction.type == "expense", Transaction.deleted_at.is_(None))
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Expense not found")
    return APIResponse(data=TransactionResponse.model_validate(t).model_dump())


@router.put("/{id}")
async def update_expense(id: uuid.UUID, data: TransactionUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Transaction).where(Transaction.id == id, Transaction.user_id == current_user.id, Transaction.type == "expense", Transaction.deleted_at.is_(None))
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    is_schedule = (t.is_recurring and t.recurring_parent_id is None)

    # Revert old balance only if this was an actual posted transaction
    if not is_schedule and t.bank_account_id:
        old_acc = await db.get(BankAccount, t.bank_account_id)
        if old_acc and old_acc.user_id == current_user.id:
            old_acc.balance += t.amount
            
    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("type", None)

    # Sync frequency
    if "recurrence_frequency" in update_data or "recurring_interval" in update_data:
        freq = update_data.get("recurrence_frequency") or update_data.get("recurring_interval")
        if freq:
            update_data["recurrence_frequency"] = freq
            update_data["recurring_interval"] = freq

    for k, v in update_data.items():
        setattr(t, k, v)
        
    is_now_schedule = (t.is_recurring and t.recurring_parent_id is None)

    # Deduct new balance only if this is an actual posted transaction
    if not is_now_schedule and t.bank_account_id:
        new_acc = await db.get(BankAccount, t.bank_account_id)
        if new_acc and new_acc.user_id == current_user.id:
            new_acc.balance -= t.amount
            
    await db.commit()
    await db.refresh(t)

    # If active recurring schedule with next_due_date <= today, process it
    if is_now_schedule and t.next_due_date and t.next_due_date <= date.today():
        await process_due_recurring_expenses(db, user_id=current_user.id)
        await db.refresh(t)

        # Reload the updated transaction with relationships eagerly loaded
    result = await db.execute(
        select(Transaction)
        .options(
            selectinload(Transaction.category),
            selectinload(Transaction.bank_account)
        )
        .where(
            Transaction.id == id,
            Transaction.user_id == current_user.id
        )
    )

    t = result.scalar_one()

    return APIResponse(
        data=TransactionResponse.model_validate(t).model_dump(),
        message="Expense updated"
    )


@router.delete("/{id}")
async def delete_expense(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
    select(Transaction)
    .options(
        selectinload(Transaction.category),
        selectinload(Transaction.bank_account)
    )
    .where(
        Transaction.id == id,
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.deleted_at.is_(None)
    )
)
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    is_schedule = (t.is_recurring and t.recurring_parent_id is None)

    # Only refund balance for actual posted transactions
    if not is_schedule and t.bank_account_id:
        acc = await db.get(BankAccount, t.bank_account_id)
        if acc and acc.user_id == current_user.id:
            acc.balance += t.amount
            
    t.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Expense deleted")
