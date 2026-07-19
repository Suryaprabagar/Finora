// ============ Auth Types ============
export interface User {
  id: string
  email: string
  full_name: string
  currency: string
  currency_symbol: string
  theme: string
  phone?: string
  is_active: boolean
  created_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

// ============ API Response Types ============
export interface APIResponse<T> {
  success: boolean
  data?: T
  message?: string
  pagination?: Pagination
}

export interface Pagination {
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface APIError {
  success: false
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
}

// ============ Transaction Types ============
export type TransactionType = 'income' | 'expense' | 'transfer'
export type TransactionStatus = 'cleared' | 'pending' | 'reconciled'
export type PaymentMethod = 'cash' | 'card' | 'upi' | 'netbanking' | 'cheque'

export interface Transaction {
  id: string
  type: TransactionType
  amount: number
  description: string
  merchant?: string
  date: string
  status: TransactionStatus
  payment_method?: PaymentMethod
  category_id?: string
  category?: Category
  bank_account_id?: string
  bank_account?: BankAccount
  credit_card_id?: string
  reference_number?: string
  notes?: string
  is_recurring: boolean
  recurring_interval?: string
  tags?: string
  created_at: string
}

// ============ Category Types ============
export interface Category {
  id: string
  name: string
  type: 'income' | 'expense'
  icon?: string
  color?: string
  is_default: boolean
  created_at: string
}

// ============ Bank Account Types ============
export type AccountType = 'savings' | 'checking' | 'cash' | 'fd'

export interface BankAccount {
  id: string
  name: string
  account_type: AccountType
  bank_name?: string
  account_number?: string
  balance: number
  interest_rate?: number
  is_active: boolean
  color?: string
  notes?: string
  created_at: string
}

// ============ Credit Card Types ============
export interface CreditCard {
  id: string
  name: string
  bank_name: string
  card_number?: string
  credit_limit: number
  outstanding_balance: number
  billing_cycle_day: number
  due_day: number
  interest_rate?: number
  annual_fee?: number
  rewards_points: number
  is_active: boolean
  color?: string
  created_at: string
  utilization_percent?: number
}

// ============ Budget Types ============
export interface BudgetItem {
  id: string
  name: string
  allocated_amount: number
  category_id?: string
  spent_amount: number
  percentage_used: number
}

export interface Budget {
  id: string
  name: string
  month: number
  year: number
  total_limit: number
  alert_threshold: number
  total_spent: number
  items: BudgetItem[]
  created_at: string
}

// ============ Goal Types ============
export interface GoalContribution {
  id: string
  amount: number
  date: string
  notes?: string
  created_at: string
}

export interface Goal {
  id: string
  name: string
  description?: string
  category: string
  target_amount: number
  current_amount: number
  monthly_contribution: number
  deadline?: string
  status: 'active' | 'completed' | 'paused'
  color?: string
  icon?: string
  progress_percentage: number
  created_at: string
}

// ============ Bill Types ============
export interface Bill {
  id: string
  name: string
  category: string
  amount: number
  due_day: number
  is_recurring: boolean
  frequency: string
  auto_pay: boolean
  status: 'active' | 'paused' | 'cancelled'
  last_paid_date?: string
  next_due_date?: string
  notes?: string
  icon?: string
  created_at: string
}

// ============ Investment Types ============
export type InvestmentType = 'stocks' | 'mutual_fund' | 'gold' | 'fd' | 'ppf' | 'nps' | 'bonds' | 'etf'

export interface Investment {
  id: string
  name: string
  type: InvestmentType
  symbol?: string
  purchase_price: number
  current_price: number
  quantity: number
  purchase_date: string
  maturity_date?: string
  interest_rate?: number
  broker?: string
  folio_number?: string
  notes?: string
  is_active: boolean
  current_value: number
  gain_loss: number
  gain_loss_percent: number
  created_at: string
}

// ============ Loan Types ============
export type LoanType = 'home' | 'vehicle' | 'personal' | 'education' | 'business'

export interface Loan {
  id: string
  name: string
  lender: string
  loan_type: LoanType
  principal_amount: number
  outstanding_balance: number
  interest_rate: number
  emi_amount: number
  tenure_months: number
  paid_months: number
  start_date: string
  end_date: string
  emi_day: number
  is_active: boolean
  notes?: string
  progress_percentage: number
  created_at: string
}

// ============ Asset Types ============
export type AssetType = 'property' | 'vehicle' | 'jewellery' | 'electronics' | 'artwork' | 'other'

export interface Asset {
  id: string
  name: string
  asset_type: AssetType
  purchase_price: number
  current_value: number
  purchase_date: string
  description?: string
  location?: string
  serial_number?: string
  depreciation_rate?: number
  is_insured: boolean
  appreciation_loss: number
  appreciation_percent: number
  created_at: string
}

// ============ Insurance Types ============
export type PolicyType = 'life' | 'health' | 'vehicle' | 'property' | 'term' | 'accident'

export interface InsurancePolicy {
  id: string
  policy_name: string
  provider: string
  policy_type: PolicyType
  policy_number?: string
  coverage_amount: number
  annual_premium: number
  premium_frequency: string
  start_date: string
  renewal_date: string
  status: 'active' | 'expired' | 'cancelled' | 'pending_renewal'
  nominee?: string
  notes?: string
  created_at: string
}

// ============ Dashboard Types ============
export interface CashFlowPoint {
  month: string
  income: number
  expenses: number
  savings: number
}

export interface AssetAllocationItem {
  type: string
  value: number
  percentage: number
}

export interface DashboardData {
  net_worth: number
  cash_balance: number
  monthly_income: number
  monthly_expenses: number
  savings_rate: number
  investment_value: number
  cash_flow: CashFlowPoint[]
  asset_allocation: AssetAllocationItem[]
  recent_transactions: Transaction[]
  upcoming_bills: Bill[]
  budget_summary: Budget | null
  goals_summary: Goal[]
}

// ============ Report Types ============
export interface Report {
  id: string
  name: string
  report_type: string
  period_start: string
  period_end: string
  format: string
  status: string
  file_path?: string
  created_at: string
}
