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
  // Backend schema field is `notes`, not `description`
  notes: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface GoalContributionFormProps {
  // Accept goalId (string) so the parent doesn't need to pass the full goal object
  goalId: string
  onSuccess?: () => void
  onCancel?: () => void
}

export function GoalContributionForm({ goalId, onSuccess, onCancel }: GoalContributionFormProps) {
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
      notes: '',
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => goalsApi.contribute(goalId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['financial-overview'] })
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
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="amount">Amount *</Label>
          <Input id="amount" type="number" step="0.01" placeholder="5000" {...register('amount')} />
          {errors.amount && <p className="text-sm text-error">{errors.amount.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="date">Date *</Label>
          <Input id="date" type="date" {...register('date')} />
          {errors.date && <p className="text-sm text-error">{errors.date.message}</p>}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Notes (optional)</Label>
        <Input id="notes" placeholder="e.g. Monthly savings transfer" {...register('notes')} />
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Add Contribution'}
        </button>
      </div>
    </form>
  )
}
