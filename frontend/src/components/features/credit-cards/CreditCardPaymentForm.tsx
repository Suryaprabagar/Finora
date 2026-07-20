'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { creditCardsApi, bankAccountsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

const schema = z.object({
  amount: z.coerce.number().positive('Payment amount must be positive'),
  bank_account_id: z.string().min(1, 'Select a bank account to pay from'),
  date: z.string().min(1, 'Date is required'),
  description: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface CreditCardPaymentFormProps {
  card: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function CreditCardPaymentForm({ card, onSuccess, onCancel }: CreditCardPaymentFormProps) {
  const queryClient = useQueryClient()

  const { data: bankAccountsRes } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankAccountsApi.list().then(r => r.data),
  })

  const accounts = bankAccountsRes?.data || []

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      amount: card.outstanding_balance || 0,
      bank_account_id: '',
      date: new Date().toISOString().split('T')[0],
      description: `Payment for ${card.bank_name} Credit Card`,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => creditCardsApi.recordPayment(card.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credit-cards'] })
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      toast.success('Payment recorded successfully')
      onSuccess?.()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'An error occurred')
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1">
        <p className="text-sm font-medium text-on-surface">Card: {card.bank_name} ({card.name})</p>
        <p className="text-xs text-on-surface-variant">Outstanding Balance: {card.outstanding_balance}</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="bank_account_id">Pay From Account *</Label>
        <select 
          id="bank_account_id" 
          className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
          {...register('bank_account_id')}
        >
          <option value="">Select Account</option>
          {accounts.map((acc: any) => (
            <option key={acc.id} value={acc.id}>{acc.name} ({acc.balance})</option>
          ))}
        </select>
        {errors.bank_account_id && <p className="text-sm text-error">{errors.bank_account_id.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="amount">Payment Amount *</Label>
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
        <Label htmlFor="description">Description</Label>
        <Input id="description" {...register('description')} />
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Processing...' : 'Record Payment'}
        </button>
      </div>
    </form>
  )
}
