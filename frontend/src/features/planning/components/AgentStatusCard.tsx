import { Card } from '@/components/ui/card'
import { AlertCircle, CheckCircle2, Circle, Loader2 } from 'lucide-react'
import type { AgentInfo, AgentStatus } from '@/types/api'

const AGENT_LABELS: Record<string, string> = {
  coordinator: '协调分析',
  transport: '交通出行',
  accommodation: '住宿选择',
  attraction: '景点规划',
  dining: '美食推荐',
  strategy: '策略优化',
}

const icons: Record<AgentStatus, React.ComponentType<{ className?: string }>> = {
  idle: Circle,
  working: Loader2,
  done: CheckCircle2,
  error: AlertCircle,
}

const iconClassNames: Record<AgentStatus, string> = {
  idle: 'text-muted-foreground',
  working: 'animate-spin text-primary',
  done: 'text-green-500',
  error: 'text-destructive',
}

const statusLabels: Record<AgentStatus, string> = {
  idle: '等待中',
  working: '规划中...',
  done: '已完成',
  error: '出错',
}

interface AgentStatusCardProps {
  agent: AgentInfo
}

export function AgentStatusCard({ agent }: AgentStatusCardProps) {
  const Icon = icons[agent.status] || Circle
  const iconClass = iconClassNames[agent.status] || 'text-muted-foreground'
  const label = AGENT_LABELS[agent.name] || agent.name
  const statusText = statusLabels[agent.status] || agent.status

  return (
    <Card className="flex items-center gap-3 p-3">
      <Icon className={`h-5 w-5 shrink-0 ${iconClass}`} />
      <div className="min-w-0">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{statusText}</p>
      </div>
    </Card>
  )
}
