'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { budgetApi } from '@/lib/api'
import { PageHeader } from '@/components/shared/PageHeader'
import { formatCurrency } from '@/lib/utils'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { BudgetForm } from '@/components/features/budget/BudgetForm'

export default function BudgetPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { data: res, isLoading } = useQuery({
    queryKey: ['budget-current'],
    queryFn: () => budgetApi.getCurrent().then(r => r.data),
  })

  const budget = res?.data

  const handleEdit = () => {
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
  }

  return (
    <div>
      <PageHeader
        title="Budget"
        subtitle="Manage your monthly spending limits"
        actions={
          <button onClick={handleEdit} className="btn-primary">
            <span className="material-symbols-outlined text-[18px]">
              {budget ? 'edit' : 'add'}
            </span>
            {budget ? 'Edit Budget' : 'Create Budget'}
          </button>
        }
      />
      {isLoading ? (
        <div className="h-64 finora-card animate-pulse bg-surface-variant/30"></div>
      ) : budget ? (
        <div className="space-y-6">
          <div className="finora-card p-6">
            <div className="flex justify-between mb-2">
              <h3 className="font-display font-bold text-lg text-[#1f1b18]">Total Budget</h3>
              <p className="font-medium text-[#1f1b18]">{formatCurrency(budget.total_spent)} / {formatCurrency(budget.total_limit)}</p>
            </div>
            <div className="w-full h-4 bg-surface-variant rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all ${
                  (budget.total_spent / budget.total_limit) > 0.9 ? 'bg-error' : 'bg-primary'
                }`}
                style={{ width: `${Math.min((budget.total_spent / budget.total_limit) * 100, 100)}%` }}
              ></div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {budget.items?.map((item: any) => {
              const spent = item.spent_amount || 0;
              const limit = item.allocated_amount || 0;
              const percentage = limit > 0 ? (spent / limit) * 100 : 0;
              return (
                <div key={item.id} className="finora-card p-6">
                  <div className="flex justify-between mb-2">
                    <h4 className="font-medium text-[#1f1b18]">{item.name}</h4>
                    <p className="text-sm text-on-surface-variant">{formatCurrency(spent)} / {formatCurrency(limit)}</p>
                  </div>
                  <div className="w-full h-2 bg-surface-variant rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all ${percentage > 90 ? 'bg-error' : 'bg-tertiary'}`}
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    ></div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ) : (
        <div className="finora-card p-12 text-center">
          <p className="text-[#51443c] mb-4">No budget set for this month.</p>
          <button onClick={handleEdit} className="btn-primary">Create Budget</button>
        </div>
      )}

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>{budget ? 'Edit Budget' : 'Create Budget'}</DialogTitle>
            <DialogDescription>
              {budget ? 'Modify your budget limits for this month.' : 'Set up a new budget by adding category limits.'}
            </DialogDescription>
          </DialogHeader>
          <BudgetForm 
            initialData={budget} 
            onSuccess={handleCloseModal}
            onCancel={handleCloseModal}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
