import { useQuery } from '@tanstack/react-query'
import { tripApi } from '@/shared/api/tripApi'
import { queryKeys } from '@/shared/api/queryKeys'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Cloud, CloudRain, Sun, Wind, Droplets, Thermometer } from 'lucide-react'
import type { WeatherDay } from '@/types/api'

const WEATHER_ICONS: Record<string, typeof Sun> = {
  '晴': Sun,
  '少云': Cloud,
  '晴间多云': Cloud,
  '多云': Cloud,
  '阴': Cloud,
  '雨': CloudRain,
  '小雨': CloudRain,
  '中雨': CloudRain,
  '大雨': CloudRain,
  '阵雨': CloudRain,
  '雪': Cloud,
  '风': Wind,
}

function WeatherIcon({ text }: { text: string }) {
  for (const [key, Icon] of Object.entries(WEATHER_ICONS)) {
    if (text.includes(key)) return <Icon className="h-5 w-5 text-sky-500" />
  }
  return <Cloud className="h-5 w-5 text-sky-400" />
}

function WeatherDayRow({ day }: { day: WeatherDay }) {
  const d = new Date(day.date)
  const label = `${d.getMonth() + 1}/${d.getDate()}`

  return (
    <div className="flex items-center gap-3 py-2 border-b border-slate-100 last:border-0">
      <span className="text-xs font-medium w-10">{label}</span>
      <WeatherIcon text={day.text_day} />
      <span className="text-xs text-muted-foreground flex-1">
        {day.text_day} / {day.text_night}
      </span>
      <span className="flex items-center gap-1 text-xs">
        <Thermometer className="h-3 w-3 text-orange-400" />
        {day.temp_min}° ~ {day.temp_max}°
      </span>
      {day.humidity > 0 && (
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <Droplets className="h-3 w-3" />
          {day.humidity}%
        </span>
      )}
    </div>
  )
}

export function WeatherCard({ tripId }: { tripId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.tripWeather(tripId),
    queryFn: () => tripApi.getWeather(tripId),
    enabled: !!tripId,
    staleTime: 30 * 60 * 1000,
  })

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-4">
          <div className="h-20 animate-pulse bg-muted rounded" />
        </CardContent>
      </Card>
    )
  }

  if (!data?.weather) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground text-center py-4">
            天气信息暂不可用
          </p>
        </CardContent>
      </Card>
    )
  }

  const { weather, outfits } = data

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <Cloud className="h-4 w-4 text-sky-500" />
          {weather.city}天气预报
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          {weather.forecast.map((day) => (
            <WeatherDayRow key={day.date} day={day} />
          ))}
        </div>
        {outfits.length > 0 && (
          <div className="mt-4 pt-3 border-t border-slate-200">
            <p className="text-xs font-medium text-muted-foreground mb-2">穿搭建议</p>
            {outfits.map((o) => (
              <div key={o.date} className="flex gap-2 py-1">
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {new Date(o.date).getMonth() + 1}/{new Date(o.date).getDate()}
                </span>
                <p className="text-xs leading-relaxed">{o.suggestion}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
