import asyncio
import uuid
from datetime import datetime, timedelta
import random

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.security import get_password_hash
from app.models.user import User
from app.models.category import Category
from app.models.bank_account import BankAccount
from app.models.credit_card import CreditCard
from app.models.asset import Asset
from app.models.investment import Investment
from app.models.loan import Loan
from app.models.transaction import Transaction
from app.models.goal import Goal
from app.models.planning import AssetAllocation
from app.models.budget import Budget
from app.api.v1.auth import DEFAULT_CATEGORIES

DATABASE_URL = "sqlite+aiosqlite:///finora.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def seed():
    async with AsyncSessionLocal() as db:
        # Check if demo user exists
        result = await db.execute(select(User).where(User.email == "demo@example.com"))
        user = result.scalar_one_or_none()
        
        if user:
            print("Demo user already exists. Clearing old data...")
            # We don't cascade delete easily here without raw SQL, so let's just make a new demo user with a unique email for this seed if we want, or raw delete
            await db.execute(Category.__table__.delete().where(Category.user_id == user.id))
            await db.execute(Transaction.__table__.delete().where(Transaction.user_id == user.id))
            await db.execute(BankAccount.__table__.delete().where(BankAccount.user_id == user.id))
            await db.execute(CreditCard.__table__.delete().where(CreditCard.user_id == user.id))
            await db.execute(Asset.__table__.delete().where(Asset.user_id == user.id))
            await db.execute(Investment.__table__.delete().where(Investment.user_id == user.id))
            await db.execute(Loan.__table__.delete().where(Loan.user_id == user.id))
            await db.execute(Goal.__table__.delete().where(Goal.user_id == user.id))
            await db.execute(AssetAllocation.__table__.delete())
            await db.execute(Budget.__table__.delete().where(Budget.user_id == user.id))
            await db.commit()
        else:
            user = User(
                email="demo@example.com",
                full_name="Demo User",
                hashed_password=get_password_hash("password")
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"Created demo user: demo@example.com / password")

        # Create categories
        categories = {}
        for cat_data in DEFAULT_CATEGORIES:
            category = Category(
                user_id=user.id,
                name=cat_data["name"],
                type=cat_data["type"],
                icon=cat_data["icon"],
                color=cat_data["color"],
                is_default=True,
            )
            db.add(category)
            await db.flush()
            categories[cat_data["name"]] = category.id
            
        # Bank Accounts
        checking = BankAccount(user_id=user.id, name="Main Checking", bank_name="Chase", account_type="checking", balance=12500.0)
        savings = BankAccount(user_id=user.id, name="High Yield Savings", bank_name="Ally", account_type="savings", balance=45000.0)
        db.add_all([checking, savings])
        await db.flush()

        # Credit Cards
        cc = CreditCard(user_id=user.id, name="Sapphire Reserve", bank_name="Chase", credit_limit=30000.0, outstanding_balance=2450.0, interest_rate=19.99, billing_cycle_day=15, due_day=5)
        db.add(cc)

        # Assets
        house = Asset(user_id=user.id, name="Primary Residence", asset_type="property", purchase_price=450000.0, current_value=520000.0, purchase_date=datetime.now().date())
        car = Asset(user_id=user.id, name="Tesla Model 3", asset_type="vehicle", purchase_price=45000.0, current_value=32000.0, purchase_date=datetime.now().date())
        db.add_all([house, car])
        await db.flush()

        # Investments
        vanguard = Investment(user_id=user.id, name="Vanguard S&P 500", type="etf", broker="Vanguard", purchase_price=100000.0, current_price=538.92, quantity=250.5, purchase_date=datetime.now().date())
        db.add(vanguard)
        await db.flush()

        # Loans
        mortgage = Loan(user_id=user.id, name="Mortgage", lender="Chase", loan_type="mortgage", principal_amount=360000.0, outstanding_balance=345000.0, interest_rate=3.5, start_date=datetime.now().date() - timedelta(days=700), end_date=datetime.now().date() + timedelta(days=10000), emi_amount=1850.0, tenure_months=360)
        db.add(mortgage)

        # Financial Objectives
        house_goal = Goal(
            user_id=user.id,
            name="Buy Rental Property",
            goal_type="House",
            target_amount=100000.0,
            target_date=datetime.now().date() + timedelta(days=365*2),
            importance="High",
            risk_profile="Moderate"
        )
        db.add(house_goal)
        await db.flush()

        # Allocate assets to goal
        alloc1 = AssetAllocation(user_id=user.id, objective_type="goal", objective_id=house_goal.id, asset_type="bank_account", asset_id=savings.id, allocation_type="fixed", allocation_value=20000.0)
        alloc2 = AssetAllocation(user_id=user.id, objective_type="goal", objective_id=house_goal.id, asset_type="investment", asset_id=vanguard.id, allocation_type="percentage", allocation_value=20.0)
        db.add_all([alloc1, alloc2])

        # Transactions (Last 90 days)
        now = datetime.now()
        for i in range(90):
            date = now - timedelta(days=i)
            # Daily coffee
            db.add(Transaction(user_id=user.id, amount=5.50, type="expense", category_id=categories["Food & Dining"], date=date, description="Coffee", payment_method="credit_card"))
            
            # Weekly groceries
            if i % 7 == 0:
                db.add(Transaction(user_id=user.id, amount=120.0, type="expense", category_id=categories["Food & Dining"], date=date, description="Groceries", payment_method="credit_card"))
                
            # Monthly rent/mortgage
            if date.day == 1:
                db.add(Transaction(user_id=user.id, amount=1850.0, type="expense", category_id=categories["Housing & Rent"], date=date, description="Mortgage Payment", payment_method="bank_transfer"))
                
            # Bi-weekly salary
            if i % 14 == 0:
                db.add(Transaction(user_id=user.id, amount=3500.0, type="income", category_id=categories["Salary"], date=date, description="Salary", payment_method="bank_transfer"))

        await db.commit()
        print("Successfully seeded demo data for demo@example.com!")

if __name__ == "__main__":
    asyncio.run(seed())
