import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Trip, TravelStyle } from '@/types/api'

const styleLabel: Record<TravelStyle, string> = {
  relaxed: '轻松',
  balanced: '适中',
  compact: '紧凑',
}

export function TripSidebar({ trip }: { trip: Trip }) {
  return (
    <aside className="hidden w-72 shrink-0 lg:block" aria-label="行程概览">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">行程概览</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">目的地</span>
            <span className="font-medium">{trip.destination}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">天数</span>
            <span className="font-medium">{trip.days?.length ?? 0} 天</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">景点数</span>
            <span className="font-medium">{trip.summary?.attraction_count ?? 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">预算</span>
            <span className="font-medium">
              ¥{(trip.summary?.total_cost ?? 0).toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">风格</span>
            <span className="font-medium">
              {styleLabel[trip.travel_style] || trip.travel_style}
            </span>
          </div>
        </CardContent>
      </Card>
    </aside>
  )
}
