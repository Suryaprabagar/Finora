'use client'

import { useQuery } from '@tanstack/react-query'
import { loansApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency } from '@/lib/utils'

export default function LoansPage() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['loans-summary'],
    queryFn: () => loansApi.getSummary().then(r => r.data),
  })

  const summary = res?.data

  return (
    <div>
      <PageHeader
        title="Loans"
        subtitle="Manage your debts and EMIs"
        actions={
          <button className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Loan
          </button>
        }
      />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <StatCard
          title="Total Outstanding Debt"
          value={summary ? formatCurrency(summary.total_outstanding) : '₹0'}
          loading={isLoading}
          icon="handshake"
          iconBg="bg-error-container"
        />
        <StatCard
          title="Total Monthly EMI"
          value={summary ? formatCurrency(summary.total_emi) : '₹0'}
          loading={isLoading}
          icon="calendar_month"
        />
      </div>
      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6">Active Loans</h3>
        <p className="text-on-surface-variant">Loans list goes here</p>
      </div>
    </div>
  )
}
