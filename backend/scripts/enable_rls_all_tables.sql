-- =============================================================================
-- Finora: Enable Row Level Security on all public tables
-- =============================================================================
-- Run this in the Supabase SQL Editor (or via psql as a superuser).
--
-- Security findings addressed:
--   [ERROR] rls_disabled_in_public  - 22 tables
--   [ERROR] sensitive_columns_exposed - bank_accounts, credit_cards
--
-- Policy model:
--   - Owner tables (have user_id): user sees only rows WHERE user_id = auth.uid()
--   - Child tables (linked via FK): access allowed via EXISTS on parent's user_id
--   - alembic_version: RLS enabled, zero policies => completely blocked from API
--   - FORCE ROW LEVEL SECURITY ensures even table OWNER role is restricted
-- =============================================================================


-- ---------------------------------------------------------------------------
-- SECTION 1: alembic_version (system table — block all API access)
-- ---------------------------------------------------------------------------
ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;
-- No policies created intentionally: zero rows visible to PostgREST/API clients.


-- ---------------------------------------------------------------------------
-- SECTION 2: users
-- ---------------------------------------------------------------------------
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users FORCE ROW LEVEL SECURITY;

CREATE POLICY "users_select_own"
  ON public.users FOR SELECT
  USING (id = auth.uid());

CREATE POLICY "users_insert_own"
  ON public.users FOR INSERT
  WITH CHECK (id = auth.uid());

CREATE POLICY "users_update_own"
  ON public.users FOR UPDATE
  USING (id = auth.uid())
  WITH CHECK (id = auth.uid());

CREATE POLICY "users_delete_own"
  ON public.users FOR DELETE
  USING (id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 3: asset_allocations
-- ---------------------------------------------------------------------------
ALTER TABLE public.asset_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asset_allocations FORCE ROW LEVEL SECURITY;

CREATE POLICY "asset_allocations_select_own"
  ON public.asset_allocations FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "asset_allocations_insert_own"
  ON public.asset_allocations FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "asset_allocations_update_own"
  ON public.asset_allocations FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "asset_allocations_delete_own"
  ON public.asset_allocations FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 4: assets
-- ---------------------------------------------------------------------------
ALTER TABLE public.assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assets FORCE ROW LEVEL SECURITY;

CREATE POLICY "assets_select_own"
  ON public.assets FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "assets_insert_own"
  ON public.assets FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "assets_update_own"
  ON public.assets FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "assets_delete_own"
  ON public.assets FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 5: bank_accounts  [SENSITIVE: account_number]
-- ---------------------------------------------------------------------------
ALTER TABLE public.bank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bank_accounts FORCE ROW LEVEL SECURITY;

CREATE POLICY "bank_accounts_select_own"
  ON public.bank_accounts FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "bank_accounts_insert_own"
  ON public.bank_accounts FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "bank_accounts_update_own"
  ON public.bank_accounts FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "bank_accounts_delete_own"
  ON public.bank_accounts FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 6: budgets
-- ---------------------------------------------------------------------------
ALTER TABLE public.budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budgets FORCE ROW LEVEL SECURITY;

CREATE POLICY "budgets_select_own"
  ON public.budgets FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "budgets_insert_own"
  ON public.budgets FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "budgets_update_own"
  ON public.budgets FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "budgets_delete_own"
  ON public.budgets FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 7: categories
-- ---------------------------------------------------------------------------
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories FORCE ROW LEVEL SECURITY;

CREATE POLICY "categories_select_own"
  ON public.categories FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "categories_insert_own"
  ON public.categories FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "categories_update_own"
  ON public.categories FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "categories_delete_own"
  ON public.categories FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 8: credit_cards  [SENSITIVE: card_number]
-- ---------------------------------------------------------------------------
ALTER TABLE public.credit_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_cards FORCE ROW LEVEL SECURITY;

CREATE POLICY "credit_cards_select_own"
  ON public.credit_cards FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "credit_cards_insert_own"
  ON public.credit_cards FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "credit_cards_update_own"
  ON public.credit_cards FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "credit_cards_delete_own"
  ON public.credit_cards FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 9: goals
-- ---------------------------------------------------------------------------
ALTER TABLE public.goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.goals FORCE ROW LEVEL SECURITY;

CREATE POLICY "goals_select_own"
  ON public.goals FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "goals_insert_own"
  ON public.goals FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "goals_update_own"
  ON public.goals FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "goals_delete_own"
  ON public.goals FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 10: insurance_policies
-- ---------------------------------------------------------------------------
ALTER TABLE public.insurance_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.insurance_policies FORCE ROW LEVEL SECURITY;

CREATE POLICY "insurance_policies_select_own"
  ON public.insurance_policies FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "insurance_policies_insert_own"
  ON public.insurance_policies FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "insurance_policies_update_own"
  ON public.insurance_policies FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "insurance_policies_delete_own"
  ON public.insurance_policies FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 11: investments
-- ---------------------------------------------------------------------------
ALTER TABLE public.investments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investments FORCE ROW LEVEL SECURITY;

CREATE POLICY "investments_select_own"
  ON public.investments FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "investments_insert_own"
  ON public.investments FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "investments_update_own"
  ON public.investments FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "investments_delete_own"
  ON public.investments FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 12: objective_history
-- ---------------------------------------------------------------------------
ALTER TABLE public.objective_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.objective_history FORCE ROW LEVEL SECURITY;

CREATE POLICY "objective_history_select_own"
  ON public.objective_history FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "objective_history_insert_own"
  ON public.objective_history FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "objective_history_update_own"
  ON public.objective_history FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "objective_history_delete_own"
  ON public.objective_history FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 13: reports
-- ---------------------------------------------------------------------------
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports FORCE ROW LEVEL SECURITY;

CREATE POLICY "reports_select_own"
  ON public.reports FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "reports_insert_own"
  ON public.reports FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "reports_update_own"
  ON public.reports FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "reports_delete_own"
  ON public.reports FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 14: bills
-- ---------------------------------------------------------------------------
ALTER TABLE public.bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bills FORCE ROW LEVEL SECURITY;

CREATE POLICY "bills_select_own"
  ON public.bills FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "bills_insert_own"
  ON public.bills FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "bills_update_own"
  ON public.bills FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "bills_delete_own"
  ON public.bills FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 15: loans
-- ---------------------------------------------------------------------------
ALTER TABLE public.loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.loans FORCE ROW LEVEL SECURITY;

CREATE POLICY "loans_select_own"
  ON public.loans FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "loans_insert_own"
  ON public.loans FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "loans_update_own"
  ON public.loans FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "loans_delete_own"
  ON public.loans FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 16: transactions
-- ---------------------------------------------------------------------------
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions FORCE ROW LEVEL SECURITY;

CREATE POLICY "transactions_select_own"
  ON public.transactions FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "transactions_insert_own"
  ON public.transactions FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "transactions_update_own"
  ON public.transactions FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "transactions_delete_own"
  ON public.transactions FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 17: portfolio_snapshots
-- ---------------------------------------------------------------------------
ALTER TABLE public.portfolio_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_snapshots FORCE ROW LEVEL SECURITY;

CREATE POLICY "portfolio_snapshots_select_own"
  ON public.portfolio_snapshots FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "portfolio_snapshots_insert_own"
  ON public.portfolio_snapshots FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "portfolio_snapshots_update_own"
  ON public.portfolio_snapshots FOR UPDATE
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "portfolio_snapshots_delete_own"
  ON public.portfolio_snapshots FOR DELETE
  USING (user_id = auth.uid());


-- ---------------------------------------------------------------------------
-- SECTION 18: budget_items  (child of budgets)
-- ---------------------------------------------------------------------------
ALTER TABLE public.budget_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budget_items FORCE ROW LEVEL SECURITY;

CREATE POLICY "budget_items_select_own"
  ON public.budget_items FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.budgets p
      WHERE p.id = budget_items.budget_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "budget_items_insert_own"
  ON public.budget_items FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.budgets p
      WHERE p.id = budget_items.budget_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "budget_items_update_own"
  ON public.budget_items FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.budgets p
      WHERE p.id = budget_items.budget_id
        AND p.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.budgets p
      WHERE p.id = budget_items.budget_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "budget_items_delete_own"
  ON public.budget_items FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.budgets p
      WHERE p.id = budget_items.budget_id
        AND p.user_id = auth.uid()
    )
  );


-- ---------------------------------------------------------------------------
-- SECTION 19: goal_contributions  (child of goals)
-- ---------------------------------------------------------------------------
ALTER TABLE public.goal_contributions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.goal_contributions FORCE ROW LEVEL SECURITY;

CREATE POLICY "goal_contributions_select_own"
  ON public.goal_contributions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.goals p
      WHERE p.id = goal_contributions.goal_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "goal_contributions_insert_own"
  ON public.goal_contributions FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.goals p
      WHERE p.id = goal_contributions.goal_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "goal_contributions_update_own"
  ON public.goal_contributions FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.goals p
      WHERE p.id = goal_contributions.goal_id
        AND p.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.goals p
      WHERE p.id = goal_contributions.goal_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "goal_contributions_delete_own"
  ON public.goal_contributions FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.goals p
      WHERE p.id = goal_contributions.goal_id
        AND p.user_id = auth.uid()
    )
  );


-- ---------------------------------------------------------------------------
-- SECTION 20: insurance_claims  (child of insurance_policies)
-- ---------------------------------------------------------------------------
ALTER TABLE public.insurance_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.insurance_claims FORCE ROW LEVEL SECURITY;

CREATE POLICY "insurance_claims_select_own"
  ON public.insurance_claims FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.insurance_policies p
      WHERE p.id = insurance_claims.policy_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "insurance_claims_insert_own"
  ON public.insurance_claims FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.insurance_policies p
      WHERE p.id = insurance_claims.policy_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "insurance_claims_update_own"
  ON public.insurance_claims FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.insurance_policies p
      WHERE p.id = insurance_claims.policy_id
        AND p.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.insurance_policies p
      WHERE p.id = insurance_claims.policy_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "insurance_claims_delete_own"
  ON public.insurance_claims FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.insurance_policies p
      WHERE p.id = insurance_claims.policy_id
        AND p.user_id = auth.uid()
    )
  );


-- ---------------------------------------------------------------------------
-- SECTION 21: bill_payments  (child of bills)
-- ---------------------------------------------------------------------------
ALTER TABLE public.bill_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bill_payments FORCE ROW LEVEL SECURITY;

CREATE POLICY "bill_payments_select_own"
  ON public.bill_payments FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.bills p
      WHERE p.id = bill_payments.bill_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "bill_payments_insert_own"
  ON public.bill_payments FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.bills p
      WHERE p.id = bill_payments.bill_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "bill_payments_update_own"
  ON public.bill_payments FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.bills p
      WHERE p.id = bill_payments.bill_id
        AND p.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.bills p
      WHERE p.id = bill_payments.bill_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "bill_payments_delete_own"
  ON public.bill_payments FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.bills p
      WHERE p.id = bill_payments.bill_id
        AND p.user_id = auth.uid()
    )
  );


-- ---------------------------------------------------------------------------
-- SECTION 22: loan_payments  (child of loans)
-- ---------------------------------------------------------------------------
ALTER TABLE public.loan_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.loan_payments FORCE ROW LEVEL SECURITY;

CREATE POLICY "loan_payments_select_own"
  ON public.loan_payments FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.loans p
      WHERE p.id = loan_payments.loan_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "loan_payments_insert_own"
  ON public.loan_payments FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.loans p
      WHERE p.id = loan_payments.loan_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "loan_payments_update_own"
  ON public.loan_payments FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.loans p
      WHERE p.id = loan_payments.loan_id
        AND p.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.loans p
      WHERE p.id = loan_payments.loan_id
        AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "loan_payments_delete_own"
  ON public.loan_payments FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.loans p
      WHERE p.id = loan_payments.loan_id
        AND p.user_id = auth.uid()
    )
  );


-- =============================================================================
-- VERIFICATION QUERY
-- Run this after applying to confirm all tables have RLS enabled + policies set
-- =============================================================================
/*
SELECT
  t.tablename,
  t.rowsecurity AS rls_enabled,
  count(p.policyname) AS policy_count
FROM pg_tables t
LEFT JOIN pg_policies p
  ON t.schemaname = p.schemaname AND t.tablename = p.tablename
WHERE t.schemaname = 'public'
GROUP BY t.tablename, t.rowsecurity
ORDER BY t.tablename;
*/
