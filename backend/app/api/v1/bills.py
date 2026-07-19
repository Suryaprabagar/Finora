from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, asc
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.user import User
from app.models.bill import Bill, BillPayment
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.bill import BillCreate, BillUpdate, BillResponse, BillPaymentCreate
import uuid
from datetime import date, datetime, timezone, timedelta

router = APIRouter()

def compute_next_due_date(due_day: int, from_date: date) -> date:
    try:
        if due_day >= from_date.day:
            return date(from_date.year, from_date.month, due_day)
        else:
            if from_date.month == 12:
                return date(from_date.year + 1, 1, due_day)
            else:
                return date(from_date.year, from_date.month + 1, due_day)
    except ValueError:
        # handle edge cases like Feb 29
        return date(from_date.year, from_date.month + 1 if from_date.month < 12 else 1, 28)

@router.get("/")
async def get_bills(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Bill)
        .where(Bill.user_id == current_user.id, Bill.deleted_at.is_(None))
        .order_by(asc(Bill.next_due_date))
    )
    bills = result.scalars().all()
    return APIResponse(data=[BillResponse.model_validate(b).model_dump() for b in bills])

@router.get("/upcoming")
async def get_upcoming_bills(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    next_30 = today + timedelta(days=30)
    result = await db.execute(
        select(Bill)
        .where(
            Bill.user_id == current_user.id,
            Bill.status == "active",
            Bill.next_due_date <= next_30,
            Bill.deleted_at.is_(None)
        )
        .order_by(asc(Bill.next_due_date))
    )
    bills = result.scalars().all()
    data = []
    for b in bills:
        b_data = BillResponse.model_validate(b).model_dump()
        b_data["days_until_due"] = (b.next_due_date - today).days if b.next_due_date else None
        data.append(b_data)
    return APIResponse(data=data)

@router.get("/summary")
async def get_bills_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    next_30 = today + timedelta(days=30)
    current_month_start = today.replace(day=1)
    
    upcoming_r = await db.execute(
        select(func.coalesce(func.sum(Bill.amount), 0))
        .where(Bill.user_id == current_user.id, Bill.status == "active", Bill.next_due_date <= next_30, Bill.deleted_at.is_(None))
    )
    upcoming_amount = float(upcoming_r.scalar() or 0)
    
    paid_r = await db.execute(
        select(func.coalesce(func.sum(BillPayment.amount_paid), 0))
        .join(Bill)
        .where(Bill.user_id == current_user.id, BillPayment.paid_date >= current_month_start, Bill.deleted_at.is_(None))
    )
    paid_mtd = float(paid_r.scalar() or 0)
    
    overdue_r = await db.execute(
        select(func.count(Bill.id))
        .where(Bill.user_id == current_user.id, Bill.status == "active", Bill.next_due_date < today, Bill.deleted_at.is_(None))
    )
    overdue_count = overdue_r.scalar() or 0
    
    active_r = await db.execute(
        select(func.count(Bill.id))
        .where(Bill.user_id == current_user.id, Bill.status == "active", Bill.deleted_at.is_(None))
    )
    active_count = active_r.scalar() or 0
    
    avg_r = await db.execute(
        select(func.coalesce(func.sum(Bill.amount), 0))
        .where(Bill.user_id == current_user.id, Bill.status == "active", Bill.deleted_at.is_(None))
    )
    monthly_average = float(avg_r.scalar() or 0)
    
    return APIResponse(data={
        "upcoming_amount": upcoming_amount,
        "paid_mtd": paid_mtd,
        "overdue_count": overdue_count,
        "monthly_average": monthly_average,
        "active_count": active_count
    })

@router.post("/", status_code=201)
async def create_bill(data: BillCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    bill_data = data.model_dump()
    bill_data["next_due_date"] = compute_next_due_date(data.due_day, date.today())
    bill = Bill(**bill_data, user_id=current_user.id)
    db.add(bill)
    await db.commit()
    await db.refresh(bill)
    return APIResponse(data=BillResponse.model_validate(bill).model_dump(), message="Bill created")

@router.get("/{id}")
async def get_bill(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Bill).options(selectinload(Bill.payments)).where(Bill.id == id, Bill.user_id == current_user.id, Bill.deleted_at.is_(None))
    )
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return APIResponse(data=BillResponse.model_validate(bill).model_dump())

@router.put("/{id}")
async def update_bill(id: uuid.UUID, data: BillUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Bill).where(Bill.id == id, Bill.user_id == current_user.id, Bill.deleted_at.is_(None))
    )
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(bill, k, v)
        
    if "due_day" in update_data:
        bill.next_due_date = compute_next_due_date(bill.due_day, date.today())
        
    await db.commit()
    await db.refresh(bill)
    return APIResponse(data=BillResponse.model_validate(bill).model_dump(), message="Bill updated")

@router.delete("/{id}")
async def delete_bill(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Bill).where(Bill.id == id, Bill.user_id == current_user.id, Bill.deleted_at.is_(None))
    )
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    bill.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Bill deleted")

@router.post("/{id}/pay")
async def pay_bill(id: uuid.UUID, data: BillPaymentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Bill).where(Bill.id == id, Bill.user_id == current_user.id, Bill.deleted_at.is_(None))
    )
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    payment = BillPayment(**data.model_dump(), bill_id=bill.id)
    db.add(payment)
    
    bill.last_paid_date = data.paid_date
    if bill.next_due_date and data.paid_date >= bill.next_due_date:
        next_month_start = date(bill.next_due_date.year, bill.next_due_date.month, 1) + timedelta(days=32)
        bill.next_due_date = compute_next_due_date(bill.due_day, next_month_start)
    else:
        # Just compute from next month
        bill.next_due_date = compute_next_due_date(bill.due_day, date.today() + timedelta(days=15))
        
    await db.commit()
    return APIResponse(message="Bill payment recorded")
