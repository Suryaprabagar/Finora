from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.models.user import User
from app.models.asset import Asset
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse
import uuid
from datetime import datetime, timezone

router = APIRouter()

@router.get("/")
async def get_assets(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Asset)
        .where(Asset.user_id == current_user.id, Asset.deleted_at.is_(None))
        .order_by(desc(Asset.created_at))
    )
    assets = result.scalars().all()
    
    data = []
    for asset in assets:
        a_data = AssetResponse.model_validate(asset).model_dump()
        appreciation_loss = float(asset.current_value) - float(asset.purchase_price)
        a_data["appreciation_loss"] = appreciation_loss
        a_data["appreciation_percent"] = (appreciation_loss / float(asset.purchase_price) * 100) if float(asset.purchase_price) > 0 else 0
        data.append(a_data)
        
    return APIResponse(data=data)

@router.get("/summary")
async def get_assets_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Asset).where(Asset.user_id == current_user.id, Asset.deleted_at.is_(None))
    )
    assets = result.scalars().all()
    
    total_value = 0
    total_purchase = 0
    by_type = {}
    
    for asset in assets:
        c_val = float(asset.current_value)
        p_val = float(asset.purchase_price)
        total_value += c_val
        total_purchase += p_val
        
        if asset.type not in by_type:
            by_type[asset.type] = {"value": 0, "count": 0}
        by_type[asset.type]["value"] += c_val
        by_type[asset.type]["count"] += 1
        
    total_appreciation = total_value - total_purchase
    
    by_type_list = [
        {"type": k, "value": v["value"], "count": v["count"]}
        for k, v in by_type.items()
    ]
    
    return APIResponse(data={
        "total_value": total_value,
        "total_purchase": total_purchase,
        "total_appreciation": total_appreciation,
        "by_type": by_type_list
    })

@router.post("/", status_code=201)
async def create_asset(data: AssetCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    asset = Asset(**data.model_dump(), user_id=current_user.id)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return APIResponse(data=AssetResponse.model_validate(asset).model_dump(), message="Asset created")

@router.get("/{id}")
async def get_asset(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Asset).where(Asset.id == id, Asset.user_id == current_user.id, Asset.deleted_at.is_(None))
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return APIResponse(data=AssetResponse.model_validate(asset).model_dump())

@router.put("/{id}")
async def update_asset(id: uuid.UUID, data: AssetUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Asset).where(Asset.id == id, Asset.user_id == current_user.id, Asset.deleted_at.is_(None))
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(asset, k, v)
        
    await db.commit()
    await db.refresh(asset)
    return APIResponse(data=AssetResponse.model_validate(asset).model_dump(), message="Asset updated")

@router.delete("/{id}")
async def delete_asset(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Asset).where(Asset.id == id, Asset.user_id == current_user.id, Asset.deleted_at.is_(None))
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    asset.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Asset deleted")
