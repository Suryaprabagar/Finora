import uuid
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.investment import Investment
from app.core.analytics.allocation_service import AllocationService
from app.core.analytics.risk_service import RiskService
from app.core.analytics.benchmark_service import BenchmarkService
from app.core.analytics.performance_service import PerformanceService
from app.core.analytics.portfolio_service import PortfolioService

class AnalyticsService:
    @staticmethod
    async def get_dashboard_analytics(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Orchestrates all analytics services to build the dashboard payload."""
        
        # 1. Fetch active investments
        result = await db.execute(
            select(Investment).where(
                Investment.user_id == user_id, 
                Investment.is_active.is_(True), 
                Investment.deleted_at.is_(None)
            )
        )
        investments = result.scalars().all()
        
        # 2. Asset Allocation
        allocation_data = AllocationService.calculate_allocation(investments)
        
        # 3. Risk Profile
        risk_data = RiskService.calculate_risk_profile(allocation_data["distribution"])
        
        # 4. Performance Summary (Top/Worst & Totals)
        perf_data = PerformanceService.calculate_performance_summary(investments)
        
        # 5. Portfolio Growth History
        history_data = await PortfolioService.get_growth_history(db, user_id)
        
        # 6. Benchmark Performance
        benchmark_data = BenchmarkService.get_benchmarks_performance()
        
        return {
            "summary": perf_data["summary"],
            "allocation": allocation_data,
            "risk_profile": risk_data,
            "performance": {
                "top_performers": perf_data["top_performers"],
                "worst_performers": perf_data["worst_performers"]
            },
            "growth_history": history_data,
            "benchmarks": benchmark_data,
            "last_updated": datetime.utcnow().isoformat()
        }
