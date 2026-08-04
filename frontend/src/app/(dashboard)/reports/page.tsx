'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { createColumnHelper } from '@tanstack/react-table'
import { format } from 'date-fns'
import { 
  BarChart, Bar, Tooltip, ResponsiveContainer, Cell,
  AreaChart, Area
} from 'recharts'
import { analyticsApi, reportsApi } from '@/lib/api'
import { formatCurrency, formatCompact } from '@/lib/utils'

export default function ReportsPage() {
  const [incomePeriod, setIncomePeriod] = useState<'Yearly' | 'Monthly'>('Monthly')

  // Fetch Reports Data
  const { data: analytics } = useQuery({
    queryKey: ['reports-analytics'],
    queryFn: analyticsApi.getReports
  })

  // Fetch Generated Reports list
  const { data: reportsRes } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsApi.list()
  })

  // Fallback Data based on real payload structure
  const incomeData = analytics?.income || []
  const expensesData = analytics?.expenses || []
  const budgetData = analytics?.budget || { budget: 0, actual: 0, variance: 0 }
  const cashFlowData = analytics?.cashflow || []
  const investmentsData = analytics?.investments || { allocation: {}, sharpe_ratio: null, volatility: null }
  const netWorthGrowthPct: number | null = analytics?.net_worth_growth_pct ?? null
  const reports = reportsRes?.data?.data || []

  const columnHelper = createColumnHelper<any>()
  const columns = [
    columnHelper.accessor('name', {
      header: 'Report Name',
      cell: info => (
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-on-surface-variant text-[20px]">
            {info.row.original.formats.includes('EXCEL') || info.row.original.formats.includes('CSV') ? 'table_chart' : 'description'}
          </span>
          <span className="font-semibold text-[#1f1b18]">{info.getValue()}</span>
        </div>
      )
    }),
    columnHelper.accessor('date', {
      header: 'Date',
      cell: info => <span className="text-on-surface-variant">{format(new Date(info.getValue()), 'MMM dd, yyyy')}</span>
    }),
    columnHelper.accessor('period', {
      header: 'Period',
      cell: info => <span className="text-on-surface-variant">{info.getValue()}</span>
    }),
    columnHelper.accessor('formats', {
      header: 'Format',
      cell: info => (
        <div className="flex gap-2">
          {info.getValue()?.map?.((f: string) => (
            <span key={f} className="text-[10px] font-bold px-2 py-1 bg-surface-variant/50 text-[#5d4037] rounded uppercase">
              {f}
            </span>
          ))}
        </div>
      )
    }),
    columnHelper.display({
      id: 'actions',
      header: 'Actions',
      cell: () => (
        <div className="flex items-center gap-4 text-on-surface-variant">
          <button className="hover:text-primary transition-colors"><span className="material-symbols-outlined text-[18px]">picture_as_pdf</span></button>
          <button className="hover:text-primary transition-colors"><span className="material-symbols-outlined text-[18px]">grid_on</span></button>
          <button className="hover:text-primary transition-colors"><span className="material-symbols-outlined text-[18px]">data_object</span></button>
        </div>
      )
    })
  ]

  return (
    <div className="max-w-7xl mx-auto pb-12">
      <PageHeader
        title="Reports & Analytics"
        subtitle=""
      />
      
      {/* Search Header Area */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center -mt-16 mb-8 relative z-10 w-full md:w-auto md:ml-auto md:max-w-md">
         <div className="relative w-full">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[18px]">search</span>
            <input 
              type="text" 
              placeholder="Search reports..."
              className="w-full bg-[#f6ece4] border-none rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-1 focus:ring-primary/30 outline-none"
            />
         </div>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="finora-card p-5">
          <div className="flex justify-between items-start mb-4">
            <span className="text-xs font-bold tracking-wider text-on-surface-variant uppercase">Monthly Reports</span>
            <span className="material-symbols-outlined text-on-surface-variant text-[18px]">calendar_month</span>
          </div>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-3xl font-display font-bold text-[#1f1b18]">{reports.length}</span>
            <span className="text-sm text-on-surface-variant">Generated</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-[#5d4037] font-medium">
            <span className="material-symbols-outlined text-[14px]">trending_up</span>
            +2 from last period
          </div>
        </div>

        <div className="finora-card p-5">
          <div className="flex justify-between items-start mb-4">
            <span className="text-xs font-bold tracking-wider text-on-surface-variant uppercase">Annual Reports</span>
            <span className="material-symbols-outlined text-on-surface-variant text-[18px]">bar_chart</span>
          </div>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-3xl font-display font-bold text-[#1f1b18]">{new Date().getFullYear()}</span>
            <span className="text-sm text-on-surface-variant">Full Year</span>
          </div>
          <p className="text-xs text-on-surface-variant mt-1">Audited & Finalized</p>
        </div>

        <div className="finora-card p-5">
          <div className="flex justify-between items-start mb-4">
            <span className="text-xs font-bold tracking-wider text-on-surface-variant uppercase">Cash Flow Summary</span>
            <span className="material-symbols-outlined text-on-surface-variant text-[18px]">account_balance_wallet</span>
          </div>
          <div className="mb-1">
            <span className="text-2xl font-display font-bold text-[#1f1b18]">{formatCompact(cashFlowData.reduce((acc: number, cur: any) => acc + cur.value, 0))}</span>
          </div>
          <p className="text-xs text-on-surface-variant mt-1">Net Surplus</p>
        </div>

        <div className="finora-card p-5">
          <div className="flex justify-between items-start mb-4">
            <span className="text-xs font-bold tracking-wider text-on-surface-variant uppercase">Net Worth Growth</span>
            <span className="material-symbols-outlined text-on-surface-variant text-[18px]">show_chart</span>
          </div>
          <div className="mb-1">
            {netWorthGrowthPct !== null ? (
              <span className={`text-2xl font-display font-bold ${netWorthGrowthPct >= 0 ? 'text-[#5d4037]' : 'text-error'}`}>
                {netWorthGrowthPct >= 0 ? '+' : ''}{netWorthGrowthPct}%
              </span>
            ) : (
              <span className="text-2xl font-display font-bold text-on-surface-variant">N/A</span>
            )}
          </div>
          <p className="text-xs text-on-surface-variant mt-1">{netWorthGrowthPct !== null ? 'Portfolio Growth' : 'No snapshot data yet'}</p>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        
        {/* Income Performance (spans 2 cols) */}
        <div className="finora-card p-6 md:col-span-2 border border-outline-variant/30">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase">Income Performance</h3>
            <div className="flex bg-[#f6ece4] rounded-full p-1">
              <button 
                className={`px-4 py-1 rounded-full text-xs font-semibold transition-colors ${incomePeriod === 'Yearly' ? 'bg-[#795548] text-white' : 'text-[#5d4037]'}`}
                onClick={() => setIncomePeriod('Yearly')}
              >
                Yearly
              </button>
              <button 
                className={`px-4 py-1 rounded-full text-xs font-semibold transition-colors ${incomePeriod === 'Monthly' ? 'bg-[#795548] text-white' : 'text-[#5d4037]'}`}
                onClick={() => setIncomePeriod('Monthly')}
              >
                Monthly
              </button>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={incomeData}>
                <Tooltip cursor={{fill: 'transparent'}} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {incomeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={index === 4 ? '#8d6e63' : '#e7d8c9'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Expenses Breakdown */}
        <div className="finora-card p-6 flex flex-col justify-between border border-outline-variant/30">
          <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase mb-6">Expenses Breakdown</h3>
          
          <div className="space-y-6 flex-grow">
            {expensesData.map((e: any, index: number) => {
              const colors = ['#5d4037', '#e3ae97', '#8d6e63', '#a1887f', '#d7ccc8']
              const color = colors[index % colors.length]
              return (
                <div key={e.name}>
                  <div className="flex justify-between text-sm font-semibold mb-2">
                    <span className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: color}}></div>{e.name}</span>
                    <span>{e.percentage}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-variant/30 rounded-full overflow-hidden">
                    <div className="h-full" style={{ width: `${e.percentage}%`, backgroundColor: color }}></div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

      </div>

      {/* Lower Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        
        {/* Budget vs Actual */}
        <div className="finora-card p-6 flex flex-col justify-between h-72 border border-outline-variant/30">
          <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase">Budget vs Actual</h3>
          <div className="relative h-24 my-6 flex items-end justify-start">
             <div className="absolute left-0 bottom-4 h-16 bg-[#ebdcd0]" style={{ width: `${Math.min(100, (budgetData.budget / Math.max(budgetData.budget, budgetData.actual)) * 100)}%` }}></div>
             <div className="absolute left-0 bottom-4 h-8 bg-[#d8c2b5] z-10 border-t border-r border-[#ebdcd0]/50" style={{ width: `${Math.min(100, (budgetData.actual / Math.max(budgetData.budget, budgetData.actual)) * 100)}%` }}></div>
          </div>
          <div>
            <p className="text-xs text-on-surface-variant mb-1">Variance</p>
            <div className="flex justify-between items-center">
              <span className="text-2xl font-display font-bold text-[#5d4037]">{formatCurrency(budgetData.variance)}</span>
              {budgetData.variance < 0 && <span className="text-[10px] font-bold px-2 py-0.5 bg-error-container text-error rounded capitalize">OVER BUDGET</span>}
            </div>
          </div>
        </div>

        {/* Cash Flow Trends */}
        <div className="finora-card p-6 flex flex-col justify-between h-72 border border-outline-variant/30">
          <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase">Cash Flow Trends</h3>
          <div className="h-32 -mx-2 my-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cashFlowData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#e7d8c9" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#e7d8c9" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="value" stroke="#8d6e63" strokeWidth={4} fillOpacity={1} fill="url(#colorValue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-[#5d4037] font-medium leading-relaxed">Stable positive cash flow maintained for 6 months.</p>
        </div>

        {/* Investment Performance */}
        <div className="finora-card p-6 flex flex-col h-72 border border-outline-variant/30">
          <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase mb-8">Investment Performance</h3>
          
          <div className="mb-8">
            <p className="text-xs font-semibold text-on-surface-variant mb-3">Current Allocation</p>
            <div className="h-3 w-full bg-[#ebdcd0] rounded-full overflow-hidden flex">
              {Object.entries(investmentsData.allocation).map(([key, val]: [string, any], index) => {
                const colors = ['#795548', '#d7ccc8', '#e3ae97', '#a1887f']
                return (
                  <div key={key} className="h-full" style={{ width: `${val}%`, backgroundColor: colors[index % colors.length] }}></div>
                )
              })}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-auto">
             <div className="bg-[#f6ece4] p-4 rounded-xl text-center">
                <p className="text-[10px] font-bold tracking-wider text-on-surface-variant uppercase mb-1">Sharpe Ratio</p>
                <p className="text-xl font-display font-semibold text-[#1f1b18]">
                  {investmentsData.sharpe_ratio !== null && investmentsData.sharpe_ratio !== undefined ? investmentsData.sharpe_ratio : 'N/A'}
                </p>
             </div>
             <div className="bg-[#f6ece4] p-4 rounded-xl text-center">
                <p className="text-[10px] font-bold tracking-wider text-on-surface-variant uppercase mb-1">Volatility</p>
                <p className="text-xl font-display font-semibold text-[#1f1b18]">
                  {investmentsData.volatility !== null && investmentsData.volatility !== undefined ? `${investmentsData.volatility}%` : 'N/A'}
                </p>
             </div>
          </div>
        </div>
      </div>

      {/* Report Library */}
      <div className="finora-card overflow-hidden">
        <div className="p-6 border-b border-outline-variant flex flex-col md:flex-row justify-between items-start md:items-center">
          <div>
            <h3 className="text-xs font-bold tracking-wider text-[#1f1b18] uppercase">Report Library</h3>
            <p className="text-xs text-on-surface-variant mt-1">Access and download your historical financial records.</p>
          </div>
          <button className="mt-4 md:mt-0 flex items-center gap-2 bg-[#795548] hover:bg-[#5d4037] text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Generate Custom Report
          </button>
        </div>
        
        <DataTable columns={columns} data={reports} />
      </div>

    </div>
  )
}
