'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { loansApi, bankAccountsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  lender: z.string().min(1, 'Lender is required'),
  loan_type: z.enum(['home', 'car', 'personal', 'education', 'other']),
  principal_amount: z.coerce.number().positive('Principal amount must be positive'),
  outstanding_balance: z.coerce.number().positive('Outstanding balance must be positive'),
  interest_rate: z.coerce.number().positive('Interest rate must be positive'),
  emi_amount: z.coerce.number().positive('EMI amount must be positive'),
  tenure_months: z.coerce.number().positive('Tenure must be positive'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  emi_day: z.coerce.number().min(1).max(31).default(1),
  bank_account_id: z.string().optional().nullable(),
  notes: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface LoanFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function LoanForm({ initialData, onSuccess, onCancel }: LoanFormProps) {
  const queryClient = useQueryClient()
  const isEditing = !!initialData

  const { data: bankAccountsRes } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankAccountsApi.list().then(r => r.data),
  })

  const accounts = bankAccountsRes?.data || []

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      lender: '',
      loan_type: 'other',
      principal_amount: 0,
      outstanding_balance: 0,
      interest_rate: 0,
      emi_amount: 0,
      tenure_months: 12,
      start_date: new Date().toISOString().split('T')[0],
      end_date: new Date(Date.now() + 365*24*60*60*1000).toISOString().split('T')[0],
      emi_day: 1,
      bank_account_id: null,
      notes: '',
    },
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        lender: initialData.lender,
        loan_type: initialData.loan_type,
        principal_amount: initialData.principal_amount,
        outstanding_balance: initialData.outstanding_balance,
        interest_rate: initialData.interest_rate,
        emi_amount: initialData.emi_amount,
        tenure_months: initialData.tenure_months,
        start_date: initialData.start_date,
        end_date: initialData.end_date,
        emi_day: initialData.emi_day || 1,
        bank_account_id: initialData.bank_account_id || null,
        notes: initialData.notes || '',
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      const payload = {
        ...data,
        bank_account_id: data.bank_account_id === '' ? null : data.bank_account_id
      }
      return isEditing 
        ? loansApi.update(initialData.id, payload)
        : loansApi.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] })
      queryClient.invalidateQueries({ queryKey: ['loans-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Loan updated' : 'Loan created')
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
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="lender">Lender / Bank Name *</Label>
          <Input id="lender" placeholder="e.g. SBI, HDFC" {...register('lender')} />
          {errors.lender && <p className="text-sm text-error">{errors.lender.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="name">Loan Name *</Label>
          <Input id="name" placeholder="e.g. Home Loan" {...register('name')} />
          {errors.name && <p className="text-sm text-error">{errors.name.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="loan_type">Loan Type *</Label>
          <select 
            id="loan_type" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('loan_type')}
          >
            <option value="home">Home Loan</option>
            <option value="car">Car Loan</option>
            <option value="personal">Personal Loan</option>
            <option value="education">Education Loan</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="interest_rate">Interest Rate (% APR) *</Label>
          <Input id="interest_rate" type="number" step="0.01" {...register('interest_rate')} />
          {errors.interest_rate && <p className="text-sm text-error">{errors.interest_rate.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="principal_amount">Principal Amount *</Label>
          <Input id="principal_amount" type="number" step="0.01" {...register('principal_amount')} />
          {errors.principal_amount && <p className="text-sm text-error">{errors.principal_amount.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="outstanding_balance">Outstanding Balance *</Label>
          <Input id="outstanding_balance" type="number" step="0.01" {...register('outstanding_balance')} />
          {errors.outstanding_balance && <p className="text-sm text-error">{errors.outstanding_balance.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="emi_amount">Monthly EMI Amount *</Label>
          <Input id="emi_amount" type="number" step="0.01" {...register('emi_amount')} />
          {errors.emi_amount && <p className="text-sm text-error">{errors.emi_amount.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="tenure_months">Tenure (Months) *</Label>
          <Input id="tenure_months" type="number" {...register('tenure_months')} />
          {errors.tenure_months && <p className="text-sm text-error">{errors.tenure_months.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2 col-span-1">
          <Label htmlFor="emi_day">EMI Day (1-31) *</Label>
          <Input id="emi_day" type="number" min="1" max="31" {...register('emi_day')} />
        </div>
        <div className="space-y-2 col-span-1">
          <Label htmlFor="start_date">Start Date *</Label>
          <Input id="start_date" type="date" {...register('start_date')} />
          {errors.start_date && <p className="text-sm text-error">{errors.start_date.message}</p>}
        </div>
        <div className="space-y-2 col-span-1">
          <Label htmlFor="end_date">End Date *</Label>
          <Input id="end_date" type="date" {...register('end_date')} />
          {errors.end_date && <p className="text-sm text-error">{errors.end_date.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="bank_account_id">Payment Bank Account (Optional)</Label>
          <select 
            id="bank_account_id" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('bank_account_id')}
          >
            <option value="">None</option>
            {accounts.map((acc: any) => (
              <option key={acc.id} value={acc.id}>{acc.name} ({acc.balance})</option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="notes">Notes</Label>
          <Input id="notes" placeholder="e.g. Loan Account ID" {...register('notes')} />
        </div>
      </div>

      <div className="pt-4 flex justify-end gap-3 sticky bottom-0 bg-white pb-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Loan'}
        </button>
      </div>
    </form>
  )
}
