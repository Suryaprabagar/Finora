from typing import List, Dict, Any, Type
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.planning import AssetAllocation
from app.models.asset import Asset
from app.models.bank_account import BankAccount
from app.models.investment import Investment


class AllocationEngine:
    """Dynamically calculates funding based on linked assets."""

    @staticmethod
    async def calculate_current_funding(
        db: AsyncSession, 
        objective_id: uuid.UUID, 
        objective_type: str
    ) -> Decimal:
        """
        Calculates the total funding for an objective based on its linked assets.
        """
        query = select(AssetAllocation).where(
            AssetAllocation.objective_id == objective_id,
            AssetAllocation.objective_type == objective_type
        )
        result = await db.execute(query)
        allocations = result.scalars().all()

        total_funding = Decimal("0")
        
        for allocation in allocations:
            if allocation.allocation_type == "fixed":
                total_funding += allocation.allocation_value
            elif allocation.allocation_type == "percentage":
                asset_balance = await AllocationEngine.get_asset_balance(db, allocation.asset_id, allocation.asset_type)
                total_funding += (asset_balance * allocation.allocation_value) / Decimal("100")
                
        return total_funding

    @staticmethod
    async def get_asset_balance(db: AsyncSession, asset_id: uuid.UUID, asset_type: str) -> Decimal:
        """
        Fetches the live balance of a linked asset.
        """
        if asset_type == "BankAccount":
            query = select(BankAccount).where(BankAccount.id == asset_id)
            result = await db.execute(query)
            account = result.scalars().first()
            return account.balance if account else Decimal("0")
            
        elif asset_type == "Investment":
            query = select(Investment).where(Investment.id == asset_id)
            result = await db.execute(query)
            investment = result.scalars().first()
            return investment.current_value if investment else Decimal("0")
            
        elif asset_type == "Asset":
            query = select(Asset).where(Asset.id == asset_id)
            result = await db.execute(query)
            asset = result.scalars().first()
            return asset.current_value if asset else Decimal("0")
            
        return Decimal("0")

    @staticmethod
    async def validate_allocation(
        db: AsyncSession, 
        asset_id: uuid.UUID, 
        asset_type: str, 
        new_allocation_type: str, 
        new_allocation_value: Decimal,
        exclude_allocation_id: uuid.UUID | None = None
    ) -> bool:
        """
        Validates that total allocations on a single asset do not exceed 100% (for percentages)
        or the asset's total balance (for mixed/fixed).
        For simplicity in this engine version, we check percentage totals.
        """
        query = select(AssetAllocation).where(
            AssetAllocation.asset_id == asset_id,
            AssetAllocation.asset_type == asset_type
        )
        result = await db.execute(query)
        allocations = result.scalars().all()
        
        total_percentage = Decimal("0")
        total_fixed = Decimal("0")
        
        for alloc in allocations:
            if exclude_allocation_id and alloc.id == exclude_allocation_id:
                continue
            if alloc.allocation_type == "percentage":
                total_percentage += alloc.allocation_value
            elif alloc.allocation_type == "fixed":
                total_fixed += alloc.allocation_value
                
        if new_allocation_type == "percentage":
            total_percentage += new_allocation_value
        else:
            total_fixed += new_allocation_value
            
        if total_percentage > Decimal("100"):
            raise ValueError(f"Total percentage allocation for this asset exceeds 100% (Current: {total_percentage}%)")
            
        # Additional checks can be added to ensure total_fixed + (balance * total_percentage/100) <= balance
        # However, balances fluctuate, so strict validation at allocation time is complex. 
        # Typically, we just warn or cap at runtime.
        
        return True
