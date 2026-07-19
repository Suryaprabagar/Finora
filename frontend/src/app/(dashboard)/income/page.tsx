'use client'

import { useQuery } from '@tanstack/react-query'
import { incomeApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { BarChart } from '@/components/shared/charts/BarChart'
import { formatCurrency } from '@/lib/utils'

export default function IncomePage() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['income-summary'],
    queryFn: () => incomeApi.getSummary().then(r => r.data),
  })

  const summary = res?.data

  return (
    <div>
      <PageHeader
        title="Income"
        subtitle="Track your incoming cash flow"
        actions={
          <button className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Income
          </button>
        }
      />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Total Income (This Month)"
          value={summary ? formatCurrency(summary.total_month) : '₹0'}
          loading={isLoading}
          icon="trending_up"
          iconBg="bg-tertiary-fixed"
        />
        <StatCard
          title="Average Monthly"
          value={summary ? formatCurrency(summary.average_monthly) : '₹0'}
          loading={isLoading}
          icon="calculate"
        />
        <StatCard
          title="Projected (Yearly)"
          value={summary ? formatCurrency(summary.projected_yearly) : '₹0'}
          loading={isLoading}
          icon="event"
        />
      </div>
      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6">Income Trend</h3>
        {isLoading ? (
          <div className="h-[300px] animate-pulse bg-surface-variant/30 rounded-lg"></div>
        ) : (
          <BarChart
            data={summary?.trend || []}
            xKey="month"
            bars={[{ key: 'amount', label: 'Income', color: 'var(--tertiary)' }]}
          />
        )}
      </div>
    </div>
  )
}
