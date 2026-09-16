'use client'

import { useState, useRef, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { expensesApi, budgetApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DonutChart } from '@/components/shared/charts/DonutChart'
import { downloadCSV } from '@/lib/export'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { TransactionForm } from '@/components/features/transactions/TransactionForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { EmptyState } from '@/components/shared/EmptyState'
import { toast } from 'sonner'

export default function ExpensesPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingTransaction, setEditingTransaction] = useState<any>(null)
  const [transactionToDelete, setTransactionToDelete] = useState<any>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [velocityPeriod, setVelocityPeriod] = useState<'Monthly'>('Monthly')

  const closeTimerRef = useRef<ReturnType<typeof setTimeout>>(null)

  useEffect(() => {
    return () => {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    }
  }, [])

  const queryClient = useQueryClient()

  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['expenses-summary'],
    queryFn: () => expensesApi.getSummary().then(r => r.data),
  })

  const { data: categoriesRes, isLoading: isCategoriesLoading } = useQuery({
    queryKey: ['expenses-by-category'],
    queryFn: () => expensesApi.getByCategory().then(r => r.data),
  })

  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['expenses-list'],
    queryFn: () => expensesApi.list().then(r => r.data),
  })

  const { data: trendsRes, isLoading: isTrendsLoading } = useQuery({
    queryKey: ['expenses-trends'],
    queryFn: () => expensesApi.getTrends().then(r => r.data),
  })

  const { data: merchantsRes, isLoading: isMerchantsLoading } = useQuery({
    queryKey: ['expenses-by-merchant'],
    queryFn: () => expensesApi.getByMerchant().then(r => r.data),
  })

  const { data: budgetRes, isLoading: isBudgetLoading } = useQuery({
    queryKey: ['budget-current'],
    queryFn: () => budgetApi.getCurrent().then(r => r.data),
  })

  const { data: upcomingRes, isLoading: isUpcomingLoading } = useQuery({
    queryKey: ['expenses-upcoming-recurring'],
    queryFn: () => expensesApi.getUpcomingRecurring().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => expensesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses-list'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-summary'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-by-category'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-trends'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-by-merchant'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-recurring'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-upcoming-recurring'] })
      queryClient.invalidateQueries({ queryKey: ['budget-current'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })

      toast.success('Expense transaction deleted successfully')
      setTransactionToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete transaction')
    }
  })

  const summary = summaryRes?.data || { monthly_total: 0, top_category: 'None', avg_daily: 0, recurring_total: 0, recurring_count: 0 }
  const categoriesData = categoriesRes?.data || []
  const trendsData = trendsRes?.data || []
  const merchantsData = merchantsRes?.data || []
  const upcomingItems = upcomingRes?.data || []
  const currentBudget = budgetRes?.data || null
  const expenses = useMemo(() => {
    const list = listRes?.data || []
    if (!searchTerm) return list
    const term = searchTerm.toLowerCase()
    return list.filter((tx: any) =>
      tx.description?.toLowerCase().includes(term) ||
      tx.category?.name?.toLowerCase().includes(term) ||
      tx.bank_account?.name?.toLowerCase().includes(term)
    )
  }, [listRes?.data, searchTerm])

  const handleAdd = () => {
    setEditingTransaction({ type: 'expense' })
    setIsModalOpen(true)
  }

  const handleEdit = (tx: any) => {
    setEditingTransaction(tx)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    closeTimerRef.current = setTimeout(() => setEditingTransaction(null), 200)
  }

  return (
    <div className="space-y-6 pb-12">
      <PageHeader
        title="Expense Management"
        subtitle="Track and manage your spending across all categories."
        actions={
          <div className="flex items-center gap-3">
            <div className="flex gap-2">
              <button className="px-4 py-2 bg-surface-container-lowest border border-outline-variant hover:bg-surface-container-low rounded-md text-[13px] font-bold text-on-surface flex items-center gap-2 transition-colors shrink-0 shadow-sm">
                <span className="material-symbols-outlined text-[18px]">filter_list</span>
                Filter
              </button>
              <button onClick={() => {
                if (!expenses || expenses.length === 0) {
                  toast.error('No records to export')
                  return
                }
                downloadCSV(expenses, 'expenses_history')
                toast.success('Export downloaded')
              }} className="px-4 py-2 bg-surface-container-lowest border border-outline-variant hover:bg-surface-container-low rounded-md text-[13px] font-bold text-on-surface flex items-center gap-2 transition-colors shrink-0 shadow-sm">
                <span className="material-symbols-outlined text-[18px]">download</span>
                Export CSV
              </button>
            </div>
            <button
              type="button"
              className="hidden sm:flex items-center gap-2 px-4 py-2 bg-surface-container-lowest border border-outline-variant rounded-md text-sm font-medium text-on-surface"
            >
              <span className="material-symbols-outlined text-[18px]">
                calendar_today
              </span>
              Current Month
            </button>
            <button onClick={handleAdd} className="btn-primary">
              <span className="material-symbols-outlined text-[18px]">add</span>
              Add Expense
            </button>
          </div>
        }
      />

      {/* 5 Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px]">
          <p className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-3">Monthly Spending</p>
          <div className="flex items-baseline gap-2 mt-auto">
            <h3 className="text-[22px] font-bold font-display text-on-surface">{formatCurrency(summary.monthly_total)}</h3>
            <span className="text-[11px] font-semibold text-error bg-error-container/40 px-2 py-0.5 rounded-full flex items-center gap-0.5">
              <span className="material-symbols-outlined text-[13px]">
                {summary.change_pct >= 0 ? 'trending_up' : 'trending_down'}
              </span>

              {Math.abs(Number(summary.change_pct) || 0).toFixed(1)}%
            </span>

          </div>
          <div className="w-full bg-error h-1 rounded-full overflow-hidden mt-2"></div>
        </div>

        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px]">
          <p className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-3">
            Avg. Daily Spend
          </p>

          <h3 className="text-[22px] font-bold font-display text-on-surface mb-1 mt-auto">
            {formatCurrency(summary.avg_daily)}
          </h3>

          <p className="text-[10px] text-on-surface-variant font-medium">
            Based on your spending this month
          </p>
        </div>

        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px]">
          <p className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-3">
            Largest Expense
          </p>

          <h3 className="text-[22px] font-bold font-display text-on-surface mb-1 mt-auto">
            {formatCurrency(summary.largest_expense?.amount || 0)}
          </h3>

          <p className="text-[10px] text-on-surface-variant font-medium truncate">
            {summary.largest_expense?.merchant ||
              summary.largest_expense?.description ||
              summary.largest_expense?.category ||
              'No expenses this month'}
          </p>
        </div>

        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px]">
          <p className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-3">
            Remaining Budget
          </p>

          <h3 className="text-[22px] font-bold font-display text-on-surface mb-1 mt-auto">
            {isBudgetLoading
              ? '—'
              : currentBudget
                ? formatCurrency(currentBudget.remaining_total || 0)
                : '—'}
          </h3>

          <p className="text-[10px] text-tertiary font-medium">
            {currentBudget
              ? `${currentBudget.days_remaining} days remaining`
              : 'No budget set for this month'}
          </p>
        </div>

        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px] bg-surface-container-low border-none shadow-none">
          <p className="text-[10px] font-bold tracking-widest text-primary uppercase mb-3">
            Recurring
          </p>

          <h3 className="text-[22px] font-bold font-display text-on-surface mb-1 mt-auto">
            {formatCurrency(summary.recurring_total || 0)}
          </h3>

          <p className="text-[10px] text-on-surface-variant font-medium">
            {summary.recurring_count || 0} recurring expenses this month
          </p>
        </div>
      </div>

      {/* Row 2: Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 finora-card p-6">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">Spending Velocity</h3>
            <div className="flex bg-surface-container rounded p-0.5 border border-outline-variant/30">
              <button onClick={() => setVelocityPeriod('Monthly')} className={`px-3 py-1 text-xs font-medium rounded ${velocityPeriod === 'Monthly' ? 'bg-surface-container-lowest shadow-sm text-on-surface' : 'text-on-surface-variant hover:text-on-surface'}`}>Monthly</button>
            </div>
          </div>
          <div className="h-[200px] flex items-end justify-between gap-1 sm:gap-2 px-1 relative">
            <div className="absolute top-[30%] left-0 right-0 border-t border-dashed border-outline-variant z-0"></div>
            {(() => {
              const data = trendsData
              const maxAmount = Math.max(...data.map((item: any) => item.amount), 0)

              return data.map((item: any, i: number) => {
                const isHighest = item.amount === maxAmount && item.amount > 0
                const barHeight = maxAmount > 0 ? (item.amount / maxAmount) * 100 : 0
                const dateStr = item.month

                return (
                  <div
                    key={i}
                    className="w-full h-full flex flex-col justify-end items-center gap-3 z-10 group cursor-pointer max-w-[64px]"
                  >
                    <div
                      className={`w-full relative rounded-t transition-colors ${isHighest
                        ? 'bg-primary'
                        : 'bg-surface-variant group-hover:bg-outline-variant'
                        }`}
                      style={{ height: `${barHeight}%` }}
                    >
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-inverse-surface text-inverse-on-surface text-[11px] font-medium px-3 py-1.5 rounded shadow whitespace-nowrap z-30 text-center pointer-events-none">
                        {isHighest ? 'Peak' : dateStr}:<br />
                        {formatCurrency(item.amount)}
                        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-inverse-surface rotate-45"></div>
                      </div>
                    </div>

                    <span
                      className={`text-[10px] font-medium h-4 ${isHighest
                        ? 'text-primary font-bold'
                        : 'text-on-surface-variant'
                        }`}
                    >
                      {dateStr}
                    </span>
                  </div>
                )
              })
            })()}
          </div>
        </div>

        <div className="finora-card p-6 flex flex-col">
          <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-4">Allocation by Category</h3>
          <div className="flex-1">
            {isCategoriesLoading ? (
              <div className="h-[300px] flex items-center justify-center">
                <div className="w-48 h-48 rounded-full border-8 border-surface-variant/30 animate-pulse" />
              </div>
            ) : (categoriesData.length > 0 && categoriesData.reduce((sum: number, c: any) => sum + Number(c.total || c.amount || c.value || 0), 0) > 0) ? (
              <DonutChart
                data={categoriesData.map((c: any, i: number) => {
                  const colors = ['var(--color-primary)', 'var(--color-secondary)', 'var(--color-tertiary)', 'var(--color-outline-variant)', 'var(--color-surface-variant)'];
                  return {
                    name: c.category || c.name,
                    value: Number(c.total || c.amount || c.value || 0),
                    color: colors[i % colors.length]
                  };
                })}
                height={300}
                centerLabel="Total"
                centerValue={formatCurrency(summary.monthly_total || 0)}
              />
            ) : (
              <EmptyState title="No expense data" icon="pie_chart" />
            )}
          </div>
        </div>
      </div>

      {/* Row 3: Sub Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Top Merchants */}
        <div className="finora-card p-6">
          <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-6">
            Top Merchants
          </h3>

          <div className="space-y-5">
            {isMerchantsLoading ? (
              [1, 2, 3].map((i) => (
                <div key={i} className="space-y-2 animate-pulse">
                  <div className="h-8 bg-surface-container rounded" />
                  <div className="h-1 bg-surface-container rounded" />
                </div>
              ))
            ) : merchantsData.length > 0 ? (
              merchantsData.map((merchant: any, i: number) => (
                <div
                  key={merchant.merchant || i}
                  className="flex flex-col gap-2"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-surface-container rounded flex items-center justify-center shrink-0">
                      <span className="material-symbols-outlined text-[16px] text-on-surface-variant">
                        receipt_long
                      </span>
                    </div>

                    <div className="flex-1 flex justify-between items-end gap-3">
                      <span className="text-[13px] font-bold text-on-surface truncate">
                        {merchant.merchant}
                      </span>

                      <span className="text-[13px] font-bold text-on-surface whitespace-nowrap">
                        {formatCurrency(merchant.amount)}
                      </span>
                    </div>
                  </div>

                  <div className="pl-11 pr-2">
                    <div className="w-full bg-surface-container h-1 rounded-full overflow-hidden">
                      <div
                        className="bg-primary h-full rounded-full transition-all"
                        style={{
                          width: `${Math.min(
                            Math.max(Number(merchant.percentage) || 0, 0),
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState title="No expense data" icon="storefront" />
            )}
          </div>
        </div>

        {/* Monthly Comparison */}
        <div className="finora-card p-6 flex flex-col justify-between">
          <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-4">
            Monthly Comparison
          </h3>

          {trendsData.length >= 2 ? (
            <>
              {(() => {
                const previousMonth = trendsData[trendsData.length - 2]
                const currentMonth = trendsData[trendsData.length - 1]

                const previousAmount = Number(previousMonth.amount) || 0
                const currentAmount = Number(currentMonth.amount) || 0
                const maxAmount = Math.max(previousAmount, currentAmount, 1)

                const changePct =
                  previousAmount > 0
                    ? ((currentAmount - previousAmount) / previousAmount) * 100
                    : null

                const previousBarHeight =
                  (previousAmount / maxAmount) * 140

                const currentBarHeight =
                  (currentAmount / maxAmount) * 140

                return (
                  <>
                    <div className="flex-1 flex items-end justify-center gap-6 sm:gap-12 relative px-4 sm:px-8">
                      <div className="flex flex-col items-center gap-3 w-12 sm:w-16">
                        <div
                          className="w-full bg-surface-container rounded-t transition-all"
                          style={{ height: `${previousBarHeight}px` }}
                        />
                        <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest text-center">
                          {previousMonth.month}
                        </span>
                        <span className="text-[13px] font-bold text-on-surface">
                          {formatCurrency(previousAmount)}
                        </span>
                      </div>

                      <div className="flex flex-col items-center gap-3 w-12 sm:w-16">
                        <div
                          className="w-full bg-primary rounded-t transition-all"
                          style={{ height: `${currentBarHeight}px` }}
                        />
                        <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest text-center">
                          {currentMonth.month}
                        </span>
                        <span className="text-[13px] font-bold text-on-surface">
                          {formatCurrency(currentAmount)}
                        </span>
                      </div>
                    </div>

                    <p className="text-center text-[11px] text-on-surface-variant font-medium mt-4 italic">
                      {changePct === null
                        ? 'No previous month data available for comparison.'
                        : currentAmount === previousAmount
                          ? 'Spending is unchanged compared to last month.'
                          : changePct > 0
                            ? `Spending is up ${Math.abs(changePct).toFixed(1)}% compared to last month.`
                            : `Spending is down ${Math.abs(changePct).toFixed(1)}% compared to last month.`}
                    </p>
                  </>
                )
              })()}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <EmptyState title="Not enough expense data" icon="bar_chart" />
            </div>
          )}
        </div>

      </div>

      {/* Row 4: Table */}
      <div className="finora-card overflow-hidden">
        <div className="p-5 border-b border-surface-container flex flex-col sm:flex-row justify-between items-center gap-4">
          <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">Recent Transactions</h3>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button className="px-3 py-1.5 bg-surface-container-lowest border border-outline-variant rounded-md text-[12px] font-bold text-on-surface flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px]">category</span> Category
            </button>
            <button className="px-3 py-1.5 bg-surface-container-lowest border border-outline-variant rounded-md text-[12px] font-bold text-on-surface flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px]">account_balance</span> Account
            </button>
            <button className="px-3 py-1.5 bg-surface-container-lowest border border-outline-variant rounded-md text-[12px] font-bold text-on-surface flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px]">calendar_today</span> Date Range
            </button>
            <div className="flex-1"></div>
            <button className="px-3 py-1.5 text-primary text-[12px] font-bold flex items-center gap-1.5 ml-4">
              <span className="material-symbols-outlined text-[16px]">download</span> Export CSV
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-[13px] text-left">
            <thead className="bg-surface-container/30 text-[10px] uppercase font-bold text-on-surface-variant tracking-wider">
              <tr>
                <th className="px-6 py-4">Merchant</th>
                <th className="px-6 py-4 text-center">Category</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4">Account</th>
                <th className="px-6 py-4 text-right">Amount</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container">
              {isListLoading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-on-surface-variant font-medium">Loading...</td>
                </tr>
              ) : expenses.length > 0 ? (
                expenses.map((tx: any, i: number) => (
                  <tr key={tx.id} className="hover:bg-surface-container-low/50 transition-colors group">
                    <td className="px-6 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center text-primary font-bold text-[13px]">
                          {tx.description.charAt(0)}
                        </div>
                        <div>
                          <p className="font-bold text-on-surface">{tx.description}</p>
                          <p className="text-[10px] text-on-surface-variant">Ref: #TXN-{tx.id.substring(0, 5)}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-3 text-center">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-surface-container-low border border-surface-container text-on-surface-variant text-[11px] font-bold rounded">
                        <span className="material-symbols-outlined text-[14px]">sell</span>
                        {tx.category?.name || 'Uncategorized'}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-on-surface-variant font-medium">
                      {new Date(tx.date).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })}
                    </td>
                    <td className="px-6 py-3 text-on-surface-variant font-medium">
                      {tx.bank_account?.name || '-'}
                      <br />
                      <span className="text-[10px] opacity-70">
                        {tx.bank_account?.account_number ? `(****${tx.bank_account.account_number.slice(-4)})` : ''}
                      </span>
                    </td>
                    <td className={`px-6 py-3 text-right font-bold font-display text-[14px] ${i === 3 ? 'text-error' : 'text-on-surface'}`}>
                      {formatCurrency(tx.amount)}
                    </td>
                    <td className="px-6 py-3">
                      {i === 3 ? (
                        <span className="chip-overdue">
                          <div className="w-1.5 h-1.5 rounded-full bg-error"></div>
                          Flagged
                        </span>
                      ) : tx.status === 'pending' ? (
                        <span className="chip-pending">
                          <div className="w-1.5 h-1.5 rounded-full bg-secondary"></div>
                          Pending
                        </span>
                      ) : (
                        <span className="chip-cleared">
                          <div className="w-1.5 h-1.5 rounded-full bg-tertiary"></div>
                          Cleared
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-3 text-center">
                      <div className="flex items-center justify-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => handleEdit(tx)} className="text-on-surface-variant hover:text-primary transition-colors" title="Edit">
                          <span className="material-symbols-outlined text-[18px]">edit</span>
                        </button>
                        <button onClick={() => setTransactionToDelete(tx)} className="text-on-surface-variant hover:text-secondary transition-colors" title="Delete">
                          <span className="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-on-surface-variant font-medium">No records found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="p-4 border-t border-surface-container flex justify-between items-center text-[12px] font-medium text-on-surface-variant">
          <span>Showing 1-{Math.min(10, expenses.length)} of {expenses.length} transactions</span>
          <div className="flex items-center gap-1.5">
            <button className="w-7 h-7 flex items-center justify-center border border-outline-variant rounded hover:bg-surface-container-low bg-surface-container-lowest"><span className="material-symbols-outlined text-[14px]">chevron_left</span></button>
            <button className="w-7 h-7 flex items-center justify-center border border-primary bg-primary text-on-primary rounded font-bold">1</button>
            <button className="w-7 h-7 flex items-center justify-center border border-outline-variant rounded hover:bg-surface-container-low bg-surface-container-lowest text-on-surface font-bold">2</button>
            <button className="w-7 h-7 flex items-center justify-center border border-outline-variant rounded hover:bg-surface-container-low bg-surface-container-lowest text-on-surface font-bold">3</button>
            <button className="w-7 h-7 flex items-center justify-center border border-outline-variant rounded hover:bg-surface-container-low bg-surface-container-lowest"><span className="material-symbols-outlined text-[14px]">chevron_right</span></button>
          </div>
        </div>
      </div>

      {/* Row 5: 3 Small Bottom Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
        <div className="finora-card p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">Upcoming Recurring</h3>
            {upcomingItems.length > 0 && (
              <span className="text-[11px] font-bold text-primary">
                {upcomingItems.length} active
              </span>
            )}
          </div>
          {isUpcomingLoading ? (
            <div className="py-8 text-center text-on-surface-variant text-xs font-medium">
              Loading recurring expenses...
            </div>
          ) : upcomingItems.length === 0 ? (
            <div className="py-8 text-center text-on-surface-variant flex flex-col items-center justify-center">
              <div className="w-10 h-10 rounded-full bg-surface-container-low flex items-center justify-center text-on-surface-variant mb-2">
                <span className="material-symbols-outlined text-[20px]">repeat</span>
              </div>
              <p className="text-[13px] font-semibold text-on-surface">No recurring expenses</p>
              <p className="text-[11px] text-on-surface-variant mt-0.5">Scheduled bills and subscriptions will appear here.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {upcomingItems.map((sub: any) => (
                <div key={sub.id} className="flex justify-between items-center">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-surface-container-low flex items-center justify-center text-on-surface-variant shrink-0">
                      <span className="material-symbols-outlined text-[18px]">
                        {sub.category?.icon || 'repeat'}
                      </span>
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13px] font-bold text-on-surface truncate">
                        {sub.merchant || sub.description || 'Recurring Expense'}
                      </p>
                      <p className="text-[11px] text-on-surface-variant font-medium">
                        {sub.days_until_due === null || sub.days_until_due === undefined
                          ? (sub.next_due_date ? formatDate(sub.next_due_date) : 'Scheduled')
                          : sub.days_until_due === 0
                            ? 'Due today'
                            : sub.days_until_due === 1
                              ? 'Due tomorrow'
                              : sub.days_until_due < 0
                                ? `Overdue by ${Math.abs(sub.days_until_due)} days`
                                : `Due in ${sub.days_until_due} days`}
                      </p>
                    </div>
                  </div>
                  <span className="font-bold font-display text-[14px] text-on-surface shrink-0 ml-2">
                    {formatCurrency(sub.amount)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="finora-card p-6">
          <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-6">
            Budget Consumption
          </h3>

          <div className="space-y-6">
            {isBudgetLoading ? (
              [1, 2, 3].map((i) => (
                <div key={i} className="space-y-2 animate-pulse">
                  <div className="flex justify-between">
                    <div className="h-3 w-32 bg-surface-container rounded" />
                    <div className="h-3 w-24 bg-surface-container rounded" />
                  </div>
                  <div className="w-full h-1.5 bg-surface-container rounded-full" />
                </div>
              ))
            ) : currentBudget?.items?.length > 0 ? (
              currentBudget.items.map((item: any, i: number) => {
                const allocated = Number(item.allocated_amount) || 0
                const spent = Number(item.spent_amount) || 0
                const percentage =
                  allocated > 0
                    ? Math.min((spent / allocated) * 100, 100)
                    : 0

                return (
                  <div key={item.id || i} className="space-y-2">
                    <div className="flex justify-between items-end">
                      <span className="text-[12px] font-bold text-on-surface">
                        {item.name || item.category?.name || 'Uncategorized'}
                      </span>

                      <div className="text-[11px]">
                        <span className="text-on-surface-variant font-medium">
                          {formatCurrency(spent)}
                        </span>

                        <span className="text-on-surface-variant opacity-60">
                          {' / '}{formatCurrency(allocated)}
                        </span>
                      </div>
                    </div>

                    <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })
            ) : (
              <EmptyState
                title="No budget set for this month"
                icon="account_balance"
              />
            )}
          </div>
        </div>

        <div className="finora-card p-6 bg-primary text-on-primary border-none relative overflow-hidden flex flex-col justify-between">
          <span className="material-symbols-outlined absolute right-6 top-6 text-[40px] opacity-20 transform -rotate-12">trending_up</span>
          <div>
            <h3 className="text-[10px] font-bold tracking-widest uppercase mb-4 opacity-80">Wealth Insight</h3>
            <p className="text-[13px] font-medium leading-relaxed">
              Your dining out expenses have decreased by <span className="font-bold">12%</span> this month. If this trend continues, you can reach your "European Summer" goal <span className="font-bold">2 months</span> earlier than projected.
            </p>
          </div>
          <div className="mt-6 space-y-4">
            <div className="flex items-center gap-2 text-[11px] font-bold tracking-widest uppercase">
              <span className="material-symbols-outlined text-[16px]">trending_down</span>
              Positive Momentum
            </div>
            <button className="w-full py-2.5 bg-white/10 hover:bg-white/20 transition-colors rounded border border-white/20 text-[12px] font-bold">
              Update Savings Goal
            </button>
          </div>
        </div>
      </div>

      {/* Dialogs */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingTransaction?.id ? 'Edit Expense' : 'Add Expense'}</DialogTitle>
            <DialogDescription>
              {editingTransaction?.id ? 'Update the details of your expense record.' : 'Create a new outgoing transaction record.'}
            </DialogDescription>
          </DialogHeader>
          {editingTransaction && (
            <TransactionForm
              initialData={editingTransaction}
              onSuccess={handleCloseModal}
              onCancel={handleCloseModal}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <ConfirmDialog
        open={!!transactionToDelete}
        onCancel={() => setTransactionToDelete(null)}
        onConfirm={() => deleteMutation.mutate(transactionToDelete?.id)}
        title="Delete Expense Record"
        description="Are you sure you want to delete this expense transaction? This will also revert the balance deduction on the associated bank account."
        confirmLabel={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        variant="danger"
      />
    </div>
  )
}
