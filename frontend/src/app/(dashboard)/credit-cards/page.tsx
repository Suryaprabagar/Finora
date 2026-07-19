'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { creditCardsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { CreditCardForm } from '@/components/features/credit-cards/CreditCardForm'
import { CreditCardPaymentForm } from '@/components/features/credit-cards/CreditCardPaymentForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'

export default function CreditCardsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCard, setEditingCard] = useState<any>(null)
  const [cardToDelete, setCardToDelete] = useState<any>(null)
  const [paymentCard, setPaymentCard] = useState<any>(null)

  const queryClient = useQueryClient()

  const { data: res, isLoading } = useQuery({
    queryKey: ['credit-cards'],
    queryFn: () => creditCardsApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => creditCardsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credit-cards'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Credit card deleted successfully')
      setCardToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete credit card')
    }
  })

  const cards = res?.data || []
  const totalOutstanding = cards.reduce((acc: number, curr: any) => acc + curr.outstanding_balance, 0)
  const totalLimit = cards.reduce((acc: number, curr: any) => acc + curr.credit_limit, 0)

  const handleAdd = () => {
    setEditingCard(null)
    setIsModalOpen(true)
  }

  const handleEdit = (card: any) => {
    setEditingCard(card)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setTimeout(() => setEditingCard(null), 200)
  }

  return (
    <div>
      <PageHeader
        title="Credit Cards"
        subtitle="Manage your credit cards and track outstanding balances"
        actions={
          <button onClick={handleAdd} className="btn-primary">
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
          cards.map((card: any) => {
            const usagePercent = card.credit_limit > 0 ? (card.outstanding_balance / card.credit_limit) * 100 : 0;
            return (
              <div key={card.id} className="finora-card p-6 flex flex-col justify-between group relative overflow-hidden">
                {card.color && (
                  <div 
                    className="absolute top-0 left-0 right-0 h-1.5" 
                    style={{ backgroundColor: card.color }}
                  />
                )}
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="font-medium text-lg text-[#1f1b18]">{card.bank_name}</h4>
                      <p className="text-sm text-on-surface-variant">{card.name} {card.card_number ? `•••• ${card.card_number.slice(-4)}` : ''}</p>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                      <button onClick={() => handleEdit(card)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md">
                        <span className="material-symbols-outlined text-[18px]">edit</span>
                      </button>
                      <button onClick={() => setCardToDelete(card)} className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/50 rounded-md">
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </div>
                  </div>
                  <div className="mb-4">
                    <p className="text-xs text-on-surface-variant mb-1">Outstanding Balance</p>
                    <p className="text-2xl font-display font-bold text-[#1f1b18]">{formatCurrency(card.outstanding_balance)}</p>
                  </div>
                </div>

                <div>
                  <div className="w-full h-2 bg-surface-variant rounded-full overflow-hidden mb-2">
                    <div 
                      className={`h-full transition-all ${usagePercent > 80 ? 'bg-error' : 'bg-primary'}`}
                      style={{ width: `${Math.min(usagePercent, 100)}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between items-center">
                    <button 
                      onClick={() => setPaymentCard(card)}
                      className="text-xs font-semibold text-primary hover:bg-primary-container/30 px-2.5 py-1 rounded transition-colors"
                    >
                      Record Payment
                    </button>
                    <p className="text-xs text-on-surface-variant">Limit: {formatCurrency(card.credit_limit)}</p>
                  </div>
                </div>
              </div>
            )
          })
        ) : (
          <div className="col-span-full finora-card p-12 text-center">
            <p className="text-on-surface-variant mb-4">No credit cards added yet.</p>
            <button onClick={handleAdd} className="btn-primary">Add Card</button>
          </div>
        )}
      </div>

      {/* Create / Edit Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingCard ? 'Edit Credit Card' : 'Add Credit Card'}</DialogTitle>
            <DialogDescription>
              {editingCard ? 'Update your card parameters below.' : 'Add a new credit card to track your outstanding balances.'}
            </DialogDescription>
          </DialogHeader>
          <CreditCardForm 
            initialData={editingCard} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      {/* Record Payment Modal */}
      <Dialog open={!!paymentCard} onOpenChange={(open) => !open && setPaymentCard(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
            <DialogDescription>
              Record a payment to reduce the outstanding balance on your credit card.
            </DialogDescription>
          </DialogHeader>
          {paymentCard && (
            <CreditCardPaymentForm 
              card={paymentCard}
              onSuccess={() => setPaymentCard(null)}
              onCancel={() => setPaymentCard(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!cardToDelete}
        onClose={() => setCardToDelete(null)}
        onConfirm={() => deleteMutation.mutate(cardToDelete?.id)}
        title="Delete Credit Card"
        description={`Are you sure you want to delete ${cardToDelete?.bank_name} - ${cardToDelete?.name}? This action cannot be undone.`}
        confirmText={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        isDestructive
      />
    </div>
  )
}
