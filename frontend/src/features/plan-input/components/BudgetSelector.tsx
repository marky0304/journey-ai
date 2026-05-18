import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function BudgetSelector({
  min,
  max,
  onChange,
}: {
  min: number
  max: number
  onChange: (min: number, max: number) => void
}) {
  return (
    <div className="space-y-2">
      <Label>预算范围 (元)</Label>
      <div className="flex items-center gap-2">
        <Input
          type="number"
          placeholder="最低"
          value={min || ''}
          onChange={(e) => onChange(Number(e.target.value), max)}
        />
        <span className="text-muted-foreground">—</span>
        <Input
          type="number"
          placeholder="最高"
          value={max || ''}
          onChange={(e) => onChange(min, Number(e.target.value))}
        />
      </div>
    </div>
  )
}
