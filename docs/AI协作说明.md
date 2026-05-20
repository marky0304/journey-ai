# AI 协作说明

本文档为 AI 编程助手（Claude Code、Copilot 等）提供项目上下文，帮助快速理解架构约定、代码模式和开发工作流。

## 0. 开发者角色与协作模式

**marky0304** 是本项目的唯一开发者，负责从整体架构设计到具体代码实现的全链路开发。

### 协作原则

| 维度 | marky0304 负责 | AI 助手负责 |
|------|---------------|-------------|
| 架构设计 | 最终决策，确定技术方向 | 提供参考意见，不替代决策 |
| 代码实现 | 把控整体结构，写核心逻辑 | 辅助编写、补全、重构 |
| 代码审查 | 最终审核 | 主动 review，标注问题级别 |
| 调试排错 | 判断根因方向 | 辅助定位、提供修复方案 |
| 文档维护 | 确认内容准确性 | 辅助更新、保持同步 |

### AI 行为准则

1. **架构决策先问** — 涉及新增模块、修改数据流、调整分层时，先提出方案供确认，不直接落代码
2. **简洁输出** — 无需在每个回复末尾总结做了什么；直接说结果即可
3. **代码审查自动触发** — 每次写代码后自动进行 code review
4. **遵循现有模式** — 新增代码遵循项目已有的命名、分层、错误处理习惯，不引入新的范式
5. **中文优先** — 对话和注释使用中文

## 1. 项目概述

旅程AI 是一个基于多智能体协作的智能旅行规划平台。核心流程：

```
用户输入 → 协调智能体(预算分配) → [交通 ‖ 住宿 ‖ 景点 ‖ 餐饮] → 策略智能体(整合) → 最终行程
```

## 2. 架构原则

### 2.1 后端分层

```
api/     → 路由层（薄层，仅参数校验和调用 service）
services/ → 业务逻辑层
agent/   → AI 智能体层（纯函数，输入 state 输出 dict）
models/  → ORM 模型（SQLAlchemy）
schemas/ → Pydantic 模型（请求/响应验证）
core/    → 基础设施（数据库连接、LLM 客户端、认证）
tasks/   → Celery 异步任务
```

### 2.2 前端分层

```
features/    → 功能模块（每个模块自包含：页面 + 组件 + hooks）
shared/      → 共享层（API 客户端、状态 store、布局组件）
components/  → 通用 UI 组件（shadcn/ui）
router/      → 路由配置 + 懒加载 + 路由守卫
types/       → 共享类型定义
```

### 2.3 关键约定

- **不可变性优先** — 始终创建新对象，不修改现有对象
- **API 响应格式** — 统一使用 `{ success, data, error, meta }` 信封
- **状态分类** — 服务端状态用 React Query，客户端状态用 Zustand，URL 状态用 search params
- **错误处理** — 每一层显式处理错误，不静默吞掉异常

## 3. AI 智能体系统

### 3.1 状态定义 (`backend/app/agent/state.py`)

```python
class AgentState(TypedDict):
    start_location: str
    destination: str
    start_date: str
    end_date: str
    budget_min: int
    budget_max: int
    currency: str
    preferences: List[str]
    travel_style: str
    messages: Annotated[list, add_messages]
    constraints: Optional[dict]      # 协调器解析的预算分配
    transport_plan: Optional[dict]
    accommodation_plan: Optional[dict]
    attraction_plan: Optional[dict]
    dining_plan: Optional[dict]
    final_plan: Optional[dict]
    error: Optional[str]
```

### 3.2 管道执行 (`backend/app/agent/graph.py`)

```
run_trip_pipeline(initial_state):
  1. coordinator_node(state) → 解析预算分配，存入 state.constraints
  2. asyncio.gather(
       transport_node(state, budget_target),
       accommodation_node(state, budget_target),
       attraction_node(state, budget_target),
       dining_node(state, budget_target),
     )
  3. strategy_node(state) → 整合为最终行程 JSON
```

### 3.3 预算流向（重要）

协调器将总预算按比例分配给各智能体：
- 交通 30%、住宿 30%、景点 25%、餐饮 15%

每个智能体接收具体的 `budget_target` 金额，必须在 prompt 中被告知「尽量用满此预算」。

### 3.4 添加新智能体

1. 创建 `backend/app/agent/新agent.py`，定义 `async def xxx_node(state: AgentState, ...) -> dict`
2. 在 `graph.py` 中导入并加入管道
3. 如需新状态字段，在 `state.py` 中添加
4. 在 `planning_task.py` 和 `api/trip.py` 的 initial_state 中添加默认值

## 4. 前端路由与功能模块

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | HomePage | 首页（Hero + 特色 + 流程） |
| `/plan` | PlanInputPage | 行程输入表单 |
| `/planning/:taskId` | PlanningPage | 规划进度展示 |
| `/trip/:tripId` | TripResultPage | 行程结果展示 |
| `/inspire` | InspirePage | 目的地灵感 |
| `/knowledge` | KnowledgePage | 知识库管理 |
| `/settings` | SettingsPage | 用户设置 |
| `*` | NotFoundPage | 404 |

### 4.1 状态管理

- `useAuthStore` (Zustand + persist) — 认证 token、用户信息
- `useTripStore` (Zustand) — 当前行程、规划阶段
- React Query — 所有 API 数据（缓存、重试、失效策略）

### 4.2 API 客户端 (`frontend/src/shared/api/client.ts`)

Axios 实例，自动注入 Bearer token，拦截 401 弹出登录框。

## 5. 数据库模型

| 模型 | 表 | 说明 |
|------|-----|------|
| User | users | 用户（JWT 认证） |
| Trip | trips | 行程（JSON 存储 days 数据） |
| PlanningTask | planning_tasks | 规划任务状态机 |
| ChatSession | chat_sessions | 聊天会话 |
| UserPreference | user_preferences | 用户偏好 |
| UserKnowledge | user_knowledge | 用户提交的知识 |
| LearnHistory | learn_histories | 知识学习历史 |
| GlobalKnowledge | global_knowledge | 全局合并知识库 |

## 6. 开发工作流

### 6.1 环境启动

```bash
# 后端
cd backend && python main.py

# 前端（另一个终端）
cd frontend && npm run dev
```

### 6.2 代码规范

- Python: PEP 8, type hints, black 格式化
- TypeScript: 严格模式, interface > type（对象形状）, Zod 验证输入
- 文件大小: 200-400 行典型，800 行上限
- 函数大小: < 50 行
- 嵌套深度: < 4 层

### 6.3 关键文件路径

| 用途 | 路径 |
|------|------|
| 后端入口 | `backend/main.py` |
| 配置 | `backend/app/config.py` |
| API 路由 | `backend/app/api/trip.py` |
| 智能体管道 | `backend/app/agent/graph.py` |
| 前端入口 | `frontend/src/main.tsx` |
| 路由配置 | `frontend/src/router/index.tsx` |
| 类型定义 | `frontend/src/types/api.ts` |
| API 客户端 | `frontend/src/shared/api/client.ts` |

## 7. 常见任务指南

> 较大改动（新增模块、修改管道流程、数据结构变更）先与开发者确认再动手。小改动（文案调整、bug 修复、样式修正）可直接执行。

### 修改 AI 规划逻辑

1. 定位到 `backend/app/agent/` 下对应的智能体文件
2. 修改 System Prompt（`XXX_PROMPT` 常量）
3. 如需修改数据结构，先更新 `state.py`，再更新所有 initial_state 初始化点
4. 测试：启动后端，调用 `/api/trip/plan` 接口

### 添加新前端页面

1. 在 `frontend/src/features/` 下创建功能目录
2. 在 `lazyPages.ts` 中添加懒加载导入
3. 在 `routes.ts` 中添加路由常量
4. 在 `router/index.tsx` 中注册路由
5. 如需新 API，在 `tripApi.ts` 中添加方法，在 `queryKeys.ts` 中添加 key

### 调试智能体输出

每个智能体的原始 LLM 输出存储在对应 plan 的 `raw` 字段中：
- `state["transport_plan"]["raw"]`
- `state["final_plan"]["raw"]` — 策略整合的最终输出

## 8. 注意事项

- **LLM 输出格式不稳定** — `extract_trip_from_final_plan()` 有 JSON 解析容错逻辑，修改时注意保持
- **双部署模式** — 有 Redis 时走 Celery 队列，无 Redis 时走 `asyncio.create_task`，两处 initial_state 需同步更新
- **预算匹配** — 协调器输出 budget_share，graph.py 解析后传递给各智能体，确保总消费接近用户预算
- **嵌入回退链** — BGE → MiniLM → SimpleChineseEmbedding，确保离线可用
- **前端地图** — 高德地图通过动态脚本加载，需处理加载失败情况
