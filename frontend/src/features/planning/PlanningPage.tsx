import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, XCircle } from 'lucide-react'
import { tripApi } from '@/shared/api/tripApi'
import { queryKeys } from '@/shared/api/queryKeys'
import { useTripStore } from '@/shared/stores/useTripStore'
import { ProgressIndicator } from './components/ProgressIndicator'
import { AgentStatusCard } from './components/AgentStatusCard'

const SUCCESS_REDIRECT_DELAY_MS = 1500

export default function PlanningPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const reset = useTripStore((s) => s.reset)
  const updatePlanningProgress = useTripStore((s) => s.updatePlanningProgress)
  const clearPlanning = useTripStore((s) => s.clearPlanning)

  const { data, error, isLoading } = useQuery({
    queryKey: queryKeys.planningTask(taskId!),
    queryFn: () => {
      if (!taskId) throw new Error('Missing taskId')
      return tripApi.getPlanningStatus(taskId)
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'completed' || status === 'failed') return false
      return 2000
    },
    enabled: !!taskId,
  })

  const cancelMutation = useMutation({
    mutationFn: () => {
      if (!taskId) throw new Error('Missing taskId')
      return tripApi.cancelTask(taskId)
    },
    onSuccess: () => {
      reset()
      navigate('/plan')
    },
    onError: () => toast.error('取消失败，请重试'),
  })

  useEffect(() => {
    if (data) {
      updatePlanningProgress(data.status, data.progress, data.agents, data.error_message)
    }
  }, [data, updatePlanningProgress])

  useEffect(() => {
    if (data?.status === 'completed' && data.trip_id) {
      const timer = setTimeout(() => {
        navigate(`/trip/${data.trip_id}`)
      }, SUCCESS_REDIRECT_DELAY_MS)
      return () => clearTimeout(timer)
    }
  }, [data?.status, data?.trip_id, navigate])

  useEffect(() => {
    if (data?.status === 'completed' || data?.status === 'failed') {
      const timer = setTimeout(() => clearPlanning(), 3000)
      return () => clearTimeout(timer)
    }
  }, [data?.status, clearPlanning])

  if (error || data?.status === 'failed') {
    return (
      <div className="container mx-auto max-w-2xl px-4 py-12">
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-12">
            <XCircle className="h-16 w-16 text-destructive" />
            <h2 className="text-xl font-semibold">规划失败</h2>
            <p className="text-sm text-muted-foreground">
              {data?.error_message || '请稍后重试'}
            </p>
            <Button onClick={() => navigate('/plan')}>重新规划</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container mx-auto max-w-2xl px-4 py-12">
        <Card>
          <CardContent className="flex flex-col items-center gap-4 py-12">
            <Loader2 className="h-16 w-16 animate-spin text-primary" />
            <h2 className="text-xl font-semibold">正在加载...</h2>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-2xl px-4 py-12">
      <Card>
        <CardHeader className="text-center">
          <CardTitle>AI 正在为你规划行程</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {data?.status === 'completed' && (
            <p className="text-center text-green-500 font-medium">
              规划完成，即将跳转...
            </p>
          )}

          <ProgressIndicator progress={data?.progress ?? 0} />

          <div className="grid grid-cols-2 gap-3">
            {data?.agents?.map((agent) => (
              <AgentStatusCard key={agent.name} agent={agent} />
            ))}
          </div>

          <Button
            variant="outline"
            className="w-full"
            disabled={cancelMutation.isPending}
            onClick={() => cancelMutation.mutate()}
          >
            {cancelMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            取消规划
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
