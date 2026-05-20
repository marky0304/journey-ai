import type { DayPlan } from '@/types/api'

export function DayTabs({
  days,
  activeDay,
  onSelect,
}: {
  days: DayPlan[]
  activeDay: number
  onSelect: (i: number) => void
}) {
  return (
    <div role="tablist" aria-label="选择日期" className="flex gap-2 border-b pb-4">
      {days.map((day, i) => (
        <button
          key={day.day_index}
          role="tab"
          aria-selected={i === activeDay}
          tabIndex={i === activeDay ? 0 : -1}
          className={`rounded-md px-4 py-2 text-sm font-medium transition ${
            i === activeDay
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:bg-muted'
          }`}
          onClick={() => onSelect(i)}
        >
          第 {day.day_index} 天
        </button>
      ))}
    </div>
  )
}
