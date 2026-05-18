# 智能旅游行程规划平台 — 全栈架构设计

**版本**: v1.0 | **日期**: 2026-05-18 | **阶段**: MVP

---

## 一、整体技术栈

| 层 | 前端 | 后端 |
|----|------|------|
| 框架 | Vite 6 + React 18 (SPA) | Python FastAPI |
| UI | shadcn/ui + Tailwind CSS 4 | — |
| 路由 | React Router v7 | FastAPI Router |
| 客户端状态 | Zustand（persist） | — |
| 服务端数据 | TanStack Query v5 | — |
| HTTP | axios | — |
| Agent 编排 | — | LangChain LangGraph |
| LLM | — | DeepSeek API |
| 数据库 | — | PostgreSQL + Redis |
| 任务队列 | — | Celery + Redis |
| 类型 | TypeScript 5 | Pydantic v2 |

---

## 二、项目目录结构（monorepo）

```
智旅平台/
├── frontend/                       ← Vite + React SPA
│   ├── src/
│   │   ├── main.tsx                ← Provider 挂载（React Query / Router / Toaster）
│   │   ├── App.tsx                 ← 根组件，Suspense 包裹
│   │   ├── index.css               ← Tailwind 入口
│   │   ├── router/
│   │   │   ├── index.tsx           ← RouterProvider + 路由表
│   │   │   ├── routes.ts           ← 路由常量
│   │   │   ├── guards.tsx          ← ProtectedRoute 骨架
│   │   │   └── lazyPages.ts        ← React.lazy() 集中声明
│   │   ├── features/
│   │   │   ├── home/               ← 首页
│   │   │   │   ├── HomePage.tsx
│   │   │   │   └── components/
│   │   │   │       ├── HeroSection.tsx
│   │   │   │       ├── FeatureSection.tsx
│   │   │   │       └── HowItWorks.tsx
│   │   │   ├── plan-input/         ← 需求输入
│   │   │   │   ├── PlanInputPage.tsx
│   │   │   │   ├── components/
│   │   │   │   │   ├── DestinationInput.tsx
│   │   │   │   │   ├── DateRangePicker.tsx
│   │   │   │   │   ├── BudgetSelector.tsx
│   │   │   │   │   ├── PreferenceTags.tsx
│   │   │   │   │   └── TravelStyleSelect.tsx
│   │   │   │   └── hooks/usePlanForm.ts
│   │   │   ├── planning/           ← 规划进度
│   │   │   │   ├── PlanningPage.tsx
│   │   │   │   └── components/
│   │   │   │       ├── PlanSummary.tsx
│   │   │   │       ├── ProgressIndicator.tsx
│   │   │   │       └── AgentStatusCard.tsx
│   │   │   └── trip-result/        ← 行程结果
│   │   │       ├── TripResultPage.tsx
│   │   │       ├── components/
│   │   │       │   ├── TripHeader.tsx
│   │   │       │   ├── DayTabs.tsx
│   │   │       │   ├── DayTimeline.tsx
│   │   │       │   ├── TimelineItem.tsx
│   │   │       │   ├── ActivityCard.tsx
│   │   │       │   ├── TripActions.tsx
│   │   │       │   └── TripSidebar.tsx
│   │   │       └── types.ts
│   │   ├── shared/
│   │   │   ├── ui/                 ← shadcn/ui 组件
│   │   │   ├── api/
│   │   │   │   ├── client.ts       ← axios 实例 + 拦截器
│   │   │   │   ├── queryKeys.ts    ← queryKey 集中管理
│   │   │   │   └── tripApi.ts      ← 行程 API 函数
│   │   │   ├── stores/useTripStore.ts
│   │   │   └── components/layout/
│   │   │       ├── AppLayout.tsx
│   │   │       ├── Header.tsx
│   │   │       └── Footer.tsx
│   │   └── lib/utils.ts
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                        ← Python FastAPI
│   ├── main.py                     ← 入口，CORS，挂载路由
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   ├── app/
│   │   ├── config.py               ← 环境变量集中管理
│   │   ├── api/
│   │   │   ├── router.py           ← 主路由汇总
│   │   │   └── trip.py             ← /api/trip/* 端点
│   │   ├── agent/                  ← LangGraph Agent 引擎
│   │   │   ├── graph.py            ← StateGraph 编排
│   │   │   ├── state.py            ← AgentState TypedDict
│   │   │   ├── coordinator.py      ← 协调 Agent
│   │   │   ├── transport.py        ← 交通 Agent
│   │   │   ├── accommodation.py    ← 住宿 Agent
│   │   │   ├── attraction.py       ← 景点 Agent
│   │   │   ├── dining.py           ← 餐饮 Agent
│   │   │   ├── strategy.py         ← 策略优化 Agent
│   │   │   └── tools.py            ← 工具函数
│   │   ├── models/
│   │   │   ├── trip.py             ← Trip/Activity ORM
│   │   │   └── task.py             ← PlanningTask ORM
│   │   ├── schemas/
│   │   │   ├── trip.py             ← Pydantic 响应模型
│   │   │   └── request.py          ← 请求参数模型
│   │   ├── services/
│   │   │   ├── trip_service.py     ← 行程 CRUD
│   │   │   └── task_service.py     ← 任务管理
│   │   ├── tasks/
│   │   │   ├── celery_app.py       ← Celery 配置
│   │   │   └── planning_task.py    ← 异步 Agent 编排任务
│   │   └── core/
│   │       ├── database.py         ← PostgreSQL
│   │       ├── redis.py            ← Redis
│   │       └── llm.py              ← DeepSeek LLM 初始化
│   └── migrations/                 ← Alembic
│
├── docker-compose.yml              ← 启动全部服务
└── docs/
    └── superpowers/specs/
        └── 2026-05-18-全栈架构-design.md
```

---

## 三、前端设计

### 3.1 路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | HomePage | 产品展示 + CTA 入口 |
| `/plan` | PlanInputPage | 需求输入表单 |
| `/planning/:taskId` | PlanningPage | 等待 AI 规划 |
| `/trip/:tripId` | TripResultPage | 完整行程展示 |
| `/settings` | SettingsPage | 设置（MVP 占位） |
| `*` | → `/` | 未知路由重定向 |

- **路由守卫**: `ProtectedRoute` 骨架（MVP 直接透传）
- **懒加载**: 所有页面 `React.lazy()` + `<Suspense>`

### 3.2 组件树

```
HomePage              ← /          HeroSection / FeatureSection / HowItWorks
PlanInputPage         ← /plan      DestinationInput / DateRangePicker / BudgetSelector / PreferenceTags / SubmitButton
PlanningPage          ← /planning  PlanSummary / ProgressIndicator / AgentStatusCard ×5 / CancelButton
TripResultPage        ← /trip      TripHeader / DayTabs / DayTimeline / TripActions / TripSidebar
```

### 3.3 数据流

```
/plan → useCreateTrip(mutation) → store.setTaskId(id) → navigate(/planning/:id)
/planning/:id → usePlanningTask(query, 2s轮询, completed/failed自停) → navigate(/trip/:tripId)
/trip/:tripId → useTripResult(query) → onSuccess: store.setTrip + invalidate planningTask
重新规划 → store.reset() → navigate(/plan)
```

**TanStack Query Hooks**: `useCreateTrip` / `usePlanningTask` / `useTripResult` / `useCancelTask`

**Zustand Store**: `currentTaskId` + `currentTrip`（persist 到 localStorage）

### 3.4 核心类型

```ts
type TaskStatus  = 'pending' | 'processing' | 'completed' | 'failed'
type AgentStatus = 'idle' | 'working' | 'done' | 'error'
type AgentType   = 'coordinator' | 'transport' | 'accommodation' | 'attraction' | 'dining' | 'strategy'

interface Trip {
  id: string
  destination: string
  dates: { start: string; end: string }
  budget: { min: number; max: number; currency: string }
  preferences: string[]
  travelStyle: string
  days: DayPlan[]
  summary: { totalCost: number; attractionCount: number }
}

interface DayPlan { dayIndex: number; date: string; activities: Activity[] }

interface Activity {
  id: string
  type: 'transport' | 'attraction' | 'dining' | 'hotel'
  name: string; startTime: string; endTime: string; duration: number
  location?: GeoPoint; description?: string; tips?: string; imageUrl?: string
}
```

---

## 四、后端设计

### 4.1 API 接口

```
POST   /api/trip/plan              → 创建规划任务，返回 { taskId }
GET    /api/trip/planning/:taskId  → 查询进度 { status, progress, agents: [...] }
GET    /api/trip/:tripId           → 获取完整行程 { trip: Trip }
POST   /api/trip/:taskId/cancel    → 取消任务
```

### 4.2 Agent 编排流程（LangGraph StateGraph）

```
POST /api/trip/plan
    ↓
Celery 异步任务启动
    ↓
Coordinator Agent（解析需求 → 分解子任务 → 提取约束）
    ↓
┌──────── 并行执行（Send API）────────┐
│                                      │
Transport  Accommodation  Attraction  Dining
  Agent       Agent         Agent     Agent
│                                      │
└──────── 结果汇总 ────────────────┘
    ↓
Strategy Agent（冲突检测 → 路线优化 → 成本控制 → 最终方案）
    ↓
结果写入 PostgreSQL + 缓存 Redis
    ↓
任务状态 → completed
```

Agent 间通信通过 LangGraph 的 `StateGraph` 消息流，每个 Agent 共享 AgentState，独立写入自己的方案片段。

### 4.3 数据库模型（核心表）

```sql
-- planning_tasks: 规划任务
id (UUID PK), status, preferences (JSONB), created_at, completed_at

-- trips: 行程
id (UUID PK), task_id (FK), destination, dates, budget (JSONB),
preferences, travel_style, data (JSONB: days/activities), summary (JSONB),
created_at

-- agent_logs: Agent 执行日志（可观测）
id, task_id, agent_name, status, input, output (JSONB), started_at, finished_at
```

图关系（景点相邻、景点-餐厅距离等）用 JSONB 字段存储，知识图谱量大了再迁 Neo4j。

---

## 五、不在 MVP 范围

- 用户认证/登录注册（路由守卫已预留）
- 一站式预订（订单管理、支付、OTA 对接）
- 实时行程调整（WebSocket 推送）
- 智能导游交互（推送通知、位置服务）
- 地图视图、设置页完整功能(SettingsPage only placeholder)
- Neo4j 知识图谱（PostgreSQL JSONB 暂代）

---

## 六、向后兼容

- 前端 features/ 模块独立，增删功能不波及
- 后端 agent/ 每个 Agent 独立文件，新增 Agent 不改编排主干
- API 接口可扩展 query/body 参数，不破坏现有契约
- Zustand persist 新增字段不影响已有缓存
