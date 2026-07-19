import apiClient from './client'
import type { APIResponse, AuthTokens, User } from '@/types'

export const authApi = {
  register: (data: { full_name: string; email: string; password: string }) =>
    apiClient.post<APIResponse<{ user: User; tokens: AuthTokens }>>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<APIResponse<{ user: User; tokens: AuthTokens }>>('/auth/login', data),

  refresh: (refresh_token: string) =>
    apiClient.post<APIResponse<{ access_token: string }>>('/auth/refresh', { refresh_token }),

  logout: () => apiClient.post<APIResponse<null>>('/auth/logout'),

  forgotPassword: (email: string) =>
    apiClient.post<APIResponse<{ reset_token: string; message: string }>>('/auth/forgot-password', { email }),

  resetPassword: (token: string, new_password: string) =>
    apiClient.post<APIResponse<null>>('/auth/reset-password', { token, new_password }),

  me: () => apiClient.get<APIResponse<User>>('/auth/me'),
}
