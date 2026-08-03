from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.user import User
from app.models.loan import Loan, LoanPayment
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.loan import LoanCreate, LoanUpdate, LoanResponse, LoanPaymentCreate
import uuid
import calendar
from datetime import date, datetime, timezone
from decimal import Decimal

router = APIRouter()

@router.get("/")
async def get_loans(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Loan).where(Loan.user_id == current_user.id, Loan.is_active.is_(True), Loan.deleted_at.is_(None))
    )
    loans = result.scalars().all()
    
    data = []
    for loan in loans:
        l_data = LoanResponse.model_validate(loan).model_dump()
        l_data["progress_percentage"] = round((loan.paid_months / loan.tenure_months) * 100, 1) if loan.tenure_months > 0 else 0
        data.append(l_data)
        
    return APIResponse(data=data)

@router.get("/summary")
async def get_loans_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(
            func.coalesce(func.sum(Loan.outstanding_balance), 0).label("total_outstanding"),
            func.coalesce(func.sum(Loan.emi_amount), 0).label("monthly_emi"),
            func.count(Loan.id).label("active_count")
        )
        .where(Loan.user_id == current_user.id, Loan.is_active.is_(True), Loan.deleted_at.is_(None))
    )
    totals = result.one()
    
    paid_r = await db.execute(
        select(func.coalesce(func.sum(LoanPayment.principal_component + LoanPayment.interest_component), 0))
        .join(Loan)
        .where(Loan.user_id == current_user.id, Loan.deleted_at.is_(None))
    )
    total_paid = float(paid_r.scalar() or 0)
    
    return APIResponse(data={
        "total_outstanding": float(totals.total_outstanding),
        "monthly_emi": float(totals.monthly_emi),
        "active_count": totals.active_count,
        "total_paid": total_paid
    })

@router.get("/{id}/schedule")
async def get_loan_schedule(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Loan).where(Loan.id == id, Loan.user_id == current_user.id, Loan.deleted_at.is_(None))
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    monthly_rate = float(loan.interest_rate) / 100 / 12
    emi = float(loan.emi_amount)
    balance = float(loan.outstanding_balance)
    schedule = []
    
    start_date = loan.start_date
    for i in range(1, loan.tenure_months - loan.paid_months + 1):
        if balance <= 0:
            break
            
        interest = balance * monthly_rate
        principal = emi - interest
        
        if balance < principal:
            principal = balance
            emi = principal + interest
            
        balance -= principal
        
        month_offset = start_date.month + loan.paid_months + i - 1
        year_offset = start_date.year
        while month_offset > 12:
            month_offset -= 12
            year_offset += 1
            
        # BUG-022 fix: clamp to max days in target month to prevent ValueError
        # e.g. a loan started on the 31st would crash in Feb (28 days), Apr (30 days), etc.
        max_day = calendar.monthrange(year_offset, month_offset)[1]
        p_date = date(year_offset, month_offset, min(start_date.day, max_day))
        
        schedule.append({
            "month": loan.paid_months + i,
            "date": p_date.isoformat(),
            "emi": round(emi, 2),
            "principal": round(principal, 2),
            "interest": round(interest, 2),
            "balance": round(balance, 2)
        })
        
    return APIResponse(data=schedule)

@router.post("/", status_code=201)
async def create_loan(data: LoanCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    loan = Loan(**data.model_dump(), user_id=current_user.id)
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    return APIResponse(data=LoanResponse.model_validate(loan).model_dump(), message="Loan created")

@router.get("/{id}")
async def get_loan(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Loan).options(selectinload(Loan.payments)).where(Loan.id == id, Loan.user_id == current_user.id, Loan.deleted_at.is_(None))
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return APIResponse(data=LoanResponse.model_validate(loan).model_dump())

@router.put("/{id}")
async def update_loan(id: uuid.UUID, data: LoanUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Loan).where(Loan.id == id, Loan.user_id == current_user.id, Loan.deleted_at.is_(None))
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(loan, k, v)
        
    await db.commit()
    await db.refresh(loan)
    return APIResponse(data=LoanResponse.model_validate(loan).model_dump(), message="Loan updated")

@router.delete("/{id}")
async def delete_loan(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Loan).where(Loan.id == id, Loan.user_id == current_user.id, Loan.deleted_at.is_(None))
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    loan.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Loan deleted")

@router.post("/{id}/payment")
async def record_payment(id: uuid.UUID, data: LoanPaymentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.transaction import Transaction
    from app.models.bank_account import BankAccount
    from app.models.category import Category

    result = await db.execute(
        select(Loan).where(Loan.id == id, Loan.user_id == current_user.id, Loan.deleted_at.is_(None))
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    monthly_rate = float(loan.interest_rate) / 100 / 12
    interest_component = float(loan.outstanding_balance) * monthly_rate
    
    amount_paid = data.amount_paid if data.amount_paid is not None else loan.emi_amount
    principal_component = float(amount_paid) - interest_component
    
    payment = LoanPayment(
        loan_id=loan.id,
        payment_date=data.payment_date,
        emi_amount=Decimal(amount_paid),
        principal_component=Decimal(principal_component),
        interest_component=Decimal(interest_component),
        balance_after=Decimal(float(loan.outstanding_balance) - principal_component)
    )
    db.add(payment)
    
    # Double-entry logic
    if data.bank_account_id:
        bank_result = await db.execute(
            select(BankAccount).where(BankAccount.id == data.bank_account_id, BankAccount.user_id == current_user.id)
        )
        bank_account = bank_result.scalar_one_or_none()
        if bank_account:
            bank_account.balance -= amount_paid
            
            cat_result = await db.execute(select(Category).where(Category.user_id == current_user.id, Category.type == 'expense'))
            category = cat_result.scalars().first()
            
            transaction = Transaction(
                user_id=current_user.id,
                amount=amount_paid,
                type="expense",
                category_id=category.id if category else None,
                date=data.payment_date,
                description=f"Loan Payment: {loan.name}",
                payment_method="bank_transfer",
                bank_account_id=bank_account.id,
                status="completed"
            )
            db.add(transaction)
            
    loan.outstanding_balance -= Decimal(principal_component)
    loan.paid_months += 1
    
    if loan.outstanding_balance <= 0:
        loan.is_active = False
        
    await db.commit()
    return APIResponse(message="Loan payment recorded")
