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
  target_amount: z.coerce.number().positive('Target amount must be positive'),
  current_amount: z.coerce.number().min(0, 'Current amount cannot be negative'),
  target_date: z.string().optional(),
  category: z.string().optional(),
  color: z.string().default('#0EA5E9'),
  status: z.enum(['active', 'completed', 'paused']).default('active'),
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
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      target_amount: 0,
      current_amount: 0,
      target_date: '',
      category: 'Savings',
      color: '#0EA5E9',
      status: 'active',
    },
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        target_amount: initialData.target_amount,
        current_amount: initialData.current_amount,
        target_date: initialData.target_date || '',
        category: initialData.category || 'Savings',
        color: initialData.color || '#0EA5E9',
        status: initialData.status || 'active',
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
      queryClient.invalidateQueries({ queryKey: ['goals-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Goal updated' : 'Goal created')
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
        <Label htmlFor="name">Goal Name *</Label>
        <Input id="name" placeholder="e.g. Buy a New Car" {...register('name')} />
        {errors.name && <p className="text-sm text-error">{errors.name.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="target_amount">Target Amount *</Label>
          <Input id="target_amount" type="number" step="0.01" {...register('target_amount')} />
          {errors.target_amount && <p className="text-sm text-error">{errors.target_amount.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="current_amount">Starting Savings</Label>
          <Input id="current_amount" type="number" step="0.01" {...register('current_amount')} disabled={isEditing} />
          {errors.current_amount && <p className="text-sm text-error">{errors.current_amount.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="target_date">Target Date</Label>
          <Input id="target_date" type="date" {...register('target_date')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="color">Goal Color Accent</Label>
          <Input id="color" type="color" {...register('color')} className="h-10 cursor-pointer" />
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
            <option value="Savings">Savings</option>
            <option value="Retirement">Retirement</option>
            <option value="Investment">Investment</option>
            <option value="Travel">Travel</option>
            <option value="Emergency">Emergency Fund</option>
            <option value="Property">Property</option>
            <option value="Other">Other</option>
          </select>
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
              <option value="completed">Completed</option>
              <option value="paused">Paused</option>
            </select>
          </div>
        )}
      </div>

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Goal'}
        </button>
      </div>
    </form>
  )
}
