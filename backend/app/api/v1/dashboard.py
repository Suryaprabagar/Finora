"""Dashboard aggregation endpoint - returns all KPIs in a single call."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import selectinload
from datetime import date, datetime
from decimal import Decimal
from app.core.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.bank_account import BankAccount
from app.models.credit_card import CreditCard
from app.models.investment import Investment
from app.models.loan import Loan
from app.models.asset import Asset
from app.models.bill import Bill
from app.models.goal import Goal
from app.models.budget import Budget, BudgetItem
from app.models.category import Category
from app.schemas.common import APIResponse
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all dashboard KPIs and summaries in a single API call."""
    today = date.today()
    current_month_start = today.replace(day=1)
    user_id = current_user.id

    # --- Cash Balance (sum of all active bank accounts) ---
    bank_result = await db.execute(
        select(func.coalesce(func.sum(BankAccount.balance), 0))
        .where(BankAccount.user_id == user_id, BankAccount.is_active.is_(True), BankAccount.deleted_at.is_(None))
    )
    cash_balance = float(bank_result.scalar() or 0)

    # --- Investment Value ---
    inv_result = await db.execute(
        select(func.coalesce(func.sum(Investment.current_price * Investment.quantity), 0))
        .where(Investment.user_id == user_id, Investment.is_active.is_(True), Investment.deleted_at.is_(None))
    )
    investment_value = float(inv_result.scalar() or 0)

    # --- Asset Value ---
    asset_result = await db.execute(
        select(func.coalesce(func.sum(Asset.current_value), 0))
        .where(Asset.user_id == user_id, Asset.deleted_at.is_(None))
    )
    asset_value = float(asset_result.scalar() or 0)

    # --- Loan Outstanding ---
    loan_result = await db.execute(
        select(func.coalesce(func.sum(Loan.outstanding_balance), 0))
        .where(Loan.user_id == user_id, Loan.is_active.is_(True), Loan.deleted_at.is_(None))
    )
    loan_total = float(loan_result.scalar() or 0)

    # --- Credit Card Outstanding ---
    cc_result = await db.execute(
        select(func.coalesce(func.sum(CreditCard.outstanding_balance), 0))
        .where(CreditCard.user_id == user_id, CreditCard.is_active.is_(True), CreditCard.deleted_at.is_(None))
    )
    cc_balance = float(cc_result.scalar() or 0)

    # --- Net Worth ---
    net_worth = cash_balance + investment_value + asset_value - loan_total - cc_balance

    # --- Monthly Income (current month) ---
    income_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "income",
            Transaction.date >= current_month_start,
            Transaction.date <= today,
            Transaction.deleted_at.is_(None),
        )
    )
    monthly_income = float(income_result.scalar() or 0)

    # --- Monthly Expenses (current month) ---
    expense_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.date >= current_month_start,
            Transaction.date <= today,
            Transaction.deleted_at.is_(None),
        )
    )
    monthly_expenses = float(expense_result.scalar() or 0)

    # --- Savings Rate ---
    savings_rate = 0.0
    if monthly_income > 0:
        savings_rate = round(((monthly_income - monthly_expenses) / monthly_income) * 100, 1)

    # --- Cash Flow (last 6 months) ---
    cash_flow = []
    for i in range(5, -1, -1):
        # Calculate month start/end
        month_offset = today.month - i
        year_offset = today.year
        while month_offset <= 0:
            month_offset += 12
            year_offset -= 1
        m_start = date(year_offset, month_offset, 1)
        if month_offset == 12:
            m_end = date(year_offset + 1, 1, 1)
        else:
            m_end = date(year_offset, month_offset + 1, 1)

        inc_r = await db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.user_id == user_id, Transaction.type == "income",
                   Transaction.date >= m_start, Transaction.date < m_end,
                   Transaction.deleted_at.is_(None))
        )
        exp_r = await db.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.user_id == user_id, Transaction.type == "expense",
                   Transaction.date >= m_start, Transaction.date < m_end,
                   Transaction.deleted_at.is_(None))
        )
        month_income = float(inc_r.scalar() or 0)
        month_expense = float(exp_r.scalar() or 0)
        cash_flow.append({
            "month": m_start.strftime("%b"),
            "income": month_income,
            "expenses": month_expense,
            "savings": month_income - month_expense,
        })

    # --- Asset Allocation (by investment type) ---
    alloc_result = await db.execute(
        select(Investment.type, func.sum(Investment.current_price * Investment.quantity).label("value"))
        .where(Investment.user_id == user_id, Investment.is_active.is_(True), Investment.deleted_at.is_(None))
        .group_by(Investment.type)
    )
    alloc_rows = alloc_result.all()
    total_inv = sum(float(r.value) for r in alloc_rows) or 1
    asset_allocation = [
        {
            "type": r.type.replace("_", " ").title(),
            "value": float(r.value),
            "percentage": round(float(r.value) / total_inv * 100, 1),
        }
        for r in alloc_rows
    ]

    # --- Recent Transactions (last 10) ---
    txn_result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category), selectinload(Transaction.bank_account))
        .where(Transaction.user_id == user_id, Transaction.deleted_at.is_(None))
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(10)
    )
    recent_txns = txn_result.scalars().all()
    recent_transactions = [
        {
            "id": str(t.id),
            "type": t.type,
            "amount": float(t.amount),
            "description": t.description,
            "merchant": t.merchant,
            "date": t.date.isoformat(),
            "status": t.status,
            "category": {"name": t.category.name, "color": t.category.color} if t.category else None,
            "bank_account": {"name": t.bank_account.name} if t.bank_account else None,
        }
        for t in recent_txns
    ]

    # --- Upcoming Bills (next 30 days) ---
    from datetime import timedelta
    next_30 = today + timedelta(days=30)
    bills_result = await db.execute(
        select(Bill)
        .where(
            Bill.user_id == user_id,
            Bill.status == "active",
            Bill.next_due_date.is_not(None),
            Bill.next_due_date <= next_30,
            Bill.deleted_at.is_(None),
        )
        .order_by(Bill.next_due_date)
        .limit(5)
    )
    upcoming_bills_db = bills_result.scalars().all()
    upcoming_bills = [
        {
            "id": str(b.id),
            "name": b.name,
            "category": b.category,
            "amount": float(b.amount),
            "next_due_date": b.next_due_date.isoformat() if b.next_due_date else None,
            "auto_pay": b.auto_pay,
        }
        for b in upcoming_bills_db
    ]

    # --- Budget Summary (current month) ---
    budget_result = await db.execute(
        select(Budget)
        .options(selectinload(Budget.items).selectinload(BudgetItem.category))
        .where(
            Budget.user_id == user_id,
            Budget.month == today.month,
            Budget.year == today.year,
            Budget.deleted_at.is_(None),
        )
        .limit(1)
    )
    budget = budget_result.scalar_one_or_none()
    budget_summary = None
    if budget:
        items_with_spent = []
        for item in budget.items:
            spent_r = await db.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0))
                .where(
                    Transaction.user_id == user_id,
                    Transaction.category_id == item.category_id if item.category_id else False,
                    Transaction.type == "expense",
                    Transaction.date >= current_month_start,
                    Transaction.deleted_at.is_(None),
                )
            )
            spent = float(spent_r.scalar() or 0)
            pct = round(spent / float(item.allocated_amount) * 100, 1) if float(item.allocated_amount) > 0 else 0
            items_with_spent.append({
                "id": str(item.id),
                "name": item.name,
                "allocated_amount": float(item.allocated_amount),
                "spent_amount": spent,
                "percentage_used": pct,
            })
        budget_summary = {
            "id": str(budget.id),
            "name": budget.name,
            "total_limit": float(budget.total_limit),
            "total_spent": sum(i["spent_amount"] for i in items_with_spent),
            "items": items_with_spent,
        }

    # --- Goals Summary (top 5 active) ---
    goals_result = await db.execute(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.status == "active", Goal.deleted_at.is_(None))
        .order_by(Goal.created_at.desc())
        .limit(5)
    )
    goals_db = goals_result.scalars().all()
    goals_summary = [
        {
            "id": str(g.id),
            "name": g.name,
            "category": g.category,
            "target_amount": float(g.target_amount),
            "current_amount": float(g.current_amount),
            "progress_percentage": round(float(g.current_amount) / float(g.target_amount) * 100, 1)
                if float(g.target_amount) > 0 else 0,
            "deadline": g.deadline.isoformat() if g.deadline else None,
            "color": g.color,
        }
        for g in goals_db
    ]

    return APIResponse(data={
        "net_worth": round(net_worth, 2),
        "cash_balance": round(cash_balance, 2),
        "monthly_income": round(monthly_income, 2),
        "monthly_expenses": round(monthly_expenses, 2),
        "savings_rate": savings_rate,
        "investment_value": round(investment_value, 2),
        "cash_flow": cash_flow,
        "asset_allocation": asset_allocation,
        "recent_transactions": recent_transactions,
        "upcoming_bills": upcoming_bills,
        "budget_summary": budget_summary,
        "goals_summary": goals_summary,
    })
