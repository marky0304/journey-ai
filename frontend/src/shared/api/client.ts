import axios from 'axios'
import { toast } from 'sonner'

export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    toast.error(message)
    return Promise.reject(error)
  }
)
