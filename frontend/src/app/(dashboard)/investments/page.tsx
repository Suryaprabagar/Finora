'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { investmentsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { InvestmentForm } from '@/components/features/investments/InvestmentForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'

export default function InvestmentsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingInvestment, setEditingInvestment] = useState<any>(null)
  const [investmentToDelete, setInvestmentToDelete] = useState<any>(null)

  const queryClient = useQueryClient()

  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['investments-summary'],
    queryFn: () => investmentsApi.getSummary().then(r => r.data),
  })

  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['investments'],
    queryFn: () => investmentsApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => investmentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      queryClient.invalidateQueries({ queryKey: ['investments-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Investment deleted successfully')
      setInvestmentToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete investment')
    }
  })

  const summary = summaryRes?.data || { total_value: 0, total_invested: 0, total_returns: 0, returns_percentage: 0 }
  const investments = listRes?.data || []

  const handleAdd = () => {
    setEditingInvestment(null)
    setIsModalOpen(true)
  }

  const handleEdit = (investment: any) => {
    setEditingInvestment(investment)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setTimeout(() => setEditingInvestment(null), 200)
  }

  return (
    <div>
      <PageHeader
        title="Investments"
        subtitle="Track your portfolio performance"
        actions={
          <button onClick={handleAdd} className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Investment
          </button>
        }
      />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Total Portfolio Value"
          value={formatCurrency(summary.total_value)}
          loading={isSummaryLoading}
          icon="show_chart"
          iconBg="bg-tertiary-fixed"
        />
        <StatCard
          title="Total Invested"
          value={formatCurrency(summary.total_invested)}
          loading={isSummaryLoading}
          icon="savings"
        />
        <StatCard
          title="Total Returns"
          value={formatCurrency(summary.total_returns)}
          trend={{ value: summary.returns_percentage || 0, label: 'returns' }}
          loading={isSummaryLoading}
          icon="trending_up"
        />
      </div>

      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6 text-[#1f1b18]">Investment Holdings</h3>
        
        {isListLoading ? (
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <div key={i} className="h-24 animate-pulse bg-surface-variant/30 rounded-lg"></div>
            ))}
          </div>
        ) : investments.length > 0 ? (
          <div className="space-y-4">
            {investments.map((inv: any) => {
              const profit = inv.gain_loss || 0;
              const percent = inv.gain_loss_percent || 0;
              return (
                <div key={inv.id} className="border border-outline-variant rounded-xl p-4 flex justify-between items-center hover:bg-surface-variant/10 transition-colors group relative">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-base text-[#1f1b18]">{inv.name}</h4>
                      <span className="text-[10px] bg-secondary-container text-on-secondary-container px-2 py-0.5 rounded capitalize font-medium">
                        {inv.type.replace('_', ' ')}
                      </span>
                      {inv.symbol && (
                        <span className="text-xs text-on-surface-variant font-mono">({inv.symbol})</span>
                      )}
                    </div>
                    <p className="text-xs text-on-surface-variant mt-1">
                      Qty: {inv.quantity} • Buy Avg: {formatCurrency(inv.purchase_price)} • Current: {formatCurrency(inv.current_price)} • Date: {formatDate(inv.purchase_date)}
                    </p>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="font-bold text-base text-[#1f1b18]">{formatCurrency(inv.current_value)}</p>
                      <p className={`text-xs font-semibold ${profit >= 0 ? 'text-tertiary' : 'text-error'}`}>
                        {profit >= 0 ? '+' : ''}{formatCurrency(profit)} ({profit >= 0 ? '+' : ''}{percent.toFixed(2)}%)
                      </p>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-0.5">
                      <button onClick={() => handleEdit(inv)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md">
                        <span className="material-symbols-outlined text-[18px]">edit</span>
                      </button>
                      <button onClick={() => setInvestmentToDelete(inv)} className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/50 rounded-md">
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-on-surface-variant mb-4">No investments added yet.</p>
            <button onClick={handleAdd} className="btn-primary">Add an Investment</button>
          </div>
        )}
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
