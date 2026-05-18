import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { RouterProvider } from './router'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
    mutations: { onError: (err: Error) => console.error(err) },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider />
      <Toaster position="top-center" richColors />
    </QueryClientProvider>
  )
}
