import { useState, useEffect, Component } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tripApi } from '@/shared/api/tripApi'
import { queryKeys } from '@/shared/api/queryKeys'
import { useTripStore } from '@/shared/stores/useTripStore'
import { TripHeader } from './components/TripHeader'
import { DayTabs } from './components/DayTabs'
import { DayTimeline } from './components/DayTimeline'
import { TripActions } from './components/TripActions'
import { TripSidebar } from './components/TripSidebar'
import { TripMapView } from './components/TripMapView'
import { WeatherCard } from './components/WeatherCard'
import { Button } from '@/components/ui/button'
import { LoadingPage } from '@/shared/components/ui/LoadingPage'
import { AlertCircle } from 'lucide-react'
import type { Activity, Trip } from '@/types/api'

class ErrorBoundary extends Component<
  { children: React.ReactNode; onReset: () => void },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; onReset: () => void }) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  componentDidCatch(error: Error, _info: React.ErrorInfo) {
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.error('TripResultPage render error:', error)
    }
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="container mx-auto max-w-lg px-4 py-16 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
          <h2 className="mt-4 text-xl font-semibold">行程加载出错</h2>
          <p className="mt-2 text-muted-foreground">请重试或重新规划</p>
          <Button className="mt-6" onClick={this.props.onReset}>
            重新规划
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}

export default function TripResultPage() {
  const { tripId } = useParams<{ tripId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const setTrip = useTripStore((s) => s.setTrip)
  const [activeDay, setActiveDay] = useState(0)
  const [swappingId, setSwappingId] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'timeline' | 'map'>('timeline')

  useEffect(() => {
    setActiveDay(0)
  }, [tripId])

  const {
    data: trip,
    isLoading,
    error,
  } = useQuery({
    queryKey: queryKeys.tripResult(tripId!),
    queryFn: () => {
      if (!tripId) throw new Error('Missing tripId')
      return tripApi.getTrip(tripId)
    },
    enabled: !!tripId,
  })

  useEffect(() => {
    if (trip) setTrip(trip)
  }, [trip, setTrip])

  const swapMutation = useMutation({
    mutationFn: (activity: Activity) =>
      tripApi.swapActivity(tripId!, {
        day_index: activeDay,
        activity_id: activity.id,
        type: activity.type,
        name: activity.name,
        destination: trip!.destination,
        preferences: trip!.preferences,
      }),
    onMutate: async (activity) => {
      setSwappingId(activity.id)
      await queryClient.cancelQueries({ queryKey: queryKeys.tripResult(tripId!) })
      const previous = queryClient.getQueryData<Trip>(queryKeys.tripResult(tripId!))
      return { previous }
    },
    onSuccess: (newActivity, oldActivity) => {
      queryClient.setQueryData<Trip>(queryKeys.tripResult(tripId!), (old) => {
        if (!old) return old
        return {
          ...old,
          days: old.days.map((day) => {
            if (day.day_index !== activeDay) return day
            return {
              ...day,
              activities: day.activities.map((a) =>
                a.id === oldActivity.id ? newActivity : a,
              ),
            }
          }),
        }
      })
    },
    onError: (_err, _activity, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.tripResult(tripId!), context.previous)
      }
    },
    onSettled: () => {
      setSwappingId(null)
    },
  })

  const handleSwap = (activity: Activity) => {
    if (swappingId) return
    swapMutation.mutate(activity)
  }

  const handleReplan = () => {
    useTripStore.getState().reset()
    navigate('/plan')
  }

  if (isLoading) return <LoadingPage />

  if (error || !trip) {
    return (
      <div className="container mx-auto max-w-lg px-4 py-16 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
        <h2 className="mt-4 text-xl font-semibold">加载失败</h2>
        {error instanceof Error && (
          <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
        )}
        <Button className="mt-6" onClick={handleReplan}>
          重新规划
        </Button>
      </div>
    )
  }

  const safeDay = Math.min(activeDay, (trip.days?.length ?? 1) - 1)

  if (!trip.days || trip.days.length === 0) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <p className="text-muted-foreground">暂无行程数据</p>
        <Button className="mt-4" onClick={handleReplan}>
          重新规划
        </Button>
      </div>
    )
  }

  return (
    <ErrorBoundary onReset={handleReplan}>
      <div className="container mx-auto px-4 py-8">
        <TripHeader trip={trip} />
        <div className="mt-6 flex items-center gap-2">
          <Button
            variant={viewMode === 'timeline' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('timeline')}
          >
            时间轴
          </Button>
          <Button
            variant={viewMode === 'map' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('map')}
          >
            地图
          </Button>
        </div>
        <div className="mt-6 flex gap-8">
          <div className="flex-1">
            {viewMode === 'timeline' ? (
              <>
                <DayTabs
                  days={trip.days}
                  activeDay={safeDay}
                  onSelect={setActiveDay}
                />
                <DayTimeline
                  day={trip.days[safeDay]}
                  onSwap={handleSwap}
                  swappingId={swappingId}
                />
              </>
            ) : (
              <TripMapView
                days={trip.days}
                onSwap={handleSwap}
              />
            )}
          </div>
          <div className="w-72 flex-shrink-0 space-y-4">
            <WeatherCard tripId={tripId!} />
            <TripSidebar trip={trip} />
          </div>
        </div>
        <TripActions onReplan={handleReplan} />
      </div>
    </ErrorBoundary>
  )
}
