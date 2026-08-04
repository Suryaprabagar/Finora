"""Enable RLS on all public tables and add security policies

Revision ID: a1b2c3d4e5f6
Revises: cb79c60ade77
Create Date: 2026-08-04 09:00:00.000000

This migration addresses the Supabase security linter findings:
  - rls_disabled_in_public: 22 tables without Row Level Security
  - sensitive_columns_exposed: bank_accounts.account_number, credit_cards.card_number

Strategy:
  - Tables with a direct user_id column: policy allows rows WHERE user_id = auth.uid()
  - Child tables (no user_id): policy traverses to parent via EXISTS subquery
  - alembic_version: system table — RLS enabled, all direct API access blocked
  - All policies are PERMISSIVE and cover SELECT, INSERT, UPDATE, DELETE separately
    so that the JWT-authenticated Supabase client only ever sees its own data.

NOTE: These policies use auth.uid() which is the Supabase Auth function.
      If you are using a custom auth scheme, replace auth.uid() with the
      appropriate expression that returns the authenticated user's UUID.
"""
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cb79c60ade77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Tables that have a direct user_id column (owner-scoped)
# ---------------------------------------------------------------------------
OWNER_TABLES = [
    "users",
    "asset_allocations",
    "assets",
    "bank_accounts",
    "budgets",
    "categories",
    "credit_cards",
    "goals",
    "insurance_policies",
    "investments",
    "objective_history",
    "reports",
    "bills",
    "loans",
    "transactions",
    "portfolio_snapshots",
]

# ---------------------------------------------------------------------------
# Child tables — no direct user_id; access is gated via parent FK
# ---------------------------------------------------------------------------
# Each entry: (child_table, child_fk_col, parent_table, parent_pk_col)
CHILD_TABLES = [
    # budget_items -> budgets -> user_id
    ("budget_items",       "budget_id",  "budgets",            "id"),
    # goal_contributions -> goals -> user_id
    ("goal_contributions", "goal_id",    "goals",              "id"),
    # insurance_claims -> insurance_policies -> user_id
    ("insurance_claims",   "policy_id",  "insurance_policies", "id"),
    # bill_payments -> bills -> user_id
    ("bill_payments",      "bill_id",    "bills",              "id"),
    # loan_payments -> loans -> user_id
    ("loan_payments",      "loan_id",    "loans",              "id"),
]


def upgrade() -> None:
    conn = op.get_bind()

    # -----------------------------------------------------------------------
    # 1. alembic_version — system / migration table.
    #    Enable RLS and deny all direct PostgREST access.
    # -----------------------------------------------------------------------
    conn.execute(op.inline_literal(
        "ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;"
    ))
    # No SELECT/INSERT/UPDATE/DELETE policies => zero rows visible via API.
    # (Alembic connects as the postgres superuser which bypasses RLS.)

    # -----------------------------------------------------------------------
    # 2. Owner-scoped tables: user sees only their own rows
    # -----------------------------------------------------------------------
    for table in OWNER_TABLES:
        # Special-case users table: a user can only see/modify their own row.
        # (Superuser/service-role bypasses RLS for admin operations.)
        uid_expr = (
            "id = auth.uid()"
            if table == "users"
            else "user_id = auth.uid()"
        )

        conn.execute(op.inline_literal(
            f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;"
        ))
        conn.execute(op.inline_literal(
            f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY;"
        ))

        # SELECT
        conn.execute(op.inline_literal(f"""
            CREATE POLICY "{table}_select_own"
            ON public.{table}
            FOR SELECT
            USING ({uid_expr});
        """))

        # INSERT — WITH CHECK ensures the inserted row claims correct owner
        insert_check = (
            "id = auth.uid()"
            if table == "users"
            else "user_id = auth.uid()"
        )
        conn.execute(op.inline_literal(f"""
            CREATE POLICY "{table}_insert_own"
            ON public.{table}
            FOR INSERT
            WITH CHECK ({insert_check});
        """))

        # UPDATE
        conn.execute(op.inline_literal(f"""
            CREATE POLICY "{table}_update_own"
            ON public.{table}
            FOR UPDATE
            USING ({uid_expr})
            WITH CHECK ({insert_check});
        """))

        # DELETE
        conn.execute(op.inline_literal(f"""
            CREATE POLICY "{table}_delete_own"
            ON public.{table}
            FOR DELETE
            USING ({uid_expr});
        """))

    # -----------------------------------------------------------------------
    # 3. Child tables: access is allowed when the parent row belongs to the
    #    authenticated user.
    # -----------------------------------------------------------------------
    for child_table, child_fk, parent_table, parent_pk in CHILD_TABLES:
        conn.execute(op.inline_literal(
            f"ALTER TABLE public.{child_table} ENABLE ROW LEVEL SECURITY;"
        ))
        conn.execute(op.inline_literal(
            f"ALTER TABLE public.{child_table} FORCE ROW LEVEL SECURITY;"
        ))

        exists_clause = (
            f"EXISTS ("
            f"  SELECT 1 FROM public.{parent_table} p "
            f"  WHERE p.{parent_pk} = {child_table}.{child_fk} "
            f"  AND p.user_id = auth.uid()"
            f")"
        )

        # SELECT
        conn.execute(op.inline_literal(f"""
            CREATE POLICY "{child_table}_select_own"
            ON public.{child_table}
            FOR SELECT
            USING ({exists_clause});
        """))

        # INSERT
        conn.execute(op.inline_literal(f"""
            CREATE POLICY "{child_table}_insert_own"
            ON public.{child_table}
            FOR INSERT
            WITH CHECK ({exists_clause});
        """))

        # UPDATE
        conn.execute(op.inline_literal(f"""
            CREATE POLICY "{child_table}_update_own"
            ON public.{child_table}
            FOR UPDATE
            USING ({exists_clause})
            WITH CHECK ({exists_clause});
        """))

        # DELETE
        conn.execute(op.inline_literal(f"""
            CREATE POLICY "{child_table}_delete_own"
            ON public.{child_table}
            FOR DELETE
            USING ({exists_clause});
        """))


def downgrade() -> None:
    conn = op.get_bind()

    # Drop all policies and disable RLS (reverse order)
    for child_table, _, _, _ in reversed(CHILD_TABLES):
        for op_name in ("select_own", "insert_own", "update_own", "delete_own"):
            conn.execute(op.inline_literal(
                f'DROP POLICY IF EXISTS "{child_table}_{op_name}" ON public.{child_table};'
            ))
        conn.execute(op.inline_literal(
            f"ALTER TABLE public.{child_table} DISABLE ROW LEVEL SECURITY;"
        ))

    for table in reversed(OWNER_TABLES):
        for op_name in ("select_own", "insert_own", "update_own", "delete_own"):
            conn.execute(op.inline_literal(
                f'DROP POLICY IF EXISTS "{table}_{op_name}" ON public.{table};'
            ))
        conn.execute(op.inline_literal(
            f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY;"
        ))

    conn.execute(op.inline_literal(
        "ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY;"
    ))
