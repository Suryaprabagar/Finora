'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { insuranceApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { InsuranceForm } from '@/components/features/insurance/InsuranceForm'
import { InsuranceClaimForm } from '@/components/features/insurance/InsuranceClaimForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'

export default function InsurancePage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<any>(null)
  const [policyToDelete, setPolicyToDelete] = useState<any>(null)
  const [claimPolicy, setClaimPolicy] = useState<any>(null)

  const queryClient = useQueryClient()

  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['insurance-summary'],
    queryFn: () => insuranceApi.getSummary().then(r => r.data),
  })

  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['insurance'],
    queryFn: () => insuranceApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => insuranceApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['insurance'] })
      queryClient.invalidateQueries({ queryKey: ['insurance-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Insurance policy deleted successfully')
      setPolicyToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete policy')
    }
  })

  const summary = summaryRes?.data || { total_coverage: 0, total_premium: 0, active_count: 0 }
  const policies = listRes?.data || []

  const handleAdd = () => {
    setEditingPolicy(null)
    setIsModalOpen(true)
  }

  const handleEdit = (policy: any) => {
    setEditingPolicy(policy)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setTimeout(() => setEditingPolicy(null), 200)
  }

  return (
    <div>
      <PageHeader
        title="Insurance"
        subtitle="Manage your insurance policies"
        actions={
          <button onClick={handleAdd} className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            Add Policy
          </button>
        }
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Total Coverage"
          value={formatCurrency(summary.total_coverage)}
          subtitle={`${summary.active_count || 0} Active Policies`}
          loading={isSummaryLoading}
          icon="shield"
          iconBg="bg-tertiary-fixed"
        />
        <StatCard
          title="Total Annual Premium"
          value={formatCurrency(summary.total_premium)}
          loading={isSummaryLoading}
          icon="payments"
        />
      </div>

      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6 text-[#1f1b18]">Active Policies</h3>
        
        {isListLoading ? (
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <div key={i} className="h-24 animate-pulse bg-surface-variant/30 rounded-lg"></div>
            ))}
          </div>
        ) : policies.length > 0 ? (
          <div className="space-y-4">
            {policies.map((policy: any) => (
              <div key={policy.id} className="border border-outline-variant rounded-xl p-4 flex justify-between items-center hover:bg-surface-variant/10 transition-colors group relative">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-base text-[#1f1b18]">{policy.policy_name}</h4>
                    <span className="text-[10px] bg-secondary-container text-on-secondary-container px-2 py-0.5 rounded capitalize font-medium">
                      {policy.policy_type}
                    </span>
                    <span className="text-xs text-on-surface-variant">• {policy.provider}</span>
                  </div>
                  <p className="text-xs text-on-surface-variant mt-1">
                    No: {policy.policy_number || 'N/A'} • Premium: {formatCurrency(policy.annual_premium)} ({policy.premium_frequency}) • Next Renewal: {formatDate(policy.renewal_date)}
                  </p>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-xs text-on-surface-variant mb-0.5">Coverage</p>
                    <p className="font-bold text-base text-[#1f1b18]">{formatCurrency(policy.coverage_amount)}</p>
                  </div>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-0.5">
                    <button 
                      onClick={() => setClaimPolicy(policy)}
                      className="text-xs font-semibold text-primary hover:bg-primary-container/30 px-2.5 py-1.5 rounded transition-colors mr-2"
                    >
                      Log Claim
                    </button>
                    <button onClick={() => handleEdit(policy)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md">
                      <span className="material-symbols-outlined text-[18px]">edit</span>
                    </button>
                    <button onClick={() => setPolicyToDelete(policy)} className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/50 rounded-md">
                      <span className="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-on-surface-variant mb-4">No active policies registered.</p>
            <button onClick={handleAdd} className="btn-primary">Add a Policy</button>
          </div>
        )}
      </div>

      {/* Insurance creation/editing modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingPolicy ? 'Edit Insurance Policy' : 'Add Insurance Policy'}</DialogTitle>
            <DialogDescription>
              {editingPolicy ? 'Modify insurance coverage details.' : 'Register a new insurance policy to keep track of coverage.'}
            </DialogDescription>
          </DialogHeader>
          <InsuranceForm 
            initialData={editingPolicy} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      {/* Claims Modal */}
      <Dialog open={!!claimPolicy} onOpenChange={(open) => !open && setClaimPolicy(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Log Insurance Claim</DialogTitle>
            <DialogDescription>
              File a claim against this policy to record medical, vehicle, or other insurance claims.
            </DialogDescription>
          </DialogHeader>
          {claimPolicy && (
            <InsuranceClaimForm 
              policy={claimPolicy}
              onSuccess={() => setClaimPolicy(null)}
              onCancel={() => setClaimPolicy(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!policyToDelete}
        onClose={() => setPolicyToDelete(null)}
        onConfirm={() => deleteMutation.mutate(policyToDelete?.id)}
        title="Delete Policy"
        description={`Are you sure you want to delete "${policyToDelete?.policy_name}"? You will lose coverage tracking details.`}
        confirmText={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        isDestructive
      />
    </div>
  )
}
