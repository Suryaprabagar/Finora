'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { investmentsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  type: z.enum(['mutual_fund', 'stock', 'crypto', 'fd', 'gold', 'other']),
  symbol: z.string().optional(),
  purchase_price: z.coerce.number().positive('Purchase price must be positive'),
  current_price: z.coerce.number().positive('Current price must be positive'),
  quantity: z.coerce.number().positive('Quantity must be positive'),
  purchase_date: z.string().min(1, 'Purchase date is required'),
  maturity_date: z.string().optional(),
  interest_rate: z.coerce.number().optional(),
  broker: z.string().optional(),
  folio_number: z.string().optional(),
  notes: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface InvestmentFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function InvestmentForm({ initialData, onSuccess, onCancel }: InvestmentFormProps) {
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
      type: 'stock',
      symbol: '',
      purchase_price: 0,
      current_price: 0,
      quantity: 1,
      purchase_date: new Date().toISOString().split('T')[0],
      maturity_date: '',
      interest_rate: 0,
      broker: '',
      folio_number: '',
      notes: '',
    },
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        type: initialData.type,
        symbol: initialData.symbol || '',
        purchase_price: initialData.purchase_price,
        current_price: initialData.current_price,
        quantity: initialData.quantity,
        purchase_date: initialData.purchase_date,
        maturity_date: initialData.maturity_date || '',
        interest_rate: initialData.interest_rate || 0,
        broker: initialData.broker || '',
        folio_number: initialData.folio_number || '',
        notes: initialData.notes || '',
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      const payload = {
        ...data,
        maturity_date: data.maturity_date === '' ? null : data.maturity_date
      }
      return isEditing 
        ? investmentsApi.update(initialData.id, payload)
        : investmentsApi.create(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      queryClient.invalidateQueries({ queryKey: ['investments-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Investment updated' : 'Investment holding added')
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
          <Label htmlFor="name">Investment / Fund Name *</Label>
          <Input id="name" placeholder="e.g. Parag Parikh Flexi Cap" {...register('name')} />
          {errors.name && <p className="text-sm text-error">{errors.name.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="symbol">Symbol / Ticker</Label>
          <Input id="symbol" placeholder="e.g. RELIANCE, BTC" {...register('symbol')} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="type">Investment Type *</Label>
          <select 
            id="type" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('type')}
          >
            <option value="mutual_fund">Mutual Fund</option>
            <option value="stock">Equity / Stock</option>
            <option value="crypto">Cryptocurrency</option>
            <option value="fd">Fixed Deposit (FD)</option>
            <option value="gold">Gold Holdings</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="purchase_date">Purchase Date *</Label>
          <Input id="purchase_date" type="date" {...register('purchase_date')} />
          {errors.purchase_date && <p className="text-sm text-error">{errors.purchase_date.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="quantity">Quantity *</Label>
          <Input id="quantity" type="number" step="0.0001" {...register('quantity')} />
          {errors.quantity && <p className="text-sm text-error">{errors.quantity.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="purchase_price">Buy Price (Average) *</Label>
          <Input id="purchase_price" type="number" step="0.01" {...register('purchase_price')} />
          {errors.purchase_price && <p className="text-sm text-error">{errors.purchase_price.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="current_price">Current Unit Price *</Label>
          <Input id="current_price" type="number" step="0.01" {...register('current_price')} />
          {errors.current_price && <p className="text-sm text-error">{errors.current_price.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="interest_rate">Interest Rate (% for FD/Bonds)</Label>
          <Input id="interest_rate" type="number" step="0.01" {...register('interest_rate')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="maturity_date">Maturity Date (FD/Bonds)</Label>
          <Input id="maturity_date" type="date" {...register('maturity_date')} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="broker">Broker / Platform</Label>
          <Input id="broker" placeholder="e.g. Zerodha, Groww" {...register('broker')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="folio_number">Folio / Account Number</Label>
          <Input id="folio_number" placeholder="Account identifier" {...register('folio_number')} />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Input id="notes" placeholder="Notes..." {...register('notes')} />
      </div>

      <div className="pt-4 flex justify-end gap-3 sticky bottom-0 bg-white pb-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Add Investment'}
        </button>
      </div>
    </form>
  )
}
