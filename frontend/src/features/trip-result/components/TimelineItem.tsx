import { ActivityCard } from './ActivityCard'
import type { Activity } from '@/types/api'

export function TimelineItem({
  activity,
  isLast,
  onSwap,
  swappingId,
}: {
  activity: Activity
  isLast: boolean
  onSwap?: (activity: Activity) => void
  swappingId?: string | null
}) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
          {activity.start_time}
        </div>
        {!isLast && <div className="w-0.5 flex-1 bg-border" />}
      </div>
      <div className={isLast ? '' : 'pb-8'}>
        <ActivityCard
          activity={activity}
          onSwap={onSwap ? () => onSwap(activity) : undefined}
          swapping={swappingId === activity.id}
        />
      </div>
    </div>
  )
}
