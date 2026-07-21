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
import { AlertCircle, TrendingUp, ShieldCheck, Zap } from 'lucide-react'

export default function FinancialPlanningWorkspace() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingGoal, setEditingGoal] = useState<any>(null)
  const [goalToDelete, setGoalToDelete] = useState<any>(null)
  const [contributeGoal, setContributeGoal] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'goals' | 'retirement' | 'tax'>('overview')

  const queryClient = useQueryClient()

  // Fetch the new aggregated workspace overview
  const { data: overviewRes, isLoading: isOverviewLoading } = useQuery({
    queryKey: ['financial-overview'],
    queryFn: () => goalsApi.getOverview().then(r => r.data),
  })

  // List of all user objectives
  const { data: listRes, isLoading: isListLoading } = useQuery({
    queryKey: ['goals'],
    queryFn: () => goalsApi.list().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => goalsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['financial-overview'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Objective deleted successfully')
      setGoalToDelete(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete objective')
    }
  })

  const overview = overviewRes?.data?.overview || {
    total_target: 0,
    total_funding: 0,
    overall_progress: 0,
    health_summary: { 'On Track': 0, 'At Risk': 0, 'Off Track': 0, 'Completed': 0 },
    total_objectives: 0
  }
  const allObjectives = overviewRes?.data?.objectives || []

  // Calculate effective total funding including forecasted allocations
  const effectiveTotalFunding = allObjectives.reduce((sum: number, obj: any) => sum + (obj.current_funding || 0) + (obj.allocated_monthly_surplus || 0), 0)
  const effectiveOverallProgress = overview.total_target > 0 ? (effectiveTotalFunding / overview.total_target) * 100 : 0

  // Derived objectives grouped by priority
  const priorityObjectives = [...allObjectives].sort((a, b) => b.priority_score - a.priority_score).slice(0, 3)

  // Extract all recommendations across all objectives
  const allRecommendations = allObjectives.reduce((acc: any[], obj: any) => {
    return [...acc, ...(obj.recommendations || []).map((r: any) => ({ ...r, objective_name: obj.name }))]
  }, [])

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
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex justify-between items-end mb-6">
        <div>
        </div>
        <button onClick={handleAdd} className="btn-primary shadow-lg hover:shadow-xl transition-shadow flex items-center gap-2 px-6">
          <span className="material-symbols-outlined text-[20px]">add</span>
          New Objective
        </button>
      </div>

      {/* Workspace Navigation */}
      <div className="flex gap-4 border-b border-outline-variant/30 mb-8 pb-1">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'goals', label: 'Custom Goals' },
          { id: 'retirement', label: 'Retirement' },
          { id: 'tax', label: 'Tax Planning' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`pb-3 px-4 font-semibold text-sm transition-all relative ${activeTab === tab.id ? 'text-primary' : 'text-on-surface-variant hover:text-[#1f1b18]'}`}
          >
            {tab.label}
            {activeTab === tab.id && (
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Hero Overview Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="finora-card p-6 bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                  <span className="material-symbols-outlined">account_balance_wallet</span>
                </div>
                <h3 className="font-semibold text-on-surface">Total Managed Target</h3>
              </div>
              <p className="text-3xl font-display font-bold text-[#1f1b18] mb-1">{formatCurrency(overview.total_target)}</p>
              <p className="text-sm text-on-surface-variant">Across {overview.total_objectives} active objectives</p>
            </div>
            
            <div className="finora-card p-6 border border-outline-variant/50 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <span className="material-symbols-outlined text-6xl">savings</span>
              </div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center">
                  <span className="material-symbols-outlined">payments</span>
                </div>
                <h3 className="font-semibold text-on-surface">Current Funding</h3>
              </div>
              <p className="text-3xl font-display font-bold text-[#1f1b18] mb-1">{formatCurrency(effectiveTotalFunding)}</p>
              <div className="flex items-center gap-2 mt-2">
                <div className="flex-1 h-2 bg-surface-variant rounded-full overflow-hidden">
                  <div className="h-full bg-secondary rounded-full" style={{ width: `${Math.min(effectiveOverallProgress, 100)}%` }} />
                </div>
                <span className="text-sm font-semibold text-secondary">{effectiveOverallProgress.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-8 mt-8">
            
            {/* Main Objectives List */}
            <div className="space-y-6">
              <div className="flex justify-between items-center mb-2">
                <h2 className="text-xl font-display font-bold text-[#1f1b18]">Priority Objectives</h2>
                <button className="text-sm font-semibold text-primary hover:underline">View All</button>
              </div>

              {isOverviewLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-32 animate-pulse bg-surface-variant/30 rounded-xl" />
                  ))}
                </div>
              ) : priorityObjectives.length > 0 ? (
                <div className="space-y-4">
                  {priorityObjectives.map((obj: any) => {
                    const requiredSip = obj.required_sip || 0;
                    const allocated = obj.allocated_monthly_surplus || 0;
                    const isFullyFunded = allocated >= requiredSip && requiredSip > 0;
                    const hasExcess = allocated > requiredSip;
                    
                    return (
                      <div key={obj.id} className="finora-card p-5 group hover:border-primary/30 transition-colors border border-outline-variant/50">
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex gap-4">
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-inner ${
                              obj.health === 'On Track' ? 'bg-primary/10 text-primary' :
                              obj.health === 'At Risk' ? 'bg-secondary/10 text-secondary' :
                              obj.health === 'Off Track' ? 'bg-tertiary/10 text-tertiary' :
                              'bg-surface-variant text-on-surface'
                            }`}>
                              <span className="material-symbols-outlined text-2xl">
                                {obj.goal_type.toLowerCase().includes('house') ? 'real_estate_agent' :
                                 obj.goal_type.toLowerCase().includes('retire') ? 'beach_access' : 'target'}
                              </span>
                            </div>
                            <div>
                              <h4 className="font-bold text-lg text-[#1f1b18]">{obj.name}</h4>
                              <div className="flex items-center gap-3 text-sm mt-1">
                                <span className="text-on-surface-variant flex items-center gap-1">
                                  <span className="material-symbols-outlined text-[16px]">category</span> {obj.goal_type}
                                </span>
                                <span className="text-on-surface-variant flex items-center gap-1">
                                  <span className="material-symbols-outlined text-[16px]">priority</span> Priority: {obj.priority_score}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider flex items-center gap-1 ${
                              obj.health === 'On Track' ? 'bg-primary/10 text-primary' :
                              obj.health === 'At Risk' ? 'bg-secondary/10 text-secondary' :
                              'bg-tertiary/10 text-tertiary'
                            }`}>
                              {obj.health === 'On Track' && <ShieldCheck size={14} />}
                              {obj.health === 'At Risk' && <AlertCircle size={14} />}
                              {obj.health === 'Off Track' && <TrendingUp size={14} />}
                              {obj.health}
                            </span>
                            <button onClick={() => handleEdit(obj)} className="p-1.5 text-on-surface-variant hover:text-primary hover:bg-surface-variant rounded-md opacity-0 group-hover:opacity-100 transition-opacity">
                              <span className="material-symbols-outlined text-[18px]">edit</span>
                            </button>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-8 items-end">
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="font-bold text-[#1f1b18] text-lg">{formatCurrency(obj.current_funding + allocated)}</span>
                              <span className="text-on-surface-variant font-medium">of {formatCurrency(obj.target_amount)}</span>
                            </div>
                            <div className="w-full h-2.5 bg-surface-variant rounded-full overflow-hidden">
                              <div 
                                className="h-full transition-all duration-1000 ease-out bg-primary"
                                style={{ width: `${Math.min(((obj.current_funding + allocated) / obj.target_amount) * 100, 100)}%` }}
                              />
                            </div>
                          </div>
                          
                          <div className="text-right">
                             <p className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold mb-1">Required SIP / Allocated</p>
                             <div className="flex items-center justify-end gap-2">
                               <p className="text-sm font-semibold text-on-surface-variant">{formatCurrency(requiredSip)}</p>
                               <span className="text-on-surface-variant/50">/</span>
                               <p className={`text-base font-bold ${isFullyFunded ? 'text-primary' : 'text-secondary'}`}>{formatCurrency(allocated)}</p>
                             </div>
                             {hasExcess && (
                               <p className="text-xs font-semibold text-tertiary mt-1">
                                 +{formatCurrency(allocated - requiredSip)} excess surplus applied
                               </p>
                             )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="finora-card p-12 text-center border-dashed border-2 border-outline-variant">
                  <div className="w-16 h-16 bg-primary-container rounded-full flex items-center justify-center mx-auto mb-4 text-primary">
                    <span className="material-symbols-outlined text-3xl">add_task</span>
                  </div>
                  <h3 className="text-lg font-bold text-[#1f1b18] mb-2">No active objectives</h3>
                  <p className="text-on-surface-variant mb-6 max-w-md mx-auto">Start building your financial plan by creating your first wealth objective, savings goal, or retirement target.</p>
                  <button onClick={handleAdd} className="btn-primary">Create Your First Objective</button>
                </div>
              )}
            </div>


          </div>
        </>
      )}

      {/* Goal creation/editing modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingGoal ? 'Edit Objective' : 'Create Financial Objective'}</DialogTitle>
            <DialogDescription>
              {editingGoal ? 'Modify your planning parameters below.' : 'Define a new target for the Finora Planning Engine.'}
            </DialogDescription>
          </DialogHeader>
          <GoalForm 
            initialData={editingGoal} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>

      {/* Goal deletion modal */}
      <ConfirmDialog
        open={!!goalToDelete}
        onCancel={() => setGoalToDelete(null)}
        onConfirm={() => deleteMutation.mutate(goalToDelete?.id)}
        title="Delete Objective"
        description={`Are you sure you want to delete "${goalToDelete?.name}"? You will lose history of this objective.`}
        confirmLabel={deleteMutation.isPending ? 'Deleting...' : 'Delete'}
        variant="danger"
      />
    </div>
  )
}
