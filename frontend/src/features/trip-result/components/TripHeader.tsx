import { Calendar, MapPin, Wallet } from 'lucide-react'
import type { Trip } from '@/types/api'

export function TripHeader({ trip }: { trip: Trip }) {
  return (
    <header>
      <h1 className="text-3xl font-bold">{trip.destination}</h1>
      <div className="mt-3 flex flex-wrap gap-4 text-sm text-muted-foreground">
        <span className="flex items-center gap-1">
          <Calendar className="h-4 w-4" />
          {trip.dates.start} — {trip.dates.end}
        </span>
        <span className="flex items-center gap-1">
          <Wallet className="h-4 w-4" />
          ¥{(trip.summary?.total_cost ?? 0).toLocaleString()}
        </span>
        <span className="flex items-center gap-1">
          <MapPin className="h-4 w-4" />
          {trip.summary?.attraction_count ?? 0} 个景点
        </span>
      </div>
    </header>
  )
}
