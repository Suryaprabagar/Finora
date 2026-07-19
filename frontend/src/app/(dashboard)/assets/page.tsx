'use client'

import { useQuery } from '@tanstack/react-query'
import { assetsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency } from '@/lib/utils'

export default function AssetsPage() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['assets-summary'],
    queryFn: () => assetsApi.getSummary().then(r => r.data),
  })

  const summary = res?.data

  return (
    <div>
      <PageHeader
        title="Assets"
        subtitle="Keep track of your valuable possessions"
        actions={
          <button className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Asset
          </button>
        }
      />
      <div className="mb-8">
        <StatCard
          title="Total Assets Value"
          value={summary ? formatCurrency(summary.total_value) : '₹0'}
          loading={isLoading}
          icon="home_work"
        />
      </div>
      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6">Your Assets</h3>
        <p className="text-on-surface-variant">Assets list goes here</p>
      </div>
    </div>
  )
}
