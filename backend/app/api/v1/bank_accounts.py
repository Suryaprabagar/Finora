from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.user import User
from app.models.bank_account import BankAccount
from app.models.transaction import Transaction
from app.dependencies import get_current_user
from app.schemas.common import APIResponse, Pagination
from app.schemas.bank_account import BankAccountCreate, BankAccountUpdate, BankAccountResponse, TransferRequest
from app.schemas.transaction import TransactionResponse
import uuid
from datetime import datetime, timezone

router = APIRouter()

@router.get("")
async def get_bank_accounts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(BankAccount)
        .where(BankAccount.user_id == current_user.id, BankAccount.is_active.is_(True), BankAccount.deleted_at.is_(None))
        .order_by(desc(BankAccount.balance))
    )
    accounts = result.scalars().all()
    return APIResponse(data=[BankAccountResponse.model_validate(a).model_dump() for a in accounts])

@router.post("", status_code=201)
async def create_bank_account(
    data: BankAccountCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    account = BankAccount(**data.model_dump(), user_id=current_user.id)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return APIResponse(data=BankAccountResponse.model_validate(account).model_dump(), message="Bank account created")

@router.get("/{id}")
async def get_bank_account(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(BankAccount)
        .where(BankAccount.id == id, BankAccount.user_id == current_user.id, BankAccount.deleted_at.is_(None))
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    return APIResponse(data=BankAccountResponse.model_validate(account).model_dump())

@router.put("/{id}")
async def update_bank_account(
    id: uuid.UUID, 
    data: BankAccountUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(BankAccount)
        .where(BankAccount.id == id, BankAccount.user_id == current_user.id, BankAccount.deleted_at.is_(None))
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(account, k, v)
        
    await db.commit()
    await db.refresh(account)
    return APIResponse(data=BankAccountResponse.model_validate(account).model_dump(), message="Bank account updated")

@router.delete("/{id}")
async def delete_bank_account(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(BankAccount)
        .where(BankAccount.id == id, BankAccount.user_id == current_user.id, BankAccount.deleted_at.is_(None))
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Bank account not found")
        
    account.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Bank account deleted")

@router.post("/transfer")
async def transfer_funds(
    data: TransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.from_account_id == data.to_account_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")
        
    # Get accounts
    from_acc_result = await db.execute(
        select(BankAccount).where(BankAccount.id == data.from_account_id, BankAccount.user_id == current_user.id)
    )
    from_acc = from_acc_result.scalar_one_or_none()
    
    to_acc_result = await db.execute(
        select(BankAccount).where(BankAccount.id == data.to_account_id, BankAccount.user_id == current_user.id)
    )
    to_acc = to_acc_result.scalar_one_or_none()
    
    if not from_acc or not to_acc:
        raise HTTPException(status_code=404, detail="One or both bank accounts not found")
        
    # BUG-014 fix: use type="transfer" for both legs of the transfer so they
    # are excluded from income/expense aggregations and don't inflate monthly totals.
    # Create withdrawal
    withdrawal = Transaction(
        user_id=current_user.id,
        bank_account_id=from_acc.id,
        amount=data.amount,
        type="transfer",
        date=data.date,
        description=data.description or f"Transfer to {to_acc.name}",
        status="completed"
    )

    # Create deposit
    deposit = Transaction(
        user_id=current_user.id,
        bank_account_id=to_acc.id,
        amount=data.amount,
        type="transfer",
        date=data.date,
        description=data.description or f"Transfer from {from_acc.name}",
        status="completed"
    )
    
    # Update balances
    from_acc.balance -= data.amount
    to_acc.balance += data.amount
    
    db.add(withdrawal)
    db.add(deposit)
    await db.commit()
    
    return APIResponse(message="Transfer successful")

@router.get("/{id}/transactions")
async def get_account_transactions(
    id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Transaction).where(
        Transaction.bank_account_id == id,
        Transaction.user_id == current_user.id,
        Transaction.deleted_at.is_(None)
    ).order_by(desc(Transaction.date), desc(Transaction.created_at))
    
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()
    
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query.options(selectinload(Transaction.category)))
    transactions = result.scalars().all()
    
    return APIResponse(
        data=[TransactionResponse.model_validate(t).model_dump() for t in transactions],
        pagination=Pagination(page=page, per_page=per_page, total=total)
    )
