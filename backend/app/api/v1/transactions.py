from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.bank_account import BankAccount
from app.models.credit_card import CreditCard
from app.models.category import Category
from app.dependencies import get_current_user
from app.schemas.common import APIResponse, Pagination
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, List
import uuid
from fastapi.responses import StreamingResponse
import csv
from io import StringIO
import io

router = APIRouter()

@router.get("")
async def get_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    type: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    bank_account_id: Optional[uuid.UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    payment_method: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("date"),
    sort_order: str = Query("desc")
):
    query = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.deleted_at.is_(None)
    ).options(selectinload(Transaction.category), selectinload(Transaction.bank_account))

    if type:
        query = query.where(Transaction.type == type)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if bank_account_id:
        query = query.where(Transaction.bank_account_id == bank_account_id)
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    if status:
        query = query.where(Transaction.status == status)
    if payment_method:
        query = query.where(Transaction.payment_method == payment_method)
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Transaction.description.ilike(search_filter),
                Transaction.merchant.ilike(search_filter)
            )
        )

    # BUG-006 fix: only allow known safe column names to prevent ORM attribute injection
    ALLOWED_SORT_FIELDS = {"date", "amount", "description", "created_at", "merchant", "status", "type"}
    safe_sort_by = sort_by if sort_by in ALLOWED_SORT_FIELDS else "date"
    sort_col = getattr(Transaction, safe_sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_col), desc(Transaction.created_at))
    else:
        query = query.order_by(asc(sort_col), asc(Transaction.created_at))

    # Pagination
    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    transactions = result.scalars().all()

    return APIResponse(
        data=[TransactionResponse.model_validate(t).model_dump() for t in transactions],
        pagination=Pagination(page=page, per_page=per_page, total=total)
    )

@router.post("", status_code=201)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = Transaction(**data.model_dump(), user_id=current_user.id)
    db.add(transaction)
    
    if data.bank_account_id:
        bank_account = await db.get(BankAccount, data.bank_account_id)
        if bank_account and bank_account.user_id == current_user.id:
            if transaction.type == "income":
                bank_account.balance += transaction.amount
            elif transaction.type == "expense":
                bank_account.balance -= transaction.amount
                
    if data.credit_card_id:
        credit_card = await db.get(CreditCard, data.credit_card_id)
        if credit_card and credit_card.user_id == current_user.id:
            if transaction.type == "expense":
                credit_card.outstanding_balance += transaction.amount
            elif transaction.type == "income":
                credit_card.outstanding_balance = max(0, credit_card.outstanding_balance - transaction.amount)
    
    await db.commit()
    await db.refresh(transaction)
    
    # Reload with relationships
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category), selectinload(Transaction.bank_account), selectinload(Transaction.credit_card))
        .where(Transaction.id == transaction.id)
    )
    transaction = result.scalar_one()
    return APIResponse(data=TransactionResponse.model_validate(transaction).model_dump(), message="Transaction created")

@router.get("/{id}")
async def get_transaction(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category), selectinload(Transaction.bank_account))
        .where(Transaction.id == id, Transaction.user_id == current_user.id, Transaction.deleted_at.is_(None))
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return APIResponse(data=TransactionResponse.model_validate(transaction).model_dump())

@router.put("/{id}")
async def update_transaction(
    id: uuid.UUID,
    data: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == id, Transaction.user_id == current_user.id, Transaction.deleted_at.is_(None))
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # BUG-005 fix: capture ALL old field values before applying any updates.
    # SQLAlchemy's identity map means db.get(BankAccount, same_id) returns the
    # *same Python object* both times. If we revert old_acc.balance and then
    # db.get() the "new" account for apply, we get the already-modified object,
    # causing double-counting when only the amount (not the account) changed.
    old_bank_account_id = transaction.bank_account_id
    old_credit_card_id  = transaction.credit_card_id
    old_type            = transaction.type
    old_amount          = transaction.amount

    # Step 1 — revert the old balance using captured pre-update values
    if old_bank_account_id:
        old_acc = await db.get(BankAccount, old_bank_account_id)
        if old_acc:
            if old_type == "income":
                old_acc.balance -= old_amount
            elif old_type == "expense":
                old_acc.balance += old_amount

    if old_credit_card_id:
        old_cc = await db.get(CreditCard, old_credit_card_id)
        if old_cc:
            if old_type == "expense":
                old_cc.outstanding_balance = max(Decimal("0"), old_cc.outstanding_balance - old_amount)
            elif old_type == "income":
                old_cc.outstanding_balance += old_amount

    # Step 2 — apply the incoming field updates
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(transaction, k, v)

    # Step 3 — apply the new balance using the (now-updated) transaction fields
    if transaction.bank_account_id:
        new_acc = await db.get(BankAccount, transaction.bank_account_id)
        if new_acc:
            if transaction.type == "income":
                new_acc.balance += transaction.amount
            elif transaction.type == "expense":
                new_acc.balance -= transaction.amount

    if transaction.credit_card_id:
        new_cc = await db.get(CreditCard, transaction.credit_card_id)
        if new_cc:
            if transaction.type == "expense":
                new_cc.outstanding_balance += transaction.amount
            elif transaction.type == "income":
                new_cc.outstanding_balance = max(Decimal("0"), new_cc.outstanding_balance - transaction.amount)

    await db.commit()
    await db.refresh(transaction)

    # Reload with relationships for the response
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category), selectinload(Transaction.bank_account), selectinload(Transaction.credit_card))
        .where(Transaction.id == transaction.id)
    )
    transaction = result.scalar_one()

    return APIResponse(data=TransactionResponse.model_validate(transaction).model_dump(), message="Transaction updated")

@router.delete("/{id}")
async def delete_transaction(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == id, Transaction.user_id == current_user.id, Transaction.deleted_at.is_(None))
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Revert balance
    if transaction.bank_account_id:
        acc = await db.get(BankAccount, transaction.bank_account_id)
        if acc:
            if transaction.type == "income":
                acc.balance -= transaction.amount
            elif transaction.type == "expense":
                acc.balance += transaction.amount
                
    if transaction.credit_card_id:
        cc = await db.get(CreditCard, transaction.credit_card_id)
        if cc:
            if transaction.type == "expense":
                cc.outstanding_balance = max(0, cc.outstanding_balance - transaction.amount)
            elif transaction.type == "income":
                cc.outstanding_balance += transaction.amount

    transaction.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Transaction deleted")

@router.post("/bulk-delete")
async def bulk_delete(
    ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Transaction).where(Transaction.id.in_(ids), Transaction.user_id == current_user.id, Transaction.deleted_at.is_(None))
    )
    transactions = result.scalars().all()
    
    for transaction in transactions:
        # Revert balance
        if transaction.bank_account_id:
            acc = await db.get(BankAccount, transaction.bank_account_id)
            if acc:
                if transaction.type == "income":
                    acc.balance -= transaction.amount
                elif transaction.type == "expense":
                    acc.balance += transaction.amount
        transaction.deleted_at = datetime.now(timezone.utc)
        
    await db.commit()
    return APIResponse(message=f"{len(transactions)} transactions deleted")

@router.get("/export/csv")
async def export_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category), selectinload(Transaction.bank_account))
        .where(Transaction.user_id == current_user.id, Transaction.deleted_at.is_(None))
        .order_by(desc(Transaction.date))
    )
    transactions = result.scalars().all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "description", "merchant", "type", "amount", "category", "account", "status", "payment_method", "notes"])
    
    for t in transactions:
        writer.writerow([
            t.date.isoformat(),
            t.description,
            t.merchant or "",
            t.type,
            str(t.amount),
            t.category.name if t.category else "",
            t.bank_account.name if t.bank_account else "",
            t.status,
            t.payment_method or "",
            t.notes or ""
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )

@router.post("/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = await file.read()
    csv_file = io.StringIO(content.decode("utf-8"))
    reader = csv.DictReader(csv_file)
    
    categories_result = await db.execute(select(Category).where(Category.user_id == current_user.id))
    categories = {c.name.lower(): c.id for c in categories_result.scalars().all()}
    
    accounts_result = await db.execute(select(BankAccount).where(BankAccount.user_id == current_user.id))
    accounts = {a.name.lower(): a.id for a in accounts_result.scalars().all()}
    
    imported = 0
    for row in reader:
        cat_id = categories.get(row.get("category_name", "").lower())
        
        try:
            date_val = datetime.strptime(row.get("date", "").strip(), "%Y-%m-%d").date()
        except ValueError:
            date_val = date.today()
            
        amount_val = row.get("amount", "0").strip()
        try:
            amount = float(amount_val)
        except ValueError:
            amount = 0.0
            
        transaction = Transaction(
            user_id=current_user.id,
            date=date_val,
            description=row.get("description", ""),
            type=row.get("type", "expense"),
            amount=amount,
            category_id=cat_id,
            payment_method=row.get("payment_method"),
            notes=row.get("notes")
        )
        db.add(transaction)
        imported += 1
        
    await db.commit()
    return APIResponse(message=f"Imported {imported} transactions")
