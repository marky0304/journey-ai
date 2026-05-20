import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/shared/stores/useAuthStore'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const setLoginDialogOpen = useAuthStore((s) => s.setLoginDialogOpen)

  useEffect(() => {
    if (!isAuthenticated) {
      setLoginDialogOpen(true)
    }
  }, [isAuthenticated, setLoginDialogOpen])

  if (!isAuthenticated) return <Navigate to="/" replace />
  return <>{children}</>
}
