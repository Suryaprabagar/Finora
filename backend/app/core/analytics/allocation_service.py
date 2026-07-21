from typing import List, Dict, Any
from app.models.investment import Investment

class AllocationService:
    @staticmethod
    def calculate_allocation(investments: List[Investment]) -> Dict[str, Any]:
        """Calculates asset allocation from a list of investments."""
        allocation = {}
        total_value = 0.0

        # Define color map for asset categories
        color_map = {
            'stock': '#8B5E3C',
            'mutual_fund': '#A07D63',
            'etf': '#B89B85',
            'bonds': '#D6C2A8',
            'gold': '#E7E2DB',
            'reit': '#C4B9AD',
            'fd': '#F5F5F5',
            'cash': '#A3B19B',
            'crypto': '#6F6A63',
            'other': '#E0E0E0'
        }
        
        # Standardize categories
        category_mapping = {
            'stock': 'Stocks',
            'mutual_fund': 'Mutual Funds',
            'etf': 'ETFs',
            'bonds': 'Bonds',
            'gold': 'Gold',
            'reit': 'REITs',
            'fd': 'Fixed Deposits',
            'cash': 'Cash',
            'crypto': 'Crypto',
            'other': 'Other'
        }

        for inv in investments:
            current_val = float(inv.current_price * inv.quantity)
            total_value += current_val
            
            # Normalize type string
            inv_type = str(inv.type).lower().strip()
            if inv_type not in color_map:
                inv_type = 'other'
                
            if inv_type not in allocation:
                allocation[inv_type] = {
                    "type": inv_type,
                    "label": category_mapping.get(inv_type, inv_type.title()),
                    "value": 0.0,
                    "color": color_map[inv_type],
                    "asset_count": 0
                }
                
            allocation[inv_type]["value"] += current_val
            allocation[inv_type]["asset_count"] += 1

        # Calculate percentages
        allocation_list = []
        for v in allocation.values():
            pct = (v["value"] / total_value * 100) if total_value > 0 else 0.0
            v["pct"] = round(pct, 2)
            # Only include if value > 0
            if v["value"] > 0:
                allocation_list.append(v)
                
        # Sort by value descending
        allocation_list.sort(key=lambda x: x["value"], reverse=True)
        
        return {
            "total_value": round(total_value, 2),
            "distribution": allocation_list
        }
