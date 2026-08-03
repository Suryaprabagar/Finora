"""Authentication endpoints: register, login, refresh, logout, forgot/reset password."""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from app.models.user import User
from app.models.category import Category
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
from app.schemas.user import UserResponse
from app.schemas.common import APIResponse
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Default categories created for every new user
DEFAULT_CATEGORIES = [
    # Expense categories
    {"name": "Housing & Rent", "type": "expense", "icon": "home", "color": "#6f4627"},
    {"name": "Food & Dining", "type": "expense", "icon": "restaurant", "color": "#8b5e3c"},
    {"name": "Transport", "type": "expense", "icon": "directions_car", "color": "#265763"},
    {"name": "Shopping", "type": "expense", "icon": "shopping_bag", "color": "#406f7c"},
    {"name": "Entertainment", "type": "expense", "icon": "theaters", "color": "#6b5c47"},
    {"name": "Healthcare", "type": "expense", "icon": "local_hospital", "color": "#ba1a1a"},
    {"name": "Education", "type": "expense", "icon": "school", "color": "#5c6bc0"},
    {"name": "Travel", "type": "expense", "icon": "flight", "color": "#00897b"},
    {"name": "Utilities", "type": "expense", "icon": "bolt", "color": "#f57c00"},
    {"name": "Personal Care", "type": "expense", "icon": "spa", "color": "#ad1457"},
    # Income categories
    {"name": "Salary", "type": "income", "icon": "work", "color": "#265763"},
    {"name": "Freelance Income", "type": "income", "icon": "laptop", "color": "#406f7c"},
    {"name": "Investment Returns", "type": "income", "icon": "trending_up", "color": "#2e7d32"},
    {"name": "Rental Income", "type": "income", "icon": "home", "color": "#6f4627"},
    {"name": "Business Income", "type": "income", "icon": "business", "color": "#1565c0"},
]


# BUG-003 fix: renamed from register_original and made internal (not exposed as a route).
# Called by the public /register route below.
async def _do_register(data: RegisterRequest, db: AsyncSession):
    """Register a new user and create default categories."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
    )
    db.add(user)
    await db.flush()  # get user.id without committing

    # Create default categories
    for cat_data in DEFAULT_CATEGORIES:
        category = Category(
            user_id=user.id,
            name=cat_data["name"],
            type=cat_data["type"],
            icon=cat_data["icon"],
            color=cat_data["color"],
            is_default=True,
        )
        db.add(category)

    await db.commit()
    await db.refresh(user)

    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return APIResponse(
        data={
            "user": UserResponse.model_validate(user).model_dump(),
            "tokens": {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"},
        },
        message="Registration successful",
    )


# BUG-003 fix: renamed from login_original and made internal (not exposed as a route).
async def _do_login(data: LoginRequest, db: AsyncSession):
    """Authenticate user and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == data.email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return APIResponse(
        data={
            "user": UserResponse.model_validate(user).model_dump(),
            "tokens": {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"},
        },
        message="Login successful",
    )


@router.post("/refresh")
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Issue a new access token using a valid refresh token."""
    payload = verify_token(data.refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id), User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token({"sub": str(user.id)})
    return APIResponse(data={"access_token": access_token, "token_type": "bearer"}, message="Token refreshed")


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout (stateless - client should discard tokens)."""
    return APIResponse(data=None, message="Logged out successfully")


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Generate a password reset token (returned in response since no email server)."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Always return 200 to prevent email enumeration
    if not user:
        return APIResponse(
            data={"message": "If this email exists, a reset token has been generated"},
            message="Reset token generated",
        )

    # Generate reset token (UUID-based, 1 hour expiry)
    reset_token = str(uuid.uuid4()).replace("-", "")
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.commit()

    return APIResponse(
        data={
            "reset_token": reset_token,
            "expires_in": "1 hour",
            "message": "Copy this token and use it on the Reset Password page",
        },
        message="Reset token generated successfully",
    )


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using the reset token."""
    result = await db.execute(
        select(User).where(
            User.reset_token == data.token,
            User.reset_token_expires > datetime.now(timezone.utc),
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = get_password_hash(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await db.commit()

    return APIResponse(data=None, message="Password reset successfully. Please login with your new password.")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return APIResponse(data=UserResponse.model_validate(current_user).model_dump())

@router.post("/login")
async def login_wrapper(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    # BUG-002 fix: log errors internally, never return stack traces to the client
    try:
        return await _do_login(data, db)
    except HTTPException:
        raise  # let FastAPI handle HTTP exceptions normally
    except Exception:
        import traceback
        logger.error(f"Unexpected error during login: {traceback.format_exc()}")
        return APIResponse(success=False, message="An unexpected error occurred. Please try again.", data=None)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_wrapper(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # BUG-002 fix: log errors internally, never return stack traces to the client
    try:
        return await _do_register(data, db)
    except HTTPException:
        raise  # let FastAPI handle HTTP exceptions normally
    except Exception:
        import traceback
        logger.error(f"Unexpected error during register: {traceback.format_exc()}")
        return APIResponse(success=False, message="An unexpected error occurred. Please try again.", data=None)
