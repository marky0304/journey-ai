import { TimelineItem } from './TimelineItem'
import type { Activity, DayPlan } from '@/types/api'

export function DayTimeline({
  day,
  onSwap,
  swappingId,
}: {
  day: DayPlan
  onSwap?: (activity: Activity) => void
  swappingId?: string | null
}) {
  if (!day) return null

  return (
    <div className="relative mt-6 space-y-0">
      {day.activities?.map((activity, i) => (
        <TimelineItem
          key={activity.id ?? i}
          activity={activity}
          isLast={i === day.activities.length - 1}
          onSwap={onSwap}
          swappingId={swappingId}
        />
      ))}
    </div>
  )
}
