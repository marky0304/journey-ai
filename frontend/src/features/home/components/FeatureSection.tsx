import { Brain, RefreshCw, CreditCard } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'

const features = [
  { icon: Brain, title: 'AI 智能规划', description: '多 Agent 并行协作，从交通到美食，全方位覆盖你的旅行需求' },
  { icon: RefreshCw, title: '实时动态调整', description: '旅途中遇到变化？AI 自动监测并推荐最优调整方案' },
  { icon: CreditCard, title: '一站式预订', description: '行程直接转化为可预订订单，多平台比价一键下单' },
]

export function FeatureSection() {
  return (
    <section className="bg-muted/50 py-20">
      <div className="container mx-auto px-4">
        <h2 className="text-center text-3xl font-bold">为什么选择旅程AI</h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {features.map((f) => (
            <Card key={f.title}>
              <CardHeader>
                <f.icon className="h-10 w-10 text-primary" />
                <CardTitle>{f.title}</CardTitle>
                <p className="text-sm text-muted-foreground">{f.description}</p>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
