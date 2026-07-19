'use client'

import { useQuery } from '@tanstack/react-query'
import { billsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency } from '@/lib/utils'

export default function BillsPage() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['bills-summary'],
    queryFn: () => billsApi.getSummary().then(r => r.data),
  })

  const summary = res?.data

  return (
    <div>
      <PageHeader
        title="Bills"
        subtitle="Never miss a payment"
        actions={
          <button className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Bill
          </button>
        }
      />
      <div className="mb-8">
        <StatCard
          title="Upcoming Bills (This Month)"
          value={summary ? formatCurrency(summary.total_upcoming) : '₹0'}
          loading={isLoading}
          icon="calendar_month"
          iconBg="bg-secondary-fixed"
        />
      </div>
      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6">Your Bills</h3>
        <p className="text-on-surface-variant">Bills list goes here</p>
      </div>
    </div>
  )
}
