import { Link } from 'react-router-dom'
import { MapPin, User, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/router/routes'
import { useAuthStore } from '@/shared/stores/useAuthStore'

export function Header() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const user = useAuthStore((s) => s.user)
  const setLoginDialogOpen = useAuthStore((s) => s.setLoginDialogOpen)
  const logout = useAuthStore((s) => s.logout)

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link to={ROUTES.home} className="flex items-center gap-2 text-xl font-bold">
          <MapPin className="h-6 w-6 text-primary" />
          <span>旅程AI</span>
        </Link>
        <nav className="flex items-center gap-4">
          <Button variant="ghost" asChild>
            <Link to={ROUTES.plan}>开始规划</Link>
          </Button>
          {isAuthenticated ? (
            <>
              <span className="text-sm text-muted-foreground">
                <User className="h-4 w-4 inline mr-1" />
                {user?.username}
              </span>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4 mr-1" />
                退出
              </Button>
            </>
          ) : (
            <Button size="sm" onClick={() => setLoginDialogOpen(true)}>
              登录
            </Button>
          )}
        </nav>
      </div>
    </header>
  )
}
