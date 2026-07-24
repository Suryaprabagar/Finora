'use client'

import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { loansApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { LoanForm } from '@/components/features/loans/LoanForm'
import { LoanPaymentForm } from '@/components/features/loans/LoanPaymentForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'

export default function LoansPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingLoan, setEditingLoan] = useState<any>(null)
  const [loanToDelete, setLoanToDelete] = useState<any>(null)
  const [payEMI, setPayEMI] = useState<any>(null)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout>>(null)
  useEffect(() => {
    return () => {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    }
  }, [])

  const queryClient = useQueryClient()

  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['loans-summary'],
    queryFn: () => loansApi.getSummary().then(r => r.data),
  })

  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['loans'],
    queryFn: () => loansApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => loansApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] })
      queryClient.invalidateQueries({ queryKey: ['loans-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Loan deleted successfully')
      setLoanToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete loan')
    }
  })

  const summary = summaryRes?.data || { total_outstanding: 0, total_emi: 0, active_count: 0 }
  const loans = listRes?.data || []

  const handleAdd = () => {
    setEditingLoan(null)
    setIsModalOpen(true)
  }

  const handleEdit = (loan: any) => {
    setEditingLoan(loan)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    closeTimerRef.current = setTimeout(() => setEditingLoan(null), 200)
  }

  return (
    <div>
      <PageHeader
        title="Loans"
        subtitle="Manage your debts and EMIs"
        actions={
          <button onClick={handleAdd} className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Loan
          </button>
        }
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Total Outstanding Debt"
          value={formatCurrency(summary.total_outstanding)}
          subtitle={`${summary.active_count || 0} Active Loans`}
          loading={isSummaryLoading}
          icon="handshake"
          iconBg="bg-error-container"
        />
        <StatCard
          title="Total Monthly EMI"
          value={formatCurrency(summary.total_emi)}
          loading={isSummaryLoading}
          icon="calendar_month"
        />
      </div>

      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6 text-[#1f1b18]">Active Loans</h3>
        
        {isListLoading ? (
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <div key={i} className="h-24 animate-pulse bg-surface-variant/30 rounded-lg"></div>
            ))}
          </div>
        ) : loans.length > 0 ? (
          <div className="space-y-4">
            {loans.map((loan: any) => {
              const outstanding = loan.outstanding_balance || 0;
              const principal = loan.principal_amount || 0;
              const progress = principal > 0 ? ((principal - outstanding) / principal) * 100 : 0;
              return (
                <div key={loan.id} className="border border-outline-variant rounded-xl p-4 flex flex-col hover:bg-surface-variant/10 transition-colors group relative gap-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-base text-[#1f1b18]">{loan.name}</h4>
                        <span className="text-[10px] bg-secondary-container text-on-secondary-container px-2 py-0.5 rounded capitalize font-medium">
                          {loan.loan_type}
                        </span>
                        <span className="text-xs text-on-surface-variant">• {loan.lender}</span>
                      </div>
                      <p className="text-xs text-on-surface-variant mt-1">
                        EMI: {formatCurrency(loan.emi_amount)} • Rate: {loan.interest_rate}% APR • Duration: {loan.paid_months} / {loan.tenure_months} months paid
                      </p>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-xs text-on-surface-variant mb-0.5">Outstanding</p>
                        <p className="font-bold text-base text-error">{formatCurrency(outstanding)}</p>
                      </div>
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-0.5">
                        {loan.is_active && (
                          <button 
                            onClick={() => setPayEMI(loan)}
                            className="text-xs font-semibold text-primary hover:bg-primary-container/30 px-2.5 py-1.5 rounded transition-colors mr-2"
                          >
                            Pay EMI
                          </button>
                        )}
                        <button onClick={() => handleEdit(loan)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md">
                          <span className="material-symbols-outlined text-[18px]">edit</span>
                        </button>
                        <button onClick={() => setLoanToDelete(loan)} className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/50 rounded-md">
                          <span className="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-on-surface-variant">
                      <span>Paid: {formatCurrency(principal - outstanding)}</span>
                      <span>Total Principal: {formatCurrency(principal)} ({progress.toFixed(1)}%)</span>
                    </div>
                    <div className="w-full h-2 bg-surface-variant rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary transition-all"
                        style={{ width: `${Math.min(progress, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-on-surface-variant mb-4">No active loans set up yet.</p>
            <button onClick={handleAdd} className="btn-primary">Add a Loan</button>
          </div>
        )}
      </div>

      {/* Loan creation/editing modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingLoan ? 'Edit Loan Details' : 'Add Loan'}</DialogTitle>
            <DialogDescription>
              {editingLoan ? 'Modify liability details.' : 'Register a new active liability to track EMIs and balance.'}
            </DialogDescription>
          </DialogHeader>
          <LoanForm 
            initialData={editingLoan} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      {/* Pay EMI Modal */}
      <Dialog open={!!payEMI} onOpenChange={(open) => !open && setPayEMI(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record EMI Payment</DialogTitle>
            <DialogDescription>
              Log an EMI payment toward this loan to reduce the outstanding principal.
            </DialogDescription>
          </DialogHeader>
          {payEMI && (
            <LoanPaymentForm 
              loan={payEMI}
              onSuccess={() => setPayEMI(null)}
              onCancel={() => setPayEMI(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!loanToDelete}
        onCancel={() => setLoanToDelete(null)}
        onConfirm={() => deleteMutation.mutate(loanToDelete?.id)}
        title="Delete Loan"
        description={`Are you sure you want to delete "${loanToDelete?.name}"? You will lose history of EMI payments.`}
        confirmLabel={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        variant="danger"
            />
    </div>
  )
}
