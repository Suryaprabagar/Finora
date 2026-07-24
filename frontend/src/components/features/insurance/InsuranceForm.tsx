'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { insuranceApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  policy_name: z.string().min(1, 'Policy Name is required'),
  provider: z.string().min(1, 'Provider is required'),
  policy_type: z.enum(['health', 'life', 'vehicle', 'home', 'travel', 'other']),
  policy_number: z.string().optional(),
  coverage_amount: z.coerce.number().positive('Coverage amount must be positive'),
  annual_premium: z.coerce.number().positive('Premium must be positive'),
  premium_frequency: z.enum(['yearly', 'monthly', 'quarterly', 'half-yearly']).default('yearly'),
  start_date: z.string().min(1, 'Start date is required'),
  renewal_date: z.string().min(1, 'Renewal date is required'),
  nominee: z.string().optional(),
  notes: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface InsuranceFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function InsuranceForm({ initialData, onSuccess, onCancel }: InsuranceFormProps) {
  const queryClient = useQueryClient()
  const isEditing = !!initialData

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      policy_name: '',
      provider: '',
      policy_type: 'other',
      policy_number: '',
      coverage_amount: 0,
      annual_premium: 0,
      premium_frequency: 'yearly',
      start_date: new Date().toISOString().split('T')[0],
      renewal_date: new Date(Date.now() + 365*24*60*60*1000).toISOString().split('T')[0],
      nominee: '',
      notes: '',
    },
  })

  useEffect(() => {
    if (initialData) {
      reset({
        policy_name: initialData.policy_name,
        provider: initialData.provider,
        policy_type: initialData.policy_type,
        policy_number: initialData.policy_number || '',
        coverage_amount: initialData.coverage_amount,
        annual_premium: initialData.annual_premium,
        premium_frequency: initialData.premium_frequency || 'yearly',
        start_date: initialData.start_date,
        renewal_date: initialData.renewal_date,
        nominee: initialData.nominee || '',
        notes: initialData.notes || '',
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      return isEditing 
        ? insuranceApi.update(initialData.id, data)
        : insuranceApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insurance'] })
      queryClient.invalidateQueries({ queryKey: ['insurance-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Policy updated' : 'Policy created')
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
          <Label htmlFor="provider">Insurance Provider *</Label>
          <Input id="provider" placeholder="e.g. Star Health, LIC" {...register('provider')} />
          {errors.provider && <p className="text-sm text-error">{errors.provider.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="policy_name">Policy Name *</Label>
          <Input id="policy_name" placeholder="e.g. Family Optima" {...register('policy_name')} />
          {errors.policy_name && <p className="text-sm text-error">{errors.policy_name.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="policy_type">Policy Type *</Label>
          <select 
            id="policy_type" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('policy_type')}
          >
            <option value="health">Health Insurance</option>
            <option value="life">Life Insurance</option>
            <option value="vehicle">Vehicle Insurance</option>
            <option value="home">Home Insurance</option>
            <option value="travel">Travel Insurance</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="policy_number">Policy Number / ID</Label>
          <Input id="policy_number" placeholder="e.g. POL-12345" {...register('policy_number')} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="coverage_amount">Coverage Amount (Sum Insured) *</Label>
          <Input id="coverage_amount" type="number" step="0.01" {...register('coverage_amount')} />
          {errors.coverage_amount && <p className="text-sm text-error">{errors.coverage_amount.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="annual_premium">Premium *</Label>
          <Input id="annual_premium" type="number" step="0.01" {...register('annual_premium')} />
          {errors.annual_premium && <p className="text-sm text-error">{errors.annual_premium.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2 col-span-1">
          <Label htmlFor="premium_frequency">Frequency</Label>
          <select 
            id="premium_frequency" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('premium_frequency')}
          >
            <option value="yearly">Yearly</option>
            <option value="half-yearly">Half-Yearly</option>
            <option value="quarterly">Quarterly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
        <div className="space-y-2 col-span-1">
          <Label htmlFor="start_date">Start Date *</Label>
          <Input id="start_date" type="date" {...register('start_date')} />
          {errors.start_date && <p className="text-sm text-error">{errors.start_date.message}</p>}
        </div>
        <div className="space-y-2 col-span-1">
          <Label htmlFor="renewal_date">Renewal Date *</Label>
          <Input id="renewal_date" type="date" {...register('renewal_date')} />
          {errors.renewal_date && <p className="text-sm text-error">{errors.renewal_date.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="nominee">Nominee / Beneficiary</Label>
          <Input id="nominee" placeholder="e.g. Spouse Name" {...register('nominee')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="notes">Notes</Label>
          <Input id="notes" placeholder="e.g. TPA details" {...register('notes')} />
        </div>
      </div>

      <div className="pt-4 flex justify-end gap-3 sticky bottom-0 bg-white pb-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Add Policy'}
        </button>
      </div>
    </form>
  )
}
