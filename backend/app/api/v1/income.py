from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
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

@router.get("/")
async def get_income(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    query = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.type == "income",
        Transaction.deleted_at.is_(None)
    ).options(selectinload(Transaction.category), selectinload(Transaction.bank_account))

    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if search:
        search_filter = f"%{search}%"
        query = query.where(Transaction.description.ilike(search_filter))

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
async def get_income_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    current_month_start = today.replace(day=1)
    current_year_start = today.replace(month=1, day=1)
    
    monthly_r = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.user_id == current_user.id, Transaction.type == "income", Transaction.date >= current_month_start, Transaction.deleted_at.is_(None))
    )
    monthly_total = float(monthly_r.scalar() or 0)

    annual_r = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.user_id == current_user.id, Transaction.type == "income", Transaction.date >= current_year_start, Transaction.deleted_at.is_(None))
    )
    annual_total = float(annual_r.scalar() or 0)

    # BUG-016 fix: compute actual counts instead of hardcoding 0
    recurring_r = await db.execute(
        select(func.count(Transaction.id))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "income",
            Transaction.is_recurring.is_(True),
            Transaction.deleted_at.is_(None),
        )
    )
    recurring_count = recurring_r.scalar() or 0

    pending_r = await db.execute(
        select(func.count(Transaction.id))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "income",
            Transaction.status == "pending",
            Transaction.deleted_at.is_(None),
        )
    )
    pending_count = pending_r.scalar() or 0
    
    largest_r = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id, Transaction.type == "income", Transaction.date >= current_month_start, Transaction.deleted_at.is_(None))
        .order_by(desc(Transaction.amount))
        .limit(1)
    )
    largest = largest_r.scalar_one_or_none()
    largest_source = {"name": largest.description if largest else "None", "amount": float(largest.amount) if largest else 0}
    
    return APIResponse(data={
        "monthly_total": monthly_total,
        "annual_total": annual_total,
        "recurring_count": recurring_count,
        "pending_count": pending_count,
        "largest_source": largest_source
    })

@router.get("/by-category")
async def get_income_by_category(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    current_month_start = today.replace(day=1)
    
    result = await db.execute(
        select(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "income",
            Transaction.date >= current_month_start,
            Transaction.deleted_at.is_(None)
        )
        .group_by(Category.name)
    )
    rows = result.all()
    
    total_income = sum(float(r.total) for r in rows)
    data = []
    for r in rows:
        amount = float(r.total)
        data.append({
            "category": r.name,
            "amount": amount,
            "percentage": round((amount / total_income * 100), 1) if total_income > 0 else 0
        })
        
    return APIResponse(data=data)

@router.get("/trends")
async def get_income_trends(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    trends = []
    
    prev_amount = 0
    # Return last 12 months for trends
    for i in range(11, -1, -1):
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
            
        inc_r = await db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.user_id == current_user.id, Transaction.type == "income", Transaction.date >= m_start, Transaction.date < m_end, Transaction.deleted_at.is_(None))
        )
        amount = float(inc_r.scalar() or 0)
        
        vs_prev = ((amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0
        
        trends.append({
            "month": m_start.strftime("%b"),
            "year": m_start.strftime("%Y"),
            "amount": amount,
            "vs_prev_month_pct": vs_prev
        })
        
        prev_amount = amount
        
    return APIResponse(data=trends)

@router.post("/", status_code=201)
async def create_income(data: TransactionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Force type to income
    dump = data.model_dump()
    dump["type"] = "income"
    
    transaction = Transaction(**dump, user_id=current_user.id)
    db.add(transaction)
    
    if data.bank_account_id:
        acc = await db.get(BankAccount, data.bank_account_id)
        if acc:
            acc.balance += data.amount
            
    await db.commit()
    await db.refresh(transaction)
    return APIResponse(data=TransactionResponse.model_validate(transaction).model_dump(), message="Income created")

@router.get("/{id}")
async def get_income_single(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category), selectinload(Transaction.bank_account))
        .where(Transaction.id == id, Transaction.user_id == current_user.id, Transaction.type == "income", Transaction.deleted_at.is_(None))
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Income not found")
    return APIResponse(data=TransactionResponse.model_validate(t).model_dump())

@router.put("/{id}")
async def update_income(id: uuid.UUID, data: TransactionUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Transaction).where(Transaction.id == id, Transaction.user_id == current_user.id, Transaction.type == "income", Transaction.deleted_at.is_(None))
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Income not found")
        
    if t.bank_account_id:
        old_acc = await db.get(BankAccount, t.bank_account_id)
        if old_acc:
            old_acc.balance -= t.amount
            
    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("type", None) # Cannot change type here
    for k, v in update_data.items():
        setattr(t, k, v)
        
    if t.bank_account_id:
        new_acc = await db.get(BankAccount, t.bank_account_id)
        if new_acc:
            new_acc.balance += t.amount
            
    await db.commit()
    await db.refresh(t)
    return APIResponse(data=TransactionResponse.model_validate(t).model_dump(), message="Income updated")

@router.delete("/{id}")
async def delete_income(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Transaction).where(Transaction.id == id, Transaction.user_id == current_user.id, Transaction.type == "income", Transaction.deleted_at.is_(None))
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Income not found")
        
    if t.bank_account_id:
        acc = await db.get(BankAccount, t.bank_account_id)
        if acc:
            acc.balance -= t.amount
            
    t.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Income deleted")
