from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.models.user import User
from app.models.investment import Investment
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.investment import InvestmentCreate, InvestmentUpdate, InvestmentResponse
import uuid
from datetime import datetime, timezone
from app.services.market_service import fetch_eod_prices

router = APIRouter()

@router.get("/")
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
        current_value = inv.current_price * inv.quantity
        purchase_value = inv.purchase_price * inv.quantity
        gain_loss = current_value - purchase_value
        
        inv_data["current_value"] = float(current_value)
        inv_data["gain_loss"] = float(gain_loss)
        inv_data["gain_loss_percent"] = float((gain_loss / purchase_value) * 100) if purchase_value > 0 else 0
        data.append(inv_data)
        
    return APIResponse(data=data)

@router.get("/summary")
async def get_investments_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Investment)
        .where(Investment.user_id == current_user.id, Investment.is_active.is_(True), Investment.deleted_at.is_(None))
    )
    investments = result.scalars().all()
    
    total_value = 0
    total_invested = 0
    allocation = {}
    
    for inv in investments:
        current_value = float(inv.current_price * inv.quantity)
        purchase_value = float(inv.purchase_price * inv.quantity)
        total_value += current_value
        total_invested += purchase_value
        
        if inv.type not in allocation:
            allocation[inv.type] = 0
        allocation[inv.type] += current_value
        
    total_gain_loss = total_value - total_invested
    total_gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
    
    allocation_data = []
    for k, v in allocation.items():
        allocation_data.append({
            "type": k,
            "value": v,
            "pct": (v / total_value * 100) if total_value > 0 else 0
        })
        
    return APIResponse(data={
        "total_value": total_value,
        "total_invested": total_invested,
        "total_gain_loss": total_gain_loss,
        "total_gain_loss_pct": total_gain_loss_pct,
        "allocation": allocation_data
    })

@router.post("/", status_code=201)
async def create_investment(data: InvestmentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    inv = Investment(**data.model_dump(), user_id=current_user.id)
    db.add(inv)
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
        
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(inv, k, v)
        
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

