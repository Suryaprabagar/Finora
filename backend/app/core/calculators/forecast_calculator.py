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

    @staticmethod
    def calculate_required_sip(
        current_funding: Decimal,
        target_amount: Decimal,
        target_date: datetime.date,
        annual_return_rate: Decimal,
        current_date: datetime.date | None = None
    ) -> Decimal:
        """
        Calculates the required monthly SIP (Systematic Investment Plan) amount to reach 
        the target_amount by the target_date, given an annual return rate.
        Assumes monthly compounding.
        """
        if not current_date:
            current_date = datetime.date.today()

        if current_funding >= target_amount:
            return Decimal("0")

        if target_date <= current_date:
            return target_amount - current_funding

        # Calculate months remaining
        delta = relativedelta(target_date, current_date)
        months = delta.years * 12 + delta.months
        if months <= 0:
            return target_amount - current_funding

        # If return rate is <= 0, do linear math
        if annual_return_rate <= Decimal("0"):
            return (target_amount - current_funding) / Decimal(str(months))

        monthly_rate = float(annual_return_rate) / 100.0 / 12.0
        n = months
        fv = float(target_amount - current_funding)

        # FV = P * [ ((1 + r)^n - 1) / r ]
        # P = FV * r / ((1 + r)^n - 1)
        import math
        try:
            numerator = fv * monthly_rate
            denominator = math.pow(1 + monthly_rate, n) - 1
            if denominator == 0:
                 sip = fv / n
            else:
                 sip = numerator / denominator
        except OverflowError:
             sip = fv / n

        return Decimal(str(round(sip, 2)))
