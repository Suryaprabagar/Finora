'use client'

import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bankAccountsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { BankAccountForm } from '@/components/features/bank-accounts/BankAccountForm'
import { toast } from 'sonner'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'

export default function BankAccountsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState<any>(null)
  const [accountToDelete, setAccountToDelete] = useState<any>(null)

  const closeTimerRef = useRef<ReturnType<typeof setTimeout>>(null)
  useEffect(() => {
    return () => {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    }
  }, [])
  
  const queryClient = useQueryClient()

  const { data: res, isLoading } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankAccountsApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => bankAccountsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Account deleted successfully')
      setAccountToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete account')
    }
  })

  const accounts = res?.data || []
  const totalBalance = accounts.reduce((acc: number, curr: any) => acc + Number(curr.balance || 0), 0)

  const handleAdd = () => {
    setEditingAccount(null)
    setIsModalOpen(true)
  }

  const handleEdit = (account: any) => {
    setEditingAccount(account)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    closeTimerRef.current = setTimeout(() => setEditingAccount(null), 200) // Clear after animation
  }

  const handleEditCash = () => {
    const cashAccount = accounts.find((a: any) => a.account_type === 'cash')
    if (cashAccount) {
      handleEdit(cashAccount)
    } else {
      setEditingAccount({
        name: 'Physical Cash',
        account_type: 'cash',
        balance: 0,
        currency: 'INR'
      })
      setIsModalOpen(true)
    }
  }

  return (
    <div>
      <PageHeader
        title="Bank Accounts"
        subtitle="Manage your savings and checking accounts"
        actions={
          <button onClick={handleAdd} className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Account
          </button>
        }
      />
      
      <div className="mb-8">
        <StatCard
          title="Total Cash Balance"
          value={formatCurrency(totalBalance)}
          loading={isLoading}
          icon="account_balance"
          action={
            <button 
              onClick={handleEditCash} 
              className="text-xs font-bold text-primary bg-primary/10 hover:bg-primary/20 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-[14px]">payments</span>
              Add/Edit Cash
            </button>
          }
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="finora-card p-6 h-32 animate-pulse bg-surface-variant/30"></div>
          ))
        ) : accounts.length > 0 ? (
          accounts.map((account: any) => (
            <div key={account.id} className="finora-card p-6 flex flex-col justify-between group">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium text-lg mb-1 text-[#1f1b18]">{account.bank_name || account.name}</h4>
                  <p className="text-sm text-on-surface-variant capitalize">{account.account_type} {account.account_number ? `•••• ${account.account_number.slice(-4)}` : ''}</p>
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                  <button onClick={() => handleEdit(account)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md">
                    <span className="material-symbols-outlined text-[18px]">edit</span>
                  </button>
                  <button onClick={() => setAccountToDelete(account)} className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/50 rounded-md">
                    <span className="material-symbols-outlined text-[18px]">delete</span>
                  </button>
                </div>
              </div>
              <div className="mt-4">
                <p className="text-2xl font-display font-bold text-[#1f1b18]">{formatCurrency(account.balance)}</p>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full">
            <div className="finora-card p-12 text-center">
              <p>No bank accounts added yet.</p>
              <button onClick={handleAdd} className="btn-primary mt-4">Add Account</button>
            </div>
          </div>
        )}
      </div>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingAccount ? 'Edit Bank Account' : 'Add Bank Account'}</DialogTitle>
            <DialogDescription>
              {editingAccount ? 'Update your account details below.' : 'Add a new bank account to track your balance.'}
            </DialogDescription>
          </DialogHeader>
          <BankAccountForm 
            initialData={editingAccount} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!accountToDelete}
        onCancel={() => setAccountToDelete(null)}
        onConfirm={() => deleteMutation.mutate(accountToDelete?.id)}
        title="Delete Bank Account"
        description={`Are you sure you want to delete ${accountToDelete?.name}? This action cannot be undone.`}
        confirmLabel={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        variant="danger"
            />
    </div>
  )
}
