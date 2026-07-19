'use client'

import { useQuery } from '@tanstack/react-query'
import { insuranceApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency } from '@/lib/utils'

export default function InsurancePage() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['insurance-summary'],
    queryFn: () => insuranceApi.getSummary().then(r => r.data),
  })

  const summary = res?.data

  return (
    <div>
      <PageHeader
        title="Insurance"
        subtitle="Manage your insurance policies"
        actions={
          <button className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Policy
          </button>
        }
      />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <StatCard
          title="Total Coverage"
          value={summary ? formatCurrency(summary.total_coverage) : '₹0'}
          loading={isLoading}
          icon="shield"
          iconBg="bg-tertiary-fixed"
        />
        <StatCard
          title="Total Annual Premium"
          value={summary ? formatCurrency(summary.total_premium) : '₹0'}
          loading={isLoading}
          icon="payments"
        />
      </div>
      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6">Active Policies</h3>
        <p className="text-on-surface-variant">Policies list goes here</p>
      </div>
    </div>
  )
}
