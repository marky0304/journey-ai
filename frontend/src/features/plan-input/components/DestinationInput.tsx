import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function DestinationInput({
  value,
  onChange,
}: {
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="space-y-2">
      <Label>目的地</Label>
      <Input
        placeholder="例如：东京、巴黎、云南..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}
