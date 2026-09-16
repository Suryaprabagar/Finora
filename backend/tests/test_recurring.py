"""test_recurring.py — Comprehensive tests for the recurring expense feature in Finora."""
import uuid
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base
from app.models.user import User
from app.models.category import Category
from app.models.bank_account import BankAccount
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.recurring_service import (
    advance_due_date,
    process_due_recurring_expenses,
    calculate_recurring_monthly_commitment,
)


@pytest_asyncio.fixture
async def test_session():
    """In-memory SQLite database session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def user_and_account(test_session: AsyncSession):
    """Seed a test user and a funded bank account."""
    user = User(
        id=uuid.uuid4(),
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="hashed_pw",
        full_name="Test User",
    )
    test_session.add(user)
    await test_session.flush()

    account = BankAccount(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Checking Account",
        account_type="checking",
        balance=Decimal("1000.00"),
    )
    test_session.add(account)

    category = Category(
        id=uuid.uuid4(),
        user_id=user.id,
        name="Subscriptions",
        type="expense",
    )
    test_session.add(category)
    await test_session.commit()

    return user, account, category


# ── Calendar Advancement & Edge Cases ─────────────────────────────────────────

def test_calendar_advancement_weekly():
    d = date(2026, 9, 16)
    next_d = advance_due_date(d, "weekly")
    assert next_d == date(2026, 9, 23)


def test_calendar_advancement_monthly_jan31():
    jan31 = date(2025, 1, 31)
    feb = advance_due_date(jan31, "monthly", anchor_day=31)
    assert feb == date(2025, 2, 28)
    mar = advance_due_date(feb, "monthly", anchor_day=31)
    assert mar == date(2025, 3, 31)
    apr = advance_due_date(mar, "monthly", anchor_day=31)
    assert apr == date(2025, 4, 30)


def test_calendar_advancement_yearly_leap():
    leap_date = date(2024, 2, 29)
    y1 = advance_due_date(leap_date, "yearly", anchor_day=29)
    assert y1 == date(2025, 2, 28)
    y2 = advance_due_date(y1, "yearly", anchor_day=29)
    assert y2 == date(2026, 2, 28)
    y4 = advance_due_date(advance_due_date(y2, "yearly", 29), "yearly", 29)
    assert y4 == date(2028, 2, 29)


# ── Schema Validation ─────────────────────────────────────────────────────────

def test_schema_validation():
    # 1. Valid recurring
    tc = TransactionCreate(
        type="expense",
        amount=Decimal("25.00"),
        description="Netflix",
        date=date.today(),
        is_recurring=True,
        recurrence_frequency="monthly",
        next_due_date=date.today() + timedelta(days=5),
    )
    assert tc.is_recurring is True
    assert tc.recurrence_frequency == "monthly"

    # 2. Missing frequency when is_recurring=True raises
    with pytest.raises(Exception):
        TransactionCreate(
            type="expense",
            amount=Decimal("25.00"),
            description="Netflix",
            date=date.today(),
            is_recurring=True,
            next_due_date=date.today(),
        )

    # 3. Missing next_due_date when is_recurring=True raises
    with pytest.raises(Exception):
        TransactionCreate(
            type="expense",
            amount=Decimal("25.00"),
            description="Netflix",
            date=date.today(),
            is_recurring=True,
            recurrence_frequency="monthly",
        )

    # 4. Invalid frequency raises
    with pytest.raises(Exception):
        TransactionCreate(
            type="expense",
            amount=Decimal("25.00"),
            description="Netflix",
            date=date.today(),
            is_recurring=True,
            recurrence_frequency="biweekly",
            next_due_date=date.today(),
        )

    # 5. recurrence_end_date before next_due_date raises
    with pytest.raises(Exception):
        TransactionCreate(
            type="expense",
            amount=Decimal("25.00"),
            description="Netflix",
            date=date.today(),
            is_recurring=True,
            recurrence_frequency="monthly",
            next_due_date=date.today() + timedelta(days=10),
            recurrence_end_date=date.today() + timedelta(days=5),
        )


# ── Creation & Future Schedule (No Fake History / No Premature Balance Deduction) ──

@pytest.mark.asyncio
async def test_create_future_recurring_expense(test_session: AsyncSession, user_and_account):
    user, account, category = user_and_account

    # Schedule due in 10 days
    schedule = Transaction(
        user_id=user.id,
        category_id=category.id,
        bank_account_id=account.id,
        type="expense",
        amount=Decimal("49.99"),
        description="Gym Membership",
        merchant="Gym",
        date=date.today(),
        is_recurring=True,
        recurrence_frequency="monthly",
        recurring_interval="monthly",
        next_due_date=date.today() + timedelta(days=10),
    )
    test_session.add(schedule)
    await test_session.commit()

    # Process due recurring expenses
    processed = await process_due_recurring_expenses(test_session, user_id=user.id)
    assert len(processed) == 0

    # Bank balance must NOT be deducted prematurely
    await test_session.refresh(account)
    assert account.balance == Decimal("1000.00")

    # Schedule next_due_date unchanged
    await test_session.refresh(schedule)
    assert schedule.next_due_date == date.today() + timedelta(days=10)


# ── Idempotent Processing, Bank Balance Updates & Occurrence Generation ───────

@pytest.mark.asyncio
async def test_due_recurring_expense_generation_and_balance_update(test_session: AsyncSession, user_and_account):
    user, account, category = user_and_account
    today = date.today()

    # Schedule due today
    schedule = Transaction(
        user_id=user.id,
        category_id=category.id,
        bank_account_id=account.id,
        type="expense",
        amount=Decimal("100.00"),
        description="Internet Bill",
        merchant="ISP",
        date=today,
        is_recurring=True,
        recurrence_frequency="monthly",
        recurring_interval="monthly",
        next_due_date=today,
    )
    test_session.add(schedule)
    await test_session.commit()

    # Process due recurring
    processed = await process_due_recurring_expenses(test_session, user_id=user.id, as_of_date=today)
    assert len(processed) == 1

    gen_tx = processed[0]
    assert gen_tx.recurring_parent_id == schedule.id
    assert gen_tx.is_recurring is False
    assert gen_tx.amount == Decimal("100.00")
    assert gen_tx.date == today

    # Verify bank balance deducted
    await test_session.refresh(account)
    assert account.balance == Decimal("900.00")

    # Verify schedule advanced next_due_date
    await test_session.refresh(schedule)
    expected_next = advance_due_date(today, "monthly", today.day)
    assert schedule.next_due_date == expected_next

    # Idempotency test: Run process again on the same day -> ZERO new transactions!
    processed_again = await process_due_recurring_expenses(test_session, user_id=user.id, as_of_date=today)
    assert len(processed_again) == 0

    # Balance must remain unchanged
    await test_session.refresh(account)
    assert account.balance == Decimal("900.00")


# ── Multiple Missed Occurrences Handling ─────────────────────────────────────

@pytest.mark.asyncio
async def test_multiple_missed_occurrences_handled_safely(test_session: AsyncSession, user_and_account):
    user, account, category = user_and_account
    today = date(2026, 9, 16)
    three_weeks_ago = today - timedelta(days=21)

    # Weekly schedule from 3 weeks ago
    schedule = Transaction(
        user_id=user.id,
        bank_account_id=account.id,
        type="expense",
        amount=Decimal("20.00"),
        description="Weekly Cleaning",
        date=three_weeks_ago,
        is_recurring=True,
        recurrence_frequency="weekly",
        recurring_interval="weekly",
        next_due_date=three_weeks_ago,
    )
    test_session.add(schedule)
    await test_session.commit()

    processed = await process_due_recurring_expenses(test_session, user_id=user.id, as_of_date=today)
    # Occurrences on: 3 weeks ago, 2 weeks ago, 1 week ago, today = 4 occurrences!
    assert len(processed) == 4

    # 4 * 20 = 80 deducted
    await test_session.refresh(account)
    assert account.balance == Decimal("920.00")

    # Schedule should now be due 1 week from today
    await test_session.refresh(schedule)
    assert schedule.next_due_date == today + timedelta(days=7)


# ── Recurrence End Date Behavior ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recurrence_end_date_terminates(test_session: AsyncSession, user_and_account):
    user, account, _ = user_and_account
    today = date(2026, 9, 16)

    # Ends on today
    schedule = Transaction(
        user_id=user.id,
        bank_account_id=account.id,
        type="expense",
        amount=Decimal("30.00"),
        description="Limited Subscription",
        date=today - timedelta(days=7),
        is_recurring=True,
        recurrence_frequency="weekly",
        recurring_interval="weekly",
        next_due_date=today - timedelta(days=7),
        recurrence_end_date=today,
    )
    test_session.add(schedule)
    await test_session.commit()

    # Process: should generate for (today-7) and (today)
    processed = await process_due_recurring_expenses(test_session, user_id=user.id, as_of_date=today)
    assert len(processed) == 2

    await test_session.refresh(schedule)
    # Once end date is passed, is_recurring is set to False
    assert schedule.is_recurring is False


# ── Update Recurrence & Disable Recurrence ────────────────────────────────────

@pytest.mark.asyncio
async def test_disable_recurrence(test_session: AsyncSession, user_and_account):
    user, account, _ = user_and_account

    schedule = Transaction(
        user_id=user.id,
        bank_account_id=account.id,
        type="expense",
        amount=Decimal("15.00"),
        description="Music Streaming",
        date=date.today(),
        is_recurring=True,
        recurrence_frequency="monthly",
        recurring_interval="monthly",
        next_due_date=date.today() + timedelta(days=15),
    )
    test_session.add(schedule)
    await test_session.commit()

    # Disable recurrence
    schedule.is_recurring = False
    await test_session.commit()

    await test_session.refresh(schedule)
    assert schedule.is_recurring is False

    # When processor runs, disabled recurrence is skipped
    processed = await process_due_recurring_expenses(test_session, user_id=user.id, as_of_date=date.today() + timedelta(days=30))
    assert len(processed) == 0


# ── Summary Calculations & Edge Cases (No Merchant / No Category) ─────────────

@pytest.mark.asyncio
async def test_recurring_summary_calculations(test_session: AsyncSession, user_and_account):
    user, _, _ = user_and_account

    # 1 monthly of $50, 1 weekly of $10, 1 yearly of $120
    # No merchant, no category
    s1 = Transaction(
        user_id=user.id,
        type="expense",
        amount=Decimal("50.00"),
        description="No merchant monthly",
        merchant=None,
        category_id=None,
        date=date.today(),
        is_recurring=True,
        recurrence_frequency="monthly",
        next_due_date=date.today() + timedelta(days=5),
    )
    s2 = Transaction(
        user_id=user.id,
        type="expense",
        amount=Decimal("10.00"),
        description="Weekly sub",
        merchant="Coffee Club",
        date=date.today(),
        is_recurring=True,
        recurrence_frequency="weekly",
        next_due_date=date.today() + timedelta(days=3),
    )
    s3 = Transaction(
        user_id=user.id,
        type="expense",
        amount=Decimal("120.00"),
        description="Annual license",
        merchant="Software Corp",
        date=date.today(),
        is_recurring=True,
        recurrence_frequency="yearly",
        next_due_date=date.today() + timedelta(days=20),
    )
    test_session.add_all([s1, s2, s3])
    await test_session.commit()

    schedules = [s1, s2, s3]
    # Monthly commitment: 50 + (10 * 4) + (120 / 12) = 50 + 40 + 10 = 100
    monthly_total = calculate_recurring_monthly_commitment(schedules)
    assert monthly_total == 100.0


# ── Deleted Records Excluded ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deleted_recurring_records_excluded(test_session: AsyncSession, user_and_account):
    user, _, _ = user_and_account

    schedule = Transaction(
        user_id=user.id,
        type="expense",
        amount=Decimal("100.00"),
        description="Cancelled membership",
        date=date.today(),
        is_recurring=True,
        recurrence_frequency="monthly",
        next_due_date=date.today(),
        deleted_at=datetime.now(),
    )
    test_session.add(schedule)
    await test_session.commit()

    processed = await process_due_recurring_expenses(test_session, user_id=user.id)
    assert len(processed) == 0


# ── Endpoint Level Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_expense_endpoints_end_to_end(test_session: AsyncSession, user_and_account):
    user, account, category = user_and_account
    from app.api.v1.expenses import (
        create_expense,
        get_expenses,
        get_expenses_summary,
        get_upcoming_recurring_expenses,
        get_recurring_expenses,
        update_expense,
        delete_expense,
    )

    # 1. Create recurring expense (due in 5 days)
    create_data = TransactionCreate(
        type="expense",
        amount=Decimal("50.00"),
        description="Spotify Family",
        merchant="Spotify",
        date=date.today(),
        category_id=category.id,
        bank_account_id=account.id,
        is_recurring=True,
        recurrence_frequency="monthly",
        next_due_date=date.today() + timedelta(days=5),
    )
    res = await create_expense(create_data, db=test_session, current_user=user)
    assert res.data["is_recurring"] is True
    assert res.data["recurrence_frequency"] == "monthly"
    sched_id = uuid.UUID(str(res.data["id"]))

    # Ledger must NOT show the recurring schedule template as a posted transaction!
    ledger_res = await get_expenses(db=test_session, current_user=user)
    assert len(ledger_res.data) == 0  # No double counting!

    # Upcoming recurring endpoint MUST return the schedule
    upcoming_res = await get_upcoming_recurring_expenses(db=test_session, current_user=user)
    assert len(upcoming_res.data) == 1
    item = upcoming_res.data[0]
    assert item["merchant"] == "Spotify"
    assert item["amount"] == 50.0
    assert item["frequency"] == "monthly"
    assert item["days_until_due"] == 5

    # Summary endpoint MUST show real recurring count and recurring total
    summary_res = await get_expenses_summary(db=test_session, current_user=user)
    assert summary_res.data["recurring_count"] == 1
    assert summary_res.data["recurring_total"] == 50.0
    assert summary_res.data["monthly_total"] == 0.0  # Template is not counted in monthly spend!

    # Recurring endpoint MUST return all templates
    recurring_res = await get_recurring_expenses(db=test_session, current_user=user)
    assert len(recurring_res.data) == 1

    # 2. Update the recurring schedule (change amount and frequency)
    update_data = TransactionUpdate(
        amount=Decimal("60.00"),
        recurrence_frequency="weekly",
        next_due_date=date.today() + timedelta(days=2),
    )
    upd_res = await update_expense(sched_id, update_data, db=test_session, current_user=user)
    assert upd_res.data["amount"] == Decimal("60.00")
    assert upd_res.data["recurrence_frequency"] == "weekly"

    # Summary now reflects weekly: 60 * 4 = 240
    summary_res2 = await get_expenses_summary(db=test_session, current_user=user)
    assert summary_res2.data["recurring_count"] == 1
    assert summary_res2.data["recurring_total"] == 240.0

    # 3. Create a one-time expense to verify normal flow is completely intact
    one_time_data = TransactionCreate(
        type="expense",
        amount=Decimal("15.00"),
        description="Lunch at Chipotle",
        merchant="Chipotle",
        date=date.today(),
        category_id=category.id,
        bank_account_id=account.id,
        is_recurring=False,
    )
    ot_res = await create_expense(one_time_data, db=test_session, current_user=user)
    assert ot_res.data["is_recurring"] is False

    # Ledger now has exactly the one-time expense
    ledger_res2 = await get_expenses(db=test_session, current_user=user)
    assert len(ledger_res2.data) == 1
    assert ledger_res2.data[0]["description"] == "Lunch at Chipotle"

    # Monthly total now has 15.0
    summary_res3 = await get_expenses_summary(db=test_session, current_user=user)
    assert summary_res3.data["monthly_total"] == 15.0

    # 4. Delete the recurring schedule
    del_res = await delete_expense(sched_id, db=test_session, current_user=user)
    assert del_res.message == "Expense deleted"

    # Upcoming recurring is now empty
    upcoming_res2 = await get_upcoming_recurring_expenses(db=test_session, current_user=user)
    assert len(upcoming_res2.data) == 0

    # Summary recurring count is now 0
    summary_res4 = await get_expenses_summary(db=test_session, current_user=user)
    assert summary_res4.data["recurring_count"] == 0
    assert summary_res4.data["recurring_total"] == 0.0

