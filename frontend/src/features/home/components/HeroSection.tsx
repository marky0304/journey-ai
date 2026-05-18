import { useNavigate } from 'react-router-dom'
import { ArrowRight, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/router/routes'

export function HeroSection() {
  const navigate = useNavigate()
  return (
    <section className="container mx-auto px-4 py-24 text-center">
      <div className="mx-auto inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm text-muted-foreground">
        <Sparkles className="h-4 w-4" /> AI 多 Agent 协作规划
      </div>
      <h1 className="mx-auto mt-6 max-w-3xl text-5xl font-bold leading-tight tracking-tight">
        只需说出你的想法，AI 为你规划<span className="text-primary">完美旅程</span>
      </h1>
      <p className="mx-auto mt-6 max-w-xl text-lg text-muted-foreground">
        输入目的地和偏好，多个 AI Agent 并行协作，秒级生成包含交通、住宿、景点、美食的完整行程方案
      </p>
      <Button size="lg" className="mt-8 gap-2 text-base" onClick={() => navigate(ROUTES.plan)}>
        开始规划行程 <ArrowRight className="h-4 w-4" />
      </Button>
    </section>
  )
}
