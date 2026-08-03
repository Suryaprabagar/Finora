from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.category import Category
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.backup_service import export_user_data, restore_user_data
import uuid
from datetime import datetime, timezone
import json

router = APIRouter()

@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Category)
        .where(Category.user_id == current_user.id, Category.deleted_at.is_(None))
    )
    categories = result.scalars().all()
    return APIResponse(data=[CategoryResponse.model_validate(c).model_dump() for c in categories])

@router.post("/categories", status_code=201)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cat = Category(**data.model_dump(), user_id=current_user.id)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return APIResponse(data=CategoryResponse.model_validate(cat).model_dump(), message="Category created")

@router.put("/categories/{id}")
async def update_category(id: uuid.UUID, data: CategoryUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Category).where(Category.id == id, Category.user_id == current_user.id, Category.deleted_at.is_(None))
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(cat, k, v)
        
    await db.commit()
    await db.refresh(cat)
    return APIResponse(data=CategoryResponse.model_validate(cat).model_dump(), message="Category updated")

@router.delete("/categories/{id}")
async def delete_category(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Category).where(Category.id == id, Category.user_id == current_user.id, Category.deleted_at.is_(None))
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    cat.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Category deleted")

@router.post("/reset-demo")
async def reset_demo(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.email != "demo@finora.app":
        raise HTTPException(status_code=403, detail="Only demo user can reset data")
        
    try:
        from scripts.seed_data import reset_demo_data
        await reset_demo_data()
        return APIResponse(message="Demo data reset successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_data(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Exports all user data for backup."""
    try:
        data = await export_user_data(db, current_user.id)
        
        # Wrap in metadata
        backup = {
            "app": "Finora",
            "backupVersion": 1,
            "schemaVersion": 1,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "finoraVersion": "1.0.0",
            "data": data
        }
        return backup  # Return direct dict to avoid Pydantic serialization limits
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/restore")
async def restore_data(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Restores user data from a backup payload within a transaction."""
    # 1. Validate payload
    if payload.get("app") != "Finora" or "data" not in payload:
        raise HTTPException(status_code=400, detail="Invalid backup file format.")
        
    if payload.get("schemaVersion", 1) > 1:
        raise HTTPException(status_code=400, detail="Backup schema version is too new for this version of Finora.")

    # 2. Restore in transaction
    try:
        # FastAPI's async session is already in a transaction by default until commit
        await restore_user_data(db, current_user.id, payload["data"])
        await db.commit()
        return APIResponse(message="Data restored successfully.")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
