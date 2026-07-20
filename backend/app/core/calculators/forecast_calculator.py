import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta


class ForecastCalculator:
    """Projects estimated completion dates based on funding rates."""

    @staticmethod
    def forecast_completion_date(
        current_funding: Decimal, 
        target_amount: Decimal, 
        monthly_contribution: Decimal,
        current_date: datetime.date | None = None
    ) -> datetime.date | None:
        """
        Estimates the completion date given current funding and monthly contributions.
        Does not account for compound interest in this simple version, but can be extended.
        """
        if not current_date:
            current_date = datetime.date.today()

        if current_funding >= target_amount:
            return current_date

        if monthly_contribution <= Decimal("0"):
            # Cannot project if there is no positive monthly contribution
            return None

        remaining_amount = target_amount - current_funding
        
        # Calculate months needed
        months_needed = float(remaining_amount / monthly_contribution)
        
        # Ceil to the next full month
        import math
        months_needed_ceil = math.ceil(months_needed)
        
        estimated_date = current_date + relativedelta(months=+months_needed_ceil)
        return estimated_date
