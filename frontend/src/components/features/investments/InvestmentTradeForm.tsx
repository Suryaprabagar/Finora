'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { investmentsApi, bankAccountsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  action: z.enum(['buy', 'sell']),
  quantity: z.coerce.number().positive('Quantity must be positive'),
  price: z.coerce.number().positive('Price must be positive'),
  bank_account_id: z.string().optional(),
})

type FormData = z.infer<typeof schema>

interface InvestmentTradeFormProps {
  investment: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function InvestmentTradeForm({ investment, onSuccess, onCancel }: InvestmentTradeFormProps) {
  const queryClient = useQueryClient()

  const { data: accountsRes } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankAccountsApi.list().then(r => r.data),
  })
  const accounts = accountsRes?.data || []

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      action: 'buy',
      quantity: 1,
      price: investment.current_price || investment.purchase_price,
      bank_account_id: '',
    },
  })

  const action = watch('action')
  const quantity = watch('quantity')
  const price = watch('price')

  const totalAmount = (quantity || 0) * (price || 0)

  const mutation = useMutation({
    mutationFn: (data: FormData) => investmentsApi.trade(investment.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(`Successfully ${action === 'buy' ? 'bought' : 'sold'} shares!`)
      if (onSuccess) onSuccess()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (Array.isArray(detail)) {
        toast.error(detail[0].msg || 'Validation Error')
      } else {
        toast.error(detail || 'Failed to trade investment')
      }
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
      <div className="p-4 bg-surface-container rounded-lg border border-outline-variant/30 flex justify-between items-center mb-4">
        <div>
          <h4 className="font-bold text-on-surface">{investment.name}</h4>
          <p className="text-sm text-on-surface-variant">Current Holdings: <span className="font-bold">{investment.quantity}</span> units</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] uppercase font-bold tracking-wide text-on-surface-variant">Avg Price</p>
          <p className="font-bold text-on-surface">{Number(investment.purchase_price).toFixed(2)}</p>
        </div>
      </div>

      <div className="space-y-2">
        <Label>Action *</Label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" value="buy" {...register('action')} className="accent-primary w-4 h-4" />
            <span className="text-sm font-medium">Buy More</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" value="sell" {...register('action')} className="accent-error w-4 h-4" />
            <span className="text-sm font-medium">Sell Shares</span>
          </label>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="quantity">Quantity *</Label>
          <Input id="quantity" type="number" step="0.0001" {...register('quantity')} />
          {errors.quantity && <p className="text-sm text-error">{errors.quantity.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="price">Price Per Unit *</Label>
          <Input id="price" type="number" step="0.01" {...register('price')} />
          {errors.price && <p className="text-sm text-error">{errors.price.message}</p>}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="bank_account_id">Linked Bank Account</Label>
        <select 
          id="bank_account_id" 
          className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
          {...register('bank_account_id')}
        >
          <option value="">None (Do not affect balance)</option>
          {accounts.map((acc: any) => (
            <option key={acc.id} value={acc.id}>{acc.name} (Bal: {acc.balance})</option>
          ))}
        </select>
        <p className="text-[10px] text-on-surface-variant italic">
          {action === 'buy' ? 'Cost will be deducted from this account.' : 'Proceeds will be added to this account.'}
        </p>
      </div>

      <div className="bg-primary/5 p-4 rounded-lg mt-4 flex justify-between items-center">
        <span className="font-bold text-on-surface-variant uppercase text-xs tracking-wider">Total Amount</span>
        <span className="font-bold text-xl text-primary">₹{totalAmount.toFixed(2)}</span>
      </div>

      <div className="pt-4 flex justify-end gap-3 sticky bottom-0 bg-white pb-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className={`btn-primary ${action === 'sell' ? 'bg-error hover:bg-error/90 text-white border-error' : ''}`} disabled={isSubmitting}>
          {isSubmitting ? 'Processing...' : action === 'buy' ? 'Confirm Purchase' : 'Confirm Sale'}
        </button>
      </div>
    </form>
  )
}
