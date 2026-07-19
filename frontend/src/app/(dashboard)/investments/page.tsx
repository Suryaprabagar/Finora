'use client'

import { useQuery } from '@tanstack/react-query'
import { investmentsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency } from '@/lib/utils'

export default function InvestmentsPage() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['investments-summary'],
    queryFn: () => investmentsApi.getSummary().then(r => r.data),
  })

  const summary = res?.data

  return (
    <div>
      <PageHeader
        title="Investments"
        subtitle="Track your portfolio performance"
        actions={
          <button className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Investment
          </button>
        }
      />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Total Portfolio Value"
          value={summary ? formatCurrency(summary.total_value) : '₹0'}
          loading={isLoading}
          icon="show_chart"
          iconBg="bg-tertiary-fixed"
        />
        <StatCard
          title="Total Invested"
          value={summary ? formatCurrency(summary.total_invested) : '₹0'}
          loading={isLoading}
          icon="savings"
        />
        <StatCard
          title="Total Returns"
          value={summary ? formatCurrency(summary.total_returns) : '₹0'}
          trend={{ value: summary?.returns_percentage || 0, label: 'returns' }}
          loading={isLoading}
          icon="trending_up"
        />
      </div>
      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6">Investment Holdings</h3>
        <p className="text-on-surface-variant">Table goes here</p>
      </div>
    </div>
  )
}
