'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { goalsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  goal_type: z.string().min(1, 'Type is required'),
  target_amount: z.coerce.number().positive('Target amount must be positive'),
  target_date: z.string().optional(),
  strategy: z.string().default('Savings Only'),
  risk_profile: z.string().default('Moderate'),
  importance: z.string().default('Medium'),
  monthly_contribution: z.coerce.number().min(0).default(0),
  notes: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface GoalFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function GoalForm({ initialData, onSuccess, onCancel }: GoalFormProps) {
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
      name: '',
      goal_type: 'House',
      target_amount: 0,
      target_date: '',
      strategy: 'Savings Only',
      risk_profile: 'Moderate',
      importance: 'Medium',
      monthly_contribution: 0,
      notes: '',
    },
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        goal_type: initialData.goal_type || 'House',
        target_amount: initialData.target_amount,
        target_date: initialData.target_date || '',
        strategy: initialData.strategy || 'Savings Only',
        risk_profile: initialData.risk_profile || 'Moderate',
        importance: initialData.importance || 'Medium',
        monthly_contribution: initialData.monthly_contribution || 0,
        notes: initialData.notes || '',
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      const payload = {
        ...data,
        target_date: data.target_date === '' ? null : data.target_date
      }
      return isEditing 
        ? goalsApi.update(initialData.id, payload)
        : goalsApi.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['financial-overview'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Objective updated' : 'Objective created')
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
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Objective Name *</Label>
          <Input id="name" placeholder="e.g. House Downpayment" {...register('name')} />
          {errors.name && <p className="text-sm text-error">{errors.name.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="goal_type">Objective Type</Label>
          <select 
            id="goal_type" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('goal_type')}
          >
            <option value="House">House</option>
            <option value="Retirement">Retirement</option>
            <option value="Education">Education</option>
            <option value="Emergency Fund">Emergency Fund</option>
            <option value="Vehicle">Vehicle</option>
            <option value="General Wealth">General Wealth</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="target_amount">Target Amount *</Label>
          <Input id="target_amount" type="number" step="0.01" {...register('target_amount')} />
          {errors.target_amount && <p className="text-sm text-error">{errors.target_amount.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="target_date">Target Date</Label>
          <Input id="target_date" type="date" {...register('target_date')} />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="importance">Importance</Label>
          <select 
            id="importance" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('importance')}
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="risk_profile">Risk Profile</Label>
          <select 
            id="risk_profile" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('risk_profile')}
          >
            <option value="Conservative">Conservative</option>
            <option value="Moderate">Moderate</option>
            <option value="Aggressive">Aggressive</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="strategy">Strategy</Label>
          <select 
            id="strategy" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('strategy')}
          >
            <option value="Savings Only">Savings Only</option>
            <option value="Investments">Investments</option>
            <option value="Balanced">Balanced</option>
          </select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="monthly_contribution">Direct Monthly Contribution (Optional)</Label>
        <Input id="monthly_contribution" type="number" step="0.01" {...register('monthly_contribution')} />
        <p className="text-xs text-on-surface-variant">Amount you plan to contribute manually each month (not linked to assets).</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Input id="notes" placeholder="Any additional details..." {...register('notes')} />
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Objective'}
        </button>
      </div>
    </form>
  )
}
