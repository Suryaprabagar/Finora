'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { billsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { BillForm } from '@/components/features/bills/BillForm'
import { BillPaymentForm } from '@/components/features/bills/BillPaymentForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'

export default function BillsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingBill, setEditingBill] = useState<any>(null)
  const [billToDelete, setBillToDelete] = useState<any>(null)
  const [payBill, setPayBill] = useState<any>(null)

  const queryClient = useQueryClient()

  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['bills-summary'],
    queryFn: () => billsApi.getSummary().then(r => r.data),
  })

  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['bills'],
    queryFn: () => billsApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => billsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bills'] })
      queryClient.invalidateQueries({ queryKey: ['bills-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Bill deleted successfully')
      setBillToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete bill')
    }
  })

  const summary = summaryRes?.data || { upcoming_amount: 0, paid_mtd: 0, overdue_count: 0, monthly_average: 0, active_count: 0 }
  const bills = listRes?.data || []

  const handleAdd = () => {
    setEditingBill(null)
    setIsModalOpen(true)
  }

  const handleEdit = (bill: any) => {
    setEditingBill(bill)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setTimeout(() => setEditingBill(null), 200)
  }

  return (
    <div>
      <PageHeader
        title="Bills"
        subtitle="Never miss a payment"
        actions={
          <button onClick={handleAdd} className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Bill
          </button>
        }
      />
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Upcoming Bills"
          value={formatCurrency(summary.upcoming_amount)}
          subtitle={`${summary.active_count} Active Bills`}
          loading={isSummaryLoading}
          icon="calendar_month"
          iconBg="bg-secondary-fixed"
        />
        <StatCard
          title="Paid (This Month)"
          value={formatCurrency(summary.paid_mtd)}
          loading={isSummaryLoading}
          icon="check_circle"
          iconBg="bg-tertiary-fixed"
        />
        <StatCard
          title="Overdue Bills"
          value={String(summary.overdue_count)}
          loading={isSummaryLoading}
          icon="warning"
          iconBg={summary.overdue_count > 0 ? "bg-error-container text-error" : undefined}
        />
      </div>

      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6 text-[#1f1b18]">Your Bills</h3>
        
        {isListLoading ? (
          <div className="space-y-4">
            {[1, 2].map(i => (
              <div key={i} className="h-20 animate-pulse bg-surface-variant/30 rounded-lg"></div>
            ))}
          </div>
        ) : bills.length > 0 ? (
          <div className="divide-y divide-outline-variant">
            {bills.map((bill: any) => {
              const isOverdue = bill.next_due_date && new Date(bill.next_due_date) < new Date();
              return (
                <div key={bill.id} className="py-4 flex justify-between items-center group">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-[#1f1b18]">{bill.name}</h4>
                      {bill.autopay && (
                        <span className="text-[10px] bg-primary-container text-on-primary-container px-2 py-0.5 rounded font-semibold">
                          Autopay
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-on-surface-variant mt-1">
                      Due: {bill.next_due_date ? formatDate(bill.next_due_date) : 'Not scheduled'} {isOverdue && <span className="text-error font-medium">• Overdue</span>}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <p className="font-bold text-base text-[#1f1b18]">{formatCurrency(bill.amount)}</p>
                    <div className="flex gap-1">
                      {bill.status === 'active' && (
                        <button 
                          onClick={() => setPayBill(bill)}
                          className="text-xs font-semibold text-primary hover:bg-primary-container/30 px-2.5 py-1.5 rounded transition-colors"
                        >
                          Pay
                        </button>
                      )}
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-0.5">
                        <button onClick={() => handleEdit(bill)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md">
                          <span className="material-symbols-outlined text-[18px]">edit</span>
                        </button>
                        <button onClick={() => setBillToDelete(bill)} className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/50 rounded-md">
                          <span className="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-on-surface-variant mb-4">No bills added yet.</p>
            <button onClick={handleAdd} className="btn-primary">Add a Bill</button>
          </div>
        )}
      </div>

      {/* Bill add/edit modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingBill ? 'Edit Bill Details' : 'Add Bill'}</DialogTitle>
            <DialogDescription>
              {editingBill ? 'Modify the recurring bill details.' : 'Create a new recurring bill schedule.'}
            </DialogDescription>
          </DialogHeader>
          <BillForm 
            initialData={editingBill} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      {/* Bill payment modal */}
      <Dialog open={!!payBill} onOpenChange={(open) => !open && setPayBill(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
            <DialogDescription>
              Record a payment to mark this bill instance as paid.
            </DialogDescription>
          </DialogHeader>
          {payBill && (
            <BillPaymentForm 
              bill={payBill}
              onSuccess={() => setPayBill(null)}
              onCancel={() => setPayBill(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!billToDelete}
        onClose={() => setBillToDelete(null)}
        onConfirm={() => deleteMutation.mutate(billToDelete?.id)}
        title="Delete Bill"
        description={`Are you sure you want to delete ${billToDelete?.name}? You will lose tracking of future due dates.`}
        confirmText={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        isDestructive
      />
    </div>
  )
}
