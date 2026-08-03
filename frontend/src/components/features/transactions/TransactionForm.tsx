'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { transactionsApi, bankAccountsApi, settingsApi, creditCardsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect, useState } from 'react'

const schema = z.object({
  type: z.enum(['income', 'expense', 'transfer']),
  amount: z.coerce.number().positive('Amount must be positive'),
  date: z.string().min(1, 'Date is required'),
  description: z.string().min(1, 'Description is required'),
  category_id: z.string().nullable(),
  account_id: z.string().min(1, 'Account or Cash is required'),
  merchant: z.string().optional(),
  status: z.enum(['cleared', 'pending', 'failed']).default('cleared'),
  payment_method: z.string().optional(),
  notes: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface TransactionFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function TransactionForm({ initialData, onSuccess, onCancel }: TransactionFormProps) {
  const queryClient = useQueryClient()
  const isEditing = !!initialData?.id

  const { data: bankAccountsRes } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankAccountsApi.list().then(r => r.data),
  })

  const { data: creditCardsRes } = useQuery({
    queryKey: ['credit-cards'],
    queryFn: () => creditCardsApi.list().then(r => r.data),
  })

  const { data: categoriesRes } = useQuery({
    queryKey: ['categories'],
    queryFn: () => settingsApi.getCategories().then(r => r.data),
  })

  const accounts = bankAccountsRes?.data || []
  const creditCards = creditCardsRes?.data || []
  const categories = categoriesRes?.data || []

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      type: 'expense',
      amount: 0,
      date: new Date().toISOString().split('T')[0],
      description: '',
      category_id: null,
      account_id: '',
      merchant: '',
      status: 'cleared',
      payment_method: '',
      notes: '',
    },
  })

  const txType = watch('type')

  useEffect(() => {
    if (initialData) {
      let initialAccountId = ''
      if (initialData.bank_account_id) initialAccountId = `bank:${initialData.bank_account_id}`
      else if (initialData.credit_card_id) initialAccountId = `card:${initialData.credit_card_id}`
      else if (initialData.payment_method === 'cash') initialAccountId = 'cash'
      
      reset({
        type: initialData.type,
        amount: initialData.amount,
        date: initialData.date,
        description: initialData.description,
        category_id: initialData.category_id || null,
        account_id: initialAccountId,
        merchant: initialData.merchant || '',
        status: initialData.status,
        payment_method: initialData.payment_method || '',
        notes: initialData.notes || '',
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      let bank_account_id = null
      let credit_card_id = null
      let payment_method = data.payment_method
      
      if (data.account_id === 'cash') {
        payment_method = 'cash'
      } else if (data.account_id.startsWith('bank:')) {
        bank_account_id = data.account_id.split(':')[1]
      } else if (data.account_id.startsWith('card:')) {
        credit_card_id = data.account_id.split(':')[1]
        payment_method = 'card'
      }
      
      // Convert empty strings to null for optional relations
      const payload = {
        ...data,
        bank_account_id,
        credit_card_id,
        payment_method: payment_method || null,
        category_id: data.category_id === '' ? null : data.category_id,
      }
      return isEditing 
        ? transactionsApi.update(initialData.id, payload)
        : transactionsApi.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['income-list'] })
      queryClient.invalidateQueries({ queryKey: ['income-summary'] })
      queryClient.invalidateQueries({ queryKey: ['income-by-category'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-list'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-summary'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-by-category'] })
      toast.success(isEditing ? 'Transaction updated' : 'Transaction created')
      onSuccess?.()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'An error occurred')
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  const filteredCategories = categories.filter((c: any) => c.type === txType)

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Type Selector Tabs */}
      <div className="flex p-1 bg-surface-variant rounded-lg gap-1">
        {(['expense', 'income', 'transfer'] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setValue('type', t)}
            className={`flex-1 py-2 text-sm font-medium rounded-md capitalize transition-colors ${
              txType === t
                ? 'bg-white shadow text-[#1f1b18]'
                : 'text-[#51443c] hover:bg-white/50'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="amount">Amount *</Label>
          <Input id="amount" type="number" step="0.01" {...register('amount')} />
          {errors.amount && <p className="text-sm text-error">{errors.amount.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="date">Date *</Label>
          <Input id="date" type="date" {...register('date')} />
          {errors.date && <p className="text-sm text-error">{errors.date.message}</p>}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description *</Label>
        <Input id="description" placeholder="e.g. Groceries at Walmart" {...register('description')} />
        {errors.description && <p className="text-sm text-error">{errors.description.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="account_id">Account / Funding Source *</Label>
          <select 
            id="account_id" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('account_id')}
          >
            <option value="">Select Account</option>
            <option value="cash">Cash (Wallet)</option>
            {accounts.length > 0 && <optgroup label="Bank Accounts">
              {accounts.map((acc: any) => (
                <option key={`bank:${acc.id}`} value={`bank:${acc.id}`}>{acc.name} ({acc.balance})</option>
              ))}
            </optgroup>}
            {txType === 'expense' && creditCards.length > 0 && <optgroup label="Credit Cards">
              {creditCards.map((card: any) => (
                <option key={`card:${card.id}`} value={`card:${card.id}`}>{card.bank_name} {card.card_number ? `(${card.card_number})` : ''}</option>
              ))}
            </optgroup>}
          </select>
          {errors.account_id && <p className="text-sm text-error">{errors.account_id.message as string}</p>}
        </div>

        {txType !== 'transfer' && (
          <div className="space-y-2">
            <Label htmlFor="category_id">Category</Label>
            <select 
              id="category_id" 
              className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
              {...register('category_id')}
            >
              <option value="">None</option>
              {filteredCategories.map((cat: any) => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
         <div className="space-y-2">
          <Label htmlFor="merchant">Merchant (Optional)</Label>
          <Input id="merchant" placeholder="e.g. Walmart" {...register('merchant')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <select 
            id="status" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('status')}
          >
            <option value="cleared">Cleared</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Add Transaction'}
        </button>
      </div>
    </form>
  )
}
