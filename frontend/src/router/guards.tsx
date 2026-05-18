import { Navigate } from 'react-router-dom'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = true // MVP — always pass through
  if (!isAuthenticated) return <Navigate to="/" replace />
  return <>{children}</>
}
