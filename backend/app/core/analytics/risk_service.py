from typing import List, Dict, Any

class RiskService:
    # Default configurable risk weights (1-5 scale, 1 is safest, 5 is most aggressive)
    RISK_WEIGHTS = {
        'cash': 1,
        'fd': 1,
        'bonds': 2,
        'gold': 2,
        'reit': 3,
        'mutual_fund': 3, # Average, could be configurable per fund later
        'etf': 3,
        'stock': 4,
        'crypto': 5,
        'other': 3
    }
    
    @classmethod
    def calculate_risk_profile(cls, allocation_distribution: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates portfolio risk profile based on asset allocation distribution."""
        if not allocation_distribution:
            return {
                "overall_score": 0.0,
                "profile": "Unknown",
                "explanation": "Add investments to see your risk profile.",
                "breakdown": []
            }
            
        total_portfolio_value = sum(item["value"] for item in allocation_distribution)
        if total_portfolio_value == 0:
            return {
                "overall_score": 0.0,
                "profile": "Unknown",
                "explanation": "Portfolio value is zero.",
                "breakdown": []
            }

        weighted_risk_sum = 0.0
        breakdown = []
        
        for item in allocation_distribution:
            asset_type = item["type"]
            weight = cls.RISK_WEIGHTS.get(asset_type, 3)
            allocation_ratio = item["value"] / total_portfolio_value
            
            contribution = weight * allocation_ratio
            weighted_risk_sum += contribution
            
            breakdown.append({
                "type": item["label"],
                "percentage": item["pct"],
                "risk_weight": weight,
                "risk_contribution": round(contribution, 2)
            })

        score = round(weighted_risk_sum, 2)
        
        # Determine profile category
        if score < 2.0:
            profile = "Conservative"
            exp = "Optimized for capital preservation with minimal volatility exposure."
        elif score < 3.0:
            profile = "Moderate"
            exp = "Balanced approach for steady long-term growth with calculated volatility."
        elif score < 4.0:
            profile = "Growth"
            exp = "Focuses on capital appreciation with higher exposure to market fluctuations."
        else:
            profile = "Aggressive"
            exp = "Maximizes returns with significant exposure to high-risk assets."
            
        return {
            "overall_score": score,
            "profile": profile,
            "explanation": exp,
            "breakdown": breakdown
        }
