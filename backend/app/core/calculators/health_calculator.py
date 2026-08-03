from datetime import date
from decimal import Decimal


class HealthCalculator:
    """Calculates objective health (On Track, At Risk, Off Track)."""

    @staticmethod
    def calculate_health(
        current_funding: Decimal, 
        target_amount: Decimal, 
        target_date: date | None, 
        start_date: date,
        current_date: date | None = None
    ) -> str:
        """
        Determines if an objective is On Track, At Risk, or Off Track.
        """
        if not current_date:
            current_date = date.today()

        if current_funding >= target_amount:
            return "Completed"
            
        if not target_date:
            # Without a target date, we can't measure pacing.
            # Return "At Risk" (a known UI status) rather than "Needs Attention" which has no frontend style.
            return "On Track" if current_funding > 0 else "At Risk"

        total_days = (target_date - start_date).days
        if total_days <= 0:
            return "Off Track" if current_funding < target_amount else "Completed"

        days_passed = (current_date - start_date).days
        if days_passed < 0:
            days_passed = 0

        # Linear projection of required funding
        expected_funding = (target_amount / Decimal(total_days)) * Decimal(days_passed)

        # Allow a 10% buffer for "On Track"
        buffer_amount = expected_funding * Decimal("0.90")
        
        # Risk threshold at 75%
        risk_amount = expected_funding * Decimal("0.75")

        if current_funding >= buffer_amount:
            return "On Track"
        elif current_funding >= risk_amount:
            return "At Risk"
        else:
            return "Off Track"
