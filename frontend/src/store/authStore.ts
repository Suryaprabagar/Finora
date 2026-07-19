import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  accessToken: string | null
  refreshToken: string | null
  setAuth: (user: User, accessToken: string, refreshToken: string) => void
  updateUser: (user: Partial<User>) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      accessToken: null,
      refreshToken: null,

      setAuth: (user, accessToken, refreshToken) => {
        // Also store in localStorage for the axios interceptor
        if (typeof window !== 'undefined') {
          localStorage.setItem('finora_access_token', accessToken)
          localStorage.setItem('finora_refresh_token', refreshToken)
          // Set cookie for middleware
          document.cookie = `finora_token=${accessToken}; path=/; max-age=${60 * 60}; SameSite=Lax`
        }
        set({ user, isAuthenticated: true, accessToken, refreshToken })
      },

      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('finora_access_token')
          localStorage.removeItem('finora_refresh_token')
          // Delete cookie for middleware
          document.cookie = 'finora_token=; path=/; max-age=0;'
        }
        set({ user: null, isAuthenticated: false, accessToken: null, refreshToken: null })
      },
    }),
    {
      name: 'finora-auth',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
)
