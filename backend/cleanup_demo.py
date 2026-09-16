import asyncio
import os
import sys
from sqlalchemy import select, delete

# Setup path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import AsyncSessionLocal
from app.models import (
    User, Category, BankAccount, CreditCard, Transaction,
    Budget, BudgetItem, Goal, GoalContribution,
    Bill, BillPayment, Investment, Loan, Asset, InsurancePolicy,
    AssetAllocation
)
from app.storage.storage_manager import StorageManager
from app.core.config import settings

DEMO_EMAILS = ["demo@finora.app", "demo@example.com"]

async def cleanup():
    # 1. Load latest from drive to make sure SQLite is in sync with cloud
    sm = StorageManager(AsyncSessionLocal, settings)
    await sm.initialize()
    if settings.GOOGLE_DRIVE_ENABLED:
        print("Restoring from Drive before cleanup...")
        await sm.load_latest_state()

    # 2. Delete demo users and their data
    async with AsyncSessionLocal() as db:
        users = (await db.execute(select(User).where(User.email.in_(DEMO_EMAILS)))).scalars().all()
        if not users:
            print("No demo users found in DB.")
        else:
            for user in users:
                print(f"Deleting demo data for {user.email}...")
                uid = user.id
                await db.execute(delete(Transaction).where(Transaction.user_id == uid))
                await db.execute(delete(BudgetItem).where(BudgetItem.budget_id.in_(select(Budget.id).where(Budget.user_id == uid))))
                await db.execute(delete(Budget).where(Budget.user_id == uid))
                await db.execute(delete(GoalContribution).where(GoalContribution.goal_id.in_(select(Goal.id).where(Goal.user_id == uid))))
                await db.execute(delete(AssetAllocation).where(AssetAllocation.user_id == uid))
                await db.execute(delete(Goal).where(Goal.user_id == uid))
                await db.execute(delete(BillPayment).where(BillPayment.bill_id.in_(select(Bill.id).where(Bill.user_id == uid))))
                await db.execute(delete(Bill).where(Bill.user_id == uid))
                await db.execute(delete(Investment).where(Investment.user_id == uid))
                await db.execute(delete(Loan).where(Loan.user_id == uid))
                await db.execute(delete(Asset).where(Asset.user_id == uid))
                await db.execute(delete(InsurancePolicy).where(InsurancePolicy.user_id == uid))
                await db.execute(delete(CreditCard).where(CreditCard.user_id == uid))
                await db.execute(delete(BankAccount).where(BankAccount.user_id == uid))
                await db.execute(delete(Category).where(Category.user_id == uid))
                await db.execute(delete(User).where(User.id == uid))
            await db.commit()
            print("Demo users deleted.")

    # 3. Save cleaned state to Drive
    if settings.GOOGLE_DRIVE_ENABLED:
        print("Saving cleaned state to Drive...")
        await sm.save_state(reason="manual_cleanup")
        print("Cleanup synced to Drive.")

if __name__ == "__main__":
    asyncio.run(cleanup())
