interface ProgressIndicatorProps {
  progress: number
}

function getStatusMessage(progress: number): string {
  if (progress >= 90) return '即将完成...'
  if (progress >= 60) return '优化整合行程方案...'
  if (progress >= 30) return '各 Agent 并行规划中...'
  return '正在分析你的需求...'
}

export function ProgressIndicator({ progress }: ProgressIndicatorProps) {
  const safeProgress = Math.min(100, Math.max(0, progress))

  return (
    <div className="space-y-2">
      <div className="h-2 w-full rounded-full bg-muted">
        <div
          className="h-2 rounded-full bg-primary transition-all duration-500"
          style={{ width: `${safeProgress}%` }}
        />
      </div>
      <p className="text-center text-xs text-muted-foreground">
        {getStatusMessage(safeProgress)}
      </p>
    </div>
  )
}
