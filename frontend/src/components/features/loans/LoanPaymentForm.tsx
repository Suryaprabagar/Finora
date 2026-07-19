'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { loansApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'

const schema = z.object({
  payment_date: z.string().min(1, 'Payment date is required'),
  notes: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface LoanPaymentFormProps {
  loan: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function LoanPaymentForm({ loan, onSuccess, onCancel }: LoanPaymentFormProps) {
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      payment_date: new Date().toISOString().split('T')[0],
      notes: `EMI Payment for ${loan.name}`,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) => loansApi.recordPayment(loan.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] })
      queryClient.invalidateQueries({ queryKey: ['loans-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('EMI Payment recorded successfully')
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
        <p className="text-sm font-medium text-[#1f1b18]">Loan: {loan.name} ({loan.lender})</p>
        <p className="text-xs text-on-surface-variant">EMI Amount: {loan.emi_amount}</p>
        <p className="text-xs text-on-surface-variant">Outstanding Balance: {loan.outstanding_balance}</p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="payment_date">Payment Date *</Label>
        <Input id="payment_date" type="date" {...register('payment_date')} />
        {errors.payment_date && <p className="text-sm text-error">{errors.payment_date.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Input id="notes" {...register('notes')} />
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Recording...' : 'Record EMI Payment'}
        </button>
      </div>
    </form>
  )
}
