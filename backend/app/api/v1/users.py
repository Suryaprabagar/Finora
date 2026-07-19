"""User profile endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.auth import ChangePasswordRequest
from app.schemas.common import APIResponse
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/me")
async def get_profile(current_user: User = Depends(get_current_user)):
    return APIResponse(data=UserResponse.model_validate(current_user).model_dump())

@router.put("/me")
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.currency is not None:
        current_user.currency = data.currency
    if data.currency_symbol is not None:
        current_user.currency_symbol = data.currency_symbol
    if data.theme is not None:
        current_user.theme = data.theme
    if data.phone is not None:
        current_user.phone = data.phone
    await db.commit()
    await db.refresh(current_user)
    return APIResponse(data=UserResponse.model_validate(current_user).model_dump(), message="Profile updated")

@router.post("/me/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(data.new_password)
    await db.commit()
    return APIResponse(data=None, message="Password changed successfully")
