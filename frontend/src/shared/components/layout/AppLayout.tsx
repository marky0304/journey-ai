import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Footer } from './Footer'
import { Live2DCompanion } from '@/features/travel-companion/Live2DCompanion'
import { LoginDialog } from '@/features/auth/LoginDialog'

export function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <Live2DCompanion />
      <LoginDialog />
    </div>
  )
}
