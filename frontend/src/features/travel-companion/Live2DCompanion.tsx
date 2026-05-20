import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import * as PIXI from 'pixi.js'
import type { Live2DModel } from 'pixi-live2d-display/cubism4'
import { SpeechBubble } from './SpeechBubble'
import { CompanionDialog } from './CompanionDialog'
import { StatusDot, getStatusType } from './StatusDot'
import { getCompanionContent } from './companionContent'
import { useTripStore, getPhase } from '@/shared/stores/useTripStore'
import type { TripPhase } from '@/shared/stores/useTripStore'
import type { ExpressionName, Position } from './types'

const CUBISM_CORE_URL = 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js'

let coreLoaded = false
let corePromise: Promise<void> | null = null

function loadCubismCore(): Promise<void> {
  if (coreLoaded) return Promise.resolve()
  if (corePromise) return corePromise

  corePromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = CUBISM_CORE_URL
    script.onload = () => {
      coreLoaded = true
      resolve()
    }
    script.onerror = () => reject(new Error('Failed to load Cubism Core'))
    document.head.appendChild(script)
  })

  return corePromise
}

const CANVAS_W = 220
const CANVAS_H = 280
const DEFAULT_RIGHT = 20
const DEFAULT_BOTTOM = 20
const POSITION_KEY = 'companion-position'
function loadPosition(): Position {
  try {
    const raw = localStorage.getItem(POSITION_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return {
    x: window.innerWidth - CANVAS_W / 2 - DEFAULT_RIGHT,
    y: window.innerHeight - CANVAS_H * 0.9 - DEFAULT_BOTTOM,
  }
}

function savePosition(pos: Position) {
  try {
    localStorage.setItem(POSITION_KEY, JSON.stringify(pos))
  } catch { /* ignore */ }
}

const PHASE_EXPRESSION: Record<TripPhase, ExpressionName> = {
  no_plan: 'Idle',
  planning: 'Loading',
  plan_generated: 'StarEye',
  trip_active: 'Amaze',
}

export function Live2DCompanion() {
  const canvasContainerRef = useRef<HTMLDivElement>(null)
  const appRef = useRef<PIXI.Application | null>(null)
  const modelRef = useRef<Live2DModel | null>(null)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showBubble, setShowBubble] = useState(false)
  const bubbleIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [dialogOpen, setDialogOpen] = useState(false)
  const [celebrating, setCelebrating] = useState(false)
  const [position, setPosition] = useState<Position>(loadPosition)
  const draggingRef = useRef(false)
  const dragStartRef = useRef<{ mx: number; my: number; px: number; py: number }>({ mx: 0, my: 0, px: 0, py: 0 })

  const trip = useTripStore((s) => s.currentTrip)
  const tripActive = useTripStore((s) => s.tripActive)
  const planning = useTripStore((s) => s.planning)
  const phase = getPhase(trip, tripActive, planning.taskId)
  const content = getCompanionContent(phase)

  const hasError =
    planning.errorMessage != null ||
    planning.agents.some((a) => a.status === 'error')
  const statusType = getStatusType(phase, hasError)

  const AGENT_CN: Record<string, string> = {
    coordinator: '总协调', transport: '交通', accommodation: '住宿',
    attraction: '景点', dining: '美食', strategy: '策略',
  }

  const phrases = useMemo(() => {
    if (phase !== 'planning') return content.phrases
    const { progress, agents } = planning
    const workingList = agents.filter((a) => a.status === 'working')
    const doneCount = agents.filter((a) => a.status === 'done').length
    const total = agents.length || 6
    const result: string[] = []

    if (progress < 25) {
      result.push('正在分析你的需求...')
    } else if (progress < 60) {
      result.push(`${doneCount}/${total} 模块已并行启动`)
    } else if (progress < 90) {
      result.push('正在汇总生成最终方案...')
    } else {
      result.push('马上就好，稍等哦~')
    }

    if (workingList.length > 0) {
      const names = workingList.map((a) => AGENT_CN[a.name] || a.name)
      result.push(`${names.slice(0, 3).join('、')} 规划中...`)
    }
    if (doneCount > 0 && doneCount < total) {
      result.push(`${doneCount} 个模块已完成`)
    }
    result.push(`总进度 ${progress}%`)
    result.push('点击我查看规划进度！')

    return result
  }, [phase, planning, content.phrases])

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      draggingRef.current = false
      dragStartRef.current = { mx: e.clientX, my: e.clientY, px: position.x, py: position.y }

      const onMove = (ev: MouseEvent) => {
        const dx = ev.clientX - dragStartRef.current.mx
        const dy = ev.clientY - dragStartRef.current.my
        if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
          draggingRef.current = true
        }
        setPosition({
          x: dragStartRef.current.px + dx,
          y: dragStartRef.current.py + dy,
        })
      }

      const onUp = () => {
        document.removeEventListener('mousemove', onMove)
        document.removeEventListener('mouseup', onUp)
        setPosition((prev) => {
          savePosition(prev)
          return prev
        })
      }

      document.addEventListener('mousemove', onMove)
      document.addEventListener('mouseup', onUp)
    },
    [position],
  )

  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      const touch = e.touches[0]
      draggingRef.current = false
      dragStartRef.current = { mx: touch.clientX, my: touch.clientY, px: position.x, py: position.y }

      const onMove = (ev: TouchEvent) => {
        const t = ev.touches[0]
        const dx = t.clientX - dragStartRef.current.mx
        const dy = t.clientY - dragStartRef.current.my
        if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
          draggingRef.current = true
        }
        setPosition({
          x: dragStartRef.current.px + dx,
          y: dragStartRef.current.py + dy,
        })
      }

      const onUp = () => {
        document.removeEventListener('touchmove', onMove)
        document.removeEventListener('touchend', onUp)
        setPosition((prev) => {
          savePosition(prev)
          return prev
        })
      }

      document.addEventListener('touchmove', onMove, { passive: true })
      document.addEventListener('touchend', onUp)
    },
    [position],
  )

  useEffect(() => {
    let cancelled = false

    async function init() {
      try {
        await loadCubismCore()

        const { Live2DModel: L2DModel } = await import('pixi-live2d-display/cubism4')

        if (cancelled || !canvasContainerRef.current) return

        const app = new PIXI.Application({
          width: CANVAS_W,
          height: CANVAS_H,
          backgroundAlpha: 0,
          antialias: true,
          resolution: window.devicePixelRatio || 1,
          autoDensity: true,
        })

        appRef.current = app
        canvasContainerRef.current.appendChild(app.view as HTMLCanvasElement)

        const model = await L2DModel.from('/live2d/Doro/Doro.model3.json', {
          ticker: PIXI.Ticker.shared,
        })

        if (cancelled) {
          model.destroy()
          app.destroy(true)
          return
        }

        model.anchor.set(0.5, 0.7)
        model.x = CANVAS_W / 2
        model.y = CANVAS_H - 20
        model.scale.set(0.1, 0.1)
        model.eventMode = 'static'

        model.on('hit', handleCompanionClick)

        app.stage.addChild(model)
        modelRef.current = model
        setReady(true)
      } catch (e) {
        if (!cancelled) setError(String(e))
      }
    }

    init()

    return () => {
      cancelled = true
      if (modelRef.current) {
        modelRef.current.destroy()
        modelRef.current = null
      }
      if (appRef.current) {
        appRef.current.destroy(true, { children: true, texture: true })
        appRef.current = null
      }
      if (bubbleIntervalRef.current) clearInterval(bubbleIntervalRef.current)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!modelRef.current) return
    const expr = PHASE_EXPRESSION[phase] || 'Idle'
    modelRef.current.expression(expr).catch(() => {})
  }, [phase])

  useEffect(() => {
    if (!modelRef.current || celebrating) return
    modelRef.current.motion('Idle', undefined, 3).catch(() => {})
  }, [celebrating])

  useEffect(() => {
    if (!ready) return
    const delay = phase === 'planning' ? 5000 + Math.random() * 3000 : 12000 + Math.random() * 8000
    bubbleIntervalRef.current = setInterval(() => {
      setShowBubble(true)
    }, delay)
    setShowBubble(true)
    return () => {
      if (bubbleIntervalRef.current) clearInterval(bubbleIntervalRef.current)
    }
  }, [ready, phase])

  const handleCompanionClick = useCallback(() => {
    if (draggingRef.current) return

    setCelebrating(true)
    if (modelRef.current) {
      modelRef.current.motion('jump', undefined, 1).catch(() => {})
    }
    setTimeout(() => setCelebrating(false), 600)
    setDialogOpen(true)
  }, [])

  return (
    <>
      <CompanionDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />

      <div className="fixed inset-0 pointer-events-none z-[9999]">
        <div
          className="absolute pointer-events-auto select-none cursor-grab active:cursor-grabbing"
          style={{
            left: position.x,
            top: position.y,
            width: CANVAS_W,
            height: CANVAS_H,
            transform: 'translate(-50%, -90%)',
          }}
          onMouseDown={handleMouseDown}
          onTouchStart={handleTouchStart}
          title="点击和小旅互动"
        >
          <SpeechBubble
            visible={showBubble}
            onHide={() => setShowBubble(false)}
            phrases={phrases}
          />

          {statusType && <StatusDot type={statusType} />}

          <div
            ref={canvasContainerRef}
            className={`relative ${celebrating ? 'animate-jump' : 'animate-bounce-small'}`}
          >
            {error && (
              <div className="text-xs text-red-500 bg-white/80 rounded p-1 absolute inset-0 flex items-center justify-center">
                加载失败
              </div>
            )}
            {!ready && !error && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
