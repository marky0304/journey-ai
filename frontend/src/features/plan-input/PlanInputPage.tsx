import { usePlanForm } from './hooks/usePlanForm'
import { DestinationInput } from './components/DestinationInput'
import { DateRangePicker } from './components/DateRangePicker'
import { BudgetSelector } from './components/BudgetSelector'
import { PreferenceTags } from './components/PreferenceTags'
import { TravelStyleSelect } from './components/TravelStyleSelect'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'

export default function PlanInputPage() {
  const { form, setForm, submit, isLoading } = usePlanForm()

  return (
    <div className="container mx-auto max-w-2xl px-4 py-12">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">设计你的旅程</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <DestinationInput
            value={form.destination}
            onChange={(v) => setForm({ ...form, destination: v })}
          />
          <DateRangePicker
            start={form.start_date}
            end={form.end_date}
            onChange={(s, e) => setForm({ ...form, start_date: s, end_date: e })}
          />
          <BudgetSelector
            min={form.budget_min}
            max={form.budget_max}
            onChange={(min, max) => setForm({ ...form, budget_min: min, budget_max: max })}
          />
          <PreferenceTags
            selected={form.preferences}
            onChange={(p) => setForm({ ...form, preferences: p })}
          />
          <TravelStyleSelect
            value={form.travel_style}
            onChange={(v) => setForm({ ...form, travel_style: v })}
          />
          <Button
            className="w-full"
            size="lg"
            disabled={!form.destination || !form.start_date || isLoading}
            onClick={submit}
          >
            {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            开始 AI 规划
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
