'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { billsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  amount: z.coerce.number().positive('Amount must be positive'),
  due_day: z.coerce.number().min(1).max(31, 'Due day must be between 1 and 31'),
  category: z.string().optional(),
  payee: z.string().optional(),
  autopay: z.boolean().default(false),
  status: z.enum(['active', 'inactive']).default('active'),
  notes: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface BillFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function BillForm({ initialData, onSuccess, onCancel }: BillFormProps) {
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
      amount: 0,
      due_day: 1,
      category: 'Utilities',
      payee: '',
      autopay: false,
      status: 'active',
      notes: '',
    },
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        amount: initialData.amount,
        due_day: initialData.due_day,
        category: initialData.category || 'Utilities',
        payee: initialData.payee || '',
        autopay: initialData.autopay || false,
        status: initialData.status || 'active',
        notes: initialData.notes || '',
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      return isEditing 
        ? billsApi.update(initialData.id, data)
        : billsApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bills'] })
      queryClient.invalidateQueries({ queryKey: ['bills-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Bill updated' : 'Bill created')
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
        <Label htmlFor="name">Bill Name *</Label>
        <Input id="name" placeholder="e.g. Electric Bill" {...register('name')} />
        {errors.name && <p className="text-sm text-error">{errors.name.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="amount">Typical Amount *</Label>
          <Input id="amount" type="number" step="0.01" {...register('amount')} />
          {errors.amount && <p className="text-sm text-error">{errors.amount.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="due_day">Due Day of Month (1-31) *</Label>
          <Input id="due_day" type="number" min="1" max="31" {...register('due_day')} />
          {errors.due_day && <p className="text-sm text-error">{errors.due_day.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="category">Category</Label>
          <select 
            id="category" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('category')}
          >
            <option value="Utilities">Utilities</option>
            <option value="Rent">Rent</option>
            <option value="Subscription">Subscription</option>
            <option value="Insurance">Insurance</option>
            <option value="Credit Card">Credit Card</option>
            <option value="Loan">Loan</option>
            <option value="Other">Other</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="payee">Payee / Vendor</Label>
          <Input id="payee" placeholder="e.g. PG&E" {...register('payee')} />
        </div>
      </div>

      <div className="flex items-center gap-2 py-2">
        <input 
          id="autopay" 
          type="checkbox" 
          className="rounded border-[#d5c3b8] text-primary focus:ring-primary w-4 h-4"
          {...register('autopay')}
        />
        <Label htmlFor="autopay" className="cursor-pointer">Enable Autopay</Label>
      </div>

      {isEditing && (
        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <select 
            id="status" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('status')}
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Input id="notes" placeholder="Any additional notes" {...register('notes')} />
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Add Bill'}
        </button>
      </div>
    </form>
  )
}
