from typing import List, Dict, Any
from app.models.investment import Investment
from decimal import Decimal

class PerformanceService:
    @staticmethod
    def calculate_performance_summary(investments: List[Investment]) -> Dict[str, Any]:
        """Calculates top performers, worst performers, and overall summary."""
        total_invested = Decimal("0")
        total_current_value = Decimal("0")
        
        performers = []
        
        for inv in investments:
            invested = inv.purchase_price * inv.quantity
            current = inv.current_price * inv.quantity
            
            total_invested += invested
            total_current_value += current
            
            gain_val = current - invested
            gain_pct = float((gain_val / invested * 100) if invested > 0 else 0)
            
            performers.append({
                "id": str(inv.id),
                "name": inv.name,
                "symbol": inv.symbol,
                "type": inv.type,
                "invested": float(invested),
                "current": float(current),
                "gain_value": float(gain_val),
                "gain_pct": gain_pct
            })
            
        total_gain = total_current_value - total_invested
        total_gain_pct = float((total_gain / total_invested * 100) if total_invested > 0 else 0)
        
        # Sort by gain percentage
        performers.sort(key=lambda x: x["gain_pct"], reverse=True)
        
        top_performers = performers[:3]
        worst_performers = [p for p in reversed(performers[-3:]) if p["gain_pct"] < 0]
        
        return {
            "summary": {
                "total_invested": float(total_invested),
                "total_current_value": float(total_current_value),
                "total_gain": float(total_gain),
                "total_gain_pct": total_gain_pct
            },
            "top_performers": top_performers,
            "worst_performers": worst_performers
        }
