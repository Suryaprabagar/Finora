from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.user import User
from app.models.credit_card import CreditCard
from app.models.transaction import Transaction
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.credit_card import CreditCardCreate, CreditCardUpdate, CreditCardResponse, CreditCardPaymentCreate
import uuid
from datetime import datetime, timezone

router = APIRouter()

@router.get("/")
async def get_credit_cards(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(CreditCard)
        .where(CreditCard.user_id == current_user.id, CreditCard.is_active.is_(True), CreditCard.deleted_at.is_(None))
        .order_by(desc(CreditCard.created_at))
    )
    cards = result.scalars().all()
    
    data = []
    for c in cards:
        c_data = CreditCardResponse.model_validate(c).model_dump()
        c_data["utilization_percent"] = (float(c.outstanding_balance) / float(c.limit) * 100) if float(c.limit) > 0 else 0
        c_data["available_credit"] = float(c.limit) - float(c.outstanding_balance)
        data.append(c_data)
        
    return APIResponse(data=data)

@router.post("/", status_code=201)
async def create_credit_card(data: CreditCardCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    card = CreditCard(**data.model_dump(), user_id=current_user.id)
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return APIResponse(data=CreditCardResponse.model_validate(card).model_dump(), message="Credit card created")

@router.get("/{id}")
async def get_credit_card(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(CreditCard).where(CreditCard.id == id, CreditCard.user_id == current_user.id, CreditCard.deleted_at.is_(None))
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")
        
    c_data = CreditCardResponse.model_validate(card).model_dump()
    c_data["utilization_percent"] = (float(card.outstanding_balance) / float(card.limit) * 100) if float(card.limit) > 0 else 0
    c_data["available_credit"] = float(card.limit) - float(card.outstanding_balance)
    return APIResponse(data=c_data)

@router.put("/{id}")
async def update_credit_card(id: uuid.UUID, data: CreditCardUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(CreditCard).where(CreditCard.id == id, CreditCard.user_id == current_user.id, CreditCard.deleted_at.is_(None))
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(card, k, v)
        
    await db.commit()
    await db.refresh(card)
    return APIResponse(data=CreditCardResponse.model_validate(card).model_dump(), message="Credit card updated")

@router.delete("/{id}")
async def delete_credit_card(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(CreditCard).where(CreditCard.id == id, CreditCard.user_id == current_user.id, CreditCard.deleted_at.is_(None))
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")
        
    card.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Credit card deleted")

@router.post("/{id}/payment")
async def credit_card_payment(id: uuid.UUID, data: CreditCardPaymentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.bank_account import BankAccount
    
    result = await db.execute(
        select(CreditCard).where(CreditCard.id == id, CreditCard.user_id == current_user.id, CreditCard.deleted_at.is_(None))
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")
        
    card.outstanding_balance -= data.amount
    
    # Double-entry logic: Deduct from bank account if provided
    bank_account_id_to_use = None
    if data.bank_account_id:
        bank_result = await db.execute(
            select(BankAccount).where(BankAccount.id == data.bank_account_id, BankAccount.user_id == current_user.id)
        )
        bank_account = bank_result.scalar_one_or_none()
        if bank_account:
            bank_account.balance -= data.amount
            bank_account_id_to_use = bank_account.id
    
    from datetime import date
    if isinstance(data.date, str):
        txn_date = date.fromisoformat(data.date)
    else:
        txn_date = data.date
        
    # Create transaction
    txn = Transaction(
        user_id=current_user.id,
        amount=data.amount,
        type="expense", # Since paying a CC is functionally moving cash to an expense bucket
        date=txn_date,
        description=f"Credit Card Payment: {card.name}",
        merchant=card.bank_name,
        payment_method="bank_transfer",
        bank_account_id=bank_account_id_to_use,
        status="completed"
    )
    db.add(txn)
    
    await db.commit()
    return APIResponse(message="Credit card payment recorded")
