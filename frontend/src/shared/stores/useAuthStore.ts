import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '@/shared/api/client'

interface User {
  id: string
  username: string
  email: string
  is_admin: boolean
}

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loginDialogOpen: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
  setLoginDialogOpen: (open: boolean) => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      loginDialogOpen: false,

      login: async (username: string, password: string) => {
        const res = await apiClient.post('/auth/login', { username, password })
        const { access_token } = res.data
        set({ token: access_token, isAuthenticated: true })
        await get().fetchMe()
      },

      register: async (username: string, email: string, password: string) => {
        const res = await apiClient.post('/auth/register', { username, email, password })
        const { access_token } = res.data
        set({ token: access_token, isAuthenticated: true })
        await get().fetchMe()
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
      },

      fetchMe: async () => {
        try {
          const token = get().token
          if (!token) return
          const res = await apiClient.get('/auth/me')
          set({ user: res.data, isAuthenticated: true })
        } catch {
          set({ user: null, isAuthenticated: false })
        }
      },

      setLoginDialogOpen: (open: boolean) => set({ loginDialogOpen: open }),
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({ token: state.token, isAuthenticated: state.isAuthenticated }),
    },
  ),
)
