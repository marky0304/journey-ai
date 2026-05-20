import type { TripPhase } from '@/shared/stores/useTripStore'

type StatusType = 'error' | 'loading' | 'success'

interface StatusDotProps {
  type: StatusType
}

const META: Record<StatusType, { gradient: string; shadow: string; label: string; className: string }> = {
  error: {
    gradient: 'linear-gradient(135deg, #ff7875, #ff4d4f)',
    shadow: '0 0 8px rgba(255, 77, 79, 0.45)',
    label: '请求出错，请重试',
    className: 'animate-pulse',
  },
  loading: {
    gradient: 'linear-gradient(135deg, #ffc53d, #faad14)',
    shadow: '0 0 8px rgba(250, 173, 20, 0.45)',
    label: '正在生成回复中',
    className: 'animate-breathe',
  },
  success: {
    gradient: 'linear-gradient(135deg, #73d13d, #52c41a)',
    shadow: '0 0 6px rgba(82, 196, 26, 0.4)',
    label: '操作已完成',
    className: '',
  },
}

export function StatusDot({ type }: StatusDotProps) {
  const { gradient, shadow, label, className } = META[type]

  return (
    <div className="absolute top-0 right-0 z-10 group">
      <div
        className={`w-3 h-3 rounded-full border-2 border-white ${className}`}
        style={{
          background: gradient,
          boxShadow: shadow,
        }}
      />
      <div
        className="absolute top-full right-0 mt-1.5 hidden group-hover:block pointer-events-none"
        style={{ zIndex: 9999 }}
      >
        <div
          className="text-[11px] text-white whitespace-nowrap rounded-lg px-2.5 py-1"
          style={{
            background: 'linear-gradient(135deg, rgba(0,0,0,0.75), rgba(0,0,0,0.65))',
            backdropFilter: 'blur(4px)',
          }}
        >
          {label}
        </div>
      </div>
    </div>
  )
}

export function getStatusType(
  phase: TripPhase,
  hasError: boolean,
): StatusType | null {
  if (phase === 'no_plan') return null
  if (hasError) return 'error'
  if (phase === 'planning') return 'loading'
  return 'success'
}
