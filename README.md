# 旅程AI — 智能旅行规划平台

基于多智能体协作与遗传算法的 AI 旅行规划平台。输入目的地、日期、预算和偏好，AI 自动生成完整的每日行程（交通、住宿、景点、餐饮），并配有交互式地图、智能旅行伙伴和知识学习系统。

## 技术栈

| 层 | 后端 | 前端 |
|---|------|------|
| 框架 | FastAPI (Python 3.12+) | React 18 + TypeScript |
| ORM / 数据 | SQLAlchemy 2.0 (async) + PostgreSQL / SQLite | TanStack React Query |
| 缓存 / 队列 | Redis + Celery | Zustand (persist) |
| AI / LLM | DeepSeek + LangChain + LangGraph | — |
| 向量检索 | ChromaDB + sentence-transformers (BGE) | — |
| 嵌入模型 | ModelScope BAAI/bge-small-zh-v1.5 | — |
| 行程优化 | 遗传算法 (GA) 多目标预算分配 | — |
| 网页抓取 | BeautifulSoup4 + trafilatura | — |
| UI 组件 | — | shadcn/ui + Radix UI + Tailwind CSS |
| 地图 | 高德地图 API | @amap/amap-jsapi-loader |
| 角色动画 | — | pixi-live2d-display (Live2D Cubism) |
| 构建 | Uvicorn | Vite 6 |

## 系统架构

```
用户请求
   │
   ▼
┌─────────────────────────────────────────────────────┐
│  FastAPI REST API                                    │
│  /api/trip  /api/auth  /api/learn  /api/v1/chat     │
└────────────┬────────────────────────────┬────────────┘
             │                            │
     ┌───────▼────────┐          ┌───────▼────────┐
     │  Trip Service   │          │  Celery Worker  │
     │  (同步响应)      │          │  (异步规划任务)   │
     └───────┬────────┘          └───────┬────────┘
             │                            │
             │                   ┌────────▼────────┐
             │                   │  AI Agent 流水线  │
             │                   │                  │
             │                   │ ① Coordinator   │
             │                   │   · 需求分析      │
             │                   │   · GA 预算分配   │
             │                   │        │         │
             │                   │ ② 并行执行 (4路)  │
             │                   │ ┌────┬────┬────┐ │
             │                   │ │交通│住宿│景点│餐饮│ │
             │                   │ └────┴────┴────┘ │
             │                   │        │         │
             │                   │ ③ Strategy      │
             │                   │   · 整合每日行程   │
             │                   └────────┬────────┘
             │                            │
     ┌───────▼────────┐          ┌───────▼────────┐
     │   PostgreSQL    │          │     Redis       │
     │   · 用户/行程     │          │   · 聊天会话     │
     │   · 任务状态      │          │   · 用户偏好     │
     │   · 知识库       │          │   · 30天TTL     │
     └────────────────┘          └────────────────┘
                                           │
                                  ┌───────▼────────┐
                                  │    ChromaDB     │
                                  │   · 知识向量索引  │
                                  │   · BGE 嵌入     │
                                  └────────────────┘
```

## 功能

### 核心流程

- **AI 行程规划** — 多智能体流水线：协调分析 → 四路并行规划（交通 ‖ 住宿 ‖ 景点 ‖ 餐饮）→ 策略整合为完整每日行程
- **遗传算法预算分配** — 用 GA 替代 LLM 做预算拆分，基于偏好/天数/目的地数/旅行风格多目标优化，避免 LLM 幻觉和超时
- **智能澄清** — 用户输入信息不足时，以对话方式追问补充（目的地歧义、日期缺失等）
- **活动替换** — 对行程中任一活动点击「换一个」，AI 实时生成替代方案
- **目的地灵感** — 根据偏好和预算推荐旅行目的地

### 辅助功能

- **天气 + 穿搭建议** — 集成和风天气 API，AI 根据天气生成每日穿搭建议
- **地图可视化** — 高德地图展示每日行程路线、POI 标记和交通路径
- **旅行伙伴「小智」** — Live2D/SVG 角色，随目的地换装，支持对话交互
- **知识学习** — 提交小红书/马蜂窝/穷游/携程等平台链接，AI 抓取并提取知识要点，向量化索引到 ChromaDB
- **知识合并** — 每月自动将用户知识按地点合并为全局知识库，低质内容自动归档
- **多会话聊天** — 按行程分组的独立对话，自动提取用户偏好关键词

### 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | 首页 | Hero 区 + 功能介绍 + 使用流程 |
| `/plan` | 行程输入 | 目的地、日期、预算、偏好、旅行风格 |
| `/planning/:taskId` | 规划进度 | 六智能体实时状态 + 进度条 |
| `/trip/:tripId` | 行程结果 | 每日时间线 + 地图 + 天气 + 活动替换 |
| `/inspire` | 目的地灵感 | AI 推荐目的地 |
| `/knowledge` | 知识库 | 提交链接学习 + 历史记录 |
| `/login` | 登录 | 用户认证 |
| `/settings` | 设置 | 个人信息管理 |

## 项目结构

```
├── backend/                          # Python FastAPI 后端
│   ├── app/
│   │   ├── agent/                    # AI 智能体系统
│   │   │   ├── coordinator.py        #   协调员：需求分析 + GA 预算分配
│   │   │   ├── budget_optimizer.py   #   遗传算法引擎 (200个体 × 150代)
│   │   │   ├── transport.py          #   交通规划智能体
│   │   │   ├── accommodation.py      #   住宿规划智能体
│   │   │   ├── attraction.py         #   景点规划智能体
│   │   │   ├── dining.py             #   餐饮规划智能体
│   │   │   ├── strategy.py           #   策略整合：汇总为每日行程 JSON
│   │   │   ├── clarify.py            #   澄清智能体：信息不足时追问
│   │   │   ├── swap.py               #   活动替换智能体
│   │   │   ├── tools.py              #   智能体工具集
│   │   │   ├── graph.py              #   流水线编排 (asyncio.gather 并行)
│   │   │   └── state.py              #   AgentState 类型定义
│   │   ├── api/                      # REST API 路由
│   │   │   ├── router.py             #   路由聚合
│   │   │   ├── trip.py               #   /api/trip — 行程规划、状态、天气、替换
│   │   │   ├── auth.py               #   /api/auth — 登录、注册、个人信息
│   │   │   ├── learn.py              #   /api/learn — 知识学习、历史管理
│   │   │   └── chat.py               #   /api/v1/chat — 多会话聊天
│   │   ├── core/                     # 基础设施
│   │   │   ├── database.py           #   SQLAlchemy async engine + session
│   │   │   ├── llm.py                #   DeepSeek LLM 工厂 (ChatOpenAI 兼容)
│   │   │   ├── redis.py              #   Redis 连接管理 (优雅降级)
│   │   │   └── auth.py               #   JWT 认证 + bcrypt 密码哈希
│   │   ├── models/                   # SQLAlchemy ORM 模型
│   │   │   ├── user.py               #   用户模型
│   │   │   ├── trip.py               #   行程模型
│   │   │   ├── task.py               #   规划任务模型
│   │   │   ├── knowledge.py          #   用户知识 / 全局知识 / 学习历史
│   │   │   └── chat.py               #   聊天会话 / 用户偏好
│   │   ├── schemas/                  # Pydantic 请求/响应模型
│   │   │   ├── request.py            #   行程规划请求
│   │   │   ├── trip.py               #   行程响应
│   │   │   ├── auth.py               #   认证请求/响应
│   │   │   ├── clarify.py            #   澄清对话
│   │   │   ├── swap.py               #   活动替换
│   │   │   ├── inspire.py            #   目的地灵感
│   │   │   ├── learn.py              #   知识学习
│   │   │   └── chat.py               #   聊天消息
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── trip_service.py       #   行程 CRUD
│   │   │   ├── task_service.py       #   任务状态管理
│   │   │   ├── weather_service.py    #   和风天气 API 集成
│   │   │   ├── geo_service.py        #   高德地理编码 API
│   │   │   ├── scraper_service.py    #   多平台网页抓取 (9 平台适配)
│   │   │   ├── redis_memory.py       #   Redis 聊天记忆 + 偏好存储
│   │   │   └── knowledge_merge.py    #   知识合并引擎
│   │   └── tasks/                    # Celery 异步任务
│   │       ├── celery_app.py         #   Celery 配置
│   │       └── planning_task.py      #   行程规划异步任务
│   ├── tests/                        # 测试
│   │   └── test_budget_optimizer.py  #   遗传算法单元测试
│   ├── scripts/
│   │   └── index_existing.py         #   历史知识重建向量索引
│   ├── chroma_data/                  # ChromaDB 持久化数据
│   ├── seed.py                       # 测试用户初始化
│   ├── main.py                       # FastAPI 应用入口
│   └── requirements.txt
├── frontend/                         # React TypeScript 前端
│   ├── src/
│   │   ├── features/                 # 功能模块 (按页面组织)
│   │   │   ├── home/                 #   首页 (Hero + 功能介绍 + 流程)
│   │   │   ├── plan-input/           #   行程输入 (表单 + 澄清对话)
│   │   │   ├── planning/             #   规划进度 (实时状态轮询)
│   │   │   ├── trip-result/          #   行程结果 (时间线 + 地图 + 天气)
│   │   │   ├── travel-companion/     #   旅行伙伴 (Live2D 角色 + 对话)
│   │   │   ├── inspire/              #   目的地灵感
│   │   │   ├── knowledge/            #   知识学习
│   │   │   └── auth/                 #   登录认证
│   │   ├── shared/                   # 共享层
│   │   │   ├── api/                  #   API 客户端 (Axios) + React Query keys
│   │   │   ├── stores/               #   Zustand 全局状态
│   │   │   └── components/           #   布局组件 (Header, Footer, AppLayout)
│   │   ├── components/ui/            # shadcn/ui 基础组件
│   │   ├── router/                   # 路由配置 + 懒加载 + 路由守卫
│   │   ├── hooks/                    # 自定义 Hooks (useAMap)
│   │   ├── types/                    # TypeScript 类型定义
│   │   └── lib/                      # 工具函数
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── package.json
├── docs/                             # 项目文档
│   └── 排错记录.md                    #   开发排错记录
├── docker-compose.yml                # PostgreSQL + Redis 容器编排
├── .gitignore
└── README.md
```

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- Docker (可选，用于 PostgreSQL + Redis)

### 1. 启动基础设施 (可选)

```bash
docker-compose up -d    # 启动 PostgreSQL:5432 + Redis:6379
```

> Docker 不可用时，可将 `.env` 中 `DATABASE_URL` 改为 SQLite：
> `DATABASE_URL=sqlite+aiosqlite:///./travel_planner.db`
> Redis 不可用时系统会自动降级，不影响核心流程。

### 2. 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 等

# 初始化测试用户
python seed.py

# 启动 API 服务 (http://localhost:8000)
python main.py
```

> 如果系统 Python 已安装全部依赖，可直接跳过虚拟环境和 pip install，
> 用系统 Python 运行：`python main.py`

```bash
# 如果提示端口被占用，先释放端口:
#   Windows: netstat -ano | findstr :8000  然后  taskkill -PID <PID> -F
#   Linux/Mac: lsof -ti:8000 | xargs kill -9

# (可选) 启动 Celery Worker 处理异步规划任务
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

### 3. 前端

```bash
cd frontend
npm install

# 启动开发服务器 (http://localhost:5173)
npm run dev
```

### 4. 测试账号

| 字段 | 值 |
|------|-----|
| 用户名 | `test` |
| 密码 | `123456` |

## 环境变量

### 后端 (`backend/.env`)

| 变量 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `DATABASE_URL` | 数据库连接 (asyncpg) | 是 | `postgresql+asyncpg://postgres:postgres@localhost:5432/travel_planner` |
| `REDIS_URL` | Redis 连接 | 否 | `redis://localhost:6379/0` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 是 | — |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | 是 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 模型名称 | 是 | `deepseek-chat` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 是 | — |
| `SENIVERSE_API_KEY` | 和风天气 API 密钥 | 否 | — |
| `AMAP_API_KEY` | 高德地图 API 密钥 | 否 | — |

### 前端 (`frontend/.env`)

| 变量 | 说明 |
|------|------|
| `VITE_AMAP_KEY` | 高德地图 JS API 密钥 |
| `VITE_AMAP_VERSION` | 高德地图 API 版本 |

## API 概览

启动后端后访问 http://localhost:8000/docs 查看 Swagger UI。

### 行程规划

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/trip/clarify` | 提交需求，返回澄清问题或确认 |
| `POST` | `/api/trip/plan` | 创建规划任务，返回 task_id |
| `GET` | `/api/trip/planning/{task_id}` | 轮询任务进度与智能体状态 |
| `GET` | `/api/trip/{trip_id}` | 获取完整行程 |
| `GET` | `/api/trip/{trip_id}/weather` | 获取行程天气 + 穿搭建议 |
| `POST` | `/api/trip/{trip_id}/swap` | 替换行程中的活动 |
| `POST` | `/api/trip/{task_id}/cancel` | 取消规划任务 |

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/login` | 用户登录 |
| `POST` | `/api/auth/register` | 用户注册 |
| `GET` | `/api/auth/profile` | 获取个人信息 |

### 知识学习

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/learn/analyze` | 提交 URL，AI 抓取并分析 |
| `GET` | `/api/learn/recent` | 最近学习记录 |
| `GET` | `/api/learn/history` | 全部学习历史 |
| `DELETE` | `/api/learn/history/{id}` | 删除学习记录 |

### 聊天

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/chat/context` | 获取行程上下文 |
| `POST` | `/api/v1/chat/send` | 发送聊天消息 |
| `GET` | `/api/v1/chat/history` | 聊天历史分组 |
| `GET` | `/api/v1/chat/session/{id}` | 获取会话消息 |
| `POST` | `/api/v1/chat/restore` | 恢复历史会话 |
| `DELETE` | `/api/v1/chat/session/{id}` | 删除会话 |

## 核心设计

### 遗传算法预算优化

协调智能体使用遗传算法（GA）替代 LLM 进行预算分配，在四个类别（交通、住宿、景点、餐饮）之间寻找最优比例：

- **种群规模**: 200 个染色体
- **进化代数**: 150 代
- **选择**: 锦标赛选择 (size=3) + 精英保留 (10%)
- **交叉**: SBX (Simulated Binary Crossover, η=20)
- **变异**: 多项式变异 (η=20, rate=10%)
- **适应度**: 基于用户偏好加权目标向量的欧氏距离 + 边界惩罚项
- **约束**: 每类最低 3%，最高 50%（软约束，通过惩罚项实现）

偏好关键词自动映射到类别权重（如「美食」→ 餐饮 1.7×，「舒适」→ 住宿 1.55×），经济模式自动切换为基础分配方案。

### 多智能体并行流水线

1. **Coordinator（协调员）**: 解析用户需求，计算天数/目的地数，运行 GA 预算分配，生成需求摘要
2. **并行规划**: 四个专业智能体通过 `asyncio.gather` 同时执行，各自获得预算上限
   - **Transport**: 交通方式与路线规划
   - **Accommodation**: 住宿推荐与预算匹配
   - **Attraction**: 景点筛选与游览时间
   - **Dining**: 餐饮推荐与口味匹配
3. **Strategy（策略整合）**: 汇总四路结果，生成结构化 JSON 每日行程

错误隔离：任一智能体失败（异常）不影响其他智能体继续执行，失败结果以 `error` 字段标记。

### 向量检索与知识学习

- 使用 ModelScope `BAAI/bge-small-zh-v1.5` 嵌入模型
- 知识要点存入 ChromaDB，支持语义检索
- 网页抓取覆盖 9 个平台（小红书、马蜂窝、穷游、携程、微博、B站、抖音、美团、大众点评）
- 多策略降级：完整抓取 → 轻量抓取 → Meta 标签提取 → URL 文本提取

### Redis 优雅降级

所有 Redis 操作都包含 `None` 检查和异常捕获。当 Redis 不可用时（未启动、连接超时、网络故障），系统自动降级为空值返回，不影响核心流程。

## 开发命令

### 后端

```bash
cd backend

# 运行测试
pytest

# 运行测试 + 覆盖率
pytest --cov=app --cov-report=term-missing

# 历史知识重建向量索引
python scripts/index_existing.py
```

### 前端

```bash
cd frontend

# 类型检查
npm run typecheck

# 代码检查
npm run lint

# 代码格式化
npm run format

# 生产构建
npm run build
```
学习小红书书知识：
<img width="916" height="800" alt="image" src="https://github.com/user-attachments/assets/6419e4cc-c1bf-432d-816e-94be99009625" />


规划好的行程：
<img width="1860" height="915" alt="cb76e0ab51b677aae780cee9ede49539" src="https://github.com/user-attachments/assets/b5b60d35-1c19-4746-bd0b-c8cdaa492cf1" />
