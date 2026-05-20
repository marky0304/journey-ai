import { useEffect, useRef, useState, useCallback } from 'react'
import { useAMap } from '@/hooks/useAMap'
import type { DayPlan, Activity } from '@/types/api'

const DAY_COLORS = [
  '#4A90D9', '#50C878', '#FF6B35', '#9B59B6',
  '#E74C3C', '#1ABC9C', '#F39C12', '#2980B9',
]

interface TripMapViewProps {
  days: DayPlan[]
  onSwap?: (activity: Activity) => void
}

export function TripMapView({ days, onSwap }: TripMapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<AMap.Map | null>(null)
  const { AMap: AMapApi, loaded, error: loadError } = useAMap()
  const [mapReady, setMapReady] = useState(false)
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null)
  const [walking, setWalking] = useState(false)

  const allActivities = days.flatMap((day) =>
    day.activities
      .filter((a) => a.location?.lat && a.location?.lng)
      .map((a) => ({ ...a, dayIndex: day.day_index })),
  )

  useEffect(() => {
    if (!loaded || !AMapApi || !containerRef.current || mapRef.current) return

    const map = new AMapApi.Map(containerRef.current, {
      zoom: 12,
      center: [116.397428, 39.90923],
      viewMode: '3D',
      resizeEnable: true,
    })

    mapRef.current = map
    setMapReady(true)

    return () => {
      map.destroy()
      mapRef.current = null
    }
  }, [loaded, AMapApi])

  useEffect(() => {
    if (!mapReady || !AMapApi || !mapRef.current || allActivities.length === 0) return

    const map = mapRef.current

    const overlays: (AMap.Marker | AMap.Polyline)[] = []
    const grouped: Map<number, Activity[]> = new Map()

    for (const a of allActivities) {
      if (!grouped.has(a.dayIndex)) grouped.set(a.dayIndex, [])
      grouped.get(a.dayIndex)!.push(a)
    }

    let firstPos: [number, number] | null = null

    for (const [dayIdx, acts] of grouped) {
      const color = DAY_COLORS[dayIdx % DAY_COLORS.length]
      const path: [number, number][] = []

      for (const a of acts) {
        const pos: [number, number] = [a.location!.lng, a.location!.lat]
        path.push(pos)
        if (!firstPos) firstPos = pos

        try {
          const marker = new AMapApi.Marker({
            position: pos,
            label: {
              content: `<div style="background:${color};color:#fff;padding:2px 6px;border-radius:8px;font-size:11px;white-space:nowrap">${a.name}</div>`,
              direction: 'top',
            },
            zIndex: 100,
          })
          if (marker) {
            marker.on('click', () => setSelectedActivity(a))
            overlays.push(marker)
          }
        } catch {
          // marker creation failed — skip
        }
      }

      if (path.length >= 2) {
        try {
          const polyline = new AMapApi.Polyline({
            path,
            strokeColor: color,
            strokeWeight: 4,
            strokeOpacity: 0.7,
            lineJoin: 'round',
            zIndex: 50,
          })
          if (polyline) overlays.push(polyline)
        } catch {
          // polyline creation failed — skip
        }
      }
    }

    if (overlays.length > 0) {
      map.add(overlays)
    }

    if (firstPos) {
      map.setFitView(undefined, false, [60, 60, 60, 60])
    }

    return () => {
      if (overlays.length > 0) {
        try {
          map.remove(overlays)
        } catch {
          // map may already be destroyed
        }
      }
    }
  }, [mapReady, AMapApi, allActivities])

  const handleWalk = useCallback(() => {
    if (!mapRef.current || !AMapApi || allActivities.length < 2 || walking) return

    setWalking(true)
    const charEl = document.createElement('div')
    charEl.innerHTML = `<div style="font-size:28px;transform:translate(-50%,-100%)">🧭</div>`
    const charMarker = new AMapApi.Marker({
      content: charEl,
      position: [allActivities[0].location!.lng, allActivities[0].location!.lat],
      zIndex: 200,
      offset: new AMapApi.Pixel(0, 0) as unknown as { x: number; y: number },
    })
    mapRef.current.add(charMarker)

    let i = 0
    const steps = allActivities.length
    const interval = setInterval(() => {
      i++
      if (i >= steps) {
        clearInterval(interval)
        mapRef.current?.remove(charMarker)
        setWalking(false)
        return
      }
      const next = allActivities[i]
      if (next.location) {
        charMarker.setPosition([next.location.lng, next.location.lat])
      }
    }, 1200)
  }, [AMapApi, allActivities, walking])

  if (loadError) {
    return (
      <div className="rounded-lg border bg-muted/20 p-8 text-center text-sm text-muted-foreground">
        {loadError}
      </div>
    )
  }

  if (!loaded) {
    return (
      <div className="rounded-lg border bg-muted/20 p-8 flex items-center justify-center" style={{ height: 400 }}>
        <div className="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex gap-2 flex-wrap">
          {days.map((day, i) => (
            <span
              key={day.day_index}
              className="inline-flex items-center gap-1.5 text-xs"
            >
              <span
                className="inline-block w-3 h-3 rounded-full"
                style={{ background: DAY_COLORS[i % DAY_COLORS.length] }}
              />
              第{day.day_index}天
            </span>
          ))}
        </div>
        {allActivities.length >= 2 && (
          <button
            onClick={handleWalk}
            disabled={walking}
            className="px-3 py-1.5 text-xs rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {walking ? '行走中...' : '开始行走'}
          </button>
        )}
      </div>

      <div
        ref={containerRef}
        className="rounded-lg border overflow-hidden"
        style={{ width: '100%', height: 400 }}
      />

      {selectedActivity && (
        <div className="rounded-lg border bg-card p-4 text-sm space-y-1">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">{selectedActivity.name}</h4>
            <button
              onClick={() => setSelectedActivity(null)}
              className="text-muted-foreground hover:text-foreground"
            >
              ✕
            </button>
          </div>
          {selectedActivity.description && (
            <p className="text-muted-foreground">{selectedActivity.description}</p>
          )}
          <div className="flex gap-4 text-xs text-muted-foreground">
            <span>{selectedActivity.start_time} - {selectedActivity.end_time}</span>
          </div>
          {selectedActivity.tips && (
            <p className="text-xs text-muted-foreground">小贴士: {selectedActivity.tips}</p>
          )}
          {onSwap && (
            <button
              onClick={() => onSwap(selectedActivity)}
              className="mt-2 px-3 py-1 text-xs rounded bg-secondary hover:bg-secondary/80"
            >
              换一个
            </button>
          )}
        </div>
      )}
    </div>
  )
}
