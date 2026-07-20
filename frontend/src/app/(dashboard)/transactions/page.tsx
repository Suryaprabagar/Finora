'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { transactionsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { DataTable } from '@/components/shared/DataTable'
import { formatCurrency, formatDate, getStatusClass } from '@/lib/utils'
import { Transaction } from '@/types'
import { ColumnDef } from '@tanstack/react-table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { TransactionForm } from '@/components/features/transactions/TransactionForm'
import { toast } from 'sonner'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { downloadCSV } from '@/lib/export'

export default function TransactionsPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingTxn, setEditingTxn] = useState<any>(null)
  const [txnToDelete, setTxnToDelete] = useState<any>(null)

  const queryClient = useQueryClient()

  const { data: res, isLoading } = useQuery({
    queryKey: ['transactions', page, search],
    queryFn: () => transactionsApi.list({ page, per_page: 10, search }).then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => transactionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
      toast.success('Transaction deleted successfully')
      setTxnToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete transaction')
    }
  })

  const handleAdd = () => {
    setEditingTxn(null)
    setIsModalOpen(true)
  }

  const handleEdit = (txn: any) => {
    setEditingTxn(txn)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setTimeout(() => setEditingTxn(null), 200)
  }

  const handleExport = () => {
    if (!res?.data || res.data.length === 0) {
      toast.error('No transactions to export')
      return
    }
    downloadCSV(res.data, 'transactions_export')
    toast.success('Export downloaded')
  }

  const columns: ColumnDef<Transaction>[] = [
    {
      accessorKey: 'date',
      header: 'Date',
      cell: (info) => formatDate(info.getValue() as string),
    },
    {
      accessorKey: 'description',
      header: 'Description',
      cell: (info) => <span className="font-medium">{info.getValue() as string}</span>,
    },
    {
      accessorKey: 'category.name',
      header: 'Category',
      cell: (info) => info.getValue() || '-',
    },
    {
      accessorKey: 'amount',
      header: 'Amount',
      cell: (info) => {
        const val = info.getValue() as number
        const type = info.row.original.type
        return (
          <span className={`font-medium ${type === 'income' ? 'text-tertiary' : ''}`}>
            {type === 'income' ? '+' : '-'}{formatCurrency(val)}
          </span>
        )
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: (info) => {
        const status = info.getValue() as string
        return <span className={getStatusClass(status)}>{status}</span>
      },
    },
    {
      id: 'actions',
      cell: ({ row }) => {
        const txn = row.original
        return (
          <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
             <button onClick={() => handleEdit(txn)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md">
                <span className="material-symbols-outlined text-[18px]">edit</span>
              </button>
              <button onClick={() => setTxnToDelete(txn)} className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/50 rounded-md">
                <span className="material-symbols-outlined text-[18px]">delete</span>
              </button>
          </div>
        )
      }
    }
  ]

  return (
    <div>
      <PageHeader
        title="Transactions"
        subtitle="View and manage all your financial transactions."
        actions={
          <div className="flex gap-3">
            <button onClick={handleExport} className="px-4 py-2 bg-surface-container-lowest border border-outline-variant hover:bg-surface-container-low rounded-md text-[13px] font-bold text-on-surface flex items-center gap-2 transition-colors">
              <span className="material-symbols-outlined text-[18px]">download</span>
              Export
            </button>
            <button onClick={handleAdd} className="btn-primary">
              <span className="material-symbols-outlined text-[18px]">add</span>
              Add Transaction
            </button>
          </div>
        }
      />
      <div className="finora-card rounded-xl overflow-hidden">
        <DataTable
          data={res?.data || []}
          columns={columns}
          loading={isLoading}
          searchable
          onSearch={setSearch}
          pagination={{
            page: res?.pagination?.page || 1,
            perPage: res?.pagination?.per_page || 10,
            total: res?.pagination?.total || 0,
            onPageChange: setPage,
          }}
        />
      </div>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingTxn ? 'Edit Transaction' : 'Add Transaction'}</DialogTitle>
            <DialogDescription>
              {editingTxn ? 'Update your transaction details below.' : 'Add a new income or expense transaction.'}
            </DialogDescription>
          </DialogHeader>
          <TransactionForm 
            initialData={editingTxn} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!txnToDelete}
        onCancel={() => setTxnToDelete(null)}
        onConfirm={() => deleteMutation.mutate(txnToDelete?.id)}
        title="Delete Transaction"
        description={`Are you sure you want to delete this transaction for ${formatCurrency(txnToDelete?.amount || 0)}? This will affect your account balance.`}
        confirmLabel={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        variant="danger"
            />
    </div>
  )
}
