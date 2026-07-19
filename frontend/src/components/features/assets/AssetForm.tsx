'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { assetsApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  asset_type: z.enum(['property', 'vehicle', 'jewellery', 'electronics', 'artwork', 'other']),
  purchase_price: z.coerce.number().positive('Purchase price must be positive'),
  current_value: z.coerce.number().positive('Current value must be positive'),
  purchase_date: z.string().min(1, 'Purchase date is required'),
  description: z.string().optional(),
  location: z.string().optional(),
  serial_number: z.string().optional(),
  depreciation_rate: z.coerce.number().min(0).max(100).optional(),
  is_insured: z.boolean().default(false),
})

type FormData = z.infer<typeof schema>

interface AssetFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function AssetForm({ initialData, onSuccess, onCancel }: AssetFormProps) {
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
      asset_type: 'other',
      purchase_price: 0,
      current_value: 0,
      purchase_date: new Date().toISOString().split('T')[0],
      description: '',
      location: '',
      serial_number: '',
      depreciation_rate: 0,
      is_insured: false,
    },
  })

  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name,
        asset_type: initialData.asset_type,
        purchase_price: initialData.purchase_price,
        current_value: initialData.current_value,
        purchase_date: initialData.purchase_date,
        description: initialData.description || '',
        location: initialData.location || '',
        serial_number: initialData.serial_number || '',
        depreciation_rate: initialData.depreciation_rate || 0,
        is_insured: initialData.is_insured || false,
      })
    }
  }, [initialData, reset])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      return isEditing 
        ? assetsApi.update(initialData.id, data)
        : assetsApi.create(data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] })
      queryClient.invalidateQueries({ queryKey: ['assets-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isEditing ? 'Asset updated' : 'Asset created')
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
        <Label htmlFor="name">Asset Name *</Label>
        <Input id="name" placeholder="e.g. Apartment, Tesla Model 3" {...register('name')} />
        {errors.name && <p className="text-sm text-error">{errors.name.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="asset_type">Asset Type *</Label>
          <select 
            id="asset_type" 
            className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
            {...register('asset_type')}
          >
            <option value="property">Property</option>
            <option value="vehicle">Vehicle</option>
            <option value="jewellery">Jewellery</option>
            <option value="electronics">Electronics</option>
            <option value="artwork">Artwork</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="purchase_date">Purchase Date *</Label>
          <Input id="purchase_date" type="date" {...register('purchase_date')} />
          {errors.purchase_date && <p className="text-sm text-error">{errors.purchase_date.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="purchase_price">Purchase Price *</Label>
          <Input id="purchase_price" type="number" step="0.01" {...register('purchase_price')} />
          {errors.purchase_price && <p className="text-sm text-error">{errors.purchase_price.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="current_value">Current Estimated Value *</Label>
          <Input id="current_value" type="number" step="0.01" {...register('current_value')} />
          {errors.current_value && <p className="text-sm text-error">{errors.current_value.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="location">Location / Storage</Label>
          <Input id="location" placeholder="e.g. Home, Bank Safe" {...register('location')} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="serial_number">Serial Number / ID</Label>
          <Input id="serial_number" placeholder="e.g. VIN or model no." {...register('serial_number')} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="depreciation_rate">Annual Depreciation Rate (%)</Label>
          <Input id="depreciation_rate" type="number" step="0.1" placeholder="e.g. 5" {...register('depreciation_rate')} />
        </div>
        <div className="flex items-center gap-2 py-2 self-end">
          <input 
            id="is_insured" 
            type="checkbox" 
            className="rounded border-[#d5c3b8] text-primary focus:ring-primary w-4 h-4"
            {...register('is_insured')}
          />
          <Label htmlFor="is_insured" className="cursor-pointer">Insured Asset</Label>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Input id="description" placeholder="Description of the asset..." {...register('description')} />
      </div>

      <div className="pt-4 flex justify-end gap-3 sticky bottom-0 bg-white pb-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : isEditing ? 'Save Changes' : 'Add Asset'}
        </button>
      </div>
    </form>
  )
}
