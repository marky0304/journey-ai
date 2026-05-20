import { useState, useCallback, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { tripApi } from '@/shared/api/tripApi'
import { apiClient } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import { useTripStore, getPhase } from '@/shared/stores/useTripStore'
import { useAuthStore } from '@/shared/stores/useAuthStore'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  X, Send, Sparkles, MapPin, Calendar, BookOpen,
  MessageCircle, Navigation, AlertCircle, Trash2,
  Play, Sun, Thermometer, Clock, Wind, Phone, Wifi, Cloud, DollarSign,
  History, Lightbulb, CheckCircle2, Loader2, ArrowRight, Brain,
} from 'lucide-react'
import type { ClarifyResponse, LearnHistoryItem, LearnAnalyzeResult, AgentInfo, Trip, TravelStyle, ClarifyRequest, PlanRequest, TripSessionGroup } from '@/types/api'
import { ProgressIndicator } from '@/features/planning/components/ProgressIndicator'
import { AgentStatusCard } from '@/features/planning/components/AgentStatusCard'

// ─── Chat types ────────────────────────────────────────────────
interface ChatMessage {
  role: 'companion' | 'user'
  content: string
  options?: string[]
  tripPlan?: Trip
}

const QUICK_OPTIONS = [
  { label: '推荐目的地', reply: '帮我推荐一个适合现在去的目的地吧' },
  { label: '3-5 天短途', reply: '我想去一个3-5天的短途旅行' },
  { label: '亲子出游', reply: '带家人去，适合亲子的地方' },
  { label: '美食之旅', reply: '想来一场以美食为主题的旅行' },
]

const TRAVEL_QA_OPTIONS = [
  { label: '当地美食推荐', reply: '有什么当地特色美食推荐吗？' },
  { label: '必去景点', reply: '有哪些必去的景点？' },
  { label: '交通攻略', reply: '当地的交通怎么安排比较方便？' },
  { label: '旅行小贴士', reply: '有什么实用的旅行小贴士吗？' },
]

// ─── Learn helpers ──────────────────────────────────────────────
const PLATFORM_RULES: { pattern: RegExp; name: string; color: string }[] = [
  { pattern: /xiaohongshu\.com|xhslink\.com/, name: '小红书', color: '#FF2442' },
  { pattern: /douyin\.com/, name: '抖音', color: '#000000' },
  { pattern: /bilibili\.com|b23\.tv/, name: 'B站', color: '#00A1D6' },
  { pattern: /weibo\.com/, name: '微博', color: '#E6162D' },
  { pattern: /mafengwo\.cn/, name: '马蜂窝', color: '#FFD700' },
  { pattern: /qyer\.com/, name: '穷游', color: '#00BFFF' },
  { pattern: /ctrip\.com/, name: '携程', color: '#2577E3' },
  { pattern: /meituan\.com/, name: '美团', color: '#FFD100' },
  { pattern: /dianping\.com/, name: '大众点评', color: '#FF6633' },
]

function detectPlatform(url: string): { name: string; color: string } {
  for (const rule of PLATFORM_RULES) {
    if (rule.pattern.test(url)) return { name: rule.name, color: rule.color }
  }
  return { name: '网页', color: '#6366F1' }
}

// ─── Time-based tips ───────────────────────────────────────────
function getTimeBasedTip(): { title: string; tips: string[]; Icon: typeof Sun } {
  const h = new Date().getHours()
  if (h < 10) {
    return {
      title: '早安，开启美好的一天！',
      Icon: Sun,
      tips: ['早晨景点人少，适合拍照打卡', '记得吃早餐补充能量', '检查随身物品：手机、钱包、证件'],
    }
  }
  if (h < 14) {
    return {
      title: '午间出行提醒',
      Icon: Thermometer,
      tips: ['中午气温较高，注意防晒补水', '热门餐厅可能排队，建议提前预约', '合理分配体力，适时休整'],
    }
  }
  if (h < 18) {
    return {
      title: '下午游玩小贴士',
      Icon: Clock,
      tips: ['傍晚光线最适合拍照', '关注景点闭园时间，合理安排', '当地特色小吃街可能已开市'],
    }
  }
  return {
    title: '晚间温馨提示',
    Icon: Wind,
    tips: ['夜间出行注意安全', '确认酒店入住/退房时间', '规划明天的行程和交通', '当地紧急电话：110/120/119'],
  }
}

const GENERAL_TIPS = {
  emergency: [
    { icon: Phone, label: '报警', value: '110' },
    { icon: Phone, label: '急救', value: '120' },
    { icon: Phone, label: '火警', value: '119' },
    { icon: Phone, label: '交警', value: '122' },
  ],
  transport: [
    '关注下一段交通时间，预留充足缓冲',
    '地铁/公交末班时间请提前查好',
    '打车软件确认车牌号再上车',
  ],
}

// ─── Props ──────────────────────────────────────────────────────
interface CompanionDialogProps {
  open: boolean
  onClose: () => void
}

// ─── Tab: AI 对话 ───────────────────────────────────────────────
function ChatTab({ tripId, isGeneralChat, onNavigate }: {
  tripId: string | null
  isGeneralChat: boolean
  onNavigate: () => void
}) {
  const trip = useTripStore((s) => s.currentTrip)
  const setTaskId = useTripStore((s) => s.setTaskId)
  const navigate = useNavigate()

  const sessionIdRef = useRef<string>(crypto.randomUUID())
  const hasSentMessagesRef = useRef(false)

  const initialMsg: ChatMessage = isGeneralChat
    ? (trip
        ? { role: 'companion' as const, content: '✨ 你的专属旅行方案已生成！以下是详细行程，有任何问题随时问我~', tripPlan: trip, options: TRAVEL_QA_OPTIONS.map((o) => o.label) }
        : { role: 'companion' as const, content: '嘿！有什么关于这次旅行想了解的？尽管问我！', options: TRAVEL_QA_OPTIONS.map((o) => o.label) })
    : { role: 'companion' as const, content: '嘿！我是小旅，你的旅行伙伴。告诉我你想去哪里玩？或者选一个下面的选项让我帮你推荐~', options: QUICK_OPTIONS.map((o) => o.label) }

  const [messages, setMessages] = useState<ChatMessage[]>([initialMsg])
  const [inputValue, setInputValue] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [collectedInfo, setCollectedInfo] = useState<Record<string, string>>({})
  const [showHistory, setShowHistory] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mountedRef = useRef(true)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    // Create a fresh AbortController on each mount to avoid
    // React strict mode permanently aborting the signal.
    const ctrl = new AbortController()
    abortRef.current = ctrl
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      ctrl.abort()
    }
  }, [])

  const getAbortSignal = () => abortRef.current?.signal

  const safeSetMessages = (updater: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => {
    if (mountedRef.current) setMessages(updater)
  }
  const safeSetThinking = (v: boolean) => {
    if (mountedRef.current) setIsThinking(v)
  }

  const clarifyMut = useMutation({
    mutationFn: (data: ClarifyRequest) =>
      apiClient.post<ClarifyResponse>('/trip/clarify', data, { signal: getAbortSignal() }).then((r) => r.data),
  })
  const createMut = useMutation({
    mutationFn: (data: PlanRequest) =>
      apiClient.post<{ task_id: string }>('/trip/plan', data, { signal: getAbortSignal() }).then((r) => r.data),
    onSuccess: (data) => {
      if (!mountedRef.current) return
      setTaskId(data.task_id)
      onNavigate()
      navigate(`/planning/${data.task_id}`)
    },
  })

  const chatSendMut = useMutation({
    mutationFn: (data: import('@/types/api').ChatRequest) =>
      tripApi.chat.send(data, getAbortSignal()),
  })

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  useEffect(() => {
    if (!mountedRef.current) return
    setMessages([initialMsg])
    setCollectedInfo({})
    sessionIdRef.current = crypto.randomUUID()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripId, isGeneralChat])

  // Close session on unmount to trigger preference extraction.
  // Only close if messages were actually exchanged (avoids 404 in strict mode
  // double-mount where cleanup runs before any message is sent).
  useEffect(() => {
    return () => {
      if (isGeneralChat && tripId && hasSentMessagesRef.current) {
        tripApi.chat.closeSession(sessionIdRef.current).catch(() => {})
      }
    }
  }, [isGeneralChat, tripId])

  const handleSend = useCallback(
    async (text?: string) => {
      const userMsg = (text || inputValue).trim()
      if (!userMsg || isThinking) return

      const urlRegex = /https?:\/\/[^\s]+/
      const hasUrl = urlRegex.test(userMsg)

      setInputValue('')
      const updated = [...messages, { role: 'user' as const, content: userMsg }]
      safeSetMessages(updated)
      safeSetThinking(true)

      try {
        if (hasUrl) {
          safeSetMessages((prev) => [
            ...prev,
            { role: 'companion', content: '检测到链接！你可以在"学习"Tab中查看和管理学习内容。我已经自动提取了关键信息~' },
          ])
          safeSetThinking(false)
          return
        }

        if (isGeneralChat && tripId) {
          hasSentMessagesRef.current = true
          const result = await chatSendMut.mutateAsync({
            trip_id: tripId,
            session_id: sessionIdRef.current,
            message: userMsg,
          })
          safeSetMessages((prev) => [...prev, { role: 'companion', content: result.reply }])
          safeSetThinking(false)
          return
        }

        const result = await clarifyMut.mutateAsync({
          destination: collectedInfo.destination || userMsg,
          messages: updated
            .filter((m) => m.role === 'user' || m.role === 'companion')
            .map((m) => ({ role: m.role === 'user' ? 'user' : 'ai', content: m.content })),
        })

        if (result.done) {
          safeSetMessages((prev) => [
            ...prev,
            { role: 'companion', content: '好的，我已经了解你的需求！正在为你生成专属旅行方案...' },
          ])
          await new Promise((r) => setTimeout(r, 600))
          const today = new Date().toISOString().slice(0, 10)
          const defaultEnd = new Date(Date.now() + 3 * 86400000).toISOString().slice(0, 10)
          createMut.mutate({
            start_location: result.start_location || collectedInfo.start_location || '北京',
            destination: result.destination || collectedInfo.destination || userMsg,
            start_date: result.start_date || today,
            end_date: result.end_date || defaultEnd,
            budget_min: result.budget_min ?? 0,
            budget_max: result.budget_max ?? 50000,
            currency: result.currency ?? 'CNY',
            preferences: result.preferences ?? [],
            travel_style: (result.travel_style ?? 'balanced') as TravelStyle,
          })
          safeSetThinking(false)
          return
        }

        const newInfo = { ...collectedInfo }
        if (result.destination) newInfo.destination = result.destination
        setCollectedInfo(newInfo)
        safeSetMessages((prev) => [...prev, { role: 'companion', content: result.message, options: [] }])
      } catch (err: unknown) {
        if (mountedRef.current === false) return
        const axiosErr = err as { code?: string; response?: { status?: number } }
        if (axiosErr.code === 'ERR_CANCELED') return
        const status = axiosErr.response?.status
        if (status === 404 && isGeneralChat) {
          useTripStore.getState().reset()
          safeSetMessages((prev) => [
            ...prev,
            { role: 'companion', content: '之前的行程记录似乎过期了，需要重新规划一次旅行哦~' },
          ])
        } else {
          safeSetMessages((prev) => [...prev, { role: 'companion', content: '哎呀，我好像走神了...能再说一遍吗？' }])
        }
      } finally {
        safeSetThinking(false)
      }
    },
    [inputValue, isThinking, collectedInfo, messages, clarifyMut, createMut, chatSendMut, navigate, setTaskId, isGeneralChat, tripId],
  )

  const handleOptionClick = useCallback(
    (option: string) => {
      const allOptions = isGeneralChat ? TRAVEL_QA_OPTIONS : QUICK_OPTIONS
      const matched = allOptions.find((o) => o.label === option)
      handleSend(matched?.reply || option)
    },
    [handleSend, isGeneralChat],
  )

  const isLoading = clarifyMut.isPending || createMut.isPending || chatSendMut.isPending || isThinking

  return (
    <div className="flex flex-col h-full">
      {/* Header with history button — always visible */}
      <div className="flex items-center justify-end px-3 py-1">
        <Button
          variant="ghost"
          size="sm"
          className="text-xs text-slate-400 hover:text-pink-500 h-7"
          onClick={() => setShowHistory((v) => !v)}
        >
          <History className="h-3.5 w-3.5 mr-1" />
          历史
        </Button>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Main chat area */}
        <div className={`flex flex-col flex-1 min-w-0 ${showHistory ? 'hidden sm:flex' : ''}`}>
          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`${
                    msg.role === 'user'
                      ? 'max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed bg-gradient-to-r from-pink-400 to-rose-400 text-white rounded-br-md'
                      : msg.tripPlan
                        ? 'max-w-[95%]'
                        : 'max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed bg-slate-100 text-slate-700 rounded-bl-md'
                  }`}
                >
                  {msg.tripPlan ? (
                    <TripPlanCard trip={msg.tripPlan} />
                  ) : (
                    <>{msg.content}</>
                  )}
                  {msg.options && msg.options.length > 0 && (
                    <div className="mt-2 space-y-1.5">
                      {msg.options.map((opt) => (
                        <button
                          key={opt}
                          className="block w-full text-left text-xs bg-white/60 hover:bg-white rounded-lg px-2.5 py-1.5 transition-colors text-pink-700"
                          onClick={() => handleOptionClick(opt)}
                          disabled={isLoading}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="border-t px-3 py-3 bg-white flex-shrink-0">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="输入消息...也可以粘贴链接让我学习"
                disabled={isLoading}
                className="flex-1 text-sm"
              />
              <Button
                size="icon"
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || isLoading}
                className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* History sidebar */}
        {showHistory && (
          <ChatHistorySidebar
            tripId={tripId}
            onClose={() => setShowHistory(false)}
            onRestore={(sessionId, msgs) => {
              sessionIdRef.current = sessionId
              setMessages(msgs.map((m) => ({
                role: (m.role === 'user' ? 'user' : 'companion') as 'user' | 'companion',
                content: m.content,
              })))
              setShowHistory(false)
            }}
          />
        )}
      </div>
    </div>
  )
}

// ─── History Sidebar ──────────────────────────────────────────────
function ChatHistorySidebar({ tripId, onClose, onRestore }: {
  tripId: string | null
  onClose: () => void
  onRestore: (sessionId: string, messages: { role: string; content: string }[]) => void
}) {
  const [groups, setGroups] = useState<TripSessionGroup[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    tripApi.chat.getHistory()
      .then((res) => setGroups(res.groups))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleRestore = async (originalSessionId: string) => {
    try {
      const result = await tripApi.chat.restoreSession({
        trip_id: tripId || '',
        original_session_id: originalSessionId,
      })
      onRestore(result.new_session_id, result.messages)
    } catch {
      toast.error('恢复会话失败')
    }
  }

  const handleDelete = async (sessionId: string) => {
    try {
      await tripApi.chat.deleteSession(sessionId)
      setGroups((prev) =>
        prev.map((g) => ({
          ...g,
          sessions: g.sessions.filter((s) => s.session_id !== sessionId),
        })).filter((g) => g.sessions.length > 0),
      )
    } catch {
      toast.error('删除失败')
    }
  }

  return (
    <div className="w-[280px] sm:w-[300px] border-l bg-slate-50 flex flex-col flex-shrink-0">
      <div className="flex items-center justify-between px-3 py-2.5 border-b bg-white">
        <span className="text-xs font-semibold text-slate-600">历史会话</span>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-slate-300" />
          </div>
        ) : groups.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-6">暂无历史会话</p>
        ) : (
          <div className="p-2 space-y-3">
            {groups.map((group) => (
              <div key={group.trip_id}>
                <p className="text-[10px] font-medium text-slate-500 px-1 mb-1">{group.trip_name}</p>
                {group.sessions.map((s) => (
                  <div key={s.session_id} className="bg-white rounded-lg p-2 mb-1.5 border border-slate-100">
                    <p className="text-xs text-slate-700 line-clamp-1 mb-1">{s.first_message}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-slate-400">
                        {s.message_count}条 · {new Date(s.last_active_at).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
                      </span>
                      <div className="flex gap-1">
                        <button
                          className="text-[9px] text-pink-500 hover:text-pink-600"
                          onClick={() => handleRestore(s.session_id)}
                        >
                          继续
                        </button>
                        <button
                          className="text-[9px] text-slate-400 hover:text-red-500"
                          onClick={() => handleDelete(s.session_id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Tab: 行程助手 ───────────────────────────────────────────────
function ItineraryTab({ onNavigate }: { onNavigate: () => void }) {
  const trip = useTripStore((s) => s.currentTrip)
  const setTripActive = useTripStore((s) => s.setTripActive)
  const navigate = useNavigate()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [isStartingTrip, setIsStartingTrip] = useState(false)
  const [dismissed, setDismissed] = useState<string[]>([])

  const timeTip = getTimeBasedTip()
  const TimeIcon = timeTip.Icon

  const { data: weatherData } = useQuery({
    queryKey: queryKeys.tripWeather(trip?.id ?? ''),
    queryFn: () => tripApi.getWeather(trip!.id),
    enabled: !!trip?.id,
    staleTime: 30 * 60 * 1000,
  })

  const todayWeather = weatherData?.weather?.forecast?.[0]
  const todayOutfit = weatherData?.outfits?.[0]

  if (!trip) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center px-4">
        <Calendar className="h-10 w-10 text-slate-300 mb-3" />
        <p className="text-sm text-slate-500 mb-4">还没有生成旅行方案</p>
        <Button size="sm" onClick={() => { onNavigate(); navigate('/plan') }}>去规划</Button>
      </div>
    )
  }

  const totalActivities = trip.days?.reduce((sum, d) => sum + (d.activities?.length || 0), 0) || 0

  return (
    <div className="overflow-y-auto h-full px-3 py-3 space-y-4">
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-pink-50 rounded-xl p-2.5 text-center">
          <Calendar className="h-4 w-4 text-pink-400 mx-auto mb-1" />
          <p className="text-base font-bold text-pink-700">{trip.days?.length || 0}</p>
          <p className="text-[10px] text-pink-500">天行程</p>
        </div>
        <div className="bg-amber-50 rounded-xl p-2.5 text-center">
          <MapPin className="h-4 w-4 text-amber-400 mx-auto mb-1" />
          <p className="text-base font-bold text-amber-700">{totalActivities}</p>
          <p className="text-[10px] text-amber-500">个活动</p>
        </div>
        <div className="bg-emerald-50 rounded-xl p-2.5 text-center">
          <DollarSign className="h-4 w-4 text-emerald-400 mx-auto mb-1" />
          <p className="text-sm font-bold text-emerald-700">3K-8K</p>
          <p className="text-[10px] text-emerald-500">预估预算</p>
        </div>
      </div>

      {trip.preferences && trip.preferences.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {trip.preferences.map((p) => (
            <Badge key={p} variant="secondary" className="text-[10px]">{p}</Badge>
          ))}
        </div>
      )}

      <Separator />

      <div>
        <p className="text-xs font-semibold text-slate-600 mb-2">每日行程概览</p>
        <div className="space-y-2">
          {(trip.days || []).slice(0, 5).map((day) => (
            <div key={day.day_index} className="flex gap-2.5">
              <div className="flex-shrink-0 w-7 h-7 rounded-full bg-pink-100 flex items-center justify-center">
                <span className="text-[10px] font-bold text-pink-600">{day.day_index}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-700 truncate">
                  {(day.activities || []).slice(0, 2).map((a) => a.name).join(' → ')}
                </p>
                <p className="text-[10px] text-slate-400 mt-0.5">{(day.activities || []).length} 个活动</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {todayWeather && (
        <div className="bg-sky-50 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-1.5">
            <Cloud className="h-3.5 w-3.5 text-sky-500" />
            <span className="text-xs font-semibold text-sky-700">今日天气</span>
          </div>
          <p className="text-xs text-sky-800">
            {todayWeather.text_day} · {todayWeather.temp_min}°~{todayWeather.temp_max}° · 湿度{todayWeather.humidity}%
          </p>
          {todayOutfit && (
            <p className="text-[10px] text-sky-600 mt-1">穿搭: {todayOutfit.suggestion}</p>
          )}
        </div>
      )}

      <div>
        <div className="flex items-center gap-2 mb-2">
          <TimeIcon className="h-3.5 w-3.5 text-amber-500" />
          <span className="text-xs font-semibold text-slate-600">贴心提醒</span>
        </div>
        <div className="space-y-1.5">
          {timeTip.tips
            .filter((t) => !dismissed.includes(t))
            .map((tip) => (
              <div key={tip} className="flex items-start gap-2 bg-slate-50 rounded-lg p-2.5">
                <AlertCircle className="h-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-slate-600 flex-1">{tip}</p>
                <button
                  className="text-[10px] text-slate-300 hover:text-slate-500 flex-shrink-0"
                  onClick={() => setDismissed((prev) => [...prev, tip])}
                >
                  已读
                </button>
              </div>
            ))}
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-2">
          <Phone className="h-3.5 w-3.5 text-red-400" />
          <span className="text-xs font-semibold text-slate-600">紧急电话</span>
        </div>
        <div className="grid grid-cols-4 gap-1.5">
          {GENERAL_TIPS.emergency.map((item) => (
            <div key={item.label} className="bg-red-50 rounded-lg p-2 text-center">
              <item.icon className="h-3 w-3 text-red-400 mx-auto mb-0.5" />
              <p className="text-xs font-bold text-red-600">{item.value}</p>
              <p className="text-[10px] text-red-400">{item.label}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <Navigation className="h-3.5 w-3.5 text-indigo-400" />
          <span className="text-xs font-semibold text-slate-600">出行提示</span>
        </div>
        {GENERAL_TIPS.transport.map((tip) => (
          <p key={tip} className="text-xs text-slate-500 flex items-start gap-1.5">
            <span className="text-indigo-300">•</span> {tip}
          </p>
        ))}
      </div>

      <div className="bg-slate-50 rounded-xl p-3 flex items-center gap-2">
        <Wifi className="h-3.5 w-3.5 text-slate-400" />
        <p className="text-[10px] text-slate-500">
          <span className="font-medium text-slate-600">免费WiFi: </span>
          大部分景区游客中心、星巴克、大型商场提供免费WiFi
        </p>
      </div>

      <div className="space-y-2">
        <Button
          className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white h-9 text-sm"
          onClick={() => setConfirmOpen(true)}
          disabled={isStartingTrip}
        >
          {isStartingTrip ? <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> : <Play className="h-3.5 w-3.5 mr-1.5" />}
          开始这趟旅行
        </Button>
        <Button
          variant="outline" size="sm" className="w-full"
          onClick={() => { onNavigate(); navigate(`/trip/${trip.id}`) }}
        >
          查看完整行程
        </Button>
      </div>

      {confirmOpen && (
        <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
          <DialogContent className="sm:max-w-sm">
            <DialogTitle>确认开启旅途</DialogTitle>
            <p className="text-sm text-muted-foreground">
              确定要开始 "{trip.destination}" 的旅行吗？开启后小旅将为你提供实时贴心提示。
            </p>
            <div className="flex gap-3 mt-4">
              <Button variant="outline" className="flex-1" onClick={() => setConfirmOpen(false)}>再想想</Button>
              <Button
                className="flex-1 bg-gradient-to-r from-emerald-500 to-teal-500"
                disabled={isStartingTrip}
                onClick={async () => {
                  setIsStartingTrip(true)
                  setTripActive()
                  setConfirmOpen(false)
                  // Yield to let React process state before closing the dialog
                  await new Promise((r) => setTimeout(r, 100))
                  setIsStartingTrip(false)
                  onNavigate()
                }}
              >
                {isStartingTrip ? <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> : null}
                确认出发！
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}

// ─── Tab: 学习功能 ───────────────────────────────────────────────
const LEARN_STEPS = [
  { key: 'scraping', label: '正在抓取内容...', icon: Loader2 },
  { key: 'digesting', label: 'AI 深度分析中...', icon: Brain },
  { key: 'done', label: '学习完成!', icon: CheckCircle2 },
]

function LearnTab() {
  const [recentItems, setRecentItems] = useState<LearnHistoryItem[]>([])
  const [urlInput, setUrlInput] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [analyzeStep, setAnalyzeStep] = useState(0)
  const [learnedResult, setLearnedResult] = useState<LearnAnalyzeResult | null>(null)
  const [showResult, setShowResult] = useState(false)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const navigate = useNavigate()
  const stepTimers = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    if (isAuthenticated) {
      tripApi.learn.listRecent().then((res) => setRecentItems(res.items)).catch(() => {})
    }
  }, [isAuthenticated])

  useEffect(() => {
    return () => stepTimers.current.forEach(clearTimeout)
  }, [])

  const handleAnalyze = useCallback(async () => {
    const url = urlInput.trim()
    if (!url || analyzing) return

    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    setAnalyzing(true)
    setUrlInput('')
    setShowResult(false)
    setLearnedResult(null)
    setAnalyzeStep(0)

    const t1 = setTimeout(() => setAnalyzeStep(1), 1500)
    stepTimers.current = [t1]

    try {
      const result = await tripApi.learn.analyze(url)
      setAnalyzeStep(2)
      setLearnedResult(result)
      setShowResult(true)
      setRecentItems((prev) => [result.history, ...prev].slice(0, 10))

      // Auto-dismiss result after 8 seconds
      const t2 = setTimeout(() => setShowResult(false), 8000)
      stepTimers.current.push(t2)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      if (detail) toast.error(detail)
      else toast.error('分析失败，请稍后重试')
    } finally {
      stepTimers.current.forEach(clearTimeout)
      stepTimers.current = []
      setAnalyzing(false)
    }
  }, [urlInput, analyzing, isAuthenticated, navigate])

  const handleDeleteRecent = useCallback(async (id: string) => {
    try {
      await tripApi.learn.deleteHistory(id)
      setRecentItems((prev) => prev.filter((item) => item.id !== id))
    } catch {
      toast.error('删除失败')
    }
  }, [])

  const currentStep = LEARN_STEPS[analyzeStep]

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <BookOpen className="h-10 w-10 text-slate-300 mb-3" />
        <p className="text-sm text-slate-500 mb-3">登录后使用学习功能</p>
        <Button size="sm" onClick={() => navigate('/login')} className="bg-gradient-to-r from-pink-400 to-rose-400">
          去登录
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Input bar */}
      <div className="px-3 py-3 border-b">
        <div className="flex gap-2">
          <Input
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            placeholder="粘贴旅行攻略链接，我来学习..."
            disabled={analyzing}
            className="flex-1 text-sm"
          />
          <Button size="icon" onClick={handleAnalyze} disabled={!urlInput.trim() || analyzing}
            className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500">
            <BookOpen className="h-4 w-4" />
          </Button>
        </div>

        {/* Learning progress */}
        {analyzing && (
          <div className="mt-2.5 bg-pink-50 rounded-xl p-3 flex items-center gap-3">
            <div className="flex-shrink-0">
              {currentStep && <currentStep.icon className={`h-5 w-5 text-pink-500 ${analyzeStep < 2 ? 'animate-spin' : ''}`} />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-pink-700">{currentStep?.label || '处理中...'}</p>
              <div className="mt-1.5 flex gap-1">
                {LEARN_STEPS.map((step, i) => (
                  <div
                    key={step.key}
                    className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                      i < analyzeStep ? 'bg-pink-300' : i === analyzeStep ? 'bg-pink-400 animate-pulse' : 'bg-pink-100'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {!analyzing && !showResult && (
          <p className="text-[10px] text-slate-400 mt-1.5">
            支持：小红书、抖音、B站、微博、马蜂窝、穷游、携程、美团、大众点评
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3">
        {/* Learned result card */}
        {showResult && learnedResult && (
          <div className="mb-3 bg-gradient-to-br from-pink-50 to-rose-50 rounded-xl p-3 border border-pink-100 animate-in slide-in-from-top-2 duration-300">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-xs font-semibold text-green-700">知识已吸收!</span>
              <span className="text-[9px] text-slate-400 ml-auto">
                {learnedResult.knowledge_points.length} 个知识点
              </span>
            </div>
            <h4 className="text-sm font-semibold text-slate-800 mb-1">{learnedResult.history.title}</h4>
            <p className="text-xs text-slate-600 mb-2">{learnedResult.summary}</p>
            {learnedResult.knowledge_points.length > 0 && (
              <div className="space-y-1 mb-2">
                {learnedResult.knowledge_points.slice(0, 4).map((kp, i) => (
                  <div key={i} className="flex items-start gap-1.5">
                    <Badge variant="outline" className="text-[9px] px-1 py-0 border-pink-200 text-pink-600 flex-shrink-0">
                      {kp.category}
                    </Badge>
                    <span className="text-[10px] text-slate-600">{kp.point}</span>
                  </div>
                ))}
              </div>
            )}
            {learnedResult.practical_info?.tips && (
              <div className="flex items-start gap-1.5 bg-amber-50 rounded-lg p-2 mb-2">
                <Lightbulb className="h-3 w-3 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-[10px] text-amber-700">{learnedResult.practical_info.tips}</p>
              </div>
            )}
            <div className="flex flex-wrap gap-1">
              {learnedResult.history.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-[10px] px-1.5 py-0">{tag}</Badge>
              ))}
            </div>
            <p className="text-[9px] text-slate-400 mt-2 text-center">此卡片将在几秒后自动收起，知识已永久保存在学习历史中</p>
          </div>
        )}

        {/* Recent learning section */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <History className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-xs font-semibold text-slate-600">近期学习</span>
          </div>
          <button
            onClick={() => { navigate('/knowledge') }}
            className="text-[10px] text-pink-500 hover:text-pink-600 flex items-center gap-0.5"
          >
            全部历史 <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        {recentItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <BookOpen className="h-8 w-8 text-slate-200 mb-2" />
            <p className="text-xs text-slate-400">粘贴链接，让小旅帮你学习旅行攻略</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentItems.map((item) => {
              const platform = detectPlatform(item.url)
              return (
                <div key={item.id} className="bg-slate-50 rounded-xl p-2.5 relative group hover:bg-slate-100 transition-colors">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className="text-[9px] font-bold px-1.5 py-0.5 rounded-full text-white flex-shrink-0"
                      style={{ backgroundColor: platform.color }}
                    >
                      {item.platform || platform.name}
                    </span>
                    <span className="text-[9px] text-slate-400 flex-1 truncate">{item.title}</span>
                    {item.quality_score > 0 && (
                      <span className="text-[9px] text-amber-600 bg-amber-50 px-1.5 py-0 rounded font-medium flex-shrink-0">
                        {(item.quality_score * 100).toFixed(0)}%
                      </span>
                    )}
                    <span className="text-[9px] text-slate-300 flex-shrink-0">
                      {new Date(item.learned_at).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
                    </span>
                    <button
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-red-500 flex-shrink-0"
                      onClick={() => handleDeleteRecent(item.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                  {item.knowledge_points.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {item.knowledge_points.slice(0, 2).map((kp, i) => (
                        <span key={i} className="text-[9px] text-slate-500 bg-white rounded px-1.5 py-0.5">
                          {kp.point.length > 25 ? kp.point.slice(0, 25) + '...' : kp.point}
                        </span>
                      ))}
                      {item.knowledge_points.length > 2 && (
                        <span className="text-[9px] text-slate-400">+{item.knowledge_points.length - 2}</span>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Tab: 实时定位 ───────────────────────────────────────────────
function LocationTab() {
  const trip = useTripStore((s) => s.currentTrip)

  if (!trip) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center px-4">
        <MapPin className="h-10 w-10 text-slate-300 mb-3" />
        <p className="text-sm text-slate-500 mb-1">暂未开启旅行</p>
        <p className="text-xs text-slate-400">生成并开启旅行后，这里将显示实时定位和导航</p>
      </div>
    )
  }

  const allActivities = (trip.days || []).flatMap((d) =>
    (d.activities || []).map((a) => ({ ...a, dayIndex: d.day_index })),
  )

  return (
    <div className="overflow-y-auto h-full px-3 py-3 space-y-3">
      <div className="bg-pink-50 rounded-xl p-3">
        <div className="flex items-center gap-2 mb-1.5">
          <MapPin className="h-4 w-4 text-pink-500" />
          <span className="text-sm font-semibold text-pink-700">当前位置</span>
        </div>
        <p className="text-xs text-pink-600">{trip.destination}</p>
      </div>

      <div>
        <p className="text-xs font-semibold text-slate-600 mb-2">行程路线</p>
        <div className="space-y-2">
          {allActivities.slice(0, 8).map((activity, i) => (
            <div key={activity.id || i} className="flex items-center gap-2.5">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-100 flex items-center justify-center">
                <span className="text-[10px] font-bold text-pink-600">{i + 1}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-700 truncate">{activity.name}</p>
                {activity.start_time && (
                  <p className="text-[10px] text-slate-400">{activity.start_time} - {activity.end_time}</p>
                )}
              </div>
              {activity.location?.lat && (
                <MapPin className="h-3 w-3 text-emerald-400 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="text-center">
        <p className="text-xs text-slate-400">完整地图请在行程页查看</p>
      </div>
    </div>
  )
}

// ─── TripPlanCard ──────────────────────────────────────────────
function TripPlanCard({ trip }: { trip: Trip }) {
  const navigate = useNavigate()

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      {/* Header */}
      <div className="bg-gradient-to-r from-pink-400 to-rose-400 px-4 py-3">
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-white" />
          <span className="text-sm font-bold text-white">{trip.destination}</span>
          <span className="text-[10px] text-white/80 ml-auto">
            {trip.days?.length || 0}天行程
          </span>
        </div>
        <p className="text-[10px] text-white/70 mt-1">
          {trip.dates?.start} ~ {trip.dates?.end}
          {trip.travel_style && ` · ${trip.travel_style === 'relaxed' ? '悠闲' : trip.travel_style === 'compact' ? '紧凑' : '适中'}`}
        </p>
        {(trip.preferences?.length ?? 0) > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {trip.preferences.map((p) => (
              <span key={p} className="text-[9px] bg-white/20 text-white rounded-full px-2 py-0.5">{p}</span>
            ))}
          </div>
        )}
      </div>

      {/* Daily overview */}
      <div className="px-4 py-3 space-y-3 max-h-[360px] overflow-y-auto">
        {(trip.days || []).map((day) => (
          <div key={day.day_index}>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="w-5 h-5 rounded-full bg-pink-100 text-[10px] font-bold text-pink-600 flex items-center justify-center flex-shrink-0">
                {day.day_index}
              </span>
              <span className="text-xs font-semibold text-slate-700">
                第{day.day_index}天
              </span>
              <span className="text-[9px] text-slate-400">{day.date}</span>
            </div>
            <div className="ml-7 space-y-1.5">
              {(day.activities || []).map((act, i) => (
                <div key={act.id || i} className="flex items-start gap-2 text-xs">
                  <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-rose-300 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium text-slate-700">{act.name}</span>
                    <span className="text-[9px] text-slate-400 ml-1.5">
                      {act.start_time}-{act.end_time}
                    </span>
                    {act.tips && (
                      <p className="text-[10px] text-amber-600 mt-0.5">{act.tips}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Summary */}
        {trip.summary && (
          <div className="pt-2 border-t border-slate-100 flex gap-3 text-[10px] text-slate-500">
            {trip.summary.total_cost > 0 && (
              <span>预估 ¥{trip.summary.total_cost.toLocaleString()}</span>
            )}
            {trip.summary.attraction_count > 0 && (
              <span>{trip.summary.attraction_count} 个景点</span>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="border-t px-4 py-2 flex gap-2">
        <Button
          size="sm"
          variant="outline"
          className="flex-1 text-xs h-7"
          onClick={() => navigate(`/trip/${trip.id}`)}
        >
          查看完整行程
        </Button>
        <Button
          size="sm"
          className="flex-1 text-xs h-7 bg-gradient-to-r from-emerald-500 to-teal-500"
          onClick={() => {
            useTripStore.getState().setTripActive()
          }}
        >
          开始旅行
        </Button>
      </div>
    </div>
  )
}

// ─── Tab: 规划进度 ───────────────────────────────────────────────
function PlanningTab() {
  const planning = useTripStore((s) => s.planning)
  const agents: AgentInfo[] = planning.agents.length > 0
    ? planning.agents
    : [
        { name: 'coordinator', status: 'idle' },
        { name: 'transport', status: 'idle' },
        { name: 'accommodation', status: 'idle' },
        { name: 'attraction', status: 'idle' },
        { name: 'dining', status: 'idle' },
        { name: 'strategy', status: 'idle' },
      ]

  return (
    <div className="overflow-y-auto h-full px-3 py-3 space-y-4">
      <div className="text-center">
        <p className="text-sm font-semibold text-slate-700">AI 正在为你规划行程</p>
        <p className="text-xs text-slate-400 mt-0.5">
          {planning.status === 'completed'
            ? '规划完成！'
            : planning.status === 'failed'
            ? '规划失败'
            : '各 Agent 正在并行工作中...'}
        </p>
      </div>

      <ProgressIndicator progress={planning.progress} />

      <div className="grid grid-cols-2 gap-2">
        {agents.map((agent) => (
          <AgentStatusCard key={agent.name} agent={agent} />
        ))}
      </div>

      {planning.errorMessage && (
        <div className="bg-red-50 rounded-xl p-3 text-xs text-red-600">
          {planning.errorMessage}
        </div>
      )}
    </div>
  )
}

// ─── Main Dialog ────────────────────────────────────────────────
export function CompanionDialog({ open, onClose }: CompanionDialogProps) {
  const trip = useTripStore((s) => s.currentTrip)
  const tripActive = useTripStore((s) => s.tripActive)
  const planning = useTripStore((s) => s.planning)
  const phase = getPhase(trip, tripActive, planning.taskId)
  const tripId = trip?.id ?? null
  const isGeneralChat = phase !== 'no_plan'
  const destination = trip?.destination || '未知目的地'

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-[440px] h-[620px] flex flex-col p-0 gap-0 [&>button]:hidden rounded-2xl overflow-hidden">
        <DialogTitle className="sr-only">旅行小助手</DialogTitle>

        <div className="flex items-center justify-between px-4 py-3 border-b bg-gradient-to-r from-pink-50 to-rose-50 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">旅行小助手 · 你的旅行伙伴</p>
              <p className="text-[10px] text-slate-500">
                在线{tripActive ? ` · 正在游览${destination}` : ''}
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <Tabs defaultValue={phase === 'planning' ? 'planning' : 'chat'} className="flex flex-col flex-1 min-h-0">
          <TabsList className={`grid mx-3 mt-3 flex-shrink-0 bg-pink-50 p-1 rounded-xl ${phase === 'planning' ? 'grid-cols-3' : 'grid-cols-4'}`}>
            <TabsTrigger value="chat" className="text-xs data-[state=active]:bg-white data-[state=active]:text-pink-600 rounded-lg gap-1">
              <MessageCircle className="h-3.5 w-3.5" /> 对话
            </TabsTrigger>
            {phase === 'planning' ? (
              <TabsTrigger value="planning" className="text-xs data-[state=active]:bg-white data-[state=active]:text-pink-600 rounded-lg gap-1">
                <Loader2 className="h-3.5 w-3.5" /> 规划
              </TabsTrigger>
            ) : (
              <>
                <TabsTrigger value="location" className="text-xs data-[state=active]:bg-white data-[state=active]:text-pink-600 rounded-lg gap-1">
                  <Navigation className="h-3.5 w-3.5" /> 定位
                </TabsTrigger>
                <TabsTrigger value="itinerary" className="text-xs data-[state=active]:bg-white data-[state=active]:text-pink-600 rounded-lg gap-1">
                  <Calendar className="h-3.5 w-3.5" /> 行程
                </TabsTrigger>
              </>
            )}
            <TabsTrigger value="learn" className="text-xs data-[state=active]:bg-white data-[state=active]:text-pink-600 rounded-lg gap-1">
              <BookOpen className="h-3.5 w-3.5" /> 学习
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chat" className="flex-1 min-h-0 mt-0 data-[state=inactive]:hidden">
            <ChatTab tripId={tripId} isGeneralChat={isGeneralChat} onNavigate={onClose} />
          </TabsContent>

          <TabsContent value="planning" className="flex-1 min-h-0 mt-0 data-[state=inactive]:hidden">
            <PlanningTab />
          </TabsContent>

          <TabsContent value="location" className="flex-1 min-h-0 mt-0 overflow-y-auto data-[state=inactive]:hidden">
            <LocationTab />
          </TabsContent>

          <TabsContent value="itinerary" className="flex-1 min-h-0 mt-0 overflow-y-auto data-[state=inactive]:hidden">
            <ItineraryTab onNavigate={onClose} />
          </TabsContent>

          <TabsContent value="learn" className="flex-1 min-h-0 mt-0 data-[state=inactive]:hidden">
            <LearnTab />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
