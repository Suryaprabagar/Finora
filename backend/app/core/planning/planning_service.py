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
    async def get_objective_overview(db: AsyncSession, objective: Goal, dynamic_monthly_contribution: Decimal = None) -> Dict[str, Any]:
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
        contribution_to_use = dynamic_monthly_contribution if dynamic_monthly_contribution is not None else objective.monthly_contribution
        forecast_date = ForecastCalculator.forecast_completion_date(
            current_funding=current_funding,
            target_amount=objective.target_amount,
            monthly_contribution=contribution_to_use
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
            "allocated_monthly_surplus": float(contribution_to_use)
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
        Computes dynamic surplus and waterfalls it into goals based on priority.
        """
        from sqlalchemy import func
        from app.models.transaction import Transaction
        from app.models.loan import Loan
        from app.models.credit_card import CreditCard

        # Calculate Monthly Surplus
        # Income / Expenses (assume last 30 days for simplicity)
        from datetime import date
        thirty_days_ago = date.today() - datetime.timedelta(days=30)
        
        income_r = await db.execute(select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.user_id == user_id, Transaction.type == 'income', Transaction.date >= thirty_days_ago))
        monthly_income = income_r.scalar() or Decimal("0")
        
        expense_r = await db.execute(select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.user_id == user_id, Transaction.type == 'expense', Transaction.date >= thirty_days_ago))
        monthly_expense = expense_r.scalar() or Decimal("0")
        
        loan_r = await db.execute(select(func.coalesce(func.sum(Loan.emi_amount), 0)).where(Loan.user_id == user_id, Loan.is_active.is_(True), Loan.deleted_at.is_(None)))
        monthly_emis = loan_r.scalar() or Decimal("0")
        
        cc_r = await db.execute(select(func.coalesce(func.sum(CreditCard.outstanding_balance), 0)).where(CreditCard.user_id == user_id, CreditCard.is_active.is_(True), CreditCard.deleted_at.is_(None)))
        # Assuming CC minimum payment is 5% of outstanding
        monthly_cc_min = (cc_r.scalar() or Decimal("0")) * Decimal("0.05")
        
        surplus = monthly_income - monthly_expense - monthly_emis - monthly_cc_min
        
        from app.models.investment import Investment
        inv_result = await db.execute(select(Investment).where(Investment.user_id == user_id, Investment.is_active.is_(True), Investment.deleted_at.is_(None)))
        investments = inv_result.scalars().all()
        
        total_investment_value = Decimal("0")
        weighted_return = Decimal("0")
        
        for inv in investments:
            value = inv.current_price * inv.quantity
            total_investment_value += value
            if inv.interest_rate:
                weighted_return += value * inv.interest_rate
            else:
                if inv.current_price and inv.purchase_price and inv.purchase_date:
                    days_held = (date.today() - inv.purchase_date).days
                    if days_held > 0:
                        years_held = Decimal(str(days_held)) / Decimal("365.25")
                        if years_held > 0:
                            ret = ((inv.current_price - inv.purchase_price) / inv.purchase_price) / years_held * Decimal("100")
                            weighted_return += value * ret
                            
        avg_annual_return = Decimal("8.0")
        if total_investment_value > 0:
            calculated_return = weighted_return / total_investment_value
            if calculated_return > 0:
                avg_annual_return = calculated_return

        query = select(Goal).where(Goal.user_id == user_id)
        result = await db.execute(query)
        goals = result.scalars().all()
        
        goals_with_priority = []
        for g in goals:
            ps = PriorityEngine.calculate_priority_score(g.importance, g.target_date, g.priority_override)
            goals_with_priority.append((ps, g))
            
        goals_with_priority.sort(key=lambda x: x[0], reverse=True)
        
        remaining_surplus = surplus if surplus > 0 else Decimal("0")
        
        for ps, goal in goals_with_priority:
            current_funding = await FundingCalculator.calculate_total_funding(db, goal.id, "Goal")
            
            if goal.target_date:
                required_sip = ForecastCalculator.calculate_required_sip(
                    current_funding=current_funding,
                    target_amount=goal.target_amount,
                    target_date=goal.target_date,
                    annual_return_rate=avg_annual_return
                )
            else:
                required_sip = goal.monthly_contribution if goal.monthly_contribution > 0 else (goal.target_amount - current_funding) / Decimal("60")
                if required_sip < 0: required_sip = Decimal("0")
                
            allocated = Decimal("0")
            if remaining_surplus >= required_sip:
                allocated = required_sip
                remaining_surplus -= required_sip
            else:
                allocated = remaining_surplus
                remaining_surplus = Decimal("0")
                
            goal.temp_required_sip = required_sip
            goal.temp_allocated = allocated
            
        if remaining_surplus > 0:
            for ps, goal in goals_with_priority:
                current_funding = await FundingCalculator.calculate_total_funding(db, goal.id, "Goal")
                if current_funding < goal.target_amount:
                    goal.temp_allocated += remaining_surplus
                    remaining_surplus = Decimal("0")
                    break

        objectives_data = []
        for ps, goal in goals_with_priority:
            data = await PlanningService.get_objective_overview(db, goal, dynamic_monthly_contribution=goal.temp_allocated)
            data["required_sip"] = float(goal.temp_required_sip)
            data["avg_annual_return"] = float(avg_annual_return)
            objectives_data.append(data)
            
        total_target = sum(obj["target_amount"] for obj in objectives_data)
        total_funding = sum(obj["current_funding"] for obj in objectives_data)
        
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
                "total_objectives": len(objectives_data),
                "monthly_surplus": float(surplus),
                "monthly_income": float(monthly_income),
                "monthly_expense": float(monthly_expense),
                "monthly_emis": float(monthly_emis),
                "monthly_cc_min": float(monthly_cc_min)
            },
            "objectives": objectives_data
        }
