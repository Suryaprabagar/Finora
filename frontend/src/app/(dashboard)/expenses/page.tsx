'use client'

import { useQuery } from '@tanstack/react-query'
import { expensesApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { DonutChart } from '@/components/shared/charts/DonutChart'
import { formatCurrency } from '@/lib/utils'

export default function ExpensesPage() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['expenses-summary'],
    queryFn: () => expensesApi.getSummary().then(r => r.data),
  })

  const summary = res?.data

  return (
    <div>
      <PageHeader
        title="Expenses"
        subtitle="Monitor your spending habits"
        actions={
          <button className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Expense
          </button>
        }
      />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Total Expenses (This Month)"
          value={summary ? formatCurrency(summary.total_month) : '₹0'}
          loading={isLoading}
          icon="trending_down"
          iconBg="bg-error-container"
        />
        <StatCard
          title="Top Category"
          value={summary?.top_category?.name || '-'}
          subtitle={summary ? formatCurrency(summary.top_category?.amount || 0) : ''}
          loading={isLoading}
          icon="category"
        />
        <StatCard
          title="Daily Average"
          value={summary ? formatCurrency(summary.daily_average) : '₹0'}
          loading={isLoading}
          icon="today"
        />
      </div>
      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6">Expenses by Category</h3>
        {isLoading ? (
          <div className="h-[300px] animate-pulse bg-surface-variant/30 rounded-lg"></div>
        ) : (
          <DonutChart
            data={summary?.by_category || []}
            centerLabel="Total"
            centerValue={summary ? formatCurrency(summary.total_month) : '₹0'}
          />
        )}
      </div>
    </div>
  )
}
