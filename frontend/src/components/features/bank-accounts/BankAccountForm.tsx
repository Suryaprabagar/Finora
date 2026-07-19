'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { bankAccountsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  bank_name: z.string().optional(),
  account_type: z.enum(['checking', 'savings', 'credit', 'investment', 'other']),
  account_number: z.string().optional(),
  balance: z.coerce.number(),
  currency: z.string().default('INR'),
})

type FormData = z.infer<typeof schema>

interface BankAccountFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function BankAccountForm({ initialData, onSuccess, onCancel }: BankAccountFormProps) {
  const queryClient = useQueryClient()
  const isEditing = !!initialData

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      bank_name: '',
      account_type: 'checking',
      account_number: '',
      balance: 0,
      currency: 'INR',
    },
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        bank_name: initialData.bank_name || '',
        account_type: initialData.account_type,
        account_number: initialData.account_number || '',
        balance: initialData.balance,
        currency: initialData.currency,
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      return isEditing 
        ? bankAccountsApi.update(initialData.id, data)
        : bankAccountsApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Account updated successfully' : 'Account created successfully')
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
      <div className="space-y-2">
        <Label htmlFor="name">Account Name *</Label>
        <Input id="name" placeholder="e.g. Primary Checking" {...register('name')} />
        {errors.name && <p className="text-sm text-error">{errors.name.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="bank_name">Bank Name</Label>
        <Input id="bank_name" placeholder="e.g. HDFC Bank" {...register('bank_name')} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="account_type">Account Type *</Label>
          <select 
            id="account_type" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('account_type')}
          >
            <option value="checking">Checking</option>
            <option value="savings">Savings</option>
            <option value="investment">Investment</option>
            <option value="other">Other</option>
          </select>
          {errors.account_type && <p className="text-sm text-error">{errors.account_type.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="account_number">Account Number (Last 4 digits)</Label>
          <Input id="account_number" placeholder="e.g. 1234" {...register('account_number')} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="balance">Current Balance *</Label>
          <Input id="balance" type="number" step="0.01" {...register('balance')} />
          {errors.balance && <p className="text-sm text-error">{errors.balance.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="currency">Currency</Label>
          <select 
            id="currency" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('currency')}
          >
            <option value="INR">INR (₹)</option>
            <option value="USD">USD ($)</option>
            <option value="EUR">EUR (€)</option>
            <option value="GBP">GBP (£)</option>
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
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Account'}
        </button>
      </div>
    </form>
  )
}
