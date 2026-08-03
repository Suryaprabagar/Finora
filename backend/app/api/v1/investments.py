from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.models.user import User
from app.models.investment import Investment
from app.models.bank_account import BankAccount
from app.models.transaction import Transaction
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.investment import InvestmentCreate, InvestmentUpdate, InvestmentResponse, InvestmentTrade
import uuid
from datetime import datetime, timezone
from app.services.market_service import fetch_eod_prices

router = APIRouter()

@router.get("")
async def get_investments(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Investment)
        .where(Investment.user_id == current_user.id, Investment.deleted_at.is_(None))
        .order_by(desc(Investment.created_at))
    )
    investments = result.scalars().all()
    
    data = []
    for inv in investments:
        inv_data = InvestmentResponse.model_validate(inv).model_dump()
        current_value = float(inv.current_price * inv.quantity)
        purchase_value = float(inv.purchase_price * inv.quantity)
        gain_loss = current_value - purchase_value
        inv_data["current_value"]      = current_value
        inv_data["gain_loss"]          = gain_loss
        inv_data["gain_loss_percent"]  = (gain_loss / purchase_value * 100) if purchase_value > 0 else 0
        data.append(inv_data)
        
    return APIResponse(data=data)

@router.get("/summary")
async def get_investments_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Single aggregate query — no Python loop over N rows
    agg_result = await db.execute(
        select(
            func.coalesce(func.sum(Investment.current_price * Investment.quantity), 0).label('total_value'),
            func.coalesce(func.sum(Investment.purchase_price * Investment.quantity), 0).label('total_invested'),
        )
        .where(Investment.user_id == current_user.id, Investment.is_active.is_(True), Investment.deleted_at.is_(None))
    )
    agg = agg_result.one()
    total_value    = float(agg.total_value)
    total_invested = float(agg.total_invested)

    # Allocation breakdown still needs per-type grouping — one query
    alloc_result = await db.execute(
        select(
            Investment.type,
            func.coalesce(func.sum(Investment.current_price * Investment.quantity), 0).label('value')
        )
        .where(Investment.user_id == current_user.id, Investment.is_active.is_(True), Investment.deleted_at.is_(None))
        .group_by(Investment.type)
    )
    allocation_data = [
        {"type": row.type, "value": float(row.value), "pct": (float(row.value) / total_value * 100) if total_value > 0 else 0}
        for row in alloc_result.all()
    ]

    total_gain_loss     = total_value - total_invested
    total_gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0

    return APIResponse(data={
        "total_value":         total_value,
        "total_invested":      total_invested,
        "total_gain_loss":     total_gain_loss,
        "total_gain_loss_pct": total_gain_loss_pct,
        "allocation":          allocation_data
    })

@router.post("", status_code=201)
async def create_investment(data: InvestmentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    inv = Investment(**data.model_dump(), user_id=current_user.id)
    db.add(inv)
    
    if data.bank_account_id:
        acc = await db.get(BankAccount, data.bank_account_id)
        if acc:
            acc.balance -= (data.purchase_price * data.quantity)
            
    # Bond automated transactions logic
    if data.type.lower() == "bonds" and data.bank_account_id:
        # Recurring income for frequent pay
        if data.coupon_frequency and data.next_coupon_date:
            coupon_amount = 0
            if data.interest_rate:
                # Basic estimated coupon logic: Total Value * Rate / Freq
                principal = float(data.purchase_price * data.quantity)
                rate = float(data.interest_rate) / 100.0
                freq_div = 1
                if data.coupon_frequency.lower() == 'monthly': freq_div = 12
                elif data.coupon_frequency.lower() == 'quarterly': freq_div = 4
                elif data.coupon_frequency.lower() in ('semi-annually', 'half-yearly'): freq_div = 2
                coupon_amount = (principal * rate) / freq_div
            
            recurring_inc = Transaction(
                user_id=current_user.id,
                bank_account_id=data.bank_account_id,
                type="income",
                amount=coupon_amount,
                date=data.next_coupon_date,
                description=f"Bond Coupon - {data.name}",
                is_recurring=True,
                recurring_interval=data.coupon_frequency.lower()
            )
            db.add(recurring_inc)
            
        # One-time principal payout at maturity
        if data.maturity_date:
            principal_amount = data.purchase_price * data.quantity
            maturity_inc = Transaction(
                user_id=current_user.id,
                bank_account_id=data.bank_account_id,
                type="income",
                amount=principal_amount,
                date=data.maturity_date,
                description=f"Bond Maturity Principal - {data.name}",
                is_recurring=False
            )
            db.add(maturity_inc)
            
    await db.commit()
    await db.refresh(inv)
    return APIResponse(data=InvestmentResponse.model_validate(inv).model_dump(), message="Investment created")

@router.get("/{id}")
async def get_investment(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Investment).where(Investment.id == id, Investment.user_id == current_user.id, Investment.deleted_at.is_(None))
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
        
    inv_data = InvestmentResponse.model_validate(inv).model_dump()
    current_value = inv.current_price * inv.quantity
    purchase_value = inv.purchase_price * inv.quantity
    gain_loss = current_value - purchase_value
    
    inv_data["current_value"] = float(current_value)
    inv_data["gain_loss"] = float(gain_loss)
    inv_data["gain_loss_percent"] = float((gain_loss / purchase_value) * 100) if purchase_value > 0 else 0
    return APIResponse(data=inv_data)

@router.put("/{id}")
async def update_investment(id: uuid.UUID, data: InvestmentUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Investment).where(Investment.id == id, Investment.user_id == current_user.id, Investment.deleted_at.is_(None))
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
        
    old_value = inv.purchase_price * inv.quantity
    old_acc_id = inv.bank_account_id
    
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(inv, k, v)
        
    new_value = inv.purchase_price * inv.quantity
    new_acc_id = inv.bank_account_id
    
    if old_acc_id == new_acc_id and old_acc_id is not None:
        if old_value != new_value:
            acc = await db.get(BankAccount, old_acc_id)
            if acc:
                acc.balance = acc.balance + old_value - new_value
    elif old_acc_id != new_acc_id:
        if old_acc_id is not None:
            old_acc = await db.get(BankAccount, old_acc_id)
            if old_acc:
                old_acc.balance += old_value
        if new_acc_id is not None:
            new_acc = await db.get(BankAccount, new_acc_id)
            if new_acc:
                new_acc.balance -= new_value
                
    await db.commit()
    await db.refresh(inv)
    return APIResponse(data=InvestmentResponse.model_validate(inv).model_dump(), message="Investment updated")

@router.delete("/{id}")
async def delete_investment(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Investment).where(Investment.id == id, Investment.user_id == current_user.id, Investment.deleted_at.is_(None))
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
        
    if inv.bank_account_id:
        acc = await db.get(BankAccount, inv.bank_account_id)
        if acc:
            # BUG-011 fix: refund the original purchase cost, not the current market value
            acc.balance += (inv.purchase_price * inv.quantity)
            
    inv.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Investment deleted")
@router.post("/sync")
async def sync_investment_prices(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Investment)
        .where(Investment.user_id == current_user.id, Investment.is_active.is_(True), Investment.deleted_at.is_(None))
    )
    investments = result.scalars().all()
    
    # Collect unique symbols
    symbols = list(set([inv.symbol for inv in investments if inv.symbol]))
    
    if not symbols:
        return APIResponse(message="No valid symbols found to sync.")
        
    prices = await fetch_eod_prices(symbols)
    

    updated_count = 0
    
    for inv in investments:
        if inv.symbol and inv.symbol in prices:
            inv.current_price = prices[inv.symbol]
            updated_count += 1
            
    if updated_count > 0:
        await db.commit()
        
    return APIResponse(message=f"Synced {updated_count} investments with EOD market data.")

@router.post("/{id}/trade")
async def trade_investment(id: uuid.UUID, data: InvestmentTrade, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Investment).where(Investment.id == id, Investment.user_id == current_user.id, Investment.deleted_at.is_(None))
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")

    old_qty = inv.quantity
    old_avg = inv.purchase_price
    
    if data.action == "buy":
        new_qty = old_qty + data.quantity
        new_total_cost = (old_qty * old_avg) + (data.quantity * data.price)
        new_avg = new_total_cost / new_qty if new_qty > 0 else 0
        
        inv.quantity = new_qty
        inv.purchase_price = new_avg
        inv.current_price = data.price
        
        if data.bank_account_id:
            acc = await db.get(BankAccount, data.bank_account_id)
            if acc:
                acc.balance -= (data.quantity * data.price)
                
    elif data.action == "sell":
        if data.quantity > old_qty:
            raise HTTPException(status_code=400, detail="Cannot sell more than held quantity")
            
        new_qty = old_qty - data.quantity
        inv.quantity = new_qty
        inv.current_price = data.price
        
        if data.bank_account_id:
            acc = await db.get(BankAccount, data.bank_account_id)
            if acc:
                acc.balance += (data.quantity * data.price)
                
    await db.commit()
    await db.refresh(inv)
    return APIResponse(data=InvestmentResponse.model_validate(inv).model_dump(), message=f"Investment {data.action} successful")
