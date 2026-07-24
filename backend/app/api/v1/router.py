"""Main API v1 router - aggregates all sub-routers."""
from fastapi import APIRouter
from app.api.v1 import (
    auth,
    users,
    dashboard,
    transactions,
    income,
    expenses,
    budget,
    bank_accounts,
    credit_cards,
    investments,
    loans,
    assets,
    insurance,
    bills,
    reports,
    settings as settings_router,
    analytics,
)
from app.modules.goals import router as goals_router

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(income.router, prefix="/income", tags=["Income"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
api_router.include_router(budget.router, prefix="/budget", tags=["Budget"])
api_router.include_router(bank_accounts.router, prefix="/bank-accounts", tags=["Bank Accounts"])
api_router.include_router(credit_cards.router, prefix="/credit-cards", tags=["Credit Cards"])
api_router.include_router(investments.router, prefix="/investments", tags=["Investments"])
api_router.include_router(loans.router, prefix="/loans", tags=["Loans"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(insurance.router, prefix="/insurance", tags=["Insurance"])
api_router.include_router(bills.router, prefix="/bills", tags=["Bills"])
api_router.include_router(goals_router.router, prefix="/goals", tags=["Goals & Planning"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(settings_router.router, prefix="/settings", tags=["Settings"])
api_router.include_router(analytics.router, tags=["Analytics"])
