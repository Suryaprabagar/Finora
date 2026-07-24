from typing import List, Dict, Any
from decimal import Decimal
import uuid


class RuleEngine:
    """Evaluates financial objectives against business rules to generate recommendations."""

    @staticmethod
    def evaluate_objective(objective_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes in calculated objective data and applies deterministic rules.
        """
        recommendations = []
        
        goal_type = objective_data.get("goal_type")
        health = objective_data.get("health")
        target_amount = objective_data.get("target_amount", Decimal("0"))
        current_funding = objective_data.get("current_funding", Decimal("0"))
        
        # 1. Health Rules
        if health == "Off Track":
            recommendations.append({
                "type": "warning",
                "title": "Goal is Off Track",
                "description": "Consider increasing your monthly contribution or linking more assets to meet your target.",
                "action": "Adjust Contributions"
            })
        elif health == "At Risk":
            recommendations.append({
                "type": "info",
                "title": "Goal is At Risk",
                "description": "You are slightly behind on this goal. A small increase in funding can get you back on track.",
                "action": "Review Funding"
            })
            
        # 2. Type-Specific Rules
        if goal_type == "Emergency Fund":
            # For demonstration, assume 3 months expenses is around $15,000
            # In a full implementation, we'd fetch actual expense data.
            if target_amount < Decimal("10000"):
                recommendations.append({
                    "type": "info",
                    "title": "Increase Emergency Target",
                    "description": "Financial experts recommend 3-6 months of expenses for an emergency fund.",
                    "action": "Adjust Target"
                })
                
        elif goal_type == "Retirement":
            if current_funding > Decimal("0") and objective_data.get("strategy") == "Savings Only":
                recommendations.append({
                    "type": "warning",
                    "title": "Sub-optimal Strategy",
                    "description": "Retirement goals usually benefit from Investment Growth rather than Savings Only due to inflation.",
                    "action": "Change Strategy"
                })

        return recommendations
