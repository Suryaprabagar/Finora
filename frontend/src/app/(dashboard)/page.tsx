'use client'

import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/lib/api/dashboard'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { AreaChart } from '@/components/shared/charts/AreaChart'
import { DonutChart } from '@/components/shared/charts/DonutChart'
import { formatCurrency, formatCompact, getStatusClass, formatDate } from '@/lib/utils'
import { EmptyState } from '@/components/shared/EmptyState'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function DashboardPage() {
  const router = useRouter()
  const { data: res, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.get().then(r => r.data),
  })

  const dashboardData = res?.data

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Here's an overview of your financial status"
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Net Worth"
          value={dashboardData ? formatCurrency(dashboardData.net_worth) : '₹0'}
          loading={isLoading}
          icon="account_balance_wallet"
          iconBg="bg-primary-fixed"
          href="/assets"
        />
        <StatCard
          title="Cash Balance"
          value={dashboardData ? formatCurrency(dashboardData.cash_balance) : '₹0'}
          loading={isLoading}
          icon="payments"
          iconBg="bg-secondary-fixed"
          href="/bank-accounts"
        />
        <StatCard
          title="Monthly Income"
          value={dashboardData ? formatCurrency(dashboardData.monthly_income) : '₹0'}
          loading={isLoading}
          icon="trending_up"
          iconBg="bg-tertiary-fixed"
          href="/transactions"
        />
        <StatCard
          title="Monthly Expenses"
          value={dashboardData ? formatCurrency(dashboardData.monthly_expenses) : '₹0'}
          loading={isLoading}
          icon="trending_down"
          iconBg="bg-error-container"
          href="/transactions"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Cash Flow Chart */}
        <div className="lg:col-span-2 finora-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-display font-bold text-lg text-on-surface">Cash Flow</h3>
          </div>
          {isLoading ? (
            <div className="h-[300px] bg-surface-variant/30 rounded-lg animate-pulse" />
          ) : dashboardData?.cash_flow && dashboardData.cash_flow.length > 0 ? (
            <AreaChart
              data={dashboardData.cash_flow as any}
              xKey="month"
              areas={[
                { key: 'income', label: 'Income', color: 'var(--tertiary)' },
                { key: 'expenses', label: 'Expenses', color: 'var(--error)' }
              ]}
              height={300}
            />
          ) : (
            <EmptyState title="No cash flow data" description="Add some transactions to see your cash flow." />
          )}
        </div>

        {/* Asset Allocation */}
        <div className="finora-card p-6 flex flex-col">
          <h3 className="font-display font-bold text-lg text-on-surface mb-6">Asset Allocation</h3>
          <div className="flex-1">
            {isLoading ? (
              <div className="h-[300px] flex items-center justify-center">
                <div className="w-48 h-48 rounded-full border-8 border-surface-variant/30 animate-pulse" />
              </div>
            ) : dashboardData?.asset_allocation && dashboardData.asset_allocation.length > 0 ? (
              <DonutChart
                data={dashboardData.asset_allocation.map(a => ({
                  name: a.type,
                  value: a.value,
                  // Auto assign colors based on index/type if backend doesn't provide
                  color: a.type === 'Cash' ? 'var(--secondary)' : a.type === 'Investments' ? 'var(--tertiary)' : 'var(--primary)'
                }))}
                height={300}
                centerLabel="Total Assets"
                centerValue={formatCompact(dashboardData.asset_allocation.reduce((sum, a) => sum + a.value, 0))}
              />
            ) : (
              <EmptyState title="No assets" icon="pie_chart" />
            )}
          </div>
        </div>
      </div>

      {/* Recent Transactions & Upcoming Bills */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="finora-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-bold text-lg text-on-surface">Recent Transactions</h3>
            <Link href="/transactions" className="text-sm font-medium text-primary hover:text-primary-container">View All</Link>
          </div>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="flex justify-between items-center py-2">
                  <div className="flex items-center gap-3"><div className="w-10 h-10 rounded-full bg-surface-variant animate-pulse" /><div className="w-24 h-4 bg-surface-variant rounded animate-pulse" /></div>
                  <div className="w-16 h-4 bg-surface-variant rounded animate-pulse" />
                </div>
              ))}
            </div>
          ) : dashboardData?.recent_transactions && dashboardData.recent_transactions.length > 0 ? (
            <div className="divide-y divide-outline-variant">
              {dashboardData.recent_transactions.slice(0, 5).map((t) => (
                <div key={t.id} onClick={() => router.push('/transactions')} className="py-3 flex items-center justify-between hover:bg-surface-variant/20 transition-colors -mx-2 px-2 rounded-lg cursor-pointer">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-surface-variant flex items-center justify-center shrink-0 text-on-surface-variant">
                      <span className="material-symbols-outlined text-[20px]">
                        {t.type === 'income' ? 'arrow_downward' : t.type === 'expense' ? 'arrow_upward' : 'swap_horiz'}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-sm text-on-surface">{t.description}</p>
                      <p className="text-xs text-on-surface-variant">{formatDate(t.date)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-medium text-sm ${t.type === 'income' ? 'text-tertiary' : 'text-on-surface'}`}>
                      {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                    </p>
                    <span className={getStatusClass(t.status)}>{t.status}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState 
              title="No recent transactions" 
              icon="receipt_long" 
              action={{ label: "Go to Transactions", onClick: () => router.push('/transactions') }}
            />
          )}
        </div>

        <div className="finora-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-bold text-lg text-on-surface">Upcoming Bills</h3>
            <Link href="/bills" className="text-sm font-medium text-primary hover:text-primary-container">View All</Link>
          </div>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex justify-between items-center py-2">
                  <div className="flex items-center gap-3"><div className="w-10 h-10 rounded bg-surface-variant animate-pulse" /><div className="w-24 h-4 bg-surface-variant rounded animate-pulse" /></div>
                  <div className="w-16 h-4 bg-surface-variant rounded animate-pulse" />
                </div>
              ))}
            </div>
          ) : dashboardData?.upcoming_bills && dashboardData.upcoming_bills.length > 0 ? (
             <div className="space-y-3">
              {dashboardData.upcoming_bills.slice(0, 4).map((b) => (
                <div key={b.id} onClick={() => router.push('/bills')} className="p-3 border border-outline-variant rounded-lg flex justify-between items-center bg-surface-container-lowest hover:border-primary transition-colors cursor-pointer">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-error-container/30 text-error flex items-center justify-center">
                      <span className="material-symbols-outlined text-[20px]">{b.icon || 'receipt'}</span>
                    </div>
                    <div>
                      <p className="font-medium text-sm text-on-surface">{b.name}</p>
                      <p className="text-xs text-error font-medium">Due in {b.due_day} days</p>
                    </div>
                  </div>
                  <p className="font-bold text-sm text-on-surface">{formatCurrency(b.amount)}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState 
              title="No upcoming bills" 
              icon="event" 
              action={{ label: "Manage Bills", onClick: () => router.push('/bills') }}
            />
          )}
        </div>
      </div>
    </div>
  )
}
