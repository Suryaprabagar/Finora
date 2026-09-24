'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { transactionsApi, expensesApi, bankAccountsApi, settingsApi, creditCardsApi, budgetApi } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useEffect } from 'react'

const schema = z.object({
  type: z.enum(['income', 'expense', 'budget']),

  amount: z.coerce.number().positive('Amount must be positive'),

  date: z.string().optional(),

  // YYYY-MM format for budget month
  budget_month: z.string().optional(),

  description: z.string().optional(),

  category_id: z.string().nullable(),

  account_id: z.string().optional(),

  merchant: z.string().optional(),

  status: z.enum(['cleared', 'pending', 'failed']).default('cleared'),

  payment_method: z.string().optional(),

  notes: z.string().optional(),

  is_recurring: z.boolean().default(false),

  recurrence_frequency: z.enum(['weekly', 'monthly', 'yearly']).optional().nullable(),

  next_due_date: z.string().optional().nullable(),

  recurrence_end_date: z.string().optional().nullable(),

}).superRefine((data, ctx) => {

  // BUDGET validation
  if (data.type === 'budget') {
    if (!data.budget_month || data.budget_month.trim() === '') {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Month is required',
        path: ['budget_month'],
      })
    } else {
      // Validate YYYY-MM format
      const monthRegex = /^\d{4}-(0[1-9]|1[0-2])$/
      if (!monthRegex.test(data.budget_month.trim())) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Month must be in YYYY-MM format',
          path: ['budget_month'],
        })
      }
    }
    return
  }

  // TRANSACTION validation
  if (!data.date || data.date.trim() === '') {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Date is required',
      path: ['date'],
    })
  }

  if (!data.description || data.description.trim() === '') {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Description is required',
      path: ['description'],
    })
  }

  if (!data.account_id || data.account_id.trim() === '') {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Account or Cash is required',
      path: ['account_id'],
    })
  }

  // Recurring validation
  if (data.is_recurring) {
    if (!data.recurrence_frequency) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Frequency is required for recurring expenses',
        path: ['recurrence_frequency'],
      })
    }

    if (!data.next_due_date || data.next_due_date.trim() === '') {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Next due date is required',
        path: ['next_due_date'],
      })
    } else if (
      data.recurrence_end_date &&
      data.recurrence_end_date.trim() !== ''
    ) {
      if (
        new Date(data.recurrence_end_date) <
        new Date(data.next_due_date)
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'End date cannot be before next due date',
          path: ['recurrence_end_date'],
        })
      }
    }
  }
})

type FormData = z.infer<typeof schema>

interface TransactionFormProps {
  initialData?: any
  onSuccess?: () => void
  onCancel?: () => void
}

export function TransactionForm({ initialData, onSuccess, onCancel }: TransactionFormProps) {
  const queryClient = useQueryClient()
  const isEditing = !!initialData?.id

  const { data: bankAccountsRes } = useQuery({
    queryKey: ['bank-accounts'],
    queryFn: () => bankAccountsApi.list().then(r => r.data),
  })

  const { data: creditCardsRes } = useQuery({
    queryKey: ['credit-cards'],
    queryFn: () => creditCardsApi.list().then(r => r.data),
  })

  const { data: categoriesRes } = useQuery({
    queryKey: ['categories'],
    queryFn: () => settingsApi.getCategories().then(r => r.data),
  })

  const accounts = bankAccountsRes?.data || []
  const creditCards = creditCardsRes?.data || []
  const categories = categoriesRes?.data || []

  const todayStr = new Date().toISOString().split('T')[0]
  // Default budget_month = current YYYY-MM
  const currentMonthStr = todayStr.substring(0, 7)

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      type: (initialData?.type === 'budget' ? 'budget' : initialData?.type || 'expense') as 'expense' | 'income' | 'budget',
      amount: 0,
      date: todayStr,
      budget_month: currentMonthStr,
      description: '',
      category_id: null,
      account_id: '',
      merchant: '',
      status: 'cleared' as const,
      payment_method: '',
      notes: '',
      is_recurring: false,
      recurrence_frequency: 'monthly' as const,
      next_due_date: todayStr,
      recurrence_end_date: '',
    },
  })

  const txType = watch('type')
  const isRecurring = watch('is_recurring')
  const dateValue = watch('date')
  const isBudgetMode = txType === 'budget'

  // When date changes and is_recurring is enabled without a custom next_due_date, sync next_due_date
  useEffect(() => {
    if (!isEditing && dateValue && !watch('next_due_date')) {
      setValue('next_due_date', dateValue)
    }
  }, [dateValue, isEditing, setValue, watch])

  useEffect(() => {
    if (initialData) {
      let initialAccountId = ''
      if (initialData.bank_account_id) initialAccountId = `bank:${initialData.bank_account_id}`
      else if (initialData.credit_card_id) initialAccountId = `card:${initialData.credit_card_id}`
      else if (initialData.payment_method === 'cash') initialAccountId = 'cash'

      const recFreq = (initialData.recurrence_frequency || initialData.recurring_interval || 'monthly').toLowerCase()
      const validFreq = ['weekly', 'monthly', 'yearly'].includes(recFreq) ? recFreq : 'monthly'

      reset({
        type: initialData.type || 'expense',
        amount: initialData.amount,
        date: initialData.date,
        budget_month: initialData.budget_month || currentMonthStr,
        description: initialData.description,
        category_id: initialData.category_id || null,
        account_id: initialAccountId,
        merchant: initialData.merchant || '',
        status: initialData.status || 'cleared',
        payment_method: initialData.payment_method || '',
        notes: initialData.notes || '',
        is_recurring: Boolean(initialData.is_recurring),
        recurrence_frequency: validFreq as 'weekly' | 'monthly' | 'yearly',
        next_due_date: initialData.next_due_date || initialData.date || todayStr,
        recurrence_end_date: initialData.recurrence_end_date || '',
      })
    }
  }, [initialData, reset, todayStr, currentMonthStr])

  const mutation = useMutation({
    mutationFn: (data: FormData) => {
      // ── BUDGET submission ───────────────────────────────────
      if (data.type === 'budget') {
        const [yearStr, monthStr] = (data.budget_month || currentMonthStr).split('-')
        const year = parseInt(yearStr, 10)
        const month = parseInt(monthStr, 10)
        // Derive a human-readable name
        const monthName = new Date(year, month - 1, 1).toLocaleString('default', { month: 'long' })
        const budgetPayload = {
          name: `${monthName} ${year} Budget`,
          month,
          year,
          total_limit: data.amount,
          alert_threshold: 80,
          items: data.category_id
            ? [{
                name: categories.find((c: any) => c.id === data.category_id)?.name || 'Category Budget',
                allocated_amount: data.amount,
                category_id: data.category_id,
              }]
            : [],
        }
        return budgetApi.create(budgetPayload)
      }

      // ── TRANSACTION submission (income / expense) ───────────
      let bank_account_id = null
      let credit_card_id = null
      let payment_method = data.payment_method

      if (data.account_id) {
        if (data.account_id === 'cash') {
          payment_method = 'cash'
        } else if (data.account_id.startsWith('bank:')) {
          bank_account_id = data.account_id.split(':')[1]
        } else if (data.account_id.startsWith('card:')) {
          credit_card_id = data.account_id.split(':')[1]
          payment_method = 'card'
        }
      }

      const recActive = Boolean(data.is_recurring)

      const payload: any = {
        ...data,
        bank_account_id,
        credit_card_id,
        payment_method: payment_method || null,
        category_id: data.category_id === '' ? null : data.category_id,
        is_recurring: recActive,
        recurrence_frequency: recActive ? data.recurrence_frequency : null,
        recurring_interval: recActive ? data.recurrence_frequency : null,
        next_due_date: recActive && data.next_due_date ? data.next_due_date : null,
        recurrence_end_date: recActive && data.recurrence_end_date ? data.recurrence_end_date : null,
      }

      if (data.type === 'expense') {
        return isEditing
          ? expensesApi.update(initialData.id, payload)
          : expensesApi.create(payload)
      } else {
        return isEditing
          ? transactionsApi.update(initialData.id, payload)
          : transactionsApi.create(payload)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['bank-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['credit-cards'] })
      queryClient.invalidateQueries({ queryKey: ['budget-current'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['income-list'] })
      queryClient.invalidateQueries({ queryKey: ['income-summary'] })
      queryClient.invalidateQueries({ queryKey: ['income-by-category'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-list'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-summary'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-by-category'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-trends'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-by-merchant'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-recurring'] })
      queryClient.invalidateQueries({ queryKey: ['expenses-upcoming-recurring'] })
      queryClient.invalidateQueries({ queryKey: ['reports-analytics'] })

      if (txType === 'budget') {
        toast.success('Budget saved successfully')
      } else {
        toast.success(isEditing ? 'Transaction updated' : 'Transaction created')
      }
      onSuccess?.()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail
      if (txType === 'budget') {
        toast.error(detail || 'Unable to save your budget. Please try again.')
      } else {
        toast.error(detail || 'Unable to save transaction. Please try again.')
      }
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  // Filter categories for transaction types; for budget show expense categories
  const filteredCategories = isBudgetMode
    ? categories.filter((c: any) => c.type === 'expense')
    : categories.filter((c: any) => c.type === txType)

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Type Selector Tabs — Expense | Income | Budget (no Transfer) */}
      <div className="flex p-1 bg-surface-variant rounded-lg gap-1">
        {(['expense', 'income', 'budget'] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => {
              setValue('type', t)
              if (t !== 'expense') {
                setValue('is_recurring', false)
              }
            }}
            className={`flex-1 py-2 text-sm font-medium rounded-md capitalize transition-colors ${txType === t
              ? 'bg-white shadow text-[#1f1b18]'
              : 'text-[#51443c] hover:bg-white/50'
              }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* ── BUDGET MODE FIELDS ─────────────────────────────── */}
      {isBudgetMode && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Budget Amount *</Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">₹</span>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  className="pl-7"
                  placeholder="50,000"
                  {...register('amount')}
                />
              </div>
              {errors.amount && <p className="text-sm text-error">{errors.amount.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="budget_month">Month *</Label>
              <Input
                id="budget_month"
                type="month"
                {...register('budget_month')}
              />
              {errors.budget_month && (
                <p className="text-sm text-error">{errors.budget_month.message as string}</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="category_id">Category (Optional)</Label>
            <select
              id="category_id"
              className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
              {...register('category_id')}
            >
              <option value="">All Categories (Overall Budget)</option>
              {filteredCategories.map((cat: any) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
            <p className="text-xs text-on-surface-variant">
              Leave blank to set an overall monthly spending limit.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes (Optional)</Label>
            <Input
              id="notes"
              placeholder="e.g. September monthly spending limit"
              {...register('notes')}
            />
          </div>
        </div>
      )}

      {/* ── TRANSACTION MODE FIELDS ─────────────────────────── */}
      {!isBudgetMode && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Amount *</Label>
              <Input id="amount" type="number" step="0.01" {...register('amount')} />
              {errors.amount && <p className="text-sm text-error">{errors.amount.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="date">Date *</Label>
              <Input id="date" type="date" {...register('date')} />
              {errors.date && <p className="text-sm text-error">{errors.date.message}</p>}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Input id="description" placeholder="e.g. Groceries at Walmart" {...register('description')} />
            {errors.description && <p className="text-sm text-error">{errors.description.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="account_id">Account / Funding Source *</Label>

              <select
                id="account_id"
                className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
                {...register('account_id')}
              >
                <option value="">Select Account</option>
                <option value="cash">Cash (Wallet)</option>

                {accounts.length > 0 && (
                  <optgroup label="Bank Accounts">
                    {accounts.map((acc: any) => (
                      <option key={`bank:${acc.id}`} value={`bank:${acc.id}`}>
                        {acc.name} ({acc.balance})
                      </option>
                    ))}
                  </optgroup>
                )}

                {txType === 'expense' && creditCards.length > 0 && (
                  <optgroup label="Credit Cards">
                    {creditCards.map((card: any) => (
                      <option key={`card:${card.id}`} value={`card:${card.id}`}>
                        {card.bank_name} {card.card_number ? `(${card.card_number})` : ''}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>

              {errors.account_id && (
                <p className="text-sm text-error">
                  {errors.account_id.message as string}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="category_id">Category</Label>

              <select
                id="category_id"
                className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
                {...register('category_id')}
              >
                <option value="">All Categories</option>

                {filteredCategories.map((cat: any) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="merchant">Merchant (Optional)</Label>
              <Input id="merchant" placeholder="e.g. Walmart" {...register('merchant')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
                {...register('status')}
              >
                <option value="cleared">Cleared</option>
                <option value="pending">Pending</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>

          {/* Recurrence Section (Expense Only) */}
          {txType === 'expense' && (
            <div className="pt-2 border-t border-[#d5c3b8]/40">
              <label className="flex items-center gap-2 cursor-pointer select-none py-1">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-[#d5c3b8] text-primary focus:ring-primary accent-[#6f4627]"
                  {...register('is_recurring')}
                />
                <span className="text-sm font-semibold text-[#1f1b18]">Recurring Expense</span>
              </label>

              {isRecurring && (
                <div className="p-3 bg-surface-container-low rounded-lg space-y-3 border border-outline-variant/30 mt-2">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <Label htmlFor="recurrence_frequency">Frequency *</Label>
                      <select
                        id="recurrence_frequency"
                        className="flex h-10 w-full rounded-md border border-[#d5c3b8] bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#6f4627] text-[#1f1b18]"
                        {...register('recurrence_frequency')}
                      >
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                        <option value="yearly">Yearly</option>
                      </select>
                      {errors.recurrence_frequency && (
                        <p className="text-xs text-error">{errors.recurrence_frequency.message as string}</p>
                      )}
                    </div>

                    <div className="space-y-1">
                      <Label htmlFor="next_due_date">Next Due Date *</Label>
                      <Input id="next_due_date" type="date" {...register('next_due_date')} />
                      {errors.next_due_date && (
                        <p className="text-xs text-error">{errors.next_due_date.message as string}</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label htmlFor="recurrence_end_date">End Date (Optional)</Label>
                    <Input id="recurrence_end_date" type="date" {...register('recurrence_end_date')} />
                    {errors.recurrence_end_date && (
                      <p className="text-xs text-error">{errors.recurrence_end_date.message as string}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      <div className="pt-4 flex justify-end gap-3">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting
            ? 'Saving...'
            : isBudgetMode
              ? 'Save Budget'
              : isEditing
                ? 'Save Changes'
                : 'Add Transaction'}
        </button>
      </div>
    </form>
  )
}
