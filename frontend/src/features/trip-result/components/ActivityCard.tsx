import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Clock, RefreshCw } from 'lucide-react'
import type { Activity } from '@/types/api'

const TYPE_LABELS: Record<Activity['type'], string> = {
  attraction: '景点',
  dining: '餐饮',
  transport: '交通',
  hotel: '住宿',
}

const SWAPPABLE_TYPES: Activity['type'][] = ['attraction', 'dining']

export function ActivityCard({
  activity,
  onSwap,
  swapping,
}: {
  activity: Activity
  onSwap?: () => void
  swapping?: boolean
}) {
  const canSwap = SWAPPABLE_TYPES.includes(activity.type) && onSwap

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold">{activity.name}</h4>
            <div className="mt-2 flex flex-wrap gap-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                <time dateTime={activity.start_time}>{activity.start_time}</time>
                {' - '}
                <time dateTime={activity.end_time}>{activity.end_time}</time>
              </span>
              {activity.description && <span>{activity.description}</span>}
            </div>
            {activity.tips && (
              <p className="mt-2 text-xs text-muted-foreground">
                提示: {activity.tips}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 ml-3">
            {canSwap && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-primary"
                onClick={onSwap}
                disabled={swapping}
                title="换一个"
              >
                <RefreshCw
                  className={`h-4 w-4 ${swapping ? 'animate-spin' : ''}`}
                />
              </Button>
            )}
            <Badge variant="secondary">
              {TYPE_LABELS[activity.type] || activity.type}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
