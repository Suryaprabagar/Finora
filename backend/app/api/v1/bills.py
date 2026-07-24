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
    from app.models.loan import Loan
    from app.models.credit_card import CreditCard

    today = date.today()
    next_30 = today + timedelta(days=30)
    
    # 1. Bills
    b_result = await db.execute(
        select(Bill)
        .where(
            Bill.user_id == current_user.id,
            Bill.status == "active",
            Bill.next_due_date <= next_30,
            Bill.deleted_at.is_(None)
        )
    )
    bills = b_result.scalars().all()
    
    # 2. Loans
    l_result = await db.execute(
        select(Loan).where(Loan.user_id == current_user.id, Loan.is_active.is_(True), Loan.deleted_at.is_(None))
    )
    loans = l_result.scalars().all()
    
    # 3. Credit Cards
    c_result = await db.execute(
        select(CreditCard).where(CreditCard.user_id == current_user.id, CreditCard.is_active.is_(True), CreditCard.deleted_at.is_(None))
    )
    cards = c_result.scalars().all()
    
    unified_dues = []
    
    for b in bills:
        unified_dues.append({
            "id": str(b.id),
            "name": b.name,
            "amount": float(b.amount),
            "due_date": b.next_due_date.isoformat() if b.next_due_date else None,
            "days_until_due": (b.next_due_date - today).days if b.next_due_date else None,
            "source_type": "bill",
            "icon": b.icon or "receipt"
        })
        
    for l in loans:
        # Calculate next EMI date based on emi_day
        # If emi_day has passed this month, it's next month
        next_emi_date = compute_next_due_date(l.emi_day, today)
        if next_emi_date <= next_30:
            unified_dues.append({
                "id": str(l.id),
                "name": f"EMI: {l.name}",
                "amount": float(l.emi_amount),
                "due_date": next_emi_date.isoformat(),
                "days_until_due": (next_emi_date - today).days,
                "source_type": "loan",
                "icon": "account_balance"
            })
            
    for c in cards:
        if c.outstanding_balance > 0:
            next_cc_date = compute_next_due_date(c.due_day, today)
            if next_cc_date <= next_30:
                unified_dues.append({
                    "id": str(c.id),
                    "name": f"CC Due: {c.bank_name}",
                    "amount": float(c.outstanding_balance), # Total outstanding or min due
                    "due_date": next_cc_date.isoformat(),
                    "days_until_due": (next_cc_date - today).days,
                    "source_type": "credit_card",
                    "icon": "credit_card"
                })
                
    # Sort by due date
    unified_dues.sort(key=lambda x: x["due_date"] or "")
    
    return APIResponse(data=unified_dues)

@router.get("/summary")
async def get_bills_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.loan import Loan
    from app.models.credit_card import CreditCard

    today = date.today()
    next_30 = today + timedelta(days=30)
    current_month_start = today.replace(day=1)
    
    # Upcoming Bills
    upcoming_r = await db.execute(
        select(func.coalesce(func.sum(Bill.amount), 0))
        .where(Bill.user_id == current_user.id, Bill.status == "active", Bill.next_due_date <= next_30, Bill.deleted_at.is_(None))
    )
    upcoming_amount = float(upcoming_r.scalar() or 0)
    
    # Paid Bills
    paid_r = await db.execute(
        select(func.coalesce(func.sum(BillPayment.amount_paid), 0))
        .join(Bill)
        .where(Bill.user_id == current_user.id, BillPayment.paid_date >= current_month_start, Bill.deleted_at.is_(None))
    )
    paid_mtd = float(paid_r.scalar() or 0)
    
    # Overdue
    overdue_r = await db.execute(
        select(func.count(Bill.id))
        .where(Bill.user_id == current_user.id, Bill.status == "active", Bill.next_due_date < today, Bill.deleted_at.is_(None))
    )
    overdue_count = overdue_r.scalar() or 0
    
    # Add Loans and CCs to upcoming_amount
    l_result = await db.execute(
        select(Loan).where(Loan.user_id == current_user.id, Loan.is_active.is_(True), Loan.deleted_at.is_(None))
    )
    for l in l_result.scalars().all():
        if compute_next_due_date(l.emi_day, today) <= next_30:
            upcoming_amount += float(l.emi_amount)
            
    c_result = await db.execute(
        select(CreditCard).where(CreditCard.user_id == current_user.id, CreditCard.is_active.is_(True), CreditCard.outstanding_balance > 0, CreditCard.deleted_at.is_(None))
    )
    for c in c_result.scalars().all():
        if compute_next_due_date(c.due_day, today) <= next_30:
            upcoming_amount += float(c.outstanding_balance)
            
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
    from app.models.transaction import Transaction
    from app.models.bank_account import BankAccount
    from app.models.category import Category

    result = await db.execute(
        select(Bill).where(Bill.id == id, Bill.user_id == current_user.id, Bill.deleted_at.is_(None))
    )
    bill = result.scalar_one_or_none()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
        
    payment_data = data.model_dump()
    bank_account_id = payment_data.pop('bank_account_id', None)
    
    payment = BillPayment(**payment_data, bill_id=bill.id)
    db.add(payment)
    
    # Double-entry logic: deduct from bank account and create transaction
    if bank_account_id:
        bank_result = await db.execute(
            select(BankAccount).where(BankAccount.id == bank_account_id, BankAccount.user_id == current_user.id)
        )
        bank_account = bank_result.scalar_one_or_none()
        if bank_account:
            bank_account.balance -= data.amount_paid
            
            # Find matching category
            cat_result = await db.execute(
                select(Category).where(Category.user_id == current_user.id, Category.name.ilike(f"%{bill.category}%"), Category.type == 'expense')
            )
            category = cat_result.scalar_one_or_none()
            
            if not category:
                 # Fallback to the first expense category
                 cat_result = await db.execute(select(Category).where(Category.user_id == current_user.id, Category.type == 'expense'))
                 category = cat_result.scalars().first()
                 
            transaction = Transaction(
                user_id=current_user.id,
                amount=data.amount_paid,
                type="expense",
                category_id=category.id if category else None,
                date=data.paid_date,
                description=f"Bill Payment: {bill.name}",
                payment_method="bank_transfer",
                bank_account_id=bank_account.id,
                status="completed"
            )
            db.add(transaction)
    
    bill.last_paid_date = data.paid_date
    if bill.next_due_date and data.paid_date >= bill.next_due_date:
        next_month_start = date(bill.next_due_date.year, bill.next_due_date.month, 1) + timedelta(days=32)
        bill.next_due_date = compute_next_due_date(bill.due_day, next_month_start)
    else:
        # Just compute from next month
        bill.next_due_date = compute_next_due_date(bill.due_day, date.today() + timedelta(days=15))
        
    await db.commit()
    return APIResponse(message="Bill payment recorded")
