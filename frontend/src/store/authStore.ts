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
        // BUG-020 note: Tokens are stored in BOTH Zustand persist AND raw localStorage keys.
        // This is intentional: Zustand persist writes to 'finora-auth' (the whole state),
        // while the Axios interceptor reads from 'finora_access_token'/'finora_refresh_token' directly.
        // Both must be kept in sync, which they are here and in logout().
        if (typeof window !== 'undefined') {
          localStorage.setItem('finora_access_token', accessToken)
          localStorage.setItem('finora_refresh_token', refreshToken)
          // BUG-012 fix: use ACCESS_TOKEN_EXPIRE_MINUTES from env instead of hardcoded 3600.
          // Falls back to 60 minutes (same as backend default) if not set.
          const expiresMinutes = parseInt(process.env.NEXT_PUBLIC_ACCESS_TOKEN_MINUTES || '60', 10)
          const expiresSeconds = expiresMinutes * 60
          document.cookie = `finora_token=${accessToken}; path=/; max-age=${expiresSeconds}; SameSite=Lax`
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
