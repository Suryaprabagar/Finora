'use client'

import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { assetsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { AssetForm } from '@/components/features/assets/AssetForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'

export default function AssetsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingAsset, setEditingAsset] = useState<any>(null)
  const [assetToDelete, setAssetToDelete] = useState<any>(null)

  const closeTimerRef = useRef<ReturnType<typeof setTimeout>>(null)
  useEffect(() => {
    return () => {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current)
    }
  }, [])

  const queryClient = useQueryClient()

  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['assets-summary'],
    queryFn: () => assetsApi.getSummary().then(r => r.data),
  })

  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['assets'],
    queryFn: () => assetsApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => assetsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] })
      queryClient.invalidateQueries({ queryKey: ['assets-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Asset deleted successfully')
      setAssetToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete asset')
    }
  })

  const summary = summaryRes?.data || { total_value: 0, total_purchase: 0, total_appreciation: 0 }
  const assets = listRes?.data || []

  const handleAdd = () => {
    setEditingAsset(null)
    setIsModalOpen(true)
  }

  const handleEdit = (asset: any) => {
    setEditingAsset(asset)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    closeTimerRef.current = setTimeout(() => setEditingAsset(null), 200)
  }

  return (
    <div>
      <PageHeader
        title="Assets"
        subtitle="Keep track of your valuable possessions"
        actions={
          <button onClick={handleAdd} className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Asset
          </button>
        }
      />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Total Assets Value"
          value={formatCurrency(summary.total_value)}
          loading={isSummaryLoading}
          icon="home_work"
          iconBg="bg-primary-fixed"
        />
        <StatCard
          title="Total Invested / Purchase"
          value={formatCurrency(summary.total_purchase)}
          loading={isSummaryLoading}
          icon="payments"
          iconBg="bg-secondary-fixed"
        />
        <StatCard
          title="Net Appreciation"
          value={formatCurrency(summary.total_appreciation)}
          loading={isSummaryLoading}
          icon="trending_up"
          iconBg={summary.total_appreciation >= 0 ? "bg-tertiary-fixed text-tertiary" : "bg-error-container text-error"}
        />
      </div>

      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6 text-[#1f1b18]">Your Assets</h3>
        
        {isListLoading ? (
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <div key={i} className="h-24 animate-pulse bg-surface-variant/30 rounded-lg"></div>
            ))}
          </div>
        ) : assets.length > 0 ? (
          <div className="space-y-4">
            {assets.map((asset: any) => {
              const diff = asset.appreciation_loss || 0;
              const percent = asset.appreciation_percent || 0;
              return (
                <div key={asset.id} className="border border-outline-variant rounded-xl p-4 flex justify-between items-center hover:bg-surface-variant/10 transition-colors group relative">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-base text-[#1f1b18]">{asset.name}</h4>
                      <span className="text-[10px] bg-secondary-container text-on-secondary-container px-2 py-0.5 rounded capitalize font-medium">
                        {asset.asset_type}
                      </span>
                      {asset.is_insured && (
                        <span className="text-[10px] bg-tertiary-container text-on-tertiary-container px-2 py-0.5 rounded font-semibold">
                          Insured
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-on-surface-variant mt-1">
                      Purchased on {formatDate(asset.purchase_date)} for {formatCurrency(asset.purchase_price)} {asset.location ? `• Location: ${asset.location}` : ''}
                    </p>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="font-bold text-base text-[#1f1b18]">{formatCurrency(asset.current_value)}</p>
                      <p className={`text-xs font-semibold ${diff >= 0 ? 'text-tertiary' : 'text-error'}`}>
                        {diff >= 0 ? '+' : ''}{formatCurrency(diff)} ({diff >= 0 ? '+' : ''}{percent.toFixed(1)}%)
                      </p>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-0.5">
                      <button onClick={() => handleEdit(asset)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md">
                        <span className="material-symbols-outlined text-[18px]">edit</span>
                      </button>
                      <button onClick={() => setAssetToDelete(asset)} className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/50 rounded-md">
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-on-surface-variant mb-4">No assets tracked yet.</p>
            <button onClick={handleAdd} className="btn-primary">Add an Asset</button>
          </div>
        )}
      </div>

      {/* Asset creation/editing modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingAsset ? 'Edit Asset Details' : 'Add Asset'}</DialogTitle>
            <DialogDescription>
              {editingAsset ? 'Update physical or digital asset details.' : 'Register a new asset to track current market value.'}
            </DialogDescription>
          </DialogHeader>
          <AssetForm 
            initialData={editingAsset} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!assetToDelete}
        onCancel={() => setAssetToDelete(null)}
        onConfirm={() => deleteMutation.mutate(assetToDelete?.id)}
        title="Delete Asset"
        description={`Are you sure you want to delete "${assetToDelete?.name}"? You will lose history of this asset.`}
        confirmLabel={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        variant="danger"
      />
    </div>
  )
}
