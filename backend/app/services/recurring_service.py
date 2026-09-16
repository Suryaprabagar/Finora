"""recurring_service.py — Production-ready recurring expense engine."""
from __future__ import annotations

import calendar
import logging
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.bank_account import BankAccount
from app.models.credit_card import CreditCard

logger = logging.getLogger(__name__)


def advance_due_date(current_date: date, frequency: str, anchor_day: Optional[int] = None) -> date:
    """
    Calculate the next recurrence date using calendar-aware advancement.

    Handles edge cases:
    - Weekly: exact 7-day advance.
    - Monthly: preserves anchor day-of-month (e.g. Jan 31 -> Feb 28/29 -> Mar 31).
    - Yearly: preserves anchor day-of-month (e.g. Feb 29 on leap years -> Feb 28 on non-leap years).
    """
    clean_freq = frequency.lower()
    target_day = anchor_day if anchor_day is not None else current_date.day

    if clean_freq == "weekly":
        return current_date + timedelta(days=7)

    elif clean_freq == "monthly":
        year = current_date.year + (current_date.month // 12)
        month = (current_date.month % 12) + 1
        max_days = calendar.monthrange(year, month)[1]
        day = min(target_day, max_days)
        return date(year, month, day)

    elif clean_freq == "yearly":
        year = current_date.year + 1
        month = current_date.month
        max_days = calendar.monthrange(year, month)[1]
        day = min(target_day, max_days)
        return date(year, month, day)

    else:
        # Default fallback to monthly
        year = current_date.year + (current_date.month // 12)
        month = (current_date.month % 12) + 1
        max_days = calendar.monthrange(year, month)[1]
        day = min(target_day, max_days)
        return date(year, month, day)


def calculate_recurring_monthly_commitment(schedules: List[Transaction]) -> float:
    """
    Calculate the total scheduled monthly commitment for a list of active recurring schedules.
    - monthly: 1x amount
    - weekly: 4x amount
    - yearly: amount / 12
    """
    total = Decimal("0.00")
    for s in schedules:
        freq = (s.recurrence_frequency or s.recurring_interval or "monthly").lower()
        amt = Decimal(str(s.amount))
        if freq == "weekly":
            total += amt * 4
        elif freq == "yearly":
            total += round(amt / 12, 2)
        else:  # monthly
            total += amt
    return float(total)


async def process_due_recurring_expenses(
    db: AsyncSession,
    user_id: Optional[uuid.UUID] = None,
    as_of_date: Optional[date] = None,
) -> List[Transaction]:
    """
    Find and process all recurring expenses whose next_due_date <= today.
    Idempotent: prevents duplicate transactions for the same (parent_id, date) occurrence.
    Updates bank account or credit card balances safely.
    Handles missed occurrences up to today.
    """
    today = as_of_date or date.today()

    query = select(Transaction).where(
        Transaction.type == "expense",
        Transaction.is_recurring.is_(True),
        Transaction.recurring_parent_id.is_(None),
        Transaction.deleted_at.is_(None),
        Transaction.next_due_date.isnot(None),
        Transaction.next_due_date <= today,
    )

    if user_id:
        query = query.where(Transaction.user_id == user_id)

    result = await db.execute(query)
    due_schedules = result.scalars().all()

    generated_transactions: List[Transaction] = []

    for sched in due_schedules:
        anchor_day = sched.next_due_date.day if sched.next_due_date else sched.date.day
        freq = (sched.recurrence_frequency or sched.recurring_interval or "monthly").lower()
        current_due = sched.next_due_date

        while current_due and current_due <= today:
            # Respect recurrence_end_date
            if sched.recurrence_end_date and current_due > sched.recurrence_end_date:
                sched.is_recurring = False
                break

            # Check if this occurrence was already generated
            existing_tx = await db.execute(
                select(Transaction.id).where(
                    Transaction.recurring_parent_id == sched.id,
                    Transaction.date == current_due,
                    Transaction.deleted_at.is_(None),
                )
            )
            if not existing_tx.scalar_one_or_none():
                # Generate child transaction
                child_tx = Transaction(
                    user_id=sched.user_id,
                    category_id=sched.category_id,
                    bank_account_id=sched.bank_account_id,
                    credit_card_id=sched.credit_card_id,
                    type="expense",
                    amount=sched.amount,
                    description=sched.description,
                    merchant=sched.merchant,
                    date=current_due,
                    status=sched.status or "cleared",
                    payment_method=sched.payment_method,
                    reference_number=sched.reference_number,
                    notes=sched.notes,
                    is_recurring=False,
                    recurring_parent_id=sched.id,
                )
                db.add(child_tx)

                # Update bank account or credit card balance
                if sched.bank_account_id:
                    bank_acc = await db.get(BankAccount, sched.bank_account_id)
                    if bank_acc and bank_acc.user_id == sched.user_id:
                        bank_acc.balance -= sched.amount
                elif sched.credit_card_id:
                    cc = await db.get(CreditCard, sched.credit_card_id)
                    if cc and cc.user_id == sched.user_id:
                        cc.outstanding_balance += sched.amount

                generated_transactions.append(child_tx)

            # Advance current_due
            next_date = advance_due_date(current_due, freq, anchor_day)
            if next_date <= current_due:
                break
            current_due = next_date

        # Update schedule next_due_date
        sched.next_due_date = current_due
        if sched.recurrence_end_date and current_due and current_due > sched.recurrence_end_date:
            sched.is_recurring = False

    if generated_transactions or due_schedules:
        await db.commit()

    return generated_transactions
