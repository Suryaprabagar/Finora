import uuid
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
import datetime

from app.models.goal import Goal
from app.core.calculators.allocation_engine import AllocationEngine
from app.core.calculators.funding_calculator import FundingCalculator
from app.core.calculators.health_calculator import HealthCalculator
from app.core.calculators.forecast_calculator import ForecastCalculator
from app.core.calculators.priority_engine import PriorityEngine
from app.core.rules.rule_engine import RuleEngine


class PlanningService:
    """Orchestrates the Financial Planning calculation pipeline."""

    @staticmethod
    async def get_objective_overview(db: AsyncSession, objective: Goal) -> Dict[str, Any]:
        """
        Runs the full calculation pipeline for a single objective.
        Returns a dictionary of all calculated metrics and recommendations.
        """
        # 1. Total Applied Funding
        current_funding = await FundingCalculator.calculate_total_funding(
            db, objective.id, "Goal"
        )
        
        # 2. Progress Percentage
        progress_percentage = Decimal("0")
        if objective.target_amount > 0:
            progress_percentage = (current_funding / objective.target_amount) * Decimal("100")
            progress_percentage = min(Decimal("100"), progress_percentage)
            
        # 3. Goal Health
        health = HealthCalculator.calculate_health(
            current_funding=current_funding,
            target_amount=objective.target_amount,
            target_date=objective.target_date,
            start_date=objective.created_at.date()
        )
        
        # 4. Estimated Completion Forecast
        forecast_date = ForecastCalculator.forecast_completion_date(
            current_funding=current_funding,
            target_amount=objective.target_amount,
            monthly_contribution=objective.monthly_contribution
        )
        
        # 5. Priority Score
        priority_score = PriorityEngine.calculate_priority_score(
            importance=objective.importance,
            target_date=objective.target_date,
            priority_override=objective.priority_override
        )
        
        objective_data = {
            "id": str(objective.id),
            "name": objective.name,
            "goal_type": objective.goal_type,
            "target_amount": float(objective.target_amount),
            "current_funding": float(current_funding),
            "progress_percentage": float(progress_percentage),
            "target_date": objective.target_date.isoformat() if objective.target_date else None,
            "health": health,
            "forecast_completion_date": forecast_date.isoformat() if forecast_date else None,
            "priority_score": priority_score,
            "strategy": objective.strategy,
            "risk_profile": objective.risk_profile,
        }
        
        # 6. Rule Evaluation (Recommendations)
        recommendations = RuleEngine.evaluate_objective({
            **objective_data,
            "target_amount": objective.target_amount,
            "current_funding": current_funding
        })
        
        objective_data["recommendations"] = recommendations
        return objective_data

    @staticmethod
    async def get_user_planning_overview(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Runs the calculation pipeline for all user objectives to build the workspace overview.
        """
        query = select(Goal).where(Goal.user_id == user_id)
        result = await db.execute(query)
        goals = result.scalars().all()
        
        objectives_data = []
        for goal in goals:
            data = await PlanningService.get_objective_overview(db, goal)
            objectives_data.append(data)
            
        # Sort by priority score (descending)
        objectives_data.sort(key=lambda x: x["priority_score"], reverse=True)
        
        total_target = sum(obj["target_amount"] for obj in objectives_data)
        total_funding = sum(obj["current_funding"] for obj in objectives_data)
        
        # Aggregate Health
        health_summary = {
            "On Track": len([o for o in objectives_data if o["health"] == "On Track"]),
            "At Risk": len([o for o in objectives_data if o["health"] == "At Risk"]),
            "Off Track": len([o for o in objectives_data if o["health"] == "Off Track"]),
            "Completed": len([o for o in objectives_data if o["health"] == "Completed"])
        }
        
        return {
            "overview": {
                "total_target": total_target,
                "total_funding": total_funding,
                "overall_progress": (total_funding / total_target * 100) if total_target > 0 else 0,
                "health_summary": health_summary,
                "total_objectives": len(objectives_data)
            },
            "objectives": objectives_data
        }
