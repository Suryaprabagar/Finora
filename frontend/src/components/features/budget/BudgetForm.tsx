'use client'

import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { budgetApi, settingsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const budgetItemSchema = z.object({
  category_id: z.string().nullable(),
  name: z.string().min(1, 'Name is required'),
  allocated_amount: z.coerce.number().positive('Must be positive'),
})

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  month: z.coerce.number().min(1).max(12),
  year: z.coerce.number().min(2000),
  total_limit: z.coerce.number().positive('Must be positive'),
  items: z.array(budgetItemSchema),
})

type FormData = z.infer<typeof schema>

interface BudgetFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function BudgetForm({ initialData, onSuccess, onCancel }: BudgetFormProps) {
  const queryClient = useQueryClient()
  const isEditing = !!initialData

  const { data: categoriesRes } = useQuery({
    queryKey: ['categories'],
    queryFn: () => settingsApi.getCategories().then(r => r.data),
  })

  const expenseCategories = (categoriesRes?.data || []).filter((c: any) => c.type === 'expense')

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: `Budget ${new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}`,
      month: new Date().getMonth() + 1,
      year: new Date().getFullYear(),
      total_limit: 0,
      items: [],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'items',
  })

  const items = watch('items')
  const calculatedTotal = items.reduce((sum, item) => sum + (Number(item.allocated_amount) || 0), 0)

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        month: initialData.month,
        year: initialData.year,
        total_limit: initialData.total_limit,
        items: initialData.items?.map((item: any) => ({
          category_id: item.category_id || null,
          name: item.name,
          allocated_amount: item.allocated_amount,
        })) || [],
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      // Ensure category_id is null if empty string
      const payload = {
        ...data,
        items: data.items.map(i => ({
          ...i,
          category_id: i.category_id === '' ? null : i.category_id
        }))
      }
      return isEditing 
        ? budgetApi.update(initialData.id, payload)
        : budgetApi.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budget-current'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Budget updated' : 'Budget created')
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
      <div className="space-y-2">
        <Label htmlFor="name">Budget Name *</Label>
        <Input id="name" {...register('name')} />
        {errors.name && <p className="text-sm text-error">{errors.name.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="month">Month *</Label>
          <Input id="month" type="number" min="1" max="12" {...register('month')} />
          {errors.month && <p className="text-sm text-error">{errors.month.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="year">Year *</Label>
          <Input id="year" type="number" min="2000" {...register('year')} />
          {errors.year && <p className="text-sm text-error">{errors.year.message}</p>}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="total_limit">Total Budget Limit *</Label>
        <Input id="total_limit" type="number" step="0.01" {...register('total_limit')} />
        {errors.total_limit && <p className="text-sm text-error">{errors.total_limit.message}</p>}
        <p className="text-xs text-on-surface-variant">Sum of categories: {calculatedTotal}</p>
      </div>

      <div className="space-y-4 mt-6">
        <div className="flex justify-between items-center">
          <h4 className="font-medium text-[#1f1b18]">Budget Categories</h4>
          <button 
            type="button"
            onClick={() => append({ category_id: null, name: '', allocated_amount: 0 })}
            className="text-sm text-primary hover:bg-primary-container/50 px-2 py-1 rounded transition-colors"
          >
            + Add Category
          </button>
        </div>
        
        {fields.map((field, index) => (
          <div key={field.id} className="grid grid-cols-12 gap-2 items-start border p-3 rounded-lg border-[#d5c3b8]">
            <div className="col-span-5 space-y-1">
              <Label className="text-xs">Category</Label>
              <select
                className="flex h-9 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
                {...register(`items.${index}.category_id`)}
                onChange={(e) => {
                  const sel = expenseCategories.find((c: any) => c.id === e.target.value);
                  if (sel) {
                    setValue(`items.${index}.name`, sel.name);
                  }
                }}
              >
                <option value="">Custom Name...</option>
                {expenseCategories.map((cat: any) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
            <div className="col-span-4 space-y-1">
              <Label className="text-xs">Name</Label>
              <Input className="h-9" {...register(`items.${index}.name`)} />
            </div>
            <div className="col-span-3 space-y-1 relative">
              <Label className="text-xs">Limit</Label>
              <div className="flex items-center gap-1">
                <Input className="h-9" type="number" step="0.01" {...register(`items.${index}.allocated_amount`)} />
                <button type="button" onClick={() => remove(index)} className="text-error p-1 hover:bg-error-container rounded">
                  <span className="material-symbols-outlined text-[16px]">close</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="pt-4 flex justify-end gap-3 sticky bottom-0 bg-white pb-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Budget'}
        </button>
      </div>
    </form>
  )
}
