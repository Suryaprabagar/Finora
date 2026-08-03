from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.user import User
from app.models.goal import Goal, GoalContribution
from app.dependencies import get_current_user
from app.schemas.common import APIResponse
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse, GoalContributionCreate, GoalContributionResponse
from app.core.planning.planning_service import PlanningService
import uuid
from datetime import datetime, timezone

router = APIRouter()

@router.get("/")
async def get_goals(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetches all goals, processed through the PlanningService calculation pipeline."""
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
        .order_by(desc(Goal.created_at))
    )
    goals = result.scalars().all()
    
    goals_data = []
    for g in goals:
        data = await PlanningService.get_objective_overview(db, g)
        goals_data.append(data)
        
    return APIResponse(data=goals_data)

@router.get("/overview")
async def get_goals_overview(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetches the aggregated financial planning workspace overview."""
    overview_data = await PlanningService.get_user_planning_overview(db, current_user.id)
    return APIResponse(data=overview_data)

@router.post("/", status_code=201)
async def create_goal(data: GoalCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    goal = Goal(**data.model_dump(), user_id=current_user.id)
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return APIResponse(data=GoalResponse.model_validate(goal).model_dump(), message="Goal created")

@router.get("/{id}")
async def get_goal(id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Goal).where(Goal.id == id, Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
        
    goal_data = await PlanningService.get_objective_overview(db, goal)
    return APIResponse(data=goal_data)

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

@router.post("/{id}/contribute", status_code=201)
async def contribute_to_goal(
    id: uuid.UUID,
    data: GoalContributionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a manual contribution towards a goal."""
    result = await db.execute(
        select(Goal).where(Goal.id == id, Goal.user_id == current_user.id, Goal.deleted_at.is_(None))
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    contribution = GoalContribution(
        goal_id=goal.id,
        amount=data.amount,
        date=data.date,
        notes=data.notes,
    )
    db.add(contribution)
    await db.commit()
    await db.refresh(contribution)

    return APIResponse(
        data=GoalContributionResponse.model_validate(contribution).model_dump(),
        message="Contribution recorded successfully"
    )

