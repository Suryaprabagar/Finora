import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.calculators.allocation_engine import AllocationEngine
from app.models.goal import GoalContribution


class FundingCalculator:
    """Aggregates dynamically allocated funding with manual contributions."""

    @staticmethod
    async def calculate_total_funding(
        db: AsyncSession, 
        objective_id: uuid.UUID, 
        objective_type: str
    ) -> Decimal:
        """
        Calculates total funding by adding dynamically allocated asset funds 
        and any manual contributions directly deposited.
        """
        # 1. Get allocated funding from linked assets
        allocated_funding = await AllocationEngine.calculate_current_funding(
            db, objective_id, objective_type
        )
        
        # 2. Get manual contributions (if objective is a Goal)
        manual_funding = Decimal("0")
        if objective_type == "Goal":
            query = select(func.sum(GoalContribution.amount)).where(
                GoalContribution.goal_id == objective_id
            )
            result = await db.execute(query)
            total_contributions = result.scalar()
            if total_contributions:
                manual_funding = total_contributions
                
        # Future modules (e.g., RetirementContribution) can be added here
                
        return allocated_funding + manual_funding
