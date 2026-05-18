import { Link } from 'react-router-dom'
import { MapPin } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/router/routes'

export function Header() {
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
        </nav>
      </div>
    </header>
  )
}
