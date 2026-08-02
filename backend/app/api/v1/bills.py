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
        # BUG-007 fix: handle edge cases like Feb 29, 30, 31 by clamping to 28
        # Also fix the year bug: December → January of the NEXT year
        next_month = from_date.month + 1 if from_date.month < 12 else 1
        next_year = from_date.year if from_date.month < 12 else from_date.year + 1
        return date(next_year, next_month, 28)

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
    from app.models.insurance import InsurancePolicy  # BUG-008 fix: removed duplicate import
    from app.models.goal import Goal

    today = date.today()
    next_30 = today + timedelta(days=30)  # BUG-027 fix: define the 30-day window

    # 1. Bills — BUG-027 fix: filter to bills due within the next 30 days
    b_result = await db.execute(
        select(Bill)
        .where(
            Bill.user_id == current_user.id,
            Bill.status == "active",
            Bill.deleted_at.is_(None),
            Bill.next_due_date.is_not(None),
            Bill.next_due_date <= next_30,
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
    
    # 4. Insurance
    i_result = await db.execute(
        select(InsurancePolicy).where(InsurancePolicy.user_id == current_user.id, InsurancePolicy.status == "active", InsurancePolicy.deleted_at.is_(None))
    )
    insurances = i_result.scalars().all()
    
    # 5. Goals
    g_result = await db.execute(
        select(Goal).where(Goal.user_id == current_user.id, Goal.monthly_contribution > 0, Goal.deleted_at.is_(None))
    )
    goals = g_result.scalars().all()
    
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
        next_emi_date = compute_next_due_date(l.emi_day, today)
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
            unified_dues.append({
                "id": str(c.id),
                "name": f"CC Due: {c.bank_name}",
                "amount": float(c.outstanding_balance), # Total outstanding or min due
                "due_date": next_cc_date.isoformat(),
                "days_until_due": (next_cc_date - today).days,
                "source_type": "credit_card",
                "icon": "credit_card"
            })
                
    for i in insurances:
        if i.renewal_date:
            if today <= i.renewal_date:
                unified_dues.append({
                    "id": str(i.id),
                    "name": f"Premium: {i.policy_name}",
                    "amount": float(i.annual_premium),
                    "due_date": i.renewal_date.isoformat(),
                    "days_until_due": (i.renewal_date - today).days,
                    "source_type": "insurance",
                    "icon": "shield"
                })
                
    for g in goals:
        if g.monthly_contribution > 0:
            next_goal_date = compute_next_due_date(1, today) # Assuming 1st of the month for SIP
            unified_dues.append({
                "id": str(g.id),
                "name": f"SIP: {g.name}",
                "amount": float(g.monthly_contribution),
                "due_date": next_goal_date.isoformat(),
                "days_until_due": (next_goal_date - today).days,
                "source_type": "goal",
                "icon": "target"
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
    from app.models.loan import Loan
    from app.models.credit_card import CreditCard
    from app.models.insurance import InsurancePolicy
    from app.models.goal import Goal, GoalContribution
    from decimal import Decimal

    payment_data = data.model_dump()
    bank_account_id = payment_data.pop('bank_account_id', None)
    source_type = payment_data.pop('source_type', 'bill')
    
    bill_name = "Payment"
    category_name = "General"
    
    if source_type == 'bill':
        result = await db.execute(
            select(Bill).where(Bill.id == id, Bill.user_id == current_user.id, Bill.deleted_at.is_(None))
        )
        bill = result.scalar_one_or_none()
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
            
        bill_name = bill.name
        category_name = bill.category
        
        payment = BillPayment(**payment_data, bill_id=bill.id)
        db.add(payment)
        
        bill.last_paid_date = data.paid_date
        if bill.next_due_date and data.paid_date >= bill.next_due_date:
            next_month_start = date(bill.next_due_date.year, bill.next_due_date.month, 1) + timedelta(days=32)
            bill.next_due_date = compute_next_due_date(bill.due_day, next_month_start)
        else:
            # BUG-023 fix: for early payments, advance from the current due date's month
            # instead of using an arbitrary +15 days offset from today
            current_due = bill.next_due_date or date.today()
            next_month_start = date(current_due.year, current_due.month, 1) + timedelta(days=32)
            bill.next_due_date = compute_next_due_date(bill.due_day, next_month_start)
            
    elif source_type == 'credit_card':
        result = await db.execute(
            select(CreditCard).where(CreditCard.id == id, CreditCard.user_id == current_user.id, CreditCard.deleted_at.is_(None))
        )
        card = result.scalar_one_or_none()
        if not card:
            raise HTTPException(status_code=404, detail="Credit Card not found")
            
        bill_name = f"CC Payment: {card.bank_name}"
        category_name = "Credit Card"
        card.outstanding_balance = max(Decimal("0"), card.outstanding_balance - data.amount_paid)
        
    elif source_type == 'loan':
        result = await db.execute(
            select(Loan).where(Loan.id == id, Loan.user_id == current_user.id, Loan.deleted_at.is_(None))
        )
        loan = result.scalar_one_or_none()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
            
        bill_name = f"EMI: {loan.name}"
        category_name = "Loan"
        # BUG-009 fix: the Loan model field is `outstanding_balance`, not `outstanding_amount`
        loan.outstanding_balance = max(Decimal("0"), loan.outstanding_balance - data.amount_paid)
        
    elif source_type == 'insurance':
        result = await db.execute(
            select(InsurancePolicy).where(InsurancePolicy.id == id, InsurancePolicy.user_id == current_user.id, InsurancePolicy.deleted_at.is_(None))
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise HTTPException(status_code=404, detail="Insurance Policy not found")
            
        bill_name = f"Premium: {policy.policy_name}"
        category_name = "Insurance"
        
    elif source_type == 'goal':
        result = await db.execute(
            select(Goal).where(Goal.id == id, Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
        )
        goal = result.scalar_one_or_none()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
            
        bill_name = f"SIP: {goal.name}"
        category_name = "Investment"
        
        contrib = GoalContribution(
            goal_id=goal.id,
            amount=data.amount_paid,
            date=data.paid_date,
            notes="Auto SIP Payment from Bills"
        )
        db.add(contrib)
    else:
        raise HTTPException(status_code=400, detail="Invalid source type")
    
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
                select(Category).where(Category.user_id == current_user.id, Category.name.ilike(f"%{category_name}%"), Category.type == 'expense')
            )
            category = cat_result.scalar_one_or_none()
            
            if not category:
                 cat_result = await db.execute(select(Category).where(Category.user_id == current_user.id, Category.type == 'expense'))
                 category = cat_result.scalars().first()
                 
            transaction = Transaction(
                user_id=current_user.id,
                amount=data.amount_paid,
                type="expense",
                category_id=category.id if category else None,
                date=data.paid_date,
                description=bill_name,
                payment_method="bank_transfer",
                bank_account_id=bank_account.id,
                status="completed"
            )
            db.add(transaction)
    
    await db.commit()
    return APIResponse(message=f"Payment recorded for {source_type}")
