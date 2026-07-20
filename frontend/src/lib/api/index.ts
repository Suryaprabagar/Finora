export { authApi } from './auth'
export { dashboardApi } from './dashboard'
export { transactionsApi } from './transactions'
export { default as apiClient } from './client'

// Lazy imports for other API modules
export const createApi = (path: string) => ({
  list: (params = {}) => import('./client').then(m => m.default.get(`/${path}`, { params })),
  get: (id: string) => import('./client').then(m => m.default.get(`/${path}/${id}`)),
  create: (data: unknown) => import('./client').then(m => m.default.post(`/${path}`, data)),
  update: (id: string, data: unknown) => import('./client').then(m => m.default.put(`/${path}/${id}`, data)),
  delete: (id: string) => import('./client').then(m => m.default.delete(`/${path}/${id}`)),
})

import apiClientModule from './client'
import type { APIResponse } from '@/types'

export const bankAccountsApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/bank-accounts', { params }),
  get: (id: string) => apiClientModule.get<APIResponse<any>>(`/bank-accounts/${id}`),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/bank-accounts', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/bank-accounts/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/bank-accounts/${id}`),
  transfer: (data: unknown) => apiClientModule.post<APIResponse<any>>('/bank-accounts/transfer', data),
  getTransactions: (id: string, params = {}) => apiClientModule.get<APIResponse<any[]>>(`/bank-accounts/${id}/transactions`, { params }),
}

export const creditCardsApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/credit-cards', { params }),
  get: (id: string) => apiClientModule.get<APIResponse<any>>(`/credit-cards/${id}`),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/credit-cards', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/credit-cards/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/credit-cards/${id}`),
  recordPayment: (id: string, data: unknown) => apiClientModule.post<APIResponse<any>>(`/credit-cards/${id}/payment`, data),
}

export const budgetApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/budget', { params }),
  getCurrent: () => apiClientModule.get<APIResponse<any>>('/budget/current'),
  get: (id: string) => apiClientModule.get<APIResponse<any>>(`/budget/${id}`),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/budget', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/budget/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/budget/${id}`),
}

export const goalsApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/goals', { params }),
  getOverview: () => apiClientModule.get<APIResponse<any>>('/goals/overview'),
  get: (id: string) => apiClientModule.get<APIResponse<any>>(`/goals/${id}`),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/goals', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/goals/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/goals/${id}`),
  contribute: (id: string, data: unknown) => apiClientModule.post<APIResponse<any>>(`/goals/${id}/contribute`, data),
}

export const billsApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/bills', { params }),
  getUpcoming: () => apiClientModule.get<APIResponse<any[]>>('/bills/upcoming'),
  getSummary: () => apiClientModule.get<APIResponse<any>>('/bills/summary'),
  get: (id: string) => apiClientModule.get<APIResponse<any>>(`/bills/${id}`),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/bills', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/bills/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/bills/${id}`),
  pay: (id: string, data: unknown) => apiClientModule.post<APIResponse<any>>(`/bills/${id}/pay`, data),
}

export const investmentsApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/investments', { params }),
  getSummary: () => apiClientModule.get<APIResponse<any>>('/investments/summary'),
  get: (id: string) => apiClientModule.get<APIResponse<any>>(`/investments/${id}`),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/investments', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/investments/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/investments/${id}`),
}

export const loansApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/loans', { params }),
  getSummary: () => apiClientModule.get<APIResponse<any>>('/loans/summary'),
  getSchedule: (id: string) => apiClientModule.get<APIResponse<any[]>>(`/loans/${id}/schedule`),
  get: (id: string) => apiClientModule.get<APIResponse<any>>(`/loans/${id}`),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/loans', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/loans/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/loans/${id}`),
  recordPayment: (id: string, data: unknown) => apiClientModule.post<APIResponse<any>>(`/loans/${id}/payment`, data),
}

export const assetsApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/assets', { params }),
  getSummary: () => apiClientModule.get<APIResponse<any>>('/assets/summary'),
  get: (id: string) => apiClientModule.get<APIResponse<any>>(`/assets/${id}`),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/assets', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/assets/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/assets/${id}`),
}

export const insuranceApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/insurance', { params }),
  getSummary: () => apiClientModule.get<APIResponse<any>>('/insurance/summary'),
  get: (id: string) => apiClientModule.get<APIResponse<any>>(`/insurance/${id}`),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/insurance', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/insurance/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/insurance/${id}`),
  addClaim: (id: string, data: unknown) => apiClientModule.post<APIResponse<any>>(`/insurance/${id}/claims`, data),
  getClaims: (id: string) => apiClientModule.get<APIResponse<any[]>>(`/insurance/${id}/claims`),
}

export const reportsApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/reports', { params }),
  generate: (data: unknown) => apiClientModule.post<APIResponse<any>>('/reports/generate', data),
  download: (id: string) => apiClientModule.get(`/reports/${id}/download`, { responseType: 'blob' }),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/reports/${id}`),
}

export const settingsApi = {
  getCategories: () => apiClientModule.get<APIResponse<any[]>>('/settings/categories'),
  createCategory: (data: unknown) => apiClientModule.post<APIResponse<any>>('/settings/categories', data),
  updateCategory: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/settings/categories/${id}`, data),
  deleteCategory: (id: string) => apiClientModule.delete<APIResponse<null>>(`/settings/categories/${id}`),
  resetDemo: () => apiClientModule.post<APIResponse<null>>('/settings/reset-demo'),
  updateProfile: (data: unknown) => apiClientModule.put<APIResponse<any>>('/users/me', data),
  changePassword: (data: unknown) => apiClientModule.post<APIResponse<null>>('/users/me/change-password', data),
}

export const incomeApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/income', { params }),
  getSummary: () => apiClientModule.get<APIResponse<any>>('/income/summary'),
  getByCategory: () => apiClientModule.get<APIResponse<any[]>>('/income/by-category'),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/income', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/income/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/income/${id}`),
}

export const expensesApi = {
  list: (params = {}) => apiClientModule.get<APIResponse<any[]>>('/expenses', { params }),
  getSummary: () => apiClientModule.get<APIResponse<any>>('/expenses/summary'),
  getByCategory: () => apiClientModule.get<APIResponse<any[]>>('/expenses/by-category'),
  getTrends: () => apiClientModule.get<APIResponse<any[]>>('/expenses/trends'),
  create: (data: unknown) => apiClientModule.post<APIResponse<any>>('/expenses', data),
  update: (id: string, data: unknown) => apiClientModule.put<APIResponse<any>>(`/expenses/${id}`, data),
  delete: (id: string) => apiClientModule.delete<APIResponse<null>>(`/expenses/${id}`),
}
