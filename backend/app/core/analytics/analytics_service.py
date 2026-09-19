from app.api.v1 import dashboard
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.investment import Investment
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.category import Category
from app.core.analytics.allocation_service import AllocationService
from app.core.analytics.risk_service import RiskService
from app.core.analytics.benchmark_service import BenchmarkService
from app.core.analytics.performance_service import PerformanceService
from app.core.analytics.portfolio_service import PortfolioService


class AnalyticsService:

    @staticmethod
    async def get_dashboard_analytics(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Orchestrates all analytics services to build the investments dashboard payload.

        Uses asyncio.gather so the investment DB fetch and portfolio history query
        run concurrently — total time = max(query_a, query_b) instead of their sum.
        """
        # Fire both DB-bound async operations at the same time
        inv_result, history_data = await asyncio.gather(
            db.execute(
                select(Investment).where(
                    Investment.user_id == user_id,
                    Investment.is_active.is_(True),
                    Investment.deleted_at.is_(None)
                )
            ),
            PortfolioService.get_growth_history(db, user_id),
        )
        investments = inv_result.scalars().all()

        # CPU-bound sub-services (no I/O) — run synchronously, no await needed
        allocation_data = AllocationService.calculate_allocation(investments)
        risk_data       = RiskService.calculate_risk_profile(allocation_data["distribution"])
        perf_data       = PerformanceService.calculate_performance_summary(investments)
        benchmark_data  = BenchmarkService.get_benchmarks_performance()

        return {
            "summary":       perf_data["summary"],
            "allocation":    allocation_data,
            "risk_profile":  risk_data,
            "performance": {
                "top_performers":   perf_data["top_performers"],
                "worst_performers": perf_data["worst_performers"]
            },
            "growth_history": history_data,
            "benchmarks":     benchmark_data,
            "last_updated":   datetime.utcnow().isoformat()
        }

    @staticmethod
    async def get_reports_analytics(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Build reports dashboard analytics from real user data only."""

        today = datetime.utcnow().date()
        six_months_ago = today.replace(day=1) - timedelta(days=180)
        current_month_start = today.replace(day=1)

    # ---------------------------------------------------------
    # Monthly income + expense data
    # ---------------------------------------------------------
        transaction_res = await db.execute(
            select(
                func.extract('year', Transaction.date).label('year'),
                func.extract('month', Transaction.date).label('month'),
                Transaction.type.label('type'),
                func.sum(Transaction.amount).label('total')
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.type.in_(['income', 'expense']),
                Transaction.date >= six_months_ago
            )
            .group_by(
                func.extract('year', Transaction.date),
                func.extract('month', Transaction.date),
                Transaction.type
            )
            .order_by(
                func.extract('year', Transaction.date),
                func.extract('month', Transaction.date)
            )
        )

    # ---------------------------------------------------------
    # Expense breakdown by category
    # ---------------------------------------------------------
        exp_res = await db.execute(
            select(
                Category.name,
                func.sum(Transaction.amount).label('total')
            )
            .join(
                Category,
                Transaction.category_id == Category.id
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.type == 'expense'
            )
            .group_by(Category.name)
            .order_by(func.sum(Transaction.amount).desc())
        )

    # ---------------------------------------------------------
    # Total budget
    # ---------------------------------------------------------
        budget_res = await db.execute(
            select(func.sum(Budget.total_limit))
            .where(Budget.user_id == user_id)
        )

    # ---------------------------------------------------------
    # Current month actual expenses
    # ---------------------------------------------------------
        actual_res = await db.execute(
            select(func.sum(Transaction.amount))
            .where(
                Transaction.user_id == user_id,
                Transaction.type == 'expense',
                Transaction.date >= current_month_start
            )
        )

    # ---------------------------------------------------------
    # Investments
    # ---------------------------------------------------------
        inv_res = await db.execute(
            select(Investment)
            .where(
                Investment.user_id == user_id,
                Investment.is_active.is_(True),
                Investment.deleted_at.is_(None)
            )
        )

    # ---------------------------------------------------------
    # Build monthly income / expense / cash flow
    # ---------------------------------------------------------
        months = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]

        monthly_data = {}

        for row in transaction_res.all():
            year = int(row.year)
            month = int(row.month)

            key = (year, month)

            if key not in monthly_data:
                monthly_data[key] = {
                    "name": months[month - 1],
                    "year": year,
                    "income": 0.0,
                    "expenses": 0.0,
                    "value": 0.0
                }

            amount = float(row.total or 0)

            if row.type == 'income':
                monthly_data[key]["income"] += amount

            elif row.type == 'expense':
                monthly_data[key]["expenses"] += amount

        monthly_rows = [
            monthly_data[key]
            for key in sorted(monthly_data.keys())
        ]

    # ---------------------------------------------------------
    # Real cash flow = income - expenses
    # ---------------------------------------------------------
        for row in monthly_rows:
            row["value"] = round(
                row["income"] - row["expenses"],
                2
            )

    # Income chart
        income_data = [
            {
                "name": row["name"],
                "value": row["income"]
            }
            for row in monthly_rows
            if row["income"] > 0
        ]

    # Cash flow chart
        cashflow_data = [
            {
                "name": row["name"],
                "value": row["value"]
            }
            for row in monthly_rows
        ]

    # ---------------------------------------------------------
    # Expenses breakdown
    # ---------------------------------------------------------
        expenses_data = []
        total_exp = 0.0

        for row in exp_res.all():
            value = float(row.total or 0)

            expenses_data.append({
                "name": row.name,
                "value": value
            })

            total_exp += value

        for expense in expenses_data:
            expense["percentage"] = (
                round((expense["value"] / total_exp) * 100)
                if total_exp > 0
                else 0
            )

    # ---------------------------------------------------------
    # Budget
    # ---------------------------------------------------------
        total_budget = float(budget_res.scalar() or 0)
        total_actual = float(actual_res.scalar() or 0)

        budget_data = {
            "budget": total_budget,
            "actual": total_actual,
            "variance": total_budget - total_actual
        }

    # ---------------------------------------------------------
    # Investment allocation
    # ---------------------------------------------------------
        investments = inv_res.scalars().all()

        allocation = AllocationService.calculate_allocation(
            investments
        )

    # ---------------------------------------------------------
    # Net worth growth
    # ---------------------------------------------------------
        growth_history = await PortfolioService.get_growth_history(
            db,
            user_id
        )

        net_worth_growth_pct = None

        if growth_history and len(growth_history) >= 2:
            first_val = growth_history[0]["value"]
            last_val = growth_history[-1]["value"]

            if first_val > 0:
                net_worth_growth_pct = round(
                    ((last_val - first_val) / first_val) * 100,
                    1
                )

    # ---------------------------------------------------------
    # Final response
    # ---------------------------------------------------------
        return {
            "income": income_data,

            "expenses": expenses_data,

            "budget": budget_data,

            "cashflow": cashflow_data,

            "net_worth_growth_pct": net_worth_growth_pct,

            "investments": {
                "allocation": allocation["distribution"]
            }
        }