'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { goalsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

const schema = z.object({
  amount: z.coerce.number().positive('Contribution must be positive'),
  date: z.string().min(1, 'Date is required'),
  description: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface GoalContributionFormProps {
  goal: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function GoalContributionForm({ goal, onSuccess, onCancel }: GoalContributionFormProps) {
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      amount: 0,
      date: new Date().toISOString().split('T')[0],
      description: 'Goal savings contribution',
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => goalsApi.contribute(goal.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['goals-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Contribution added successfully')
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
        <p className="text-sm font-medium text-[#1f1b18]">Goal: {goal.name}</p>
        <p className="text-xs text-on-surface-variant">Remaining target: {goal.target_amount - goal.current_amount}</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="amount">Contribution Amount *</Label>
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
        <Label htmlFor="description">Description / Source</Label>
        <Input id="description" {...register('description')} />
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Adding...' : 'Add Contribution'}
        </button>
      </div>
    </form>
  )
}
