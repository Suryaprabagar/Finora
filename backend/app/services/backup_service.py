import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.user import User
from app.models.category import Category
from app.models.bank_account import BankAccount
from app.models.credit_card import CreditCard
from app.models.transaction import Transaction
from app.models.budget import Budget, BudgetItem
from app.models.goal import Goal, GoalContribution
from app.models.bill import Bill, BillPayment
from app.models.investment import Investment
from app.models.loan import Loan, LoanPayment
from app.models.asset import Asset
from app.models.insurance import InsurancePolicy, InsuranceClaim
from app.models.report import Report
from app.models.planning import AssetAllocation, ObjectiveHistory
from app.models.portfolio_snapshot import PortfolioSnapshot

# Models directly linked to user_id
ROOT_MODELS = [
    Category, BankAccount, CreditCard, Budget, Goal, Bill, Investment, Loan, Asset, 
    InsurancePolicy, Report, AssetAllocation, ObjectiveHistory, PortfolioSnapshot, Transaction
]

# Models linked via parent
CHILD_MODELS = [
    (BudgetItem, Budget, BudgetItem.budget_id == Budget.id),
    (GoalContribution, Goal, GoalContribution.goal_id == Goal.id),
    (BillPayment, Bill, BillPayment.bill_id == Bill.id),
    (LoanPayment, Loan, LoanPayment.loan_id == Loan.id),
    (InsuranceClaim, InsurancePolicy, InsuranceClaim.policy_id == InsurancePolicy.id),
]

def serialize_value(val):
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, Decimal):
        return float(val)
    return val

async def export_user_data(db: AsyncSession, user_id: uuid.UUID) -> dict:
    data = {}
    
    # 1. Export User data (exclude sensitive stuff like hashed_password, if desired, but we might need settings)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user_dict = {}
        for c in User.__table__.columns:
            if c.name not in ["hashed_password"]:
                user_dict[c.name] = serialize_value(getattr(user, c.name))
        data["User"] = [user_dict]

    # 2. Export Root Models
    for model in ROOT_MODELS:
        result = await db.execute(select(model).where(model.user_id == user_id))
        items = result.scalars().all()
        data[model.__name__] = []
        for item in items:
            row = {}
            for c in model.__table__.columns:
                row[c.name] = serialize_value(getattr(item, c.name))
            data[model.__name__].append(row)

    # 3. Export Child Models
    for child_model, parent_model, join_cond in CHILD_MODELS:
        result = await db.execute(select(child_model).join(parent_model, join_cond).where(parent_model.user_id == user_id))
        items = result.scalars().all()
        data[child_model.__name__] = []
        for item in items:
            row = {}
            for c in child_model.__table__.columns:
                row[c.name] = serialize_value(getattr(item, c.name))
            data[child_model.__name__].append(row)
            
    return data

async def restore_user_data(db: AsyncSession, user_id: uuid.UUID, backup_data: dict):
    # This function expects to be run in a transaction and db.commit() to be called after
    
    # 1. Delete existing data for the user to avoid conflicts
    # Order matters due to foreign keys. Delete children first.
    for child_model, parent_model, join_cond in CHILD_MODELS:
        await db.execute(delete(child_model).where(
            child_model.id.in_(
                select(child_model.id).join(parent_model, join_cond).where(parent_model.user_id == user_id)
            )
        ))
        
    for model in reversed(ROOT_MODELS): # reverse to delete transactions before accounts if necessary
        await db.execute(delete(model).where(model.user_id == user_id))
        
    await db.flush() # ensure deletions happen before inserts
    
    # Helper to parse values
    def parse_value(col, val):
        if val is None:
            return None
        py_type = col.type.python_type
        if py_type == datetime:
            try:
                return datetime.fromisoformat(val)
            except ValueError:
                # Handle cases where 'Z' is used instead of '+00:00'
                return datetime.fromisoformat(val.replace('Z', '+00:00'))
        if py_type == date:
            return date.fromisoformat(val)
        if py_type == uuid.UUID:
            return uuid.UUID(val)
        if py_type == Decimal:
            return Decimal(str(val))
        return val

    # 2. Insert new data
    # Insert User settings (update instead of insert, since user already exists)
    if "User" in backup_data and len(backup_data["User"]) > 0:
        user_backup = backup_data["User"][0]
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            for c in User.__table__.columns:
                if c.name in user_backup and c.name not in ["id", "email", "hashed_password"]:
                    setattr(user, c.name, parse_value(c, user_backup[c.name]))

    # Insert root models
    for model in ROOT_MODELS:
        model_name = model.__name__
        if model_name in backup_data:
            for row in backup_data[model_name]:
                # Construct object
                kwargs = {}
                for c in model.__table__.columns:
                    if c.name in row:
                        kwargs[c.name] = parse_value(c, row[c.name])
                item = model(**kwargs)
                db.add(item)
                
    await db.flush()

    # Insert child models
    for child_model, _, _ in CHILD_MODELS:
        model_name = child_model.__name__
        if model_name in backup_data:
            for row in backup_data[model_name]:
                kwargs = {}
                for c in child_model.__table__.columns:
                    if c.name in row:
                        kwargs[c.name] = parse_value(c, row[c.name])
                item = child_model(**kwargs)
                db.add(item)

    # Committing is done by the caller
