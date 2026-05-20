import { useEffect, useState } from 'react'
import type { BubbleMessage } from './types'

const fallbackPhrases = [
  '世界那么大，一起去看看！',
  '今天适合来一场说走就走的旅行~',
  '我知道好多好玩的地方哦！',
  '点击规划你的专属旅程吧！',
  '旅行最大的快乐在于期待~',
]

function randomPhrase(): BubbleMessage {
  const idx = Math.floor(Math.random() * fallbackPhrases.length)
  return { id: `${Date.now()}-${idx}`, text: fallbackPhrases[idx], mood: 'happy' }
}

interface SpeechBubbleProps {
  visible: boolean
  onHide: () => void
  phrases?: string[]
}

export function SpeechBubble({ visible, onHide, phrases }: SpeechBubbleProps) {
  const [message, setMessage] = useState<BubbleMessage>(randomPhrase)

  useEffect(() => {
    if (!visible) return
    const pool = phrases && phrases.length > 0 ? phrases : fallbackPhrases
    const idx = Math.floor(Math.random() * pool.length)
    setMessage({ id: `${Date.now()}-${idx}`, text: pool[idx], mood: 'happy' })
    const timer = setTimeout(onHide, 5000)
    return () => clearTimeout(timer)
  }, [visible, onHide, phrases])

  if (!visible) return null

  return (
    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50">
      <div className="relative bg-white rounded-2xl px-4 py-2 shadow-lg border border-slate-200 max-w-[180px]">
        <p className="text-xs text-slate-700 leading-relaxed whitespace-normal">
          {message.text}
        </p>
        <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-b border-r border-slate-200 rotate-45" />
      </div>
    </div>
  )
}
