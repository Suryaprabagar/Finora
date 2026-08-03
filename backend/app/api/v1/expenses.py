from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.bank_account import BankAccount
from app.dependencies import get_current_user
from app.schemas.common import APIResponse, Pagination
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
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
    query = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.deleted_at.is_(None)
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

    query = query.order_by(desc(Transaction.date), desc(Transaction.created_at)).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    transactions = result.scalars().all()

    return APIResponse(
        data=[TransactionResponse.model_validate(t).model_dump() for t in transactions],
        pagination=Pagination(page=page, per_page=per_page, total=total)
    )

@router.get("/summary")
async def get_expenses_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
        .where(Transaction.user_id == current_user.id, Transaction.type == "expense", Transaction.date >= current_month_start, Transaction.deleted_at.is_(None))
    )
    monthly_total = float(monthly_r.scalar() or 0)
    
    last_r = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.user_id == current_user.id, Transaction.type == "expense", Transaction.date >= last_month_start, Transaction.date <= last_month_end, Transaction.deleted_at.is_(None))
    )
    last_month_total = float(last_r.scalar() or 0)
    
    change_pct = ((monthly_total - last_month_total) / last_month_total * 100) if last_month_total > 0 else 0
    
    days_in_month = today.day
    avg_daily = monthly_total / days_in_month if days_in_month > 0 else 0
    
    top_cat_r = await db.execute(
        select(Category.name)
        .join(Transaction)
        .where(Transaction.user_id == current_user.id, Transaction.type == "expense", Transaction.date >= current_month_start, Transaction.deleted_at.is_(None))
        .group_by(Category.name)
        .order_by(desc(func.sum(Transaction.amount)))
        .limit(1)
    )
    top_category = top_cat_r.scalar_one_or_none() or "None"

    # BUG-017 fix: compute actual recurring count instead of hardcoding 0
    recurring_r = await db.execute(
        select(func.count(Transaction.id))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.is_recurring.is_(True),
            Transaction.deleted_at.is_(None),
        )
    )
    recurring_count = recurring_r.scalar() or 0

    return APIResponse(data={
        "monthly_total": monthly_total,
        "last_month_total": last_month_total,
        "change_pct": change_pct,
        "avg_daily": avg_daily,
        "recurring_count": recurring_count,
        "top_category": top_category
    })

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
            Transaction.deleted_at.is_(None)
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
            .where(Transaction.user_id == current_user.id, Transaction.type == "expense", Transaction.date >= m_start, Transaction.date < m_end, Transaction.deleted_at.is_(None))
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
    
    transaction = Transaction(**dump, user_id=current_user.id)
    db.add(transaction)
    
    if data.bank_account_id:
        acc = await db.get(BankAccount, data.bank_account_id)
        if acc:
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
        
    if t.bank_account_id:
        old_acc = await db.get(BankAccount, t.bank_account_id)
        if old_acc:
            old_acc.balance += t.amount
            
    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("type", None)
    for k, v in update_data.items():
        setattr(t, k, v)
        
    if t.bank_account_id:
        new_acc = await db.get(BankAccount, t.bank_account_id)
        if new_acc:
            new_acc.balance -= t.amount
            
    await db.commit()
    await db.refresh(t)
    return APIResponse(data=TransactionResponse.model_validate(t).model_dump(), message="Expense updated")

@router.delete("/{id}")
async def delete_expense(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Transaction).where(Transaction.id == id, Transaction.user_id == current_user.id, Transaction.type == "expense", Transaction.deleted_at.is_(None))
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    if t.bank_account_id:
        acc = await db.get(BankAccount, t.bank_account_id)
        if acc:
            acc.balance += t.amount
            
    t.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Expense deleted")
