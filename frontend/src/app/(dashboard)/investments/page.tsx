'use client'

import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { investmentsApi, analyticsApi } from '@/lib/api'

import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { InvestmentForm } from '@/components/features/investments/InvestmentForm'
import { InvestmentTradeForm } from '@/components/features/investments/InvestmentTradeForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'

export default function InvestmentsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isTradeModalOpen, setIsTradeModalOpen] = useState(false)
  const [editingInvestment, setEditingInvestment] = useState<any>(null)
  const [investmentToTrade, setInvestmentToTrade] = useState<any>(null)
  const [investmentToDelete, setInvestmentToDelete] = useState<any>(null)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout>>(null)

  useEffect(() => {
    return () => {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    }
  }, [])

  const queryClient = useQueryClient()

  // staleTime: serve cached data on re-visits without re-fetching.
  // gcTime: keep data in cache for 10 min even when no component is mounted.
  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['investments-summary'],
    queryFn: () => investmentsApi.getSummary().then(r => r.data),
    staleTime: 2 * 60 * 1000,   // 2 min — page loads instantly on re-visit
    gcTime:   10 * 60 * 1000,   // keep in cache 10 min
  })

  const { data: analyticsRes, isLoading: isAnalyticsLoading } = useQuery({
    queryKey: ['analyticsDashboard'],
    queryFn: () => analyticsApi.getDashboard(),
    staleTime: 5 * 60 * 1000,   // 5 min — analytics is the heaviest query
    gcTime:   10 * 60 * 1000,
  })

  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['investments'],
    queryFn: () => investmentsApi.list().then(r => r.data),
    staleTime: 2 * 60 * 1000,
    gcTime:   10 * 60 * 1000,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => investmentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      queryClient.invalidateQueries({ queryKey: ['investments-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['analyticsDashboard'] })
      toast.success('Investment deleted successfully')
      setInvestmentToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete investment')
    }
  })

  const syncMutation = useMutation({
    mutationFn: () => investmentsApi.sync(),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      queryClient.invalidateQueries({ queryKey: ['investments-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['analyticsDashboard'] })
      toast.success(res.data?.message || 'Market data synced successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to sync market data')
    }
  })

  const summary = summaryRes?.data || { total_value: 0, total_invested: 0, total_returns: 0, returns_percentage: 0, total_gain_loss: 0, total_gain_loss_pct: 0 }
  const investments = listRes?.data || []
  const analytics = analyticsRes || null

  // Calculate Today's Gain from growth history if available
  let todayGain = 0
  let todayGainPct = 0
  if (analytics?.growth_history && analytics.growth_history.length >= 2) {
    const last = analytics.growth_history[analytics.growth_history.length - 1]
    const prev = analytics.growth_history[analytics.growth_history.length - 2]
    todayGain = last.value - prev.value
    todayGainPct = prev.value > 0 ? (todayGain / prev.value) * 100 : 0
  }

  const handleAdd = () => {
    setEditingInvestment(null)
    setIsModalOpen(true)
  }

  const handleEdit = (investment: any) => {
    setEditingInvestment(investment)
    setIsModalOpen(true)
  }

  const handleTrade = (investment: any) => {
    setInvestmentToTrade(investment)
    setIsTradeModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    closeTimerRef.current = setTimeout(() => setEditingInvestment(null), 200)
  }

  const handleCloseTradeModal = () => {
    setIsTradeModalOpen(false)
    closeTimerRef.current = setTimeout(() => setInvestmentToTrade(null), 200)
  }

  return (
      <div className="space-y-8 pb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* PAGE HEADER */}
      <div className="flex justify-between items-end mb-8">
        <div>
          <h2 className="text-3xl font-display text-primary font-bold tracking-tight">Investment Portfolio</h2>
          <p className="text-on-surface-variant mt-2 text-sm font-medium">Real-time overview of your stewardship assets and market performance.</p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => syncMutation.mutate()} 
            disabled={syncMutation.isPending}
            className="px-4 py-2 border border-outline-variant text-on-surface font-semibold text-sm rounded-lg hover:bg-surface-container-low transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <span className={`material-symbols-outlined text-[18px] ${syncMutation.isPending ? 'animate-spin' : ''}`}>sync</span>
            {syncMutation.isPending ? 'Syncing...' : 'Sync Market Data'}
          </button>
          <button onClick={handleAdd} className="px-4 py-2 bg-primary text-on-primary font-semibold text-sm rounded-lg hover:opacity-90 transition-all flex items-center gap-2 shadow-sm">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Trade Asset
          </button>
        </div>
      </div>

      {/* SUMMARY CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
        {/* Portfolio Value */}
        <div className="editorial-card p-6 rounded-xl lg:col-span-2 md:col-span-2">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-2">Portfolio Value</p>
          <p className="text-3xl font-display text-primary font-bold">{formatCurrency(summary.total_value)}</p>
        </div>
        
        {/* Today's Gain */}
        <div className="editorial-card p-6 rounded-xl">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-2">Today's Gain</p>
          <div className="flex flex-col mt-1">
            <p className={`text-xl font-bold ${todayGain >= 0 ? 'text-[#2e7d32]' : 'text-error'}`}>
              {todayGain >= 0 ? '+' : ''}{formatCurrency(todayGain)}
            </p>
            <p className={`text-sm font-semibold mt-0.5 ${todayGain >= 0 ? 'text-[#2e7d32]' : 'text-error'}`}>
              ({todayGain >= 0 ? '+' : ''}{todayGainPct.toFixed(2)}%)
            </p>
          </div>
        </div>
        
        {/* Total Gain */}
        <div className="editorial-card p-6 rounded-xl">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-2">Total Gain</p>
          <p className={`text-xl font-bold mt-1 ${(summary.total_gain_loss || 0) >= 0 ? 'text-[#2e7d32]' : 'text-error'}`}>
            {(summary.total_gain_loss || 0) >= 0 ? '+' : ''}{formatCurrency(summary.total_gain_loss || 0)}
          </p>
        </div>
        
        {/* Annual Return */}
        <div className="editorial-card p-6 rounded-xl">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-2">Total Return %</p>
          <p className={`text-xl font-bold mt-1 ${(summary.total_gain_loss_pct || 0) >= 0 ? 'text-[#2e7d32]' : 'text-error'}`}>
            {(summary.total_gain_loss_pct || 0) >= 0 ? '+' : ''}{(summary.total_gain_loss_pct || 0).toFixed(2)}%
          </p>
        </div>
        
      </div>

      {/* ANALYTICS SECTION */}
      {isAnalyticsLoading ? (
        <div className="flex justify-center items-center h-40">
          <p className="text-on-surface-variant animate-pulse">Loading Analytics Dashboard...</p>
        </div>
      ) : (
      <div className="grid grid-cols-12 gap-6">
        {/* Portfolio Growth */}
        <div className="col-span-12 lg:col-span-8 editorial-card p-6 rounded-xl relative overflow-hidden flex flex-col">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-1">Portfolio Growth</p>
              <h3 className="text-lg font-bold text-on-surface">Wealth Appreciation</h3>
            </div>
          </div>
          <div className="flex-1 w-full relative min-h-[220px]">
            {analytics?.growth_history && analytics.growth_history.length > 0 ? (() => {
              const pts = analytics.growth_history
              const W = 800, H = 200, PAD = 10
              const minV = Math.min(...pts.map((p: any) => p.value))
              const maxV = Math.max(...pts.map((p: any) => p.value))
              const range = maxV - minV || 1
              const coords = pts.map((p: any, i: number) => ({
                x: (i / Math.max(pts.length - 1, 1)) * W,
                y: PAD + (1 - (p.value - minV) / range) * (H - PAD * 2)
              }))
              const linePath = coords.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' ')
              const fillPath = `${linePath} L${W},${H} L0,${H} Z`
              // Show up to 7 evenly spaced date labels
              const labelIdxs = pts.length <= 7
                ? pts.map((_: any, i: number) => i)
                : [0, Math.round(pts.length * 0.17), Math.round(pts.length * 0.33), Math.round(pts.length * 0.5), Math.round(pts.length * 0.67), Math.round(pts.length * 0.83), pts.length - 1]
              return (
                <svg className="w-full h-full absolute inset-0" preserveAspectRatio="none" viewBox={`0 0 ${W} ${H}`}>
                  <defs>
                    <linearGradient id="wealthGradient" x1="0%" x2="0%" y1="0%" y2="100%">
                      <stop offset="0%" style={{ stopColor: 'rgba(139, 94, 60, 0.25)' }} />
                      <stop offset="100%" style={{ stopColor: 'rgba(139, 94, 60, 0)' }} />
                    </linearGradient>
                  </defs>
                  <path d={fillPath} fill="url(#wealthGradient)" />
                  <path d={linePath} fill="none" stroke="#8B5E3C" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                  {coords.map((c, i) => (
                    <circle key={i} cx={c.x} cy={c.y} r="3" fill="#8B5E3C" opacity="0.7" />
                  ))}
                </svg>
              )
            })() : (
              <div className="flex items-center justify-center h-full text-sm text-on-surface-variant">
                No growth history available yet.
              </div>
            )}
            <div className="absolute bottom-0 left-0 right-0 flex justify-between text-[10px] text-on-surface-variant px-2 pt-4 font-bold uppercase tracking-wider">
              {analytics?.growth_history?.length > 0 && (() => {
                const pts = analytics.growth_history
                const labelIdxs = pts.length <= 7
                  ? pts.map((_: any, i: number) => i)
                  : [0, Math.round(pts.length * 0.17), Math.round(pts.length * 0.33), Math.round(pts.length * 0.5), Math.round(pts.length * 0.67), Math.round(pts.length * 0.83), pts.length - 1]
                return labelIdxs.map((idx: number) => (
                  <span key={idx}>{new Date(pts[idx].date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}</span>
                ))
              })()}
            </div>
          </div>
        </div>
        
        {/* Asset Allocation */}
        <div className="col-span-12 lg:col-span-4 editorial-card p-6 rounded-xl">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-4">Asset Allocation</p>
          <div className="flex items-center justify-center py-4">
            <div className="relative h-40 w-40">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" fill="transparent" r="15.9" stroke="#E7E2DB" strokeWidth="4"></circle>
                {analytics?.allocation?.distribution?.map((item: any, idx: number) => {
                  let previousPct = analytics.allocation.distribution.slice(0, idx).reduce((sum: number, curr: any) => sum + curr.pct, 0);
                  let dashArray = `${item.pct} ${100 - item.pct}`;
                  let dashOffset = 100 - previousPct + 25; // +25 for visual offset adjustment
                  return (
                    <circle key={item.type} cx="18" cy="18" fill="transparent" r="15.9" stroke={item.color} strokeDasharray={dashArray} strokeDashoffset={dashOffset} strokeWidth="4"></circle>
                  )
                })}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-[10px] text-on-surface-variant uppercase tracking-wider font-bold mb-0.5">Total</p>
                <p className="font-bold text-primary text-sm">{analytics?.allocation?.distribution?.length ? 'Diversified' : 'No Assets'}</p>
              </div>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {analytics?.allocation?.distribution?.map((item: any) => (
              <div key={item.type} className="flex justify-between items-center text-xs">
                <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: item.color}}></div> <span className="font-medium text-on-surface">{item.label}</span></div>
                <span className="font-bold text-on-surface">{item.pct}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Performance vs Benchmark */}
        <div className="col-span-12 lg:col-span-8 editorial-card p-6 rounded-xl">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-8">Performance Comparison (1Y Return %)</p>
          <div className="flex gap-4 h-56 px-2">
            {(() => {
              const portfolioReturn = analytics?.summary?.total_gain_pct || 0;
              const benchmarks = analytics?.benchmarks || [];
              const allItems = [
                { name: 'Portfolio', val: portfolioReturn, isPort: true },
                ...benchmarks.map((b: any) => ({ name: b.name, val: b.return_pct, isPort: false }))
              ];
              const maxAbs = Math.max(10, ...allItems.map(i => Math.abs(i.val)));

              return allItems.map((item, idx) => {
                const isPositive = item.val >= 0;
                const heightPct = (Math.abs(item.val) / maxAbs) * 100;
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center h-full">
                    {/* Positive Space */}
                    <div className="w-full flex-1 flex items-end justify-center pb-1">
                      {isPositive && (
                        <div 
                          className={`w-4/5 rounded-t-md ${item.isPort ? 'bg-primary' : 'bg-secondary'}`} 
                          style={{ height: `${heightPct}%`, minHeight: '4px' }}
                        ></div>
                      )}
                    </div>
                    {/* Zero Line */}
                    <div className="w-full h-[1px] bg-outline-variant/60"></div>
                    {/* Negative Space */}
                    <div className="w-full flex-1 flex items-start justify-center pt-1 relative">
                      {!isPositive && (
                        <div 
                          className={`w-4/5 rounded-b-md ${item.isPort ? 'bg-primary' : 'bg-surface-variant'}`} 
                          style={{ height: `${heightPct}%`, minHeight: '4px' }}
                        ></div>
                      )}
                      {/* Label - Absolute position at bottom so they align perfectly horizontally */}
                      <div className="absolute bottom-0 text-center w-full">
                        <p className="text-[9px] sm:text-[10px] uppercase font-bold text-on-surface-variant tracking-wider leading-tight truncate">{item.name}</p>
                        <p className={`text-[10px] sm:text-xs font-bold mt-0.5 ${isPositive ? 'text-primary' : 'text-on-surface-variant'}`}>
                          {isPositive ? '+' : ''}{item.val.toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </div>
        
        {/* Risk Distribution */}
        <div className="col-span-12 lg:col-span-4 editorial-card p-6 rounded-xl flex flex-col">
          <p className="text-on-surface-variant uppercase text-xs tracking-wider font-bold mb-4">Risk Profile</p>
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="w-32 h-32 relative">
              <svg className="w-full h-full -rotate-180" viewBox="0 0 36 36">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#E7E2DB" strokeDasharray="50, 100" strokeWidth="3"></path>
                {analytics?.risk_profile && (
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#8B5E3C" strokeDasharray={`${(analytics.risk_profile.overall_score / 5) * 50}, 100`} strokeWidth="4"></path>
                )}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center mt-2">
                <span className="material-symbols-outlined text-primary text-[32px]">balance</span>
              </div>
            </div>
            <div className="text-center mt-2">
              <p className="text-lg font-bold text-on-surface">{analytics?.risk_profile?.profile || 'Unknown'}</p>
              <p className="text-[11px] text-on-surface-variant mt-1.5 leading-relaxed font-medium">{analytics?.risk_profile?.explanation}</p>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* INVESTMENT TABLE */}
      <div className="editorial-card rounded-xl overflow-hidden mt-8">
        <div className="px-6 py-5 border-b border-outline-variant/60 flex justify-between items-center bg-surface-container-lowest">
          <h3 className="font-bold text-lg text-on-surface">Current Holdings</h3>
          <div className="flex gap-2">
            <button className="p-2 text-on-surface-variant hover:bg-surface-container hover:text-primary rounded-lg transition-colors border border-transparent hover:border-outline-variant/30">
              <span className="material-symbols-outlined text-[20px]">filter_list</span>
            </button>
            <button className="p-2 text-on-surface-variant hover:bg-surface-container hover:text-primary rounded-lg transition-colors border border-transparent hover:border-outline-variant/30">
              <span className="material-symbols-outlined text-[20px]">download</span>
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-surface-container-low/50">
              <tr>
                <th className="px-6 py-4 text-on-surface-variant uppercase text-[10px] tracking-wider font-bold">Asset</th>
                <th className="px-6 py-4 text-on-surface-variant uppercase text-[10px] tracking-wider font-bold">Type</th>
                <th className="px-6 py-4 text-on-surface-variant uppercase text-[10px] tracking-wider font-bold">Quantity</th>
                <th className="px-6 py-4 text-on-surface-variant uppercase text-[10px] tracking-wider font-bold text-right">Avg Cost</th>
                <th className="px-6 py-4 text-on-surface-variant uppercase text-[10px] tracking-wider font-bold text-right">Current Price</th>
                <th className="px-6 py-4 text-on-surface-variant uppercase text-[10px] tracking-wider font-bold text-right">Total Gain</th>
                <th className="px-6 py-4 text-on-surface-variant uppercase text-[10px] tracking-wider font-bold text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/40">
              {investments.map((inv: any) => {
                const profit = inv.gain_loss || 0;
                const percent = inv.gain_loss_percent || 0;
                const isPositive = profit >= 0;
                
                return (
                  <tr key={inv.id} className="hover:bg-surface/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-4">
                        <div className="w-9 h-9 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center font-bold text-[10px] text-primary uppercase shadow-sm">
                          {inv.symbol ? inv.symbol.substring(0, 4) : inv.name.substring(0, 3)}
                        </div>
                        <div>
                          <p className="font-bold text-on-surface text-sm mb-0.5">{inv.name}</p>
                          <p className="text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">{inv.type.replace('_', ' ')} {inv.symbol ? `• ${inv.symbol}` : ''}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 bg-surface-container border border-outline-variant/30 rounded text-[9px] uppercase tracking-wider font-bold text-on-surface-variant">{inv.type.replace('_', ' ')}</span>
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-on-surface">{inv.quantity}</td>
                    <td className="px-6 py-4 text-sm text-right font-medium text-on-surface">{formatCurrency(inv.purchase_price)}</td>
                    <td className="px-6 py-4 text-sm text-right font-bold text-on-surface">{formatCurrency(inv.current_price)}</td>
                    <td className="px-6 py-4 text-right">
                      <p className={`font-bold text-sm ${isPositive ? 'text-[#2e7d32]' : 'text-error'}`}>
                        {isPositive ? '+' : ''}{formatCurrency(profit)}
                      </p>
                      <p className={`text-[10px] font-bold tracking-wide mt-0.5 ${isPositive ? 'text-[#2e7d32]' : 'text-error'}`}>
                        {isPositive ? '+' : ''}{percent.toFixed(2)}%
                      </p>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => handleTrade(inv)} className="p-2 text-on-surface-variant hover:text-primary transition-colors hover:bg-primary/10 rounded-md" title="Buy/Sell">
                          <span className="material-symbols-outlined text-[16px]">currency_exchange</span>
                        </button>
                        <button onClick={() => handleEdit(inv)} className="p-2 text-on-surface-variant hover:text-primary transition-colors hover:bg-primary/10 rounded-md" title="Edit Details">
                          <span className="material-symbols-outlined text-[16px]">edit</span>
                        </button>
                        <button onClick={() => setInvestmentToDelete(inv)} className="p-2 text-on-surface-variant hover:text-error transition-colors hover:bg-error-container/50 rounded-md" title="Delete">
                          <span className="material-symbols-outlined text-[16px]">delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
              {investments.length === 0 && !isListLoading && (
                <tr>
                  <td colSpan={7} className="px-6 py-16 text-center text-on-surface-variant text-sm font-medium">
                    <span className="material-symbols-outlined text-4xl mb-3 opacity-50 block">account_balance</span>
                    No investments in portfolio yet.<br/>Click "Trade Asset" to add one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {investments.length > 0 && (
          <div className="px-6 py-4 bg-surface-container-low flex justify-between items-center border-t border-outline-variant/40">
            <p className="text-xs text-on-surface-variant font-medium tracking-wide">Showing {investments.length} assets</p>
            <div className="flex gap-1.5">
              <button className="w-7 h-7 flex items-center justify-center border border-outline-variant/50 rounded text-xs hover:bg-surface-container transition-colors bg-white font-bold shadow-sm text-primary">1</button>
            </div>
          </div>
        )}
      </div>

      {/* INSIGHTS SECTION */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        {/* Top Performers */}
        <div className="editorial-card p-6 rounded-xl">
          <div className="flex items-center gap-2 mb-5">
            <span className="material-symbols-outlined text-[#2e7d32]">trending_up</span>
            <h4 className="text-on-surface uppercase text-xs font-bold tracking-wider">Top Performers</h4>
          </div>
          <ul className="space-y-4">
            {investments.filter((i: any) => i.gain_loss_percent > 0).sort((a: any, b: any) => b.gain_loss_percent - a.gain_loss_percent).slice(0, 2).map((inv: any) => (
              <li key={inv.id} className="flex justify-between items-center group">
                <div>
                  <p className="font-bold text-sm text-on-surface group-hover:text-primary transition-colors">{inv.name}</p>
                  <p className="text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold mt-0.5">All Time</p>
                </div>
                <span className="text-[#2e7d32] font-bold text-sm">+{inv.gain_loss_percent.toFixed(1)}%</span>
              </li>
            ))}
            {investments.filter((i: any) => i.gain_loss_percent > 0).length === 0 && (
              <li className="text-sm text-on-surface-variant italic">No positive performers yet.</li>
            )}
          </ul>
        </div>
        
        {/* Worst Performers */}
        <div className="editorial-card p-6 rounded-xl">
          <div className="flex items-center gap-2 mb-5">
            <span className="material-symbols-outlined text-error">trending_down</span>
            <h4 className="text-on-surface uppercase text-xs font-bold tracking-wider">Worst Performers</h4>
          </div>
          <ul className="space-y-4">
            {investments.filter((i: any) => i.gain_loss_percent < 0).sort((a: any, b: any) => a.gain_loss_percent - b.gain_loss_percent).slice(0, 2).map((inv: any) => (
              <li key={inv.id} className="flex justify-between items-center group">
                <div>
                  <p className="font-bold text-sm text-on-surface group-hover:text-error transition-colors">{inv.name}</p>
                  <p className="text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold mt-0.5">All Time</p>
                </div>
                <span className="text-error font-bold text-sm">{inv.gain_loss_percent.toFixed(1)}%</span>
              </li>
            ))}
            {investments.filter((i: any) => i.gain_loss_percent < 0).length === 0 && (
              <li className="text-sm text-on-surface-variant italic">No negative performers.</li>
            )}
          </ul>
        </div>
        
        {/* Recent Purchases */}
        <div className="editorial-card p-6 rounded-xl">
          <div className="flex items-center gap-2 mb-5">
            <span className="material-symbols-outlined text-primary">shopping_bag</span>
            <h4 className="text-on-surface uppercase text-xs font-bold tracking-wider">Recent Purchases</h4>
          </div>
          <ul className="space-y-4">
            {investments.sort((a: any, b: any) => new Date(b.purchase_date).getTime() - new Date(a.purchase_date).getTime()).slice(0, 2).map((inv: any) => (
              <li key={inv.id} className="flex justify-between items-center group">
                <div>
                  <p className="font-bold text-sm text-on-surface group-hover:text-primary transition-colors">{inv.name}</p>
                  <p className="text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold mt-0.5">{formatDate(inv.purchase_date)} • {inv.quantity} units</p>
                </div>
                <span className="text-on-surface-variant text-sm font-bold">{formatCurrency(inv.purchase_price)}</span>
              </li>
            ))}
            {investments.length === 0 && (
              <li className="text-sm text-on-surface-variant italic">No recent purchases.</li>
            )}
          </ul>
        </div>
      </div>

      {/* Investment creation/editing modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingInvestment ? 'Edit Investment' : 'Add Investment'}</DialogTitle>
            <DialogDescription>
              {editingInvestment ? 'Modify the investment details.' : 'Add a new investment asset to track market performance.'}
            </DialogDescription>
          </DialogHeader>
          <InvestmentForm 
            initialData={editingInvestment} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      {/* Trade modal */}
      <Dialog open={isTradeModalOpen} onOpenChange={setIsTradeModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Trade Investment</DialogTitle>
            <DialogDescription>
              Buy more units or sell your existing holdings.
            </DialogDescription>
          </DialogHeader>
          {investmentToTrade && (
            <InvestmentTradeForm 
              investment={investmentToTrade} 
              onSuccess={handleCloseTradeModal} 
              onCancel={handleCloseTradeModal} 
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!investmentToDelete}
        onCancel={() => setInvestmentToDelete(null)}
        onConfirm={() => deleteMutation.mutate(investmentToDelete?.id)}
        title="Delete Investment"
        description={`Are you sure you want to delete "${investmentToDelete?.name}"? You will lose performance tracking history.`}
        confirmLabel={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        variant="danger"
            />
    </div>
  )
}

