import { Label } from '@/components/ui/label'

const STYLES = [
  { value: 'relaxed', label: '轻松休闲', desc: '每天 2-3 个景点' },
  { value: 'balanced', label: '适中平衡', desc: '有玩有闲' },
  { value: 'compact', label: '紧凑充实', desc: '打卡更多景点' },
]

export function TravelStyleSelect({
  value,
  onChange,
}: {
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="space-y-2">
      <Label>旅行节奏</Label>
      <div className="grid grid-cols-3 gap-2">
        {STYLES.map((s) => (
          <button
            key={s.value}
            type="button"
            className={`rounded-lg border p-3 text-left transition ${
              value === s.value
                ? 'border-primary bg-primary/5 ring-1 ring-primary'
                : 'hover:border-muted-foreground/30'
            }`}
            onClick={() => onChange(s.value)}
          >
            <div className="text-sm font-medium">{s.label}</div>
            <div className="text-xs text-muted-foreground">{s.desc}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
