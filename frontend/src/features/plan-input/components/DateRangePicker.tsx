import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function DateRangePicker({
  start,
  end,
  onChange,
}: {
  start: string
  end: string
  onChange: (s: string, e: string) => void
}) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label>出发日期</Label>
        <Input type="date" value={start} onChange={(e) => onChange(e.target.value, end)} />
      </div>
      <div className="space-y-2">
        <Label>返程日期</Label>
        <Input type="date" value={end} onChange={(e) => onChange(start, e.target.value)} />
      </div>
    </div>
  )
}
