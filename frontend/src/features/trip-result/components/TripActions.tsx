import { Button } from '@/components/ui/button'
import { Download, Share2, RotateCcw } from 'lucide-react'

export function TripActions({ onReplan }: { onReplan: () => void }) {
  return (
    <div className="mt-8 flex justify-center gap-4 border-t pt-8">
      <Button variant="outline" disabled aria-label="导出 PDF（即将推出）">
        <Download className="mr-2 h-4 w-4" />
        导出 PDF
      </Button>
      <Button variant="outline" disabled aria-label="分享行程（即将推出）">
        <Share2 className="mr-2 h-4 w-4" />
        分享行程
      </Button>
      <Button variant="outline" onClick={onReplan}>
        <RotateCcw className="mr-2 h-4 w-4" />
        重新规划
      </Button>
    </div>
  )
}
