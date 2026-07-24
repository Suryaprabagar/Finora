'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { insuranceApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

const schema = z.object({
  claim_date: z.string().min(1, 'Claim date is required'),
  claim_amount: z.coerce.number().positive('Claim amount must be positive'),
  description: z.string().optional(),
  status: z.enum(['pending', 'approved', 'rejected']).default('pending'),
})

type FormData = z.infer<typeof schema>

interface InsuranceClaimFormProps {
  policy: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function InsuranceClaimForm({ policy, onSuccess, onCancel }: InsuranceClaimFormProps) {
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      claim_date: new Date().toISOString().split('T')[0],
      claim_amount: 0,
      description: `Claim against ${policy.policy_name}`,
      status: 'pending',
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => insuranceApi.addClaim(policy.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insurance'] })
      queryClient.invalidateQueries({ queryKey: ['insurance-summary'] })
      toast.success('Claim logged successfully')
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
        <p className="text-sm font-medium text-[#1f1b18]">Policy: {policy.policy_name} ({policy.provider})</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="claim_amount">Claim Amount *</Label>
          <Input id="claim_amount" type="number" step="0.01" {...register('claim_amount')} />
          {errors.claim_amount && <p className="text-sm text-error">{errors.claim_amount.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="claim_date">Claim Date *</Label>
          <Input id="claim_date" type="date" {...register('claim_date')} />
          {errors.claim_date && <p className="text-sm text-error">{errors.claim_date.message}</p>}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="status">Claim Status</Label>
        <select 
          id="status" 
          className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
          {...register('status')}
        >
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Reason / Description</Label>
        <Input id="description" {...register('description')} />
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Logging...' : 'Log Claim'}
        </button>
      </div>
    </form>
  )
}
