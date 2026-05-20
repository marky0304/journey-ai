import axios from 'axios'
import { toast } from 'sonner'
import { useAuthStore } from '@/shared/stores/useAuthStore'

export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function extractErrorMessage(error: unknown): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (!detail) return (error as { message?: string })?.message || '请求失败'
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((e: { msg?: string; loc?: string[] }) =>
        e.loc ? `${e.loc.join('.')}: ${e.msg}` : e.msg
      )
      .filter(Boolean)
      .join('; ')
  }
  return String(detail)
}

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      const store = useAuthStore.getState()
      store.logout()
      store.setLoginDialogOpen(true)
    }
    const status = error.response?.status ?? 0
    if (status >= 500 || (status >= 400 && status !== 401 && status !== 404)) {
      toast.error(extractErrorMessage(error))
    }
    return Promise.reject(error)
  }
)
