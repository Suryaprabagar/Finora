'use client'

import { useQuery } from '@tanstack/react-query'
import { goalsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { formatCurrency } from '@/lib/utils'

export default function GoalsPage() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['goals-summary'],
    queryFn: () => goalsApi.getSummary().then(r => r.data),
  })

  return (
    <div>
      <PageHeader
        title="Goals"
        subtitle="Track your financial goals"
        actions={
          <button className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            New Goal
          </button>
        }
      />
      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6">Your Goals</h3>
        {isLoading ? (
          <div className="h-32 animate-pulse bg-surface-variant/30 rounded-lg"></div>
        ) : (
          <p className="text-on-surface-variant">Goals list goes here</p>
        )}
      </div>
    </div>
  )
}
