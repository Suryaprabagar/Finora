'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { billsApi, bankAccountsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

const schema = z.object({
  amount_paid: z.coerce.number().positive('Amount must be positive'),
  paid_date: z.string().min(1, 'Payment date is required'),
  bank_account_id: z.string().min(1, 'Select a payment account'),
})

type FormData = z.infer<typeof schema>

interface BillPaymentFormProps {
  bill: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function BillPaymentForm({ bill, onSuccess, onCancel }: BillPaymentFormProps) {
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
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      amount_paid: bill.amount || 0,
      paid_date: new Date().toISOString().split('T')[0],
      bank_account_id: '',
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => billsApi.pay(bill.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bills'] })
      queryClient.invalidateQueries({ queryKey: ['bills-summary'] })
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Bill payment recorded successfully')
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
      <div>
        <p className="text-sm font-medium text-[#1f1b18]">Bill: {bill.name}</p>
        <p className="text-xs text-on-surface-variant">Due Date: {bill.next_due_date || 'N/A'}</p>
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
          <Label htmlFor="amount_paid">Amount Paid *</Label>
          <Input id="amount_paid" type="number" step="0.01" {...register('amount_paid')} />
          {errors.amount_paid && <p className="text-sm text-error">{errors.amount_paid.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="paid_date">Payment Date *</Label>
          <Input id="paid_date" type="date" {...register('paid_date')} />
          {errors.paid_date && <p className="text-sm text-error">{errors.paid_date.message}</p>}
        </div>
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Recording...' : 'Pay Bill'}
        </button>
      </div>
    </form>
  )
}
