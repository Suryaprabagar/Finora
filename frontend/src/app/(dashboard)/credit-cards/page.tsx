'use client'

import { useQuery } from '@tanstack/react-query'
import { creditCardsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency } from '@/lib/utils'

export default function CreditCardsPage() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['credit-cards'],
    queryFn: () => creditCardsApi.list().then(r => r.data),
  })

  const cards = res?.data || []
  const totalOutstanding = cards.reduce((acc, curr) => acc + curr.outstanding_balance, 0)
  const totalLimit = cards.reduce((acc, curr) => acc + curr.credit_limit, 0)

  return (
    <div>
      <PageHeader
        title="Credit Cards"
        subtitle="Manage your credit cards and track outstanding balances"
        actions={
          <button className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Card
          </button>
        }
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <StatCard
          title="Total Outstanding"
          value={formatCurrency(totalOutstanding)}
          loading={isLoading}
          icon="credit_card"
          iconBg="bg-error-container"
        />
        <StatCard
          title="Total Credit Limit"
          value={formatCurrency(totalLimit)}
          loading={isLoading}
          icon="account_balance_wallet"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="finora-card p-6 h-48 animate-pulse bg-surface-variant/30"></div>
          ))
        ) : cards.length > 0 ? (
          cards.map((card) => (
            <div key={card.id} className="finora-card p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="font-medium text-lg">{card.bank_name}</h4>
                  <p className="text-sm text-on-surface-variant">{card.name} •••• {card.card_number?.slice(-4)}</p>
                </div>
              </div>
              <div className="mb-4">
                <p className="text-xs text-on-surface-variant mb-1">Outstanding Balance</p>
                <p className="text-2xl font-display font-bold text-error">{formatCurrency(card.outstanding_balance)}</p>
              </div>
              <div className="w-full h-2 bg-surface-variant rounded-full overflow-hidden mb-2">
                <div 
                  className="h-full bg-primary" 
                  style={{ width: `${Math.min((card.outstanding_balance / card.credit_limit) * 100, 100)}%` }}
                ></div>
              </div>
              <p className="text-xs text-on-surface-variant text-right">Limit: {formatCurrency(card.credit_limit)}</p>
            </div>
          ))
        ) : (
          <div className="col-span-full finora-card p-12 text-center">
            <p>No credit cards added yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}
