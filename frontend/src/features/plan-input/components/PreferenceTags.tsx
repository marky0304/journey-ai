import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'

const TAGS = ['文化历史', '自然风景', '美食', '购物', '探险', '摄影', '亲子', '浪漫']

export function PreferenceTags({
  selected,
  onChange,
}: {
  selected: string[]
  onChange: (v: string[]) => void
}) {
  const toggle = (tag: string) => {
    if (selected.includes(tag)) {
      onChange(selected.filter((t) => t !== tag))
    } else {
      onChange([...selected, tag])
    }
  }

  return (
    <div className="space-y-2">
      <Label>兴趣偏好（可多选）</Label>
      <div className="flex flex-wrap gap-2">
        {TAGS.map((tag) => (
          <Badge
            key={tag}
            variant={selected.includes(tag) ? 'default' : 'outline'}
            className="cursor-pointer px-4 py-2 text-sm"
            onClick={() => toggle(tag)}
          >
            {tag}
          </Badge>
        ))}
      </div>
    </div>
  )
}
