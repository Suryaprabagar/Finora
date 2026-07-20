'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { incomeApi } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { TransactionForm } from '@/components/features/transactions/TransactionForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'
import { PageHeader } from '@/components/shared/PageHeader'
import { DonutChart } from '@/components/shared/charts/DonutChart'
import { downloadCSV } from '@/lib/export'

export default function IncomePage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingTransaction, setEditingTransaction] = useState<any>(null)
  const [transactionToDelete, setTransactionToDelete] = useState<any>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [trendPeriod, setTrendPeriod] = useState<'6M' | '1Y' | 'All'>('1Y')

  const queryClient = useQueryClient()

  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['income-summary'],
    queryFn: () => incomeApi.getSummary().then(r => r.data),
  })

  const { data: categoriesRes, isLoading: isCategoriesLoading } = useQuery({
    queryKey: ['income-by-category'],
    queryFn: () => incomeApi.getByCategory().then(r => r.data),
  })

  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['income-list'],
    queryFn: () => incomeApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => incomeApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['income-list'] })
      queryClient.invalidateQueries({ queryKey: ['income-summary'] })
      queryClient.invalidateQueries({ queryKey: ['income-by-category'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Income transaction deleted successfully')
      setTransactionToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete transaction')
    }
  })

  const summary = summaryRes?.data || { monthly_total: 0, annual_total: 0, recurring_count: 0, pending_count: 0, largest_source: { name: 'None', amount: 0 } }
  const categoriesData = categoriesRes?.data || []
  let incomes = listRes?.data || []
  
  if (searchTerm) {
    incomes = incomes.filter((tx: any) => 
      tx.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.category?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.bank_account?.name?.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }

  const handleAdd = () => {
    setEditingTransaction({ type: 'income' })
    setIsModalOpen(true)
  }

  const handleEdit = (tx: any) => {
    setEditingTransaction(tx)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setTimeout(() => setEditingTransaction(null), 200)
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <PageHeader
        title="Income Management"
        subtitle="Track and manage every source of income."
        actions={
          <button onClick={handleAdd} className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Income
          </button>
        }
      />
      
      {/* 5 Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px]">
          <p className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-3">Monthly Income</p>
          <div className="flex items-baseline gap-2 mt-auto">
            <h3 className="text-[22px] font-bold font-display text-on-surface">{formatCurrency(summary.monthly_total)}</h3>
            <span className="text-[11px] font-semibold text-tertiary bg-tertiary-fixed/40 px-2 py-0.5 rounded-full flex items-center gap-0.5">
              <span className="material-symbols-outlined text-[13px]">trending_up</span>4.2%
            </span>
          </div>
        </div>

        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px]">
          <p className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-3">Annual Income</p>
          <h3 className="text-[22px] font-bold font-display text-on-surface mb-2">{formatCurrency(summary.annual_total)}</h3>
          <div className="w-full bg-surface-variant h-1 rounded-full overflow-hidden mb-2 mt-auto">
            <div className="bg-primary h-full rounded-full" style={{ width: '82%' }}></div>
          </div>
          <p className="text-[10px] text-on-surface-variant font-medium">82% of target</p>
        </div>

        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px]">
          <p className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-3">Recurring Income</p>
          <h3 className="text-[22px] font-bold font-display text-on-surface mb-1 mt-auto">{formatCurrency(summary.monthly_total * 0.82)}</h3>
          <p className="text-[10px] text-on-surface-variant italic font-medium">8 sources active</p>
        </div>

        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px]">
          <p className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-3">Pending Income</p>
          <h3 className="text-[22px] font-bold font-display text-on-surface mb-1 mt-auto">{formatCurrency(2100)}</h3>
          <p className="text-[10px] text-tertiary font-medium">3 deposits due</p>
        </div>

        <div className="finora-card p-5 flex flex-col justify-between min-h-[130px] bg-surface-container-low border-none shadow-none">
          <p className="text-[10px] font-bold tracking-widest text-primary uppercase mb-3">Largest Source</p>
          <h3 className="text-[22px] font-bold font-display text-on-surface mb-1 mt-auto">{formatCurrency(summary.largest_source.amount)}</h3>
          <p className="text-[10px] text-on-surface-variant font-medium">{summary.largest_source.name}</p>
        </div>
      </div>

      {/* Charts & Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column (Span 2) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Main Chart Card */}
          <div className="finora-card p-6">
            <div className="flex justify-between items-center mb-10">
              <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">Monthly Income Trend</h3>
              <div className="flex bg-surface-container rounded p-0.5 border border-outline-variant/30">
                <button onClick={() => setTrendPeriod('6M')} className={`px-3 py-1 text-xs font-medium rounded ${trendPeriod === '6M' ? 'bg-surface-container-lowest shadow-sm text-on-surface' : 'text-on-surface-variant hover:text-on-surface'}`}>6M</button>
                <button onClick={() => setTrendPeriod('1Y')} className={`px-3 py-1 text-xs font-medium rounded ${trendPeriod === '1Y' ? 'bg-surface-container-lowest shadow-sm text-on-surface' : 'text-on-surface-variant hover:text-on-surface'}`}>1Y</button>
                <button onClick={() => setTrendPeriod('All')} className={`px-3 py-1 text-xs font-medium rounded ${trendPeriod === 'All' ? 'bg-surface-container-lowest shadow-sm text-on-surface' : 'text-on-surface-variant hover:text-on-surface'}`}>All</button>
              </div>
            </div>
            
            {/* Mock Chart Visualization */}
            <div className="h-[220px] flex items-end justify-between gap-1 sm:gap-2 px-1 relative">
              <div className="absolute top-[20%] left-0 right-0 border-t border-dashed border-outline-variant z-0"></div>
              
              {/* Dummy Bars */}
              {(() => {
                const baseData = [40, 50, 45, 60, 55, 70, 75, 85, 95, 90, 80, 100];
                const baseMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                
                let data = baseData;
                let months = baseMonths;
                if (trendPeriod === '6M') {
                  data = baseData.slice(-6);
                  months = baseMonths.slice(-6);
                }
                
                return data.map((h, i, arr) => {
                  const isHighest = h === Math.max(...arr);
                  const month = months[i];
                  const showLabel = trendPeriod === '6M' ? true : (i === 0 || i === 5 || i === 10 || i === 11);
                  const val = summary.monthly_total * (h / 100);
                  return (
                    <div key={i} className="w-full h-full max-w-[48px] flex flex-col justify-end items-center gap-3 z-10 group cursor-pointer">
                      <div className={`w-full relative rounded-t transition-colors ${isHighest ? 'bg-primary' : 'bg-surface-variant group-hover:bg-outline-variant'}`} style={{ height: `${h}%` }}>
                        {/* Tooltip on hover */}
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-inverse-surface text-inverse-on-surface text-[11px] font-medium px-3 py-1.5 rounded shadow whitespace-nowrap z-20 text-center pointer-events-none">
                          {isHighest ? 'Highest' : month}:<br/>{formatCurrency(val)}
                          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-inverse-surface rotate-45"></div>
                        </div>
                      </div>
                      <span className={`text-[10px] font-medium h-4 ${isHighest ? 'text-primary font-bold' : 'text-on-surface-variant'}`}>
                        {showLabel ? month : ''}
                      </span>
                    </div>
                  )
                });
              })()}
            </div>
          </div>

          {/* Sub cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="finora-card p-6 flex flex-col justify-center">
              <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-5">Quarterly Comparison</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-on-surface-variant font-medium">Q4 (Current)</span>
                  <span className="font-bold text-on-surface">{formatCurrency(37350)}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-on-surface-variant font-medium">Q3 (Previous)</span>
                  <span className="font-bold text-on-surface">{formatCurrency(34200)}</span>
                </div>
                <div className="pt-4 border-t border-surface-container flex justify-between items-center text-[13px]">
                  <span className="font-bold text-inverse-surface">Growth</span>
                  <span className="font-bold text-tertiary">+9.2%</span>
                </div>
              </div>
            </div>

            <div className="finora-card p-6 flex items-center justify-between sm:justify-start sm:gap-8">
              <div className="w-24 h-24 relative flex items-center justify-center shrink-0">
                <svg className="absolute inset-0 w-full h-full -rotate-90">
                  <circle cx="48" cy="48" r="43" fill="none" className="stroke-surface-container" strokeWidth="5" />
                  <circle cx="48" cy="48" r="43" fill="none" className="stroke-primary" strokeWidth="5" strokeDasharray="270" strokeDashoffset="67" strokeLinecap="round" />
                </svg>
                <span className="text-[15px] font-bold text-on-surface z-10">75%</span>
              </div>
              <div>
                <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-2">Income Growth</h3>
                <p className="text-[22px] font-bold font-display text-on-surface mb-1">+{formatCurrency(2450)}</p>
                <p className="text-[11px] text-on-surface-variant font-medium leading-tight">Above yearly<br/>baseline</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Distribution */}
        <div className="finora-card p-6 flex flex-col">
          <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase mb-8">Income Distribution</h3>
          
          <div className="flex-1 space-y-7">
            {isCategoriesLoading ? (
              <div className="h-[300px] flex items-center justify-center">
                <div className="w-48 h-48 rounded-full border-8 border-surface-variant/30 animate-pulse" />
              </div>
            ) : (
              <DonutChart
                data={((categoriesData.length > 0 && categoriesData.reduce((sum: number, c: any) => sum + Number(c.percentage || c.total || c.amount || 0), 0) > 0) 
                  ? categoriesData 
                  : [
                      { category: 'Salary', percentage: 72 },
                      { category: 'Freelance', percentage: 18 },
                      { category: 'Investments', percentage: 10 }
                    ]
                ).map((c: any, i: number) => {
                  const colors = ['var(--color-primary)', 'var(--color-secondary)', 'var(--color-tertiary)', 'var(--color-outline-variant)', 'var(--color-surface-variant)'];
                  return {
                    name: c.category || c.name,
                    value: Number(c.total || c.amount || c.percentage || c.value || 0),
                    color: colors[i % colors.length]
                  };
                })}
                height={300}
                centerLabel="Total"
                centerValue={formatCurrency(summary.monthly_total || 120000)}
              />
            )}
          </div>

          <div className="mt-8 pt-6 border-t border-surface-container">
            <button className="w-full py-3.5 bg-surface-container-low hover:bg-surface-container transition-colors rounded-lg flex items-center justify-between px-4 text-primary text-[13px] font-bold">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
                Optimization Tip
              </div>
              <span className="material-symbols-outlined text-[18px]">chevron_right</span>
            </button>
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="finora-card overflow-hidden">
        <div className="p-5 border-b border-surface-container flex flex-col sm:flex-row justify-between items-center gap-4">
          <h3 className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">Recent Income History</h3>
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-[220px]">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant">search</span>
              <input 
                type="text" 
                placeholder="Filter sources..." 
                className="w-full pl-9 pr-4 py-2 bg-surface-container-low border border-transparent focus:border-outline-variant rounded-md text-[13px] font-medium outline-none transition-colors text-on-surface placeholder:text-on-surface-variant"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
            <button className="px-4 py-2 bg-surface-container-lowest border border-outline-variant hover:bg-surface-container-low rounded-md text-[13px] font-bold text-on-surface flex items-center gap-2 transition-colors shrink-0">
              <span className="material-symbols-outlined text-[18px]">filter_list</span>
              Filter
            </button>
            <button onClick={() => {
              if (!incomes || incomes.length === 0) {
                toast.error('No records to export')
                return
              }
              downloadCSV(incomes, 'income_history')
              toast.success('Export downloaded')
            }} className="px-4 py-2 bg-surface-container-lowest border border-outline-variant hover:bg-surface-container-low rounded-md text-[13px] font-bold text-on-surface flex items-center gap-2 transition-colors shrink-0">
              <span className="material-symbols-outlined text-[18px]">upload</span>
              Export
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-[13px] text-left">
            <thead className="bg-surface-container/30 text-[10px] uppercase font-bold text-on-surface-variant tracking-wider">
              <tr>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4">Source</th>
                <th className="px-6 py-4">Category</th>
                <th className="px-6 py-4">Account</th>
                <th className="px-6 py-4 text-right">Amount</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Reference</th>
                <th className="px-6 py-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-container">
              {isListLoading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-on-surface-variant font-medium">Loading...</td>
                </tr>
              ) : incomes.length > 0 ? (
                incomes.map((tx: any) => (
                  <tr key={tx.id} className="hover:bg-surface-container-low/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-on-surface-variant font-medium">
                      {new Date(tx.date).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })}
                    </td>
                    <td className="px-6 py-4 font-bold text-on-surface">{tx.description}</td>
                    <td className="px-6 py-4">
                      <span className="inline-block px-3 py-1 bg-surface-container-low border border-surface-container text-primary text-[11px] font-bold rounded-full">
                        {tx.category?.name || 'Uncategorized'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-on-surface-variant font-medium">
                      {tx.bank_account?.name || '-'}
                      <br/>
                      <span className="text-[11px] opacity-70">
                        {tx.bank_account?.account_number ? `(****${tx.bank_account.account_number.slice(-4)})` : ''}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-bold font-display text-on-surface text-[14px]">{formatCurrency(tx.amount)}</td>
                    <td className="px-6 py-4">
                      <span className={tx.status === 'pending' ? 'chip-pending' : 'chip-cleared'}>
                        <div className={`w-1.5 h-1.5 rounded-full ${tx.status === 'pending' ? 'bg-secondary' : 'bg-tertiary'}`}></div>
                        {tx.status || 'Completed'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-[11px] text-on-surface-variant font-medium">#TXN-{tx.id.substring(0,5)}</td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-3">
                        <button onClick={() => handleEdit(tx)} className="text-on-surface-variant hover:text-primary transition-colors" title="Edit">
                          <span className="material-symbols-outlined text-[18px]">edit</span>
                        </button>
                        <button onClick={() => setTransactionToDelete(tx)} className="text-on-surface-variant hover:text-secondary transition-colors" title="Delete">
                          <span className="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-6 py-8 text-center text-on-surface-variant font-medium">No records found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="p-4 border-t border-surface-container flex justify-between items-center text-[12px] font-medium text-on-surface-variant">
          <span>Showing 1-{Math.min(10, incomes.length)} of {incomes.length} results</span>
          <div className="flex items-center gap-1.5">
            <button className="w-8 h-8 flex items-center justify-center border border-outline-variant rounded hover:bg-surface-container-low bg-surface-container-lowest"><span className="material-symbols-outlined text-[16px]">chevron_left</span></button>
            <button className="w-8 h-8 flex items-center justify-center border border-primary bg-primary text-on-primary rounded font-bold">1</button>
            <button className="w-8 h-8 flex items-center justify-center border border-outline-variant rounded hover:bg-surface-container-low bg-surface-container-lowest text-on-surface font-bold">2</button>
            <button className="w-8 h-8 flex items-center justify-center border border-outline-variant rounded hover:bg-surface-container-low bg-surface-container-lowest text-on-surface font-bold">3</button>
            <span className="px-1 text-on-surface-variant">...</span>
            <button className="w-8 h-8 flex items-center justify-center border border-outline-variant rounded hover:bg-surface-container-low bg-surface-container-lowest text-on-surface font-bold">5</button>
            <button className="w-8 h-8 flex items-center justify-center border border-outline-variant rounded hover:bg-surface-container-low bg-surface-container-lowest"><span className="material-symbols-outlined text-[16px]">chevron_right</span></button>
          </div>
        </div>
      </div>

      {/* Wealth Insights Footer */}
      <div className="mt-8 pt-8">
        <div className="max-w-xl mx-auto text-center finora-card p-6 border-none bg-surface-container-low shadow-none">
          <h4 className="font-bold font-display text-on-surface mb-2 text-[15px]">Wealth Insights</h4>
          <p className="text-[13px] text-on-surface-variant mb-4 leading-relaxed font-medium">
            Based on your current trajectory, your recurring income will <br className="hidden sm:block"/>
            surpass monthly expenses by Q2 next year.
          </p>
          <button className="text-[12px] text-primary font-bold border-b-2 border-outline-variant hover:border-primary pb-0.5 transition-colors">
            View detailed forecast
          </button>
        </div>
      </div>

      {/* Dialogs */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingTransaction?.id ? 'Edit Income' : 'Add Income'}</DialogTitle>
            <DialogDescription>
              {editingTransaction?.id ? 'Update the details of your income record.' : 'Create a new incoming transaction record.'}
            </DialogDescription>
          </DialogHeader>
          {editingTransaction && (
            <TransactionForm 
              initialData={editingTransaction} 
              onSuccess={handleCloseModal}
              onCancel={handleCloseModal}
            />
          )}
        </DialogContent>
      </Dialog>
      
      {/* Delete Dialog */}
      <ConfirmDialog
        open={!!transactionToDelete}
        onCancel={() => setTransactionToDelete(null)}
        onConfirm={() => deleteMutation.mutate(transactionToDelete?.id)}
        title="Delete Income Record"
        description="Are you sure you want to delete this income transaction? This will also revert the balance update on the associated bank account."
        confirmLabel={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        variant="danger"
            />
    </div>
  )
}
