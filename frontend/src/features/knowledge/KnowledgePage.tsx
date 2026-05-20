import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { tripApi } from '@/shared/api/tripApi'
import { useAuthStore } from '@/shared/stores/useAuthStore'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, Trash2, ExternalLink, MapPin, Sparkles, ArrowLeft, History } from 'lucide-react'
import type { LearnHistoryItem } from '@/types/api'

const PLATFORM_COLORS: Record<string, string> = {
  xiaohongshu: '#FF2442',
  douyin: '#000000',
  bilibili: '#00A1D6',
  weibo: '#E6162D',
  mafengwo: '#FFD700',
  qyer: '#00BFFF',
  ctrip: '#2577E3',
  meituan: '#FFD100',
  dianping: '#FF6633',
  generic: '#6366F1',
}

function platformLabel(platform: string): string {
  const map: Record<string, string> = {
    xiaohongshu: '小红书',
    douyin: '抖音',
    bilibili: 'B站',
    weibo: '微博',
    mafengwo: '马蜂窝',
    qyer: '穷游',
    ctrip: '携程',
    meituan: '美团',
    dianping: '大众点评',
    generic: '网页',
  }
  return map[platform] || platform
}

export default function KnowledgePage() {
  const [items, setItems] = useState<LearnHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterLocation, setFilterLocation] = useState('')
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  useEffect(() => {
    if (isAuthenticated) {
      tripApi.learn.listHistory().then((res) => {
        setItems(res.items)
        setLoading(false)
      }).catch(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [isAuthenticated])

  const handleDelete = async (id: string) => {
    try {
      await tripApi.learn.deleteHistory(id)
      setItems((prev) => prev.filter((item) => item.id !== id))
    } catch {
      toast.error('删除失败')
    }
  }

  const filtered = useMemo(() => {
    return items.filter((item) => {
      if (search) {
        const q = search.toLowerCase()
        const matchTitle = item.title.toLowerCase().includes(q)
        const matchTags = item.tags.some((t) => t.toLowerCase().includes(q))
        const matchSummary = item.summary.toLowerCase().includes(q)
        if (!matchTitle && !matchTags && !matchSummary) return false
      }
      if (filterLocation) {
        if (!item.location || !item.location.toLowerCase().includes(filterLocation.toLowerCase())) {
          return false
        }
      }
      return true
    })
  }, [items, search, filterLocation])

  const stats = useMemo(() => {
    const total = items.length
    const thisMonth = items.filter((i) => {
      const d = new Date(i.learned_at)
      const now = new Date()
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    }).length
    const thisWeek = items.filter((i) => {
      const d = new Date(i.learned_at)
      const now = new Date()
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      return d >= weekAgo
    }).length
    const highQuality = items.filter((i) => i.quality_score >= 0.6).length
    return { total, thisMonth, thisWeek, highQuality }
  }, [items])

  const locations = useMemo(() => {
    const locs = new Set<string>()
    items.forEach((item) => {
      if (item.location) locs.add(item.location)
    })
    return Array.from(locs).sort()
  }, [items])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-pink-400 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-pink-50 to-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center gap-3 mb-6">
          <Link to="/" className="text-slate-400 hover:text-slate-600">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center">
            <History className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">学习历史</h1>
            <p className="text-xs text-slate-500">已消化的旅行知识记录</p>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-xl p-3 shadow-sm border text-center">
            <div className="text-2xl font-bold text-pink-500">{stats.total}</div>
            <div className="text-[10px] text-slate-400">总学习数</div>
          </div>
          <div className="bg-white rounded-xl p-3 shadow-sm border text-center">
            <div className="text-2xl font-bold text-green-500">{stats.thisMonth}</div>
            <div className="text-[10px] text-slate-400">本月学习</div>
          </div>
          <div className="bg-white rounded-xl p-3 shadow-sm border text-center">
            <div className="text-2xl font-bold text-blue-500">{stats.thisWeek}</div>
            <div className="text-[10px] text-slate-400">近7天</div>
          </div>
          <div className="bg-white rounded-xl p-3 shadow-sm border text-center">
            <div className="text-2xl font-bold text-amber-500">{stats.highQuality}</div>
            <div className="text-[10px] text-slate-400">高质量</div>
          </div>
        </div>

        <div className="flex gap-3 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索标题、标签、内容..."
              className="pl-9 text-sm"
            />
          </div>
          <select
            value={filterLocation}
            onChange={(e) => setFilterLocation(e.target.value)}
            className="text-sm border rounded-lg px-3 py-2 bg-white text-slate-600"
          >
            <option value="">全部地点</option>
            {locations.map((loc) => (
              <option key={loc} value={loc}>{loc}</option>
            ))}
          </select>
        </div>

        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <Sparkles className="h-12 w-12 text-slate-300 mb-4" />
            <p className="text-slate-500 mb-1">
              {items.length === 0 ? '还没有学习内容' : '没有匹配的内容'}
            </p>
            <p className="text-sm text-slate-400">
              {items.length === 0 ? '去旅伴小人的学习 Tab 添加链接开始学习' : '尝试修改搜索条件'}
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {filtered.map((item) => (
              <div key={item.id} className="bg-white rounded-xl p-4 shadow-sm border hover:shadow-md transition-shadow relative group">
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="text-[10px] font-bold px-2 py-0.5 rounded-full text-white"
                    style={{ backgroundColor: PLATFORM_COLORS[item.platform] || '#6366F1' }}
                  >
                    {platformLabel(item.platform)}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {new Date(item.learned_at).toLocaleDateString('zh-CN')}
                  </span>
                  {item.quality_score > 0 && (
                    <span className={`text-[9px] px-1.5 py-0 rounded font-medium ${
                      item.quality_score >= 0.6 ? 'text-green-600 bg-green-50' : 'text-amber-600 bg-amber-50'
                    }`}>
                      {(item.quality_score * 100).toFixed(0)}%
                    </span>
                  )}
                  <div className="flex-1" />
                  <button
                    className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-red-500"
                    onClick={() => handleDelete(item.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>

                {item.location && (
                  <div className="flex items-center gap-1 mb-1.5">
                    <MapPin className="h-3 w-3 text-pink-400" />
                    <span className="text-[10px] text-pink-500">{item.location}</span>
                  </div>
                )}

                <h3 className="font-semibold text-slate-800 mb-1.5">{item.title}</h3>
                <p className="text-xs text-slate-500 mb-3 line-clamp-3">{item.summary}</p>

                {item.knowledge_points.length > 0 && (
                  <div className="mb-3 space-y-1.5">
                    {item.knowledge_points.slice(0, 3).map((kp, i) => (
                      <div key={i} className="flex items-start gap-1.5">
                        <Badge variant="outline" className="text-[9px] px-1 py-0 border-pink-200 text-pink-600 flex-shrink-0">
                          {kp.category}
                        </Badge>
                        <span className="text-[10px] text-slate-600 leading-relaxed">{kp.point}</span>
                      </div>
                    ))}
                    {item.knowledge_points.length > 3 && (
                      <p className="text-[10px] text-slate-400 pl-1">
                        +{item.knowledge_points.length - 3} 条知识要点
                      </p>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <div className="flex flex-wrap gap-1 flex-1">
                    {item.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-[10px] px-1.5 py-0">{tag}</Badge>
                    ))}
                  </div>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-pink-500 hover:text-pink-600 flex items-center gap-0.5 flex-shrink-0"
                  >
                    查看原文 <ExternalLink className="h-2.5 w-2.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
