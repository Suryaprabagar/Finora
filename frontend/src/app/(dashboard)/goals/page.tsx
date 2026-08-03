'use client'

import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { goalsApi } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { GoalForm } from '@/components/features/goals/GoalForm'
import { GoalContributionForm } from '@/components/features/goals/GoalContributionForm'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { toast } from 'sonner'
import {
  AlertCircle, ShieldCheck, CheckCircle2, Target, Trash2, Pencil,
  PlusCircle, TrendingDown, TrendingUp, Info,
} from 'lucide-react'

// ── Project color map for health statuses ─────────────────────────────────────
const healthConfig: Record<string, {
  bg: string; text: string; border: string; bar: string
  icon: React.ReactNode; label: string
}> = {
  'On Track':  { bg: 'bg-primary/10',   text: 'text-primary',   border: 'border-primary/20',   bar: 'bg-primary',   icon: <ShieldCheck size={13} />,  label: 'On Track'  },
  'At Risk':   { bg: 'bg-secondary/15', text: 'text-secondary', border: 'border-secondary/25', bar: 'bg-secondary', icon: <AlertCircle size={13} />,  label: 'At Risk'   },
  'Off Track': { bg: 'bg-error/10',     text: 'text-error',     border: 'border-error/20',     bar: 'bg-error',     icon: <TrendingDown size={13} />, label: 'Off Track' },
  'Completed': { bg: 'bg-tertiary/10',  text: 'text-tertiary',  border: 'border-tertiary/20',  bar: 'bg-tertiary',  icon: <CheckCircle2 size={13} />, label: 'Completed' },
}

function HealthBadge({ health }: { health: string }) {
  const cfg = healthConfig[health] ?? healthConfig['At Risk']
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${cfg.bg} ${cfg.text}`}>
      {cfg.icon}{cfg.label}
    </span>
  )
}

function goalIcon(goalType: string) {
  const t = goalType.toLowerCase()
  if (t.includes('house') || t.includes('home')) return 'real_estate_agent'
  if (t.includes('retire'))                       return 'beach_access'
  if (t.includes('education') || t.includes('college')) return 'school'
  if (t.includes('vehicle') || t.includes('car')) return 'directions_car'
  if (t.includes('emergency'))                    return 'emergency'
  if (t.includes('business'))                     return 'business_center'
  if (t.includes('wealth'))                       return 'diamond'
  return 'target'
}

// ── Goal Card ──────────────────────────────────────────────────────────────────
function GoalCard({
  obj, portfolioReturn, onEdit, onDelete, onContribute,
}: {
  obj: any
  portfolioReturn: number
  onEdit: (g: any) => void
  onDelete: (g: any) => void
  onContribute: (g: any) => void
}) {
  const cfg          = healthConfig[obj.health] ?? healthConfig['At Risk']
  const requiredSip  = obj.required_sip ?? 0
  const allocated    = obj.allocated_monthly_surplus ?? 0
  const isFullyFunded = requiredSip > 0 && allocated >= requiredSip
  const gap          = requiredSip > 0 && !isFullyFunded ? requiredSip - allocated : 0
  const excess       = isFullyFunded && allocated > requiredSip ? allocated - requiredSip : 0
  const avgReturn    = obj.avg_annual_return ?? portfolioReturn
  const actualFunding = obj.current_funding + allocated
  const remaining    = Math.max(0, obj.target_amount - actualFunding)
  const progress     = obj.target_amount > 0
    ? Math.min((actualFunding / obj.target_amount) * 100, 100)
    : 0

  return (
    <div className={`finora-card p-5 group transition-all hover:shadow-md border ${cfg.border}`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex gap-3 items-start flex-1 min-w-0">
          <div className={`flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center ${cfg.bg} ${cfg.text}`}>
            <span className="material-symbols-outlined text-xl">{goalIcon(obj.goal_type)}</span>
          </div>
          <div className="min-w-0">
            <h4 className="font-bold text-[#1f1b18] truncate">{obj.name}</h4>
            <p className="text-xs text-on-surface-variant mt-0.5">
              {obj.goal_type} · Priority {obj.priority_score}
              {obj.target_date && ` · Due ${formatDate(obj.target_date)}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0 ml-2">
          <HealthBadge health={obj.health} />
          <button onClick={() => onContribute(obj)} title="Add contribution"
            className="p-1.5 rounded-md text-on-surface-variant hover:text-primary hover:bg-primary/10 opacity-0 group-hover:opacity-100 transition-all">
            <PlusCircle size={16} />
          </button>
          <button onClick={() => onEdit(obj)} title="Edit"
            className="p-1.5 rounded-md text-on-surface-variant hover:text-primary hover:bg-primary/10 opacity-0 group-hover:opacity-100 transition-all">
            <Pencil size={15} />
          </button>
          <button onClick={() => onDelete(obj)} title="Delete"
            className="p-1.5 rounded-md text-on-surface-variant hover:text-error hover:bg-error/10 opacity-0 group-hover:opacity-100 transition-all">
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {/* Progress */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1.5">
          <span className="font-bold text-[#1f1b18]">{formatCurrency(actualFunding)}</span>
          <span className="text-on-surface-variant">of {formatCurrency(obj.target_amount)}</span>
        </div>
        <div className="w-full h-2 bg-surface-variant rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-700 ease-out ${cfg.bar}`}
               style={{ width: `${progress}%` }} />
        </div>
        <p className="text-xs text-on-surface-variant mt-1 text-right">{progress.toFixed(1)}% funded</p>
      </div>

      {/* SIP metrics */}
      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-outline-variant/30 text-center">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-on-surface-variant font-semibold mb-0.5">Required SIP</p>
          <p className="text-sm font-bold text-[#1f1b18]">
            {requiredSip > 0 ? formatCurrency(requiredSip) : '—'}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-on-surface-variant font-semibold mb-0.5">Allocated</p>
          <p className={`text-sm font-bold ${isFullyFunded ? 'text-primary' : 'text-secondary'}`}>
            {formatCurrency(allocated)}
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-on-surface-variant font-semibold mb-0.5">Est. Completion</p>
          <p className="text-xs font-semibold text-[#1f1b18]">
            {obj.forecast_completion_date
              ? formatDate(obj.forecast_completion_date)
              : obj.health === 'Completed' ? '✓ Done' : '—'}
          </p>
        </div>
      </div>

      {/* Portfolio return rate pill — shows the rate powering this SIP calc */}
      {remaining > 0 && (
        <div className="mt-3 flex items-center justify-between text-[11px] text-on-surface-variant bg-surface-variant/40 rounded-lg px-3 py-1.5">
          <span className="flex items-center gap-1">
            <TrendingUp size={12} className="text-primary" />
            Portfolio return used: <strong className="text-primary ml-1">{avgReturn.toFixed(1)}% p.a.</strong>
          </span>
          <span className="text-on-surface-variant/70">Remaining: {formatCurrency(remaining)}</span>
        </div>
      )}

      {/* Gap / Excess strip */}
      {gap > 0.01 && (
        <div className="mt-2 flex items-center gap-2 text-xs text-secondary bg-secondary/10 rounded-lg px-3 py-2 border border-secondary/20">
          <AlertCircle size={13} className="flex-shrink-0" />
          <span>Gap of <strong>{formatCurrency(gap)}/mo</strong> — increase contributions to stay on track</span>
        </div>
      )}
      {excess > 0.01 && (
        <div className="mt-2 flex items-center gap-2 text-xs text-primary bg-primary/8 rounded-lg px-3 py-2 border border-primary/20">
          <CheckCircle2 size={13} className="flex-shrink-0" />
          <span><strong>{formatCurrency(excess)}/mo</strong> excess surplus applied to this goal</span>
        </div>
      )}
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────────
export default function FinancialPlanningWorkspace() {
  const [isModalOpen, setIsModalOpen]       = useState(false)
  const [editingGoal, setEditingGoal]       = useState<any>(null)
  const [goalToDelete, setGoalToDelete]     = useState<any>(null)
  const [contributeGoal, setContributeGoal] = useState<any>(null)
  const [activeTab, setActiveTab]           = useState<'overview' | 'goals'>('overview')
  const closeTimerRef = useRef<ReturnType<typeof setTimeout>>(null)

  useEffect(() => { return () => { if (closeTimerRef.current) clearTimeout(closeTimerRef.current) } }, [])

  const queryClient = useQueryClient()

  const { data: overviewRes, isLoading } = useQuery({
    queryKey: ['financial-overview'],
    queryFn: () => goalsApi.getOverview().then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => goalsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['financial-overview'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Objective deleted')
      setGoalToDelete(null)
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Failed to delete'),
  })

  const overview: any = overviewRes?.data?.overview ?? {
    total_target: 0, total_funding: 0, overall_progress: 0,
    health_summary: {}, total_objectives: 0, monthly_surplus: 0,
    portfolio_avg_return: 8.0, portfolio_investment_value: 0,
  }
  const allObjectives: any[] = overviewRes?.data?.objectives ?? []
  const byPriority    = [...allObjectives].sort((a, b) => b.priority_score - a.priority_score)
  const top3          = byPriority.slice(0, 3)
  const healthSummary = (overview.health_summary ?? {}) as Record<string, number>
  const portfolioReturn: number = overview.portfolio_avg_return ?? 8.0
  const portfolioValue: number  = overview.portfolio_investment_value ?? 0

  const handleAdd   = () => { setEditingGoal(null); setIsModalOpen(true) }
  const handleEdit  = (g: any) => { setEditingGoal(g); setIsModalOpen(true) }
  const handleClose = () => {
    setIsModalOpen(false)
    closeTimerRef.current = setTimeout(() => setEditingGoal(null), 200)
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">

      {/* Top bar */}
      <div className="flex justify-end">
        <button onClick={handleAdd} className="btn-primary shadow-lg hover:shadow-xl transition-shadow flex items-center gap-2 px-6">
          <span className="material-symbols-outlined text-[20px]">add</span>
          New Objective
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-outline-variant/30 pb-1">
        {([
          { id: 'overview', label: 'Overview' },
          { id: 'goals',    label: `All Objectives (${allObjectives.length})` },
        ] as const).map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`pb-3 px-4 font-semibold text-sm transition-all relative
              ${activeTab === tab.id ? 'text-primary' : 'text-on-surface-variant hover:text-[#1f1b18]'}`}
          >
            {tab.label}
            {activeTab === tab.id && (
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ── */}
      {activeTab === 'overview' && (
        <>
          {/* KPI row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="finora-card p-5 bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20">
              <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Total Target</p>
              <p className="text-2xl font-display font-bold text-[#1f1b18]">{formatCurrency(overview.total_target)}</p>
              <p className="text-xs text-on-surface-variant mt-1">{overview.total_objectives} objectives</p>
            </div>

            <div className="finora-card p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Total Funded</p>
              <p className="text-2xl font-display font-bold text-[#1f1b18]">{formatCurrency(
                overview.total_funding + allObjectives.reduce((sum, obj) => sum + (obj.allocated_monthly_surplus || 0), 0)
              )}</p>
              <div className="flex items-center gap-2 mt-1.5">
                <div className="flex-1 h-1.5 bg-surface-variant rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: `${Math.min(
                    ((overview.total_funding + allObjectives.reduce((sum, obj) => sum + (obj.allocated_monthly_surplus || 0), 0)) / overview.total_target) * 100 || 0
                  , 100)}%` }} />
                </div>
                <span className="text-xs font-bold text-primary">{(((overview.total_funding + allObjectives.reduce((sum, obj) => sum + (obj.allocated_monthly_surplus || 0), 0)) / overview.total_target) * 100 || 0).toFixed(1)}%</span>
              </div>
            </div>

            <div className="finora-card p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">Monthly Surplus</p>
              <p className={`text-2xl font-display font-bold ${(overview.monthly_surplus ?? 0) >= 0 ? 'text-primary' : 'text-error'}`}>
                {formatCurrency(overview.monthly_surplus ?? 0)}
              </p>
              <p className="text-xs text-on-surface-variant mt-1">Available for goals</p>
            </div>

            {/* Portfolio Return Rate card — the key insight */}
            <div className="finora-card p-5 border border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
              <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1 flex items-center gap-1">
                Portfolio Return
                <span title="Weighted average annual return from your investments. Used to calculate the required SIP for each goal.">
                  <Info size={11} className="opacity-60" />
                </span>
              </p>
              <p className="text-2xl font-display font-bold text-primary">{portfolioReturn.toFixed(1)}%</p>
              <p className="text-xs text-on-surface-variant mt-1">
                {portfolioValue > 0
                  ? `From ${formatCurrency(portfolioValue)} portfolio`
                  : 'Default rate (no investments)'}
              </p>
            </div>
          </div>

          {/* Health + Surplus breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Health summary */}
            <div className="finora-card p-5">
              <p className="text-sm font-bold text-[#1f1b18] mb-3">Objective Health</p>
              <div className="space-y-2">
                {([
                  ['On Track',  'text-primary',   'bg-primary'],
                  ['At Risk',   'text-secondary',  'bg-secondary'],
                  ['Off Track', 'text-error',      'bg-error'],
                  ['Completed', 'text-tertiary',   'bg-tertiary'],
                ] as const).map(([k, textCls, barCls]) => {
                  const count = healthSummary[k] ?? 0
                  const pct   = overview.total_objectives > 0 ? (count / overview.total_objectives) * 100 : 0
                  return (
                    <div key={k}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className={`font-semibold ${textCls}`}>{k}</span>
                        <span className="text-on-surface-variant">{count} goal{count !== 1 ? 's' : ''}</span>
                      </div>
                      <div className="h-1.5 bg-surface-variant rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${barCls}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Surplus waterfall */}
            <div className="finora-card p-5">
              <p className="text-sm font-bold text-[#1f1b18] mb-3">Monthly Allocation Waterfall</p>
              <div className="space-y-2 text-sm">
                {[
                  { label: 'Monthly Income',   val: overview.monthly_income   ?? 0, sign: 1  },
                  { label: 'Expenses',         val: overview.monthly_expense  ?? 0, sign: -1 },
                  { label: 'Loan EMIs',        val: overview.monthly_emis     ?? 0, sign: -1 },
                  { label: 'CC Min Payments',  val: overview.monthly_cc_min   ?? 0, sign: -1 },
                ].map(({ label, val, sign }) => (
                  <div key={label} className="flex justify-between">
                    <span className="text-on-surface-variant">{label}</span>
                    <span className={`font-semibold ${sign < 0 ? 'text-error' : 'text-primary'}`}>
                      {sign < 0 ? '− ' : '+ '}{formatCurrency(val)}
                    </span>
                  </div>
                ))}
                <div className="border-t border-outline-variant/40 pt-2 flex justify-between font-bold">
                  <span>Surplus → Goals</span>
                  <span className={`${(overview.monthly_surplus ?? 0) >= 0 ? 'text-primary' : 'text-error'}`}>
                    {formatCurrency(overview.monthly_surplus ?? 0)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Priority goals */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-display font-bold text-[#1f1b18]">Priority Objectives</h2>
              <button onClick={() => setActiveTab('goals')} className="text-sm font-semibold text-primary hover:underline">
                View All →
              </button>
            </div>

            {isLoading ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-5">
                {[1, 2, 3].map(i => <div key={i} className="h-56 animate-pulse bg-surface-variant/30 rounded-xl" />)}
              </div>
            ) : top3.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-5">
                {top3.map((obj: any) => (
                  <GoalCard key={obj.id} obj={obj} portfolioReturn={portfolioReturn}
                    onEdit={handleEdit} onDelete={setGoalToDelete} onContribute={setContributeGoal} />
                ))}
              </div>
            ) : (
              <div className="finora-card p-14 text-center border-dashed border-2 border-outline-variant">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Target size={28} className="text-primary" />
                </div>
                <h3 className="text-lg font-bold text-[#1f1b18] mb-2">No active objectives</h3>
                <p className="text-on-surface-variant mb-6 max-w-md mx-auto">
                  Start building your financial plan by creating your first wealth objective.
                </p>
                <button onClick={handleAdd} className="btn-primary">Create Your First Objective</button>
              </div>
            )}
          </div>
        </>
      )}

      {/* ── ALL GOALS TAB ── */}
      {activeTab === 'goals' && (
        <div>
          {isLoading ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {[1, 2, 3, 4].map(i => <div key={i} className="h-56 animate-pulse bg-surface-variant/30 rounded-xl" />)}
            </div>
          ) : byPriority.length > 0 ? (
            <>
              {/* Allocation summary bar */}
              <div className="finora-card p-4 mb-6 flex flex-wrap gap-5 items-center bg-gradient-to-r from-primary/5 to-transparent border border-primary/15">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">Surplus</p>
                  <p className={`text-xl font-display font-bold ${(overview.monthly_surplus ?? 0) >= 0 ? 'text-primary' : 'text-error'}`}>
                    {formatCurrency(overview.monthly_surplus ?? 0)}
                  </p>
                </div>
                <div className="h-10 w-px bg-outline-variant/40 hidden sm:block" />
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">Total Req. SIP</p>
                  <p className="text-xl font-display font-bold text-[#1f1b18]">
                    {formatCurrency(byPriority.reduce((s: number, o: any) => s + (o.required_sip ?? 0), 0))}
                  </p>
                </div>
                <div className="h-10 w-px bg-outline-variant/40 hidden sm:block" />
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">Total Allocated</p>
                  <p className="text-xl font-display font-bold text-primary">
                    {formatCurrency(byPriority.reduce((s: number, o: any) => s + (o.allocated_monthly_surplus ?? 0), 0))}
                  </p>
                </div>
                <div className="h-10 w-px bg-outline-variant/40 hidden sm:block" />
                {/* Portfolio return pill */}
                <div className="flex items-center gap-2 px-3 py-2 bg-primary/10 rounded-lg border border-primary/20">
                  <TrendingUp size={16} className="text-primary" />
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-on-surface-variant">Portfolio Return</p>
                    <p className="text-base font-bold text-primary">{portfolioReturn.toFixed(1)}% p.a.</p>
                  </div>
                </div>
                <div className="ml-auto">
                  <button onClick={handleAdd} className="btn-primary flex items-center gap-2 px-5 py-2">
                    <span className="material-symbols-outlined text-[18px]">add</span> Add Objective
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {byPriority.map((obj: any) => (
                  <GoalCard key={obj.id} obj={obj} portfolioReturn={portfolioReturn}
                    onEdit={handleEdit} onDelete={setGoalToDelete} onContribute={setContributeGoal} />
                ))}
              </div>
            </>
          ) : (
            <div className="finora-card p-14 text-center border-dashed border-2 border-outline-variant">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Target size={28} className="text-primary" />
              </div>
              <h3 className="text-lg font-bold text-[#1f1b18] mb-2">No objectives yet</h3>
              <p className="text-on-surface-variant mb-6">Define your first financial goal to start the planning engine.</p>
              <button onClick={handleAdd} className="btn-primary">Create Objective</button>
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingGoal ? 'Edit Objective' : 'Create Financial Objective'}</DialogTitle>
            <DialogDescription>
              {editingGoal ? 'Modify your planning parameters below.' : 'Define a new target for the Finora Planning Engine.'}
            </DialogDescription>
          </DialogHeader>
          <GoalForm initialData={editingGoal} onSuccess={handleClose} onCancel={handleClose} />
        </DialogContent>
      </Dialog>

      {contributeGoal && (
        <Dialog open={!!contributeGoal} onOpenChange={open => { if (!open) setContributeGoal(null) }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Contribution — {contributeGoal.name}</DialogTitle>
              <DialogDescription>Record a manual deposit towards this goal.</DialogDescription>
            </DialogHeader>
            <GoalContributionForm
              goalId={contributeGoal.id}
              onSuccess={() => {
                setContributeGoal(null)
                queryClient.invalidateQueries({ queryKey: ['financial-overview'] })
                toast.success('Contribution recorded')
              }}
              onCancel={() => setContributeGoal(null)}
            />
          </DialogContent>
        </Dialog>
      )}

      <ConfirmDialog
        open={!!goalToDelete}
        onCancel={() => setGoalToDelete(null)}
        onConfirm={() => deleteMutation.mutate(goalToDelete?.id)}
        title="Delete Objective"
        description={`Are you sure you want to delete "${goalToDelete?.name}"? All contribution history will be lost.`}
        confirmLabel={deleteMutation.isPending ? 'Deleting…' : 'Delete'}
        variant="danger"
      />
    </div>
  )
}
