'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { goalsApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/shared/StatCard'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { GoalForm } from '@/components/features/goals/GoalForm'
import { GoalContributionForm } from '@/components/features/goals/GoalContributionForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'

export default function GoalsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingGoal, setEditingGoal] = useState<any>(null)
  const [goalToDelete, setGoalToDelete] = useState<any>(null)
  const [contributeGoal, setContributeGoal] = useState<any>(null)

  const queryClient = useQueryClient()

  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['goals-summary'],
    queryFn: () => goalsApi.getSummary().then(r => r.data),
  })

  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['goals'],
    queryFn: () => goalsApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => goalsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['goals-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Goal deleted successfully')
      setGoalToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete goal')
    }
  })

  const summary = summaryRes?.data || { total_saved: 0, total_target: 0, completed_count: 0, active_count: 0, monthly_contributions: 0 }
  const goals = listRes?.data || []

  const handleAdd = () => {
    setEditingGoal(null)
    setIsModalOpen(true)
  }

  const handleEdit = (goal: any) => {
    setEditingGoal(goal)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setTimeout(() => setEditingGoal(null), 200)
  }

  return (
    <div>
      <PageHeader
        title="Goals"
        subtitle="Track your financial goals"
        actions={
          <button onClick={handleAdd} className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">add</span>
            New Goal
          </button>
        }
      />

      {/* Summary Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Total Saved"
          value={formatCurrency(summary.total_saved)}
          subtitle={`Target: ${formatCurrency(summary.total_target)}`}
          loading={isSummaryLoading}
          icon="savings"
          iconBg="bg-primary-fixed"
        />
        <StatCard
          title="Monthly Savings"
          value={formatCurrency(summary.monthly_contributions)}
          loading={isSummaryLoading}
          icon="trending_up"
          iconBg="bg-secondary-fixed"
        />
        <StatCard
          title="Active Goals"
          value={`${summary.active_count} Active`}
          subtitle={`${summary.completed_count || 0} Completed`}
          loading={isSummaryLoading}
          icon="flag"
        />
      </div>

      <div className="finora-card p-6">
        <h3 className="font-display font-bold text-lg mb-6 text-[#1f1b18]">Your Goals</h3>
        
        {isListLoading ? (
          <div className="space-y-6">
            {[1, 2].map((i) => (
              <div key={i} className="h-28 animate-pulse bg-surface-variant/30 rounded-lg"></div>
            ))}
          </div>
        ) : goals.length > 0 ? (
          <div className="space-y-6">
            {goals.map((goal: any) => {
              const progress = goal.progress_percentage || 0;
              return (
                <div key={goal.id} className="border border-outline-variant rounded-xl p-5 hover:bg-surface-variant/10 transition-colors group relative">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span 
                          className="w-3 h-3 rounded-full shrink-0" 
                          style={{ backgroundColor: goal.color || 'var(--primary)' }}
                        />
                        <h4 className="font-semibold text-base text-[#1f1b18]">{goal.name}</h4>
                        <span className={`text-xs px-2 py-0.5 rounded capitalize ${
                          goal.status === 'completed' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-secondary-container text-on-secondary-container'
                        }`}>
                          {goal.status}
                        </span>
                      </div>
                      <p className="text-xs text-on-surface-variant mt-1">
                        Category: {goal.category} {goal.target_date ? `• Target: ${formatDate(goal.target_date)}` : ''}
                      </p>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                      {goal.status !== 'completed' && (
                        <button 
                          onClick={() => setContributeGoal(goal)}
                          className="text-xs font-semibold text-primary hover:bg-primary-container/30 px-2.5 py-1.5 rounded transition-colors mr-2"
                        >
                          Contribute
                        </button>
                      )}
                      <button onClick={() => handleEdit(goal)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md">
                        <span className="material-symbols-outlined text-[18px]">edit</span>
                      </button>
                      <button onClick={() => setGoalToDelete(goal)} className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error-container/50 rounded-md">
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-bold text-[#1f1b18]">{formatCurrency(goal.current_amount)}</span>
                      <span className="text-on-surface-variant">of {formatCurrency(goal.target_amount)} ({progress}%)</span>
                    </div>
                    <div className="w-full h-3 bg-surface-variant rounded-full overflow-hidden">
                      <div 
                        className="h-full transition-all"
                        style={{ 
                          width: `${Math.min(progress, 100)}%`,
                          backgroundColor: goal.color || 'var(--primary)'
                        }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-on-surface-variant mb-4">No goals configured yet.</p>
            <button onClick={handleAdd} className="btn-primary">Create a Goal</button>
          </div>
        )}
      </div>

      {/* Goal creation/editing modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingGoal ? 'Edit Savings Goal' : 'Create Savings Goal'}</DialogTitle>
            <DialogDescription>
              {editingGoal ? 'Modify your savings parameters below.' : 'Set up a new target goal and timeline.'}
            </DialogDescription>
          </DialogHeader>
          <GoalForm 
            initialData={editingGoal} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      {/* Goal Contribution modal */}
      <Dialog open={!!contributeGoal} onOpenChange={(open) => !open && setContributeGoal(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Goal Contribution</DialogTitle>
            <DialogDescription>
              Add savings towards your goal.
            </DialogDescription>
          </DialogHeader>
          {contributeGoal && (
            <GoalContributionForm 
              goal={contributeGoal}
              onSuccess={() => setContributeGoal(null)}
              onCancel={() => setContributeGoal(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Goal deletion modal */}
      <ConfirmDialog
        isOpen={!!goalToDelete}
        onClose={() => setGoalToDelete(null)}
        onConfirm={() => deleteMutation.mutate(goalToDelete?.id)}
        title="Delete Savings Goal"
        description={`Are you sure you want to delete "${goalToDelete?.name}"? You will lose history of this goal.`}
        confirmText={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        isDestructive
      />
    </div>
  )
}
