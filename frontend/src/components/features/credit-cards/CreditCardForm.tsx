'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { creditCardsApi, bankAccountsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  bank_name: z.string().min(1, 'Bank Name is required'),
  bank_account_id: z.string().optional().or(z.literal('')),
  card_number: z.string().min(4, 'Card number must be last 4 digits').max(4, 'Card number must be last 4 digits'),
  credit_limit: z.coerce.number().positive('Credit limit must be positive'),
  outstanding_balance: z.coerce.number().min(0, 'Outstanding balance cannot be negative'),
  billing_cycle_day: z.coerce.number().min(1).max(31),
  due_day: z.coerce.number().min(1).max(31),
  interest_rate: z.coerce.number().optional(),
  annual_fee: z.coerce.number().optional(),
  color: z.string().default('#4F46E5'),
})

type FormData = z.infer<typeof schema>

interface CreditCardFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function CreditCardForm({ initialData, onSuccess, onCancel }: CreditCardFormProps) {
  const queryClient = useQueryClient()
  const isEditing = !!initialData?.id

  const { data: bankAccountsRes } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankAccountsApi.list().then(r => r.data),
  })
  const bankAccounts = bankAccountsRes?.data || []

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      bank_name: '',
      bank_account_id: '',
      card_number: '',
      credit_limit: 0,
      outstanding_balance: 0,
      billing_cycle_day: 1,
      due_day: 15,
      interest_rate: 0,
      annual_fee: 0,
      color: '#4F46E5',
    },
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        bank_name: initialData.bank_name,
        bank_account_id: initialData.bank_account_id || '',
        card_number: initialData.card_number || '',
        credit_limit: initialData.credit_limit,
        outstanding_balance: initialData.outstanding_balance,
        billing_cycle_day: initialData.billing_cycle_day,
        due_day: initialData.due_day,
        interest_rate: initialData.interest_rate || 0,
        annual_fee: initialData.annual_fee || 0,
        color: initialData.color || '#4F46E5',
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      return isEditing 
        ? creditCardsApi.update(initialData.id, data)
        : creditCardsApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credit-cards'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Credit Card updated' : 'Credit Card created')
      onSuccess?.()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        toast.error(detail[0].msg || 'Validation Error')
      } else {
        toast.error(detail || 'An error occurred')
      }
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Card Name *</Label>
          <Input id="name" placeholder="e.g. Sapphire Reserve" {...register('name')} />
          {errors.name && <p className="text-sm text-error">{errors.name.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="bank_name">Issuer Bank *</Label>
          <Input id="bank_name" placeholder="e.g. Chase" {...register('bank_name')} />
          {errors.bank_name && <p className="text-sm text-error">{errors.bank_name.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="bank_account_id">Linked Bank Account</Label>
          <select 
            id="bank_account_id" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('bank_account_id')}
          >
            <option value="">None (Standalone Card)</option>
            {bankAccounts.filter((a: any) => a.account_type !== 'cash').map((account: any) => (
              <option key={account.id} value={account.id}>
                {account.bank_name || account.name} - {account.name}
              </option>
            ))}
          </select>
          {errors.bank_account_id && <p className="text-sm text-error">{errors.bank_account_id.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="card_number">Card Number (Last 4)</Label>
          <Input id="card_number" placeholder="e.g. 4021" maxLength={4} {...register('card_number')} />
          {errors.card_number && <p className="text-sm text-error">{errors.card_number.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="credit_limit">Credit Limit *</Label>
          <Input id="credit_limit" type="number" step="0.01" {...register('credit_limit')} />
          {errors.credit_limit && <p className="text-sm text-error">{errors.credit_limit.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="outstanding_balance">Current Outstanding Balance *</Label>
          <Input id="outstanding_balance" type="number" step="0.01" {...register('outstanding_balance')} />
          {errors.outstanding_balance && <p className="text-sm text-error">{errors.outstanding_balance.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="billing_cycle_day">Billing Cycle Day (1-31) *</Label>
          <Input id="billing_cycle_day" type="number" min="1" max="31" {...register('billing_cycle_day')} />
          {errors.billing_cycle_day && <p className="text-sm text-error">{errors.billing_cycle_day.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="due_day">Payment Due Day (1-31) *</Label>
          <Input id="due_day" type="number" min="1" max="31" {...register('due_day')} />
          {errors.due_day && <p className="text-sm text-error">{errors.due_day.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="interest_rate">Interest Rate (APR %)</Label>
          <Input id="interest_rate" type="number" step="0.01" {...register('interest_rate')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="annual_fee">Annual Fee</Label>
          <Input id="annual_fee" type="number" step="0.01" {...register('annual_fee')} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="color">Card Color</Label>
          <Input id="color" type="color" className="h-10 p-1 cursor-pointer" {...register('color')} />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-outline-variant/30">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Card'}
        </button>
      </div>
    </form>
  )
}
