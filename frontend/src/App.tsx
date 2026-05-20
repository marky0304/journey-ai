import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { toast, Toaster } from 'sonner'
import { RouterProvider } from './router'
import { useAuthStore } from '@/shared/stores/useAuthStore'
import { isCancel } from 'axios'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
    mutations: {
      onError: (err: Error) => {
        if (isCancel(err)) return
        toast.error(err.message || '请求失败，请稍后重试')
      },
    },
  },
})

function AuthInit({ children }: { children: React.ReactNode }) {
  const fetchMe = useAuthStore((s) => s.fetchMe)
  const token = useAuthStore((s) => s.token)

  useEffect(() => {
    if (token) {
      fetchMe()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthInit>
        <RouterProvider />
      </AuthInit>
      <Toaster position="top-center" richColors />
    </QueryClientProvider>
  )
}
