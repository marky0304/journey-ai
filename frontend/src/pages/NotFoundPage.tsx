import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/router/routes'

export default function NotFoundPage() {
  return (
    <div className="container mx-auto flex flex-col items-center justify-center px-4 py-32">
      <h1 className="text-6xl font-bold text-muted-foreground">404</h1>
      <p className="mt-4 text-lg text-muted-foreground">页面不存在</p>
      <Button className="mt-8" asChild>
        <Link to={ROUTES.home}>返回首页</Link>
      </Button>
    </div>
  )
}
