from datetime import date
from decimal import Decimal


class PriorityEngine:
    """Calculates priority scores for financial objectives based on urgency and importance."""

    @staticmethod
    def calculate_priority_score(
        importance: str,
        target_date: date | None,
        priority_override: int | None = None,
        current_date: date | None = None
    ) -> int:
        """
        Returns a priority score from 1 (lowest) to 100 (highest).
        Override always takes precedence if set.
        """
        if priority_override is not None:
            return max(1, min(100, priority_override))
            
        if not current_date:
            current_date = date.today()

        score = 0
        
        # Base score from importance
        importance_scores = {
            "High": 60,
            "Medium": 40,
            "Low": 20
        }
        score += importance_scores.get(importance, 40)
        
        # Urgency score from target date (up to +40 points)
        if target_date:
            days_remaining = (target_date - current_date).days
            if days_remaining <= 0:
                score += 40  # Overdue or due today
            elif days_remaining <= 30:
                score += 35
            elif days_remaining <= 90:
                score += 30
            elif days_remaining <= 180:
                score += 20
            elif days_remaining <= 365:
                score += 10
            elif days_remaining <= 1095: # 3 years
                score += 5
                
        # Cap at 100
        return min(100, score)
