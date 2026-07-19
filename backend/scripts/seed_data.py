import asyncio
import os
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models import (
    User, Category, BankAccount, CreditCard, Transaction,
    Budget, BudgetItem, Goal, GoalContribution,
    Bill, BillPayment, Investment, Loan, Asset, InsurancePolicy
)

async def main():
    async with AsyncSessionLocal() as db:
        await seed_data(db)

async def seed_data(db: AsyncSession):
    # 1. Demo User
    user = User(
        email="demo@finora.app",
        full_name="Arjun Mehta",
        hashed_password=get_password_hash("demo1234"),
        currency="INR",
        currency_symbol="₹"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 2. Categories
    categories_data = [
        # Expense categories
        {"name": "Housing & Rent", "type": "expense", "icon": "home", "color": "#6f4627"},
        {"name": "Food & Dining", "type": "expense", "icon": "restaurant", "color": "#8b5e3c"},
        {"name": "Transport", "type": "expense", "icon": "directions_car", "color": "#265763"},
        {"name": "Shopping", "type": "expense", "icon": "shopping_bag", "color": "#406f7c"},
        {"name": "Entertainment", "type": "expense", "icon": "theaters", "color": "#6b5c47"},
        {"name": "Healthcare", "type": "expense", "icon": "local_hospital", "color": "#ba1a1a"},
        {"name": "Education", "type": "expense", "icon": "school", "color": "#5c6bc0"},
        {"name": "Travel", "type": "expense", "icon": "flight", "color": "#00897b"},
        {"name": "Utilities", "type": "expense", "icon": "bolt", "color": "#f57c00"},
        {"name": "Personal Care", "type": "expense", "icon": "spa", "color": "#ad1457"},
        # Income categories
        {"name": "Salary", "type": "income", "icon": "work", "color": "#265763"},
        {"name": "Freelance Income", "type": "income", "icon": "laptop", "color": "#406f7c"},
        {"name": "Investment Returns", "type": "income", "icon": "trending_up", "color": "#2e7d32"},
        {"name": "Rental Income", "type": "income", "icon": "home", "color": "#6f4627"},
        {"name": "Business Income", "type": "income", "icon": "business", "color": "#1565c0"}
    ]
    
    categories = {}
    for cat_data in categories_data:
        cat = Category(**cat_data, user_id=user.id)
        db.add(cat)
        await db.commit()
        await db.refresh(cat)
        categories[cat.name] = cat.id

    # 3. Bank Accounts
    accounts = [
        BankAccount(user_id=user.id, name="HDFC Savings", account_type="savings", balance=Decimal("845200"), account_number="1234"),
        BankAccount(user_id=user.id, name="ICICI Current", account_type="checking", balance=Decimal("285000"), account_number="5678"),
        BankAccount(user_id=user.id, name="SBI FD", account_type="fd", balance=Decimal("500000"), interest_rate=Decimal("7.1"), account_number="9012")
    ]
    for acc in accounts:
        db.add(acc)
    await db.commit()
    
    # 4. Credit Cards
    cards = [
        CreditCard(user_id=user.id, name="HDFC Regalia", bank_name="HDFC", credit_limit=Decimal("500000"), outstanding_balance=Decimal("45820"), card_number="1234"),
        CreditCard(user_id=user.id, name="Axis Magnus", bank_name="Axis", credit_limit=Decimal("300000"), outstanding_balance=Decimal("12340"), card_number="5678")
    ]
    for card in cards:
        db.add(card)
    await db.commit()
    
    # 5. Transactions (Salary + random expenses)
    today = date.today()
    for i in range(6):
        month_offset = today.month - i
        year_offset = today.year
        while month_offset <= 0:
            month_offset += 12
            year_offset -= 1
        
        # Salary
        db.add(Transaction(user_id=user.id, amount=95000, type="income", date=date(year_offset, month_offset, 1), description="Monthly Salary", category_id=categories["Salary"]))
        db.add(Transaction(user_id=user.id, amount=25000, type="income", date=date(year_offset, month_offset, 15), description="Freelance Work", category_id=categories["Freelance Income"]))
        
        # Expenses
        db.add(Transaction(user_id=user.id, amount=25000, type="expense", date=date(year_offset, month_offset, 2), description="House Rent", category_id=categories["Housing & Rent"]))
        db.add(Transaction(user_id=user.id, amount=12000, type="expense", date=date(year_offset, month_offset, 5), description="Groceries", category_id=categories["Food & Dining"]))
        db.add(Transaction(user_id=user.id, amount=3000, type="expense", date=date(year_offset, month_offset, 10), description="Electricity Bill", category_id=categories["Utilities"]))
        db.add(Transaction(user_id=user.id, amount=8000, type="expense", date=date(year_offset, month_offset, 20), description="Shopping", category_id=categories["Shopping"]))
        
    await db.commit()

    # 6. Budgets
    budget = Budget(user_id=user.id, name="Current Month Budget", month=today.month, year=today.year, total_limit=70000)
    db.add(budget)
    await db.flush()
    
    budget_items = [
        BudgetItem(budget_id=budget.id, category_id=categories["Housing & Rent"], name="Rent", allocated_amount=25000),
        BudgetItem(budget_id=budget.id, category_id=categories["Food & Dining"], name="Food", allocated_amount=20000),
        BudgetItem(budget_id=budget.id, category_id=categories["Shopping"], name="Shopping", allocated_amount=10000),
        BudgetItem(budget_id=budget.id, category_id=categories["Transport"], name="Transport", allocated_amount=5000),
        BudgetItem(budget_id=budget.id, category_id=categories["Utilities"], name="Utilities", allocated_amount=5000),
    ]
    for item in budget_items:
        db.add(item)
    await db.commit()

    # 7. Goals
    goals = [
        Goal(user_id=user.id, name="Emergency Fund", category="savings", target_amount=500000, current_amount=385000, color="#2e7d32"),
        Goal(user_id=user.id, name="Europe Vacation", category="travel", target_amount=250000, current_amount=85000, color="#00897b"),
        Goal(user_id=user.id, name="Toyota Fortuner", category="vehicle", target_amount=3500000, current_amount=800000, color="#6f4627"),
        Goal(user_id=user.id, name="Home Down Payment", category="property", target_amount=2500000, current_amount=450000, color="#1565c0"),
        Goal(user_id=user.id, name="Child Education", category="education", target_amount=5000000, current_amount=320000, color="#ad1457")
    ]
    for goal in goals:
        db.add(goal)
    await db.commit()

    # 8. Bills
    bills = [
        Bill(user_id=user.id, name="House Rent", category="rent", amount=25000, due_day=1, frequency="monthly"),
        Bill(user_id=user.id, name="Netflix", category="subscriptions", amount=649, due_day=5, frequency="monthly"),
        Bill(user_id=user.id, name="Electricity", category="utilities", amount=3000, due_day=20, frequency="monthly")
    ]
    for bill in bills:
        if bill.due_day >= today.day:
            bill.next_due_date = date(today.year, today.month, bill.due_day)
        else:
            bill.next_due_date = date(today.year, today.month + 1 if today.month < 12 else 1, bill.due_day)
        db.add(bill)
    await db.commit()

    # 9. Investments
    investments = [
        Investment(user_id=user.id, name="Reliance Industries", type="stocks", symbol="RELIANCE", quantity=Decimal("50"), purchase_price=Decimal("2200"), current_price=Decimal("2650"), purchase_date=date(2023, 1, 15)),
        Investment(user_id=user.id, name="Infosys", type="stocks", symbol="INFY", quantity=Decimal("30"), purchase_price=Decimal("1400"), current_price=Decimal("1720"), purchase_date=date(2023, 3, 20)),
        Investment(user_id=user.id, name="Gold", type="gold", quantity=Decimal("10"), purchase_price=Decimal("52000"), current_price=Decimal("63000"), purchase_date=date(2023, 5, 10))
    ]
    for inv in investments:
        db.add(inv)
    await db.commit()

    # 10. Loans
    loans = [
        Loan(user_id=user.id, name="SBI Home Loan", lender="SBI", loan_type="home", principal_amount=Decimal("7500000"), outstanding_balance=Decimal("6800000"), interest_rate=Decimal("8.5"), tenure_months=240, paid_months=60, emi_amount=Decimal("65084"), start_date=date(2021, 1, 1), end_date=date(2041, 1, 1)),
        Loan(user_id=user.id, name="HDFC Car Loan", lender="HDFC", loan_type="vehicle", principal_amount=Decimal("800000"), outstanding_balance=Decimal("450000"), interest_rate=Decimal("9.5"), tenure_months=60, paid_months=24, emi_amount=Decimal("16762"), start_date=date(2022, 6, 1), end_date=date(2027, 6, 1))
    ]
    for loan in loans:
        db.add(loan)
    await db.commit()

    # 11. Assets
    assets = [
        Asset(user_id=user.id, name="2BHK Mumbai", asset_type="property", purchase_price=Decimal("8500000"), current_value=Decimal("10500000"), purchase_date=date(2018, 5, 10)),
        Asset(user_id=user.id, name="Innova Crysta", asset_type="vehicle", purchase_price=Decimal("2200000"), current_value=Decimal("1750000"), purchase_date=date(2022, 2, 15))
    ]
    for asset in assets:
        db.add(asset)
    await db.commit()

    # 12. Insurance
    insurance = [
        InsurancePolicy(user_id=user.id, policy_name="LIC Term Plan", provider="LIC", policy_type="life", coverage_amount=Decimal("10000000"), annual_premium=Decimal("18000"), premium_frequency="yearly", start_date=date(2020, 1, 1), renewal_date=date(2040, 1, 1)),
        InsurancePolicy(user_id=user.id, provider="Star Health", policy_name="Star Health Insurance", policy_type="health", coverage_amount=Decimal("2000000"), annual_premium=Decimal("28000"), premium_frequency="yearly", start_date=date(2023, 5, 1), renewal_date=date(2024, 5, 1))
    ]
    for ins in insurance:
        db.add(ins)
    await db.commit()
    
    print("Seed data created successfully!")

async def reset_demo_data():
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "demo@finora.app"))
        user = result.scalar_one_or_none()
        if not user:
            return
            
        # Delete data in correct order
        await db.execute(delete(Transaction).where(Transaction.user_id == user.id))
        await db.execute(delete(BudgetItem).where(BudgetItem.budget_id.in_(select(Budget.id).where(Budget.user_id == user.id))))
        await db.execute(delete(Budget).where(Budget.user_id == user.id))
        await db.execute(delete(GoalContribution).where(GoalContribution.goal_id.in_(select(Goal.id).where(Goal.user_id == user.id))))
        await db.execute(delete(Goal).where(Goal.user_id == user.id))
        await db.execute(delete(BillPayment).where(BillPayment.bill_id.in_(select(Bill.id).where(Bill.user_id == user.id))))
        await db.execute(delete(Bill).where(Bill.user_id == user.id))
        await db.execute(delete(Investment).where(Investment.user_id == user.id))
        await db.execute(delete(Loan).where(Loan.user_id == user.id))
        await db.execute(delete(Asset).where(Asset.user_id == user.id))
        await db.execute(delete(InsurancePolicy).where(InsurancePolicy.user_id == user.id))
        await db.execute(delete(CreditCard).where(CreditCard.user_id == user.id))
        await db.execute(delete(BankAccount).where(BankAccount.user_id == user.id))
        await db.execute(delete(Category).where(Category.user_id == user.id))
        await db.execute(delete(User).where(User.id == user.id))
        await db.commit()
        
        await seed_data(db)

if __name__ == "__main__":
    asyncio.run(main())
