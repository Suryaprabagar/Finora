import apiClient from './client'
import type { APIResponse, Transaction, Pagination } from '@/types'

export interface TransactionFilters {
  type?: string
  category_id?: string
  bank_account_id?: string
  date_from?: string
  date_to?: string
  status?: string
  search?: string
  payment_method?: string
  page?: number
  per_page?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export const transactionsApi = {
  list: (filters: TransactionFilters = {}) =>
    apiClient.get<APIResponse<Transaction[]>>('/transactions', { params: filters }),

  get: (id: string) => apiClient.get<APIResponse<Transaction>>(`/transactions/${id}`),

  create: (data: Partial<Transaction>) =>
    apiClient.post<APIResponse<Transaction>>('/transactions', data),

  update: (id: string, data: Partial<Transaction>) =>
    apiClient.put<APIResponse<Transaction>>(`/transactions/${id}`, data),

  delete: (id: string) => apiClient.delete<APIResponse<null>>(`/transactions/${id}`),

  bulkDelete: (ids: string[]) =>
    apiClient.post<APIResponse<null>>('/transactions/bulk-delete', { ids }),

  exportCsv: (filters: TransactionFilters = {}) =>
    apiClient.get('/transactions/export/csv', { params: filters, responseType: 'blob' }),

  importCsv: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post<APIResponse<{ created: number; errors: number }>>(
      '/transactions/import/csv',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },
}
