import apiClient from './client'
import type { APIResponse, DashboardData } from '@/types'

export const dashboardApi = {
  get: () => apiClient.get<APIResponse<DashboardData>>('/dashboard'),
}
