from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.user import User
from app.models.goal import Goal, GoalContribution
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse, GoalContributionCreate
import uuid
from datetime import date, datetime, timezone

router = APIRouter()

@router.get("")
async def get_goals(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
        .order_by(desc(Goal.created_at))
    )
    goals = result.scalars().all()
    
    goals_data = []
    for g in goals:
        g_data = GoalResponse.model_validate(g).model_dump()
        g_data["progress_percentage"] = round(float(g.current_amount) / float(g.target_amount) * 100, 1) if g.target_amount > 0 else 0
        goals_data.append(g_data)
        
    return APIResponse(data=goals_data)

@router.get("/summary")
async def get_goals_summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    current_month_start = today.replace(day=1)
    
    result = await db.execute(
        select(
            func.coalesce(func.sum(Goal.current_amount), 0).label("total_saved"),
            func.coalesce(func.sum(Goal.target_amount), 0).label("total_target"),
        )
        .where(Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
    )
    totals = result.one()
    
    counts_result = await db.execute(
        select(Goal.status, func.count(Goal.id))
        .where(Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
        .group_by(Goal.status)
    )
    counts = dict(counts_result.all())
    
    contributions_result = await db.execute(
        select(func.coalesce(func.sum(GoalContribution.amount), 0))
        .join(Goal)
        .where(
            Goal.user_id == current_user.id,
            GoalContribution.date >= current_month_start,
            Goal.deleted_at.is_(None)
        )
    )
    monthly_contributions = float(contributions_result.scalar() or 0)
    
    return APIResponse(data={
        "total_saved": float(totals.total_saved),
        "total_target": float(totals.total_target),
        "completed_count": counts.get("completed", 0),
        "active_count": counts.get("active", 0),
        "monthly_contributions": monthly_contributions
    })

@router.post("", status_code=201)
async def create_goal(data: GoalCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    goal = Goal(**data.model_dump(), user_id=current_user.id)
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return APIResponse(data=GoalResponse.model_validate(goal).model_dump(), message="Goal created")

@router.get("/{id}")
async def get_goal(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Goal)
        .options(selectinload(Goal.contributions))
        .where(Goal.id == id, Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
        
    g_data = GoalResponse.model_validate(goal).model_dump()
    g_data["progress_percentage"] = round(float(goal.current_amount) / float(goal.target_amount) * 100, 1) if goal.target_amount > 0 else 0
    return APIResponse(data=g_data)

@router.put("/{id}")
async def update_goal(id: uuid.UUID, data: GoalUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Goal).where(Goal.id == id, Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(goal, k, v)
        
    await db.commit()
    await db.refresh(goal)
    return APIResponse(data=GoalResponse.model_validate(goal).model_dump(), message="Goal updated")

@router.delete("/{id}")
async def delete_goal(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Goal).where(Goal.id == id, Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
        
    goal.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return APIResponse(message="Goal deleted")

@router.post("/{id}/contribute")
async def contribute_to_goal(
    id: uuid.UUID, 
    data: GoalContributionCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Goal).where(Goal.id == id, Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
        
    contribution = GoalContribution(**data.model_dump(), goal_id=goal.id)
    db.add(contribution)
    
    goal.current_amount += data.amount
    if goal.current_amount >= goal.target_amount:
        goal.status = "completed"
        
    await db.commit()
    return APIResponse(message="Contribution added")
