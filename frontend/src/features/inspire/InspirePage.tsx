import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/client'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Sparkles, MapPin, DollarSign, Calendar, Tag } from 'lucide-react'

interface DestinationCard {
  name: string
  reason: string
  season: string
  budget_estimate: number
  highlights: string[]
  tags: string[]
}

interface InspireResponse {
  destinations: DestinationCard[]
}

export default function InspirePage() {
  const navigate = useNavigate()
  const [preferences, setPreferences] = useState('')
  const [budget, setBudget] = useState(5000)
  const [days, setDays] = useState(3)
  const [results, setResults] = useState<DestinationCard[] | null>(null)

  const inspireMutation = useMutation({
    mutationFn: (data: { preferences: string; budget_max: number; days: number }) =>
      apiClient.post<InspireResponse>('/trip/inspire', data).then((r) => r.data),
  })

  const handleInspire = () => {
    inspireMutation.mutate(
      { preferences, budget_max: budget, days },
      { onSuccess: (data) => setResults(data.destinations) },
    )
  }

  const handleSelect = (dest: DestinationCard) => {
    navigate(`/plan?destination=${encodeURIComponent(dest.name)}`)
  }

  return (
    <div className="container mx-auto max-w-3xl px-4 py-8">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold flex items-center justify-center gap-2">
          <Sparkles className="w-6 h-6 text-amber-500" />
          不知道去哪？
        </h1>
        <p className="mt-2 text-muted-foreground">
          告诉小智你的偏好，为你发现下一个心动目的地
        </p>
      </div>

      <Card className="p-6 mb-8">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">偏好</label>
            <input
              className="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="比如：海边、美食、历史文化..."
              value={preferences}
              onChange={(e) => setPreferences(e.target.value)}
            />
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium mb-1 block">预算 (元/人)</label>
              <input
                type="range"
                min={500}
                max={20000}
                step={500}
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground mt-1">{budget.toLocaleString()} 元</p>
            </div>
            <div className="w-24">
              <label className="text-sm font-medium mb-1 block">天数</label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full rounded-md border px-3 py-2 text-sm"
              >
                {[1, 2, 3, 4, 5, 7, 10].map((d) => (
                  <option key={d} value={d}>{d} 天</option>
                ))}
              </select>
            </div>
          </div>

          <Button
            onClick={handleInspire}
            disabled={inspireMutation.isPending}
            className="w-full"
          >
            {inspireMutation.isPending ? '小智正在思考...' : '帮我推荐'}
          </Button>
        </div>
      </Card>

      {inspireMutation.isError && (
        <p className="text-center text-sm text-destructive mb-4">
          推荐失败，请重试
        </p>
      )}

      {results && results.length > 0 && (
        <div className="grid gap-4 md:grid-cols-3">
          {results.map((dest, i) => (
            <Card
              key={i}
              className="p-5 cursor-pointer hover:shadow-md transition-shadow flex flex-col"
              onClick={() => handleSelect(dest)}
            >
              <h3 className="text-lg font-bold mb-2">{dest.name}</h3>
              <p className="text-xs text-muted-foreground mb-3 flex-1">
                {dest.reason}
              </p>

              <div className="space-y-1.5 text-xs text-muted-foreground">
                <div className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5" />
                  {dest.season}
                </div>
                <div className="flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5" />
                  约 {dest.budget_estimate.toLocaleString()} 元/人
                </div>
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5" />
                  {dest.highlights.slice(0, 2).join('、')}
                </div>
              </div>

              <div className="flex flex-wrap gap-1 mt-3">
                {dest.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs"
                  >
                    <Tag className="w-2.5 h-2.5" />
                    {tag}
                  </span>
                ))}
              </div>

              <Button size="sm" className="w-full mt-3" variant="outline">
                选择这里
              </Button>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
