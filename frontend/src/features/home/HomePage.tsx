import { useTripStore, getPhase } from '@/shared/stores/useTripStore'
import { HeroSection } from './components/HeroSection'
import { FeatureSection } from './components/FeatureSection'
import { HowItWorks } from './components/HowItWorks'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Calendar, Navigation } from 'lucide-react'

function ActiveTripView() {
  const trip = useTripStore((s) => s.currentTrip)
  const resetTripActive = useTripStore((s) => s.resetTripActive)

  if (!trip) return null

  const today = new Date()
  const tripStartDay = trip.dates?.start ? new Date(trip.dates.start) : today
  const elapsedDays = Math.max(0, Math.floor((today.getTime() - tripStartDay.getTime()) / 86400000))
  const totalDays = trip.days?.length || 0
  const progressPct = totalDays > 0 ? Math.min(100, Math.round((elapsedDays / totalDays) * 100)) : 0

  const todayDay = trip.days?.[elapsedDays]

  return (
    <section className="container mx-auto px-4 py-12">
      <div className="mx-auto max-w-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm text-muted-foreground">
            <Navigation className="h-4 w-4" /> 旅途进行中
          </div>
          <h2 className="mt-4 text-3xl font-bold tracking-tight">{trip.destination}</h2>
          <p className="text-muted-foreground mt-2">第 {elapsedDays + 1} / {totalDays} 天</p>
        </div>

        <div className="w-full bg-slate-200 rounded-full h-3 mb-8">
          <div
            className="bg-gradient-to-r from-sky-400 to-indigo-500 h-3 rounded-full transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>

        {todayDay ? (
          <Card className="border-2 border-amber-100 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4 text-amber-500" />
                今日行程 · Day {todayDay.day_index}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(todayDay.activities || []).map((act) => (
                <div key={act.id} className="flex items-center gap-3 bg-slate-50 rounded-lg p-3">
                  <div className="w-2 h-2 rounded-full bg-amber-400" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-700">{act.name}</p>
                    <p className="text-xs text-slate-400">{act.type}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        ) : (
          <Card className="border-2 border-slate-100">
            <CardContent className="p-6 text-center text-muted-foreground">
              <p>今天的行程已经完成啦！点击右下角小智查看旅途贴士~</p>
            </CardContent>
          </Card>
        )}

        <div className="mt-6 text-center">
          <Button variant="outline" size="sm" onClick={resetTripActive}>
            结束这趟旅行
          </Button>
        </div>
      </div>
    </section>
  )
}

export default function HomePage() {
  const trip = useTripStore((s) => s.currentTrip)
  const tripActive = useTripStore((s) => s.tripActive)
  const phase = getPhase(trip, tripActive, null)

  if (phase === 'trip_active') {
    return <ActiveTripView />
  }

  return (
    <>
      <HeroSection />
      <FeatureSection />
      <HowItWorks />
    </>
  )
}
