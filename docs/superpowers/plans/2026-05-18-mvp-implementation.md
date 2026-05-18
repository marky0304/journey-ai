# 智能旅游行程规划平台 MVP — 实现计划

> **Goal:** 构建 AI 驱动的旅游规划平台 MVP：用户输入需求 → 多 Agent 协作规划 → 展示完整行程

> **Architecture:** monorepo（frontend/ + backend/），前端 Vite+React SPA 通过 REST API 与后端 FastAPI 通信，后端 LangGraph 编排 6 个 Agent（DeepSeek），Celery 处理异步任务，PostgreSQL+Redis 存储。

---

## 构建顺序与依赖

```
Phase 0: 脚手架
├─ Task 0.1  前端 Vite 项目          } 可并行
├─ Task 0.2  后端 FastAPI 项目       }
└─ Task 0.3  Docker Compose

Phase 1: 后端核心 (串行)
├─ Task 1.1  数据库 + ORM 模型
├─ Task 1.2  Redis + Celery
├─ Task 1.3  LLM 初始化
├─ Task 1.4  Pydantic Schemas
└─ Task 1.5  业务服务层

Phase 2: Agent 引擎 (串行)
├─ Task 2.1  状态定义 + 工具函数
├─ Task 2.2  Coordinator Agent
├─ Task 2.3  4 个专业 Agent (交通/住宿/景点/餐饮)
├─ Task 2.4  Strategy Agent + Graph 编排
└─ Task 2.5  Celery 异步任务

Phase 3: API 端点
└─ Task 3.1  trip API (4 个端点)

Phase 4: 前端核心 (shadcn 先，后续可并行)
├─ Task 4.1  shadcn/ui 初始化
├─ Task 4.2  类型定义 + 工具函数
├─ Task 4.3  API 层 + Zustand Store
├─ Task 4.4  路由系统
└─ Task 4.5  布局组件

Phase 5: 前端页面 (顺序)
├─ Task 5.1  首页
├─ Task 5.2  需求输入页
├─ Task 5.3  规划进度页
├─ Task 5.4  行程结果页

Phase 6: 集成收尾
├─ Task 6.1  后端 Agent 结果写入 DB
├─ Task 6.2  前端构建验证
└─ Task 6.3  后端启动验证
```

**关键并行点**：Phase 1-3（后端）与 Phase 4（前端核心）可同时推进，双方在 Phase 6 汇合。

---

## Phase 0: 项目脚手架

### Task 0.1: 创建前端 Vite + React 项目

**创建目录**: `frontend/`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "travel-planner",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^7.0.0",
    "@tanstack/react-query": "^5.60.0",
    "zustand": "^5.0.0",
    "axios": "^1.7.0",
    "lucide-react": "^0.460.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0",
    "sonner": "^1.7.0",
    "date-fns": "^4.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "typescript": "~5.6.0",
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } },
  },
})
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

- [ ] **Step 4: 创建 tsconfig.app.json**

```json
{
  "compilerOptions": {
    "target": "ES2020", "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext", "skipLibCheck": true,
    "moduleResolution": "bundler", "allowImportingTsExtensions": true,
    "isolatedModules": true, "moduleDetection": "force",
    "noEmit": true, "jsx": "react-jsx",
    "strict": true, "noUnusedLocals": true,
    "noUnusedParameters": true, "noFallthroughCasesInSwitch": true,
    "baseUrl": ".", "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"]
}
```

- [ ] **Step 5: 创建 tsconfig.node.json**

```json
{
  "compilerOptions": {
    "target": "ES2022", "lib": ["ES2023"], "module": "ESNext",
    "skipLibCheck": true, "moduleResolution": "bundler",
    "allowImportingTsExtensions": true, "isolatedModules": true,
    "moduleDetection": "force", "noEmit": true, "strict": true,
    "noUnusedLocals": true, "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 6: 创建 tailwind.config.ts**

```ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))', input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))', background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
        secondary: { DEFAULT: 'hsl(var(--secondary))', foreground: 'hsl(var(--secondary-foreground))' },
        muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
        accent: { DEFAULT: 'hsl(var(--accent))', foreground: 'hsl(var(--accent-foreground))' },
        card: { DEFAULT: 'hsl(var(--card))', foreground: 'hsl(var(--card-foreground))' },
        destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
      },
      borderRadius: {
        lg: 'var(--radius)', md: 'calc(var(--radius) - 2px)', sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
} satisfies Config
```

- [ ] **Step 7: 创建 postcss.config.js**

```js
export default { plugins: { tailwindcss: {}, autoprefixer: {} } }
```

- [ ] **Step 8: 创建 index.html**

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>旅程AI - 智能旅行规划</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 9: 创建 src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%; --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%; --card-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%; --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%; --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%; --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%; --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%; --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%; --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%; --radius: 0.5rem;
  }
}
```

- [ ] **Step 10: 创建 src/main.tsx**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>
)
```

- [ ] **Step 11: 创建 src/App.tsx**

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { RouterProvider } from './router'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
    mutations: { onError: (err: Error) => console.error(err) },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider />
      <Toaster position="top-center" richColors />
    </QueryClientProvider>
  )
}
```

- [ ] **Step 12: 安装依赖**

```bash
cd frontend && npm install
```

---

### Task 0.2: 创建后端 FastAPI 项目

**创建目录**: `backend/app/` 及所有子包

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.115.5
uvicorn[standard]==0.32.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
pydantic==2.10.3
pydantic-settings==2.6.1
redis==5.2.1
celery[redis]==5.4.0
langchain==0.3.13
langgraph==0.2.55
langchain-openai==0.2.12
python-dotenv==1.0.1
httpx==0.28.1
```

- [ ] **Step 2: 创建 .env.example**

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/travel_planner
REDIS_URL=redis://localhost:6379/0
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

- [ ] **Step 3: 创建目录结构**

```bash
mkdir -p backend/app/{api,agent,models,schemas,services,tasks,core}
```

在每个目录下创建空的 `__init__.py`。

- [ ] **Step 4: 创建 main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.database import engine, Base

app = FastAPI(title="旅程AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 创建 app/config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/travel_planner"
    redis_url: str = "redis://localhost:6379/0"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 6: 创建 app/api/router.py**

```python
from fastapi import APIRouter

api_router = APIRouter()
# 后续 Task 3.1 挂载 trip_router
```

---

### Task 0.3: Docker Compose

**创建**: `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: travel_planner
    ports: ['5432:5432']
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ['6379:6379']

volumes:
  pgdata:
```

---

## Phase 1: 后端核心基础设施

### Task 1.1: 数据库 + ORM 模型

**创建**: `backend/app/core/database.py`, `backend/app/models/__init__.py`, `backend/app/models/task.py`, `backend/app/models/trip.py`

- [ ] **Step 1: database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session() as session:
        try: yield session
        finally: await session.close()
```

- [ ] **Step 2: models/__init__.py**

```python
from app.models.task import PlanningTask
from app.models.trip import Trip
from app.core.database import Base
__all__ = ["Base", "PlanningTask", "Trip"]
```

- [ ] **Step 3: models/task.py**

```python
import uuid, enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class TaskStatus(str, enum.Enum):
    pending = "pending"; processing = "processing"
    completed = "completed"; failed = "failed"

class PlanningTask(Base):
    __tablename__ = "planning_tasks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.pending)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

- [ ] **Step 4: models/trip.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Trip(Base):
    __tablename__ = "trips"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("planning_tasks.id"))
    destination: Mapped[str] = mapped_column(String(200))
    dates: Mapped[dict] = mapped_column(JSONB)
    budget: Mapped[dict] = mapped_column(JSONB)
    preferences: Mapped[list] = mapped_column(JSONB, default=list)
    travel_style: Mapped[str] = mapped_column(String(50))
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

### Task 1.2: Redis + Celery

**创建**: `backend/app/core/redis.py`, `backend/app/tasks/celery_app.py`

- [ ] **Step 1: redis.py**

```python
import redis.asyncio as aioredis
from app.config import settings

redis_client = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

async def get_redis():
    return redis_client
```

- [ ] **Step 2: celery_app.py**

```python
from celery import Celery
from app.config import settings

celery_app = Celery("travel_planner", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json", result_serializer="json",
    accept_content=["json"], timezone="Asia/Shanghai",
    enable_utc=True, task_track_started=True, task_acks_late=True,
)
```

---

### Task 1.3: LLM 初始化

**创建**: `backend/app/core/llm.py`

```python
from langchain_openai import ChatOpenAI
from app.config import settings

def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=temperature,
    )
```

---

### Task 1.4: Pydantic Schemas

**创建**: `backend/app/schemas/request.py`, `backend/app/schemas/trip.py`

- [ ] **Step 1: request.py**

```python
from pydantic import BaseModel, Field
from datetime import date

class PlanRequest(BaseModel):
    destination: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: date
    budget_min: int = Field(0, ge=0)
    budget_max: int = Field(100000, ge=0)
    currency: str = Field(default="CNY")
    preferences: list[str] = Field(default_factory=list)
    travel_style: str = Field(default="balanced")
```

- [ ] **Step 2: trip.py**

```python
from pydantic import BaseModel
from datetime import datetime

class GeoPoint(BaseModel):
    lat: float; lng: float

class ActivityOut(BaseModel):
    id: str; type: str; name: str; start_time: str; end_time: str
    duration: int; location: GeoPoint | None = None
    description: str | None = None; tips: str | None = None; image_url: str | None = None

class DayPlanOut(BaseModel):
    day_index: int; date: str; activities: list[ActivityOut]

class TripSummary(BaseModel):
    total_cost: int; attraction_count: int

class TripOut(BaseModel):
    id: str; destination: str; dates: dict; budget: dict; preferences: list[str]
    travel_style: str; days: list[DayPlanOut]; summary: TripSummary

class AgentInfo(BaseModel):
    name: str; status: str

class TaskStatusOut(BaseModel):
    task_id: str; status: str; progress: int; agents: list[AgentInfo]
    trip_id: str | None = None; error_message: str | None = None

class PlanResponse(BaseModel):
    task_id: str

class CancelResponse(BaseModel):
    success: bool
```

---

### Task 1.5: 业务服务层

**创建**: `backend/app/services/task_service.py`, `backend/app/services/trip_service.py`

- [ ] **Step 1: task_service.py**

```python
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import PlanningTask, TaskStatus

async def create_task(db: AsyncSession, preferences: dict, celery_task_id: str) -> PlanningTask:
    task = PlanningTask(preferences=preferences, celery_task_id=celery_task_id, status=TaskStatus.processing)
    db.add(task); await db.commit(); await db.refresh(task)
    return task

async def get_task(db: AsyncSession, task_id: uuid.UUID) -> PlanningTask | None:
    result = await db.execute(select(PlanningTask).where(PlanningTask.id == task_id))
    return result.scalar_one_or_none()

async def update_task_status(db: AsyncSession, task: PlanningTask, status: TaskStatus, error_message: str | None = None) -> None:
    task.status = status
    if error_message: task.error_message = error_message
    if status in (TaskStatus.completed, TaskStatus.failed): task.completed_at = datetime.utcnow()
    await db.commit()

async def cancel_task(db: AsyncSession, task: PlanningTask) -> None:
    task.status = TaskStatus.failed; task.error_message = "用户取消"
    task.completed_at = datetime.utcnow(); await db.commit()
```

- [ ] **Step 2: trip_service.py**

```python
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.trip import Trip

async def create_trip(db: AsyncSession, task_id: uuid.UUID, trip_data: dict) -> Trip:
    trip = Trip(
        task_id=task_id, destination=trip_data["destination"],
        dates=trip_data["dates"], budget=trip_data["budget"],
        preferences=trip_data.get("preferences", []),
        travel_style=trip_data.get("travel_style", "balanced"),
        data={"days": trip_data.get("days", [])},
        summary=trip_data.get("summary", {}),
    )
    db.add(trip); await db.commit(); await db.refresh(trip)
    return trip

async def get_trip(db: AsyncSession, trip_id: uuid.UUID) -> Trip | None:
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    return result.scalar_one_or_none()
```

---

## Phase 2: Agent 引擎

### Task 2.1: Agent 状态定义 + 工具

**创建**: `backend/app/agent/state.py`, `backend/app/agent/tools.py`

- [ ] **Step 1: state.py**

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    destination: str; start_date: str; end_date: str
    budget_min: int; budget_max: int; currency: str
    preferences: list[str]; travel_style: str

    messages: Annotated[list, add_messages]

    transport_plan: dict | None; accommodation_plan: dict | None
    attraction_plan: dict | None; dining_plan: dict | None

    final_plan: dict | None; error: str | None
```

- [ ] **Step 2: tools.py**

```python
import json
from langchain_core.tools import tool

@tool
def validate_plan_schema(plan_json: str) -> str:
    """验证行程 JSON Schema"""
    try:
        plan = json.loads(plan_json)
        for field in ["destination", "dates", "days"]:
            if field not in plan: return f"缺少必要字段: {field}"
        return "Schema 验证通过"
    except json.JSONDecodeError as e:
        return f"JSON 解析失败: {e}"
```

---

### Task 2.2: Coordinator Agent

**创建**: `backend/app/agent/coordinator.py`

```python
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.state import AgentState
from app.core.llm import get_llm

COORDINATOR_PROMPT = """你是行程规划协调员。分析用户需求，分解为交通、住宿、景点、餐饮四个子任务。输出 JSON:
{"summary": "需求摘要", "constraints": {"transport": {"budget_share": 0.3}, "accommodation": {"budget_share": 0.3}, "attraction": {"budget_share": 0.25}, "dining": {"budget_share": 0.15}}}
"""

async def coordinator_node(state: AgentState) -> dict:
    llm = get_llm(temperature=0.3)
    user_input = f"目的地: {state['destination']}\n日期: {state['start_date']} 至 {state['end_date']}\n预算: {state['budget_min']}-{state['budget_max']} {state['currency']}\n偏好: {', '.join(state['preferences'])}\n旅行风格: {state['travel_style']}"
    messages = [SystemMessage(content=COORDINATOR_PROMPT), HumanMessage(content=user_input)]
    response = await llm.ainvoke(messages)
    return {"messages": [HumanMessage(content=f"协调分析: {response.content}", name="coordinator")]}
```

---

### Task 2.3: 4 个专业 Agent

**创建**: `backend/app/agent/transport.py`, `accommodation.py`, `attraction.py`, `dining.py`

- [ ] **Step 1: transport.py**

```python
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.state import AgentState
from app.core.llm import get_llm

TRANSPORT_PROMPT = """你是交通规划专家。推荐往返大交通方案。输出 JSON:
{"type": "flight/train/car", "options": [{"name": "", "price": 0, "duration": "", "departure": "", "arrival": ""}], "total_cost": 0}
"""

async def transport_node(state: AgentState) -> dict:
    llm = get_llm()
    context = f"目的地: {state['destination']}, 日期: {state['start_date']} 至 {state['end_date']}, 预算: {state['budget_min']}-{state['budget_max']}"
    messages = [SystemMessage(content=TRANSPORT_PROMPT), HumanMessage(content=context)]
    response = await llm.ainvoke(messages)
    return {"transport_plan": {"raw": response.content}, "messages": [HumanMessage(content=f"交通方案: {response.content}", name="transport")]}
```

- [ ] **Step 2: accommodation.py**

```python
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.state import AgentState
from app.core.llm import get_llm

ACCOMMODATION_PROMPT = """你是住宿推荐专家。推荐酒店。输出 JSON:
{"hotels": [{"name": "", "area": "", "price_per_night": 0, "rating": 0}], "total_cost": 0}
"""

async def accommodation_node(state: AgentState) -> dict:
    llm = get_llm()
    context = f"目的地: {state['destination']}, 预算: {state['budget_min']}-{state['budget_max']}, 偏好: {state['preferences']}"
    messages = [SystemMessage(content=ACCOMMODATION_PROMPT), HumanMessage(content=context)]
    response = await llm.ainvoke(messages)
    return {"accommodation_plan": {"raw": response.content}, "messages": [HumanMessage(content=f"住宿方案: {response.content}", name="accommodation")]}
```

- [ ] **Step 3: attraction.py**

```python
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.state import AgentState
from app.core.llm import get_llm

ATTRACTION_PROMPT = """你是景点规划专家。设计每日游览路线。输出 JSON:
{"days": [{"day_index": 1, "date": "", "attractions": [{"name": "", "duration_min": 0, "ticket_price": 0}]}], "total_tickets": 0}
"""

async def attraction_node(state: AgentState) -> dict:
    llm = get_llm()
    context = f"目的地: {state['destination']}, 日期: {state['start_date']} 至 {state['end_date']}, 偏好: {state['preferences']}, 风格: {state['travel_style']}"
    messages = [SystemMessage(content=ATTRACTION_PROMPT), HumanMessage(content=context)]
    response = await llm.ainvoke(messages)
    return {"attraction_plan": {"raw": response.content}, "messages": [HumanMessage(content=f"景点方案: {response.content}", name="attraction")]}
```

- [ ] **Step 4: dining.py**

```python
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.state import AgentState
from app.core.llm import get_llm

DINING_PROMPT = """你是美食推荐专家。推荐每日餐厅。输出 JSON:
{"meals": [{"day_index": 1, "restaurants": [{"name": "", "meal": "lunch/dinner", "cuisine": "", "price_per_person": 0}]}], "total_cost": 0}
"""

async def dining_node(state: AgentState) -> dict:
    llm = get_llm()
    context = f"目的地: {state['destination']}, 日期: {state['start_date']} 至 {state['end_date']}, 偏好: {state['preferences']}"
    messages = [SystemMessage(content=DINING_PROMPT), HumanMessage(content=context)]
    response = await llm.ainvoke(messages)
    return {"dining_plan": {"raw": response.content}, "messages": [HumanMessage(content=f"餐饮方案: {response.content}", name="dining")]}
```

---

### Task 2.4: Strategy Agent + Graph 编排

**创建**: `backend/app/agent/strategy.py`, `backend/app/agent/graph.py`

- [ ] **Step 1: strategy.py**

```python
import json
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.state import AgentState
from app.core.llm import get_llm

STRATEGY_PROMPT = """你是策略优化专家。整合交通/住宿/景点/餐饮方案为完整每日行程。
输出完整行程 JSON:
{"destination":"","dates":{"start":"","end":""},"budget":{"min":0,"max":0,"currency":"CNY"},"preferences":[],"travel_style":"","days":[{"day_index":1,"date":"","activities":[{"id":"","type":"attraction","name":"","start_time":"09:00","end_time":"11:00","duration":120,"description":"","tips":""}]}],"summary":{"total_cost":0,"attraction_count":0}}
"""

async def strategy_node(state: AgentState) -> dict:
    llm = get_llm(temperature=0.3)
    context = f"交通方案: {state.get('transport_plan', {})}\n住宿方案: {state.get('accommodation_plan', {})}\n景点方案: {state.get('attraction_plan', {})}\n餐饮方案: {state.get('dining_plan', {})}\n偏好: {state['preferences']}\n风格: {state['travel_style']}\n预算: {state['budget_min']}-{state['budget_max']}"
    messages = [SystemMessage(content=STRATEGY_PROMPT), HumanMessage(content=context)]
    response = await llm.ainvoke(messages)
    return {"final_plan": {"raw": response.content}, "messages": [HumanMessage(content=f"最终方案: {response.content}", name="strategy")]}
```

- [ ] **Step 2: graph.py**

```python
import json, uuid, re
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.coordinator import coordinator_node
from app.agent.transport import transport_node
from app.agent.accommodation import accommodation_node
from app.agent.attraction import attraction_node
from app.agent.dining import dining_node
from app.agent.strategy import strategy_node

async def aggregate_results(state: AgentState) -> dict:
    return {"messages": []}

def build_trip_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("transport", transport_node)
    workflow.add_node("accommodation", accommodation_node)
    workflow.add_node("attraction", attraction_node)
    workflow.add_node("dining", dining_node)
    workflow.add_node("aggregate", aggregate_results)
    workflow.add_node("strategy", strategy_node)

    workflow.set_entry_point("coordinator")
    workflow.add_edge("coordinator", "transport")
    workflow.add_edge("coordinator", "accommodation")
    workflow.add_edge("coordinator", "attraction")
    workflow.add_edge("coordinator", "dining")
    workflow.add_edge("transport", "aggregate")
    workflow.add_edge("accommodation", "aggregate")
    workflow.add_edge("attraction", "aggregate")
    workflow.add_edge("dining", "aggregate")
    workflow.add_edge("aggregate", "strategy")
    workflow.add_edge("strategy", END)

    return workflow.compile()

trip_graph = build_trip_graph()

def extract_trip_from_final_plan(final_plan: dict) -> dict:
    raw = final_plan.get("raw", "{}")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', raw)
        if match: parsed = json.loads(match.group())
        else: raise ValueError(f"无法解析 Agent 输出: {raw[:200]}")

    for day in parsed.get("days", []):
        for activity in day.get("activities", []):
            if not activity.get("id"): activity["id"] = str(uuid.uuid4())
    return parsed
```

---

### Task 2.5: Celery 异步任务

**创建**: `backend/app/tasks/planning_task.py`

```python
import uuid, json
from app.tasks.celery_app import celery_app
from app.agent.graph import trip_graph, extract_trip_from_final_plan
from app.agent.state import AgentState

@celery_app.task(bind=True, max_retries=1)
def run_trip_planning(self, task_id: str, preferences: dict):
    redis = celery_app.backend.client

    initial_state: AgentState = {
        "destination": preferences["destination"],
        "start_date": str(preferences["start_date"]),
        "end_date": str(preferences["end_date"]),
        "budget_min": preferences.get("budget_min", 0),
        "budget_max": preferences.get("budget_max", 100000),
        "currency": preferences.get("currency", "CNY"),
        "preferences": preferences.get("preferences", []),
        "travel_style": preferences.get("travel_style", "balanced"),
        "messages": [], "transport_plan": None, "accommodation_plan": None,
        "attraction_plan": None, "dining_plan": None,
        "final_plan": None, "error": None,
    }

    try:
        redis.hset(f"task:{task_id}", mapping={
            "status": "processing", "progress": "10",
            "agents": json.dumps([
                {"name": "coordinator", "status": "working"},
                {"name": "transport", "status": "idle"},
                {"name": "accommodation", "status": "idle"},
                {"name": "attraction", "status": "idle"},
                {"name": "dining", "status": "idle"},
                {"name": "strategy", "status": "idle"},
            ]),
        })

        result = trip_graph.invoke(initial_state)

        if result.get("final_plan"):
            trip_data = extract_trip_from_final_plan(result["final_plan"])
            redis.hset(f"task:{task_id}", mapping={
                "status": "completed", "progress": "100",
                "trip_data": json.dumps(trip_data, ensure_ascii=False),
                "agents": json.dumps([
                    {"name": "coordinator", "status": "done"},
                    {"name": "transport", "status": "done"},
                    {"name": "accommodation", "status": "done"},
                    {"name": "attraction", "status": "done"},
                    {"name": "dining", "status": "done"},
                    {"name": "strategy", "status": "done"},
                ]),
            })
        else:
            redis.hset(f"task:{task_id}", mapping={
                "status": "failed", "progress": "0",
                "error": "Agent 规划未产生结果",
            })
    except Exception as e:
        redis.hset(f"task:{task_id}", mapping={
            "status": "failed", "progress": "0", "error": str(e),
        })
        raise
```

---

## Phase 3: API 端点

### Task 3.1: trip API（4 个端点）

**创建**: `backend/app/api/trip.py`
**修改**: `backend/app/api/router.py` — 挂载 trip_router

- [ ] **trip.py**

```python
import uuid, json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.request import PlanRequest
from app.schemas.trip import PlanResponse, TaskStatusOut, TripOut, CancelResponse
from app.services.task_service import create_task, get_task, cancel_task
from app.services.trip_service import create_trip as create_trip_record, get_trip
from app.tasks.planning_task import run_trip_planning

router = APIRouter()

@router.post("/plan", response_model=PlanResponse)
async def plan_trip(req: PlanRequest, db: AsyncSession = Depends(get_db)):
    celery_task = run_trip_planning.delay(str(uuid.uuid4()), req.model_dump(mode="json"))
    task = await create_task(db, req.model_dump(mode="json"), celery_task.id)

    redis = await get_redis()
    await redis.hset(f"task:{task.id}", mapping={
        "status": "pending", "progress": "0",
        "agents": json.dumps([
            {"name": "coordinator", "status": "idle"},
            {"name": "transport", "status": "idle"},
            {"name": "accommodation", "status": "idle"},
            {"name": "attraction", "status": "idle"},
            {"name": "dining", "status": "idle"},
            {"name": "strategy", "status": "idle"},
        ]),
    })
    return PlanResponse(task_id=str(task.id))

@router.get("/planning/{task_id}", response_model=TaskStatusOut)
async def get_planning_status(task_id: uuid.UUID):
    redis = await get_redis()
    data = await redis.hgetall(f"task:{task_id}")
    if not data: raise HTTPException(status_code=404, detail="任务不存在")
    agents = json.loads(data.get("agents", "[]"))
    return TaskStatusOut(
        task_id=str(task_id), status=data.get("status", "pending"),
        progress=int(data.get("progress", 0)), agents=agents,
        trip_id=data.get("trip_id"), error_message=data.get("error"),
    )

@router.get("/{trip_id}", response_model=TripOut)
async def get_trip_result(trip_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    trip = await get_trip(db, trip_id)
    if not trip: raise HTTPException(status_code=404, detail="行程不存在")
    return TripOut(
        id=str(trip.id), destination=trip.destination, dates=trip.dates,
        budget=trip.budget, preferences=trip.preferences,
        travel_style=trip.travel_style, days=trip.data.get("days", []),
        summary=trip.summary,
    )

@router.post("/{task_id}/cancel", response_model=CancelResponse)
async def cancel_planning(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await get_task(db, task_id)
    if not task: raise HTTPException(status_code=404, detail="任务不存在")
    await cancel_task(db, task)
    return CancelResponse(success=True)
```

- [ ] **修改 router.py**

```python
from fastapi import APIRouter
from app.api.trip import router as trip_router

api_router = APIRouter()
api_router.include_router(trip_router, prefix="/trip")
```

---

## Phase 4: 前端核心基础设施

### Task 4.1: shadcn/ui 初始化

```bash
cd frontend
npx shadcn@latest init  # TypeScript, Default, Slate, CSS variables: yes
npx shadcn@latest add button card input textarea badge tabs separator label slider calendar popover command
```

---

### Task 4.2: 类型定义 + 工具函数

**创建**: `frontend/src/lib/utils.ts`, `frontend/src/types/api.ts`

- [ ] **utils.ts**

```ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
```

- [ ] **types/api.ts**

```ts
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type AgentStatus = 'idle' | 'working' | 'done' | 'error'
export type AgentType = 'coordinator' | 'transport' | 'accommodation' | 'attraction' | 'dining' | 'strategy'

export interface GeoPoint { lat: number; lng: number }

export interface Activity {
  id: string; type: 'transport' | 'attraction' | 'dining' | 'hotel'
  name: string; start_time: string; end_time: string; duration: number
  location?: GeoPoint; description?: string; tips?: string; image_url?: string
}

export interface DayPlan { day_index: number; date: string; activities: Activity[] }

export interface Trip {
  id: string; destination: string
  dates: { start: string; end: string }
  budget: { min: number; max: number; currency: string }
  preferences: string[]; travel_style: string
  days: DayPlan[]; summary: { total_cost: number; attraction_count: number }
}

export interface AgentInfo { name: string; status: AgentStatus }

export interface TaskStatusResponse {
  task_id: string; status: TaskStatus; progress: number
  agents: AgentInfo[]; trip_id?: string; error_message?: string
}

export interface PlanRequest {
  destination: string; start_date: string; end_date: string
  budget_min: number; budget_max: number; currency: string
  preferences: string[]; travel_style: string
}
```

---

### Task 4.3: API 层 + Zustand Store

**创建**: `frontend/src/shared/api/client.ts`, `queryKeys.ts`, `tripApi.ts`, `frontend/src/shared/stores/useTripStore.ts`

- [ ] **client.ts**

```ts
import axios from 'axios'
import { toast } from 'sonner'

export const apiClient = axios.create({
  baseURL: '/api', timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    toast.error(message)
    return Promise.reject(error)
  }
)
```

- [ ] **queryKeys.ts**

```ts
export const queryKeys = {
  planningTask: (taskId: string) => ['planningTask', taskId] as const,
  tripResult: (tripId: string) => ['tripResult', tripId] as const,
}
```

- [ ] **tripApi.ts**

```ts
import { apiClient } from './client'
import type { PlanRequest, TaskStatusResponse, Trip } from '@/types/api'

export const tripApi = {
  createTrip: (data: PlanRequest) => apiClient.post<{ task_id: string }>('/trip/plan', data).then(r => r.data),
  getPlanningStatus: (taskId: string) => apiClient.get<TaskStatusResponse>(`/trip/planning/${taskId}`).then(r => r.data),
  getTrip: (tripId: string) => apiClient.get<Trip>(`/trip/${tripId}`).then(r => r.data),
  cancelTask: (taskId: string) => apiClient.post<{ success: boolean }>(`/trip/${taskId}/cancel`).then(r => r.data),
}
```

- [ ] **useTripStore.ts**

```ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Trip } from '@/types/api'

interface TripStore {
  currentTaskId: string | null; currentTrip: Trip | null
  setTaskId: (id: string) => void; setTrip: (trip: Trip) => void; reset: () => void
}

export const useTripStore = create<TripStore>()(
  persist(
    (set) => ({
      currentTaskId: null, currentTrip: null,
      setTaskId: (id) => set({ currentTaskId: id }),
      setTrip: (trip) => set({ currentTrip: trip }),
      reset: () => set({ currentTaskId: null, currentTrip: null }),
    }),
    { name: 'trip-store' }
  )
)
```

---

### Task 4.4: 路由系统

**创建**: `frontend/src/router/routes.ts`, `lazyPages.ts`, `guards.tsx`, `index.tsx`, `frontend/src/shared/components/ui/LoadingPage.tsx`

- [ ] **routes.ts**

```ts
export const ROUTES = {
  home: '/', plan: '/plan', planning: '/planning/:taskId',
  trip: '/trip/:tripId', settings: '/settings',
} as const
```

- [ ] **lazyPages.ts**

```ts
import { lazy } from 'react'
export const HomePage = lazy(() => import('@/features/home/HomePage'))
export const PlanInputPage = lazy(() => import('@/features/plan-input/PlanInputPage'))
export const PlanningPage = lazy(() => import('@/features/planning/PlanningPage'))
export const TripResultPage = lazy(() => import('@/features/trip-result/TripResultPage'))
export const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
export const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))
```

- [ ] **guards.tsx**

```tsx
import { Navigate } from 'react-router-dom'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = true // MVP 透传
  if (!isAuthenticated) return <Navigate to="/" replace />
  return <>{children}</>
}
```

- [ ] **LoadingPage.tsx**

```tsx
import { Loader2 } from 'lucide-react'

export function LoadingPage() {
  return (
    <div className="flex h-screen items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  )
}
```

- [ ] **router/index.tsx**

```tsx
import { Suspense } from 'react'
import { createBrowserRouter, RouterProvider as ReactRouterProvider } from 'react-router-dom'
import { AppLayout } from '@/shared/components/layout/AppLayout'
import { LoadingPage } from '@/shared/components/ui/LoadingPage'
import { ROUTES } from './routes'
import { HomePage, PlanInputPage, PlanningPage, TripResultPage, SettingsPage, NotFoundPage } from './lazyPages'

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.home, element: <HomePage /> },
      { path: ROUTES.plan, element: <PlanInputPage /> },
      { path: ROUTES.planning, element: <PlanningPage /> },
      { path: ROUTES.trip, element: <TripResultPage /> },
      { path: ROUTES.settings, element: <SettingsPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

export function RouterProvider() {
  return (
    <Suspense fallback={<LoadingPage />}>
      <ReactRouterProvider router={router} />
    </Suspense>
  )
}
```

---

### Task 4.5: 布局组件

**创建**: `frontend/src/shared/components/layout/Header.tsx`, `Footer.tsx`, `AppLayout.tsx`, `frontend/src/pages/SettingsPage.tsx`, `NotFoundPage.tsx`

- [ ] **Header.tsx**

```tsx
import { Link } from 'react-router-dom'
import { MapPin } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/router/routes'

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link to={ROUTES.home} className="flex items-center gap-2 text-xl font-bold">
          <MapPin className="h-6 w-6 text-primary" /> <span>旅程AI</span>
        </Link>
        <nav className="flex items-center gap-4">
          <Button variant="ghost" asChild><Link to={ROUTES.plan}>开始规划</Link></Button>
        </nav>
      </div>
    </header>
  )
}
```

- [ ] **Footer.tsx**

```tsx
export function Footer() {
  return (
    <footer className="border-t py-8">
      <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
        <p>旅程AI — 智能旅行行程规划平台</p>
        <p className="mt-1">Powered by Multi-Agent AI</p>
      </div>
    </footer>
  )
}
```

- [ ] **AppLayout.tsx**

```tsx
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Footer } from './Footer'

export function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1"><Outlet /></main>
      <Footer />
    </div>
  )
}
```

- [ ] **SettingsPage.tsx** (占位)

```tsx
export default function SettingsPage() {
  return (
    <div className="container mx-auto px-4 py-16 text-center">
      <h1 className="text-2xl font-bold">设置</h1>
      <p className="mt-2 text-muted-foreground">功能开发中...</p>
    </div>
  )
}
```

- [ ] **NotFoundPage.tsx**

```tsx
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/router/routes'

export default function NotFoundPage() {
  return (
    <div className="container mx-auto flex flex-col items-center justify-center px-4 py-32">
      <h1 className="text-6xl font-bold text-muted-foreground">404</h1>
      <p className="mt-4 text-lg text-muted-foreground">页面不存在</p>
      <Button className="mt-8" asChild><Link to={ROUTES.home}>返回首页</Link></Button>
    </div>
  )
}
```

---

## Phase 5: 前端页面

### Task 5.1: 首页

**创建**: `frontend/src/features/home/HomePage.tsx` 及其子组件

- [ ] **HomePage.tsx**

```tsx
import { HeroSection } from './components/HeroSection'
import { FeatureSection } from './components/FeatureSection'
import { HowItWorks } from './components/HowItWorks'

export default function HomePage() {
  return (<><HeroSection /><FeatureSection /><HowItWorks /></>)
}
```

- [ ] **HeroSection.tsx**

```tsx
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ArrowRight, Sparkles } from 'lucide-react'
import { ROUTES } from '@/router/routes'

export function HeroSection() {
  const navigate = useNavigate()
  return (
    <section className="container mx-auto px-4 py-24 text-center">
      <div className="mx-auto inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm text-muted-foreground">
        <Sparkles className="h-4 w-4" /> AI 多 Agent 协作规划
      </div>
      <h1 className="mx-auto mt-6 max-w-3xl text-5xl font-bold leading-tight tracking-tight">
        只需说出你的想法，AI 为你规划<span className="text-primary">完美旅程</span>
      </h1>
      <p className="mx-auto mt-6 max-w-xl text-lg text-muted-foreground">
        输入目的地和偏好，多个 AI Agent 并行协作，秒级生成包含交通、住宿、景点、美食的完整行程方案
      </p>
      <Button size="lg" className="mt-8 gap-2 text-base" onClick={() => navigate(ROUTES.plan)}>
        开始规划行程 <ArrowRight className="h-4 w-4" />
      </Button>
    </section>
  )
}
```

- [ ] **FeatureSection.tsx**

```tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Brain, RefreshCw, CreditCard } from 'lucide-react'

const features = [
  { icon: Brain, title: 'AI 智能规划', description: '多 Agent 并行协作，从交通到美食，全方位覆盖你的旅行需求' },
  { icon: RefreshCw, title: '实时动态调整', description: '旅途中遇到变化？AI 自动监测并推荐最优调整方案' },
  { icon: CreditCard, title: '一站式预订', description: '行程直接转化为可预订订单，多平台比价一键下单' },
]

export function FeatureSection() {
  return (
    <section className="bg-muted/50 py-20">
      <div className="container mx-auto px-4">
        <h2 className="text-center text-3xl font-bold">为什么选择旅程AI</h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {features.map((f) => (
            <Card key={f.title}>
              <CardHeader>
                <f.icon className="h-10 w-10 text-primary" />
                <CardTitle>{f.title}</CardTitle>
                <p className="text-sm text-muted-foreground">{f.description}</p>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **HowItWorks.tsx**

```tsx
export function HowItWorks() {
  const steps = [
    { step: '01', title: '输入需求', desc: '告诉我们目的地、日期、预算和偏好' },
    { step: '02', title: 'AI 规划', desc: '多个 Agent 同时工作，秒级生成方案' },
    { step: '03', title: '轻松出行', desc: '确认行程，一键预订，旅途无忧' },
  ]
  return (
    <section className="py-20">
      <div className="container mx-auto px-4">
        <h2 className="text-center text-3xl font-bold">三步开启旅程</h2>
        <div className="mt-12 grid gap-8 md:grid-cols-3">
          {steps.map((s) => (
            <div key={s.step} className="text-center">
              <span className="text-4xl font-bold text-primary/30">{s.step}</span>
              <h3 className="mt-2 text-xl font-semibold">{s.title}</h3>
              <p className="mt-1 text-muted-foreground">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
```

---

### Task 5.2: 需求输入页

**创建**: `frontend/src/features/plan-input/PlanInputPage.tsx`, `hooks/usePlanForm.ts`, 6 个表单组件

- [ ] **usePlanForm.ts**

```ts
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { tripApi } from '@/shared/api/tripApi'
import { useTripStore } from '@/shared/stores/useTripStore'
import type { PlanRequest } from '@/types/api'

const INITIAL: PlanRequest = {
  destination: '', start_date: '', end_date: '',
  budget_min: 0, budget_max: 50000, currency: 'CNY',
  preferences: [], travel_style: 'balanced',
}

export function usePlanForm() {
  const [form, setForm] = useState<PlanRequest>(INITIAL)
  const navigate = useNavigate()
  const setTaskId = useTripStore((s) => s.setTaskId)

  const mutation = useMutation({
    mutationFn: tripApi.createTrip,
    onSuccess: (data) => { setTaskId(data.task_id); navigate(`/planning/${data.task_id}`) },
    onError: () => toast.error('创建规划失败，请重试'),
  })

  return { form, setForm, submit: () => mutation.mutate(form), isLoading: mutation.isPending }
}
```

- [ ] **PlanInputPage.tsx**

```tsx
import { usePlanForm } from './hooks/usePlanForm'
import { DestinationInput } from './components/DestinationInput'
import { DateRangePicker } from './components/DateRangePicker'
import { BudgetSelector } from './components/BudgetSelector'
import { PreferenceTags } from './components/PreferenceTags'
import { TravelStyleSelect } from './components/TravelStyleSelect'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'

export default function PlanInputPage() {
  const { form, setForm, submit, isLoading } = usePlanForm()
  return (
    <div className="container mx-auto max-w-2xl px-4 py-12">
      <Card>
        <CardHeader><CardTitle className="text-2xl">设计你的旅程</CardTitle></CardHeader>
        <CardContent className="space-y-6">
          <DestinationInput value={form.destination} onChange={(v) => setForm({ ...form, destination: v })} />
          <DateRangePicker start={form.start_date} end={form.end_date}
            onChange={(s, e) => setForm({ ...form, start_date: s, end_date: e })} />
          <BudgetSelector min={form.budget_min} max={form.budget_max}
            onChange={(min, max) => setForm({ ...form, budget_min: min, budget_max: max })} />
          <PreferenceTags selected={form.preferences}
            onChange={(p) => setForm({ ...form, preferences: p })} />
          <TravelStyleSelect value={form.travel_style}
            onChange={(v) => setForm({ ...form, travel_style: v })} />
          <Button className="w-full" size="lg"
            disabled={!form.destination || !form.start_date || isLoading} onClick={submit}>
            {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            开始 AI 规划
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

- [ ] **DestinationInput.tsx**

```tsx
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function DestinationInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="space-y-2">
      <Label>目的地</Label>
      <Input placeholder="例如：东京、巴黎、云南..." value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  )
}
```

- [ ] **DateRangePicker.tsx**

```tsx
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function DateRangePicker({ start, end, onChange }: { start: string; end: string; onChange: (s: string, e: string) => void }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="space-y-2"><Label>出发日期</Label><Input type="date" value={start} onChange={(e) => onChange(e.target.value, end)} /></div>
      <div className="space-y-2"><Label>返程日期</Label><Input type="date" value={end} onChange={(e) => onChange(start, e.target.value)} /></div>
    </div>
  )
}
```

- [ ] **BudgetSelector.tsx**

```tsx
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export function BudgetSelector({ min, max, onChange }: { min: number; max: number; onChange: (min: number, max: number) => void }) {
  return (
    <div className="space-y-2">
      <Label>预算范围 (元)</Label>
      <div className="flex items-center gap-2">
        <Input type="number" placeholder="最低" value={min || ''} onChange={(e) => onChange(Number(e.target.value), max)} />
        <span className="text-muted-foreground">—</span>
        <Input type="number" placeholder="最高" value={max || ''} onChange={(e) => onChange(min, Number(e.target.value))} />
      </div>
    </div>
  )
}
```

- [ ] **PreferenceTags.tsx**

```tsx
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'

const TAGS = ['文化历史', '自然风景', '美食', '购物', '探险', '摄影', '亲子', '浪漫']

export function PreferenceTags({ selected, onChange }: { selected: string[]; onChange: (v: string[]) => void }) {
  const toggle = (tag: string) => {
    selected.includes(tag) ? onChange(selected.filter(t => t !== tag)) : onChange([...selected, tag])
  }
  return (
    <div className="space-y-2">
      <Label>兴趣偏好（可多选）</Label>
      <div className="flex flex-wrap gap-2">
        {TAGS.map((tag) => (
          <Badge key={tag} variant={selected.includes(tag) ? 'default' : 'outline'}
            className="cursor-pointer px-4 py-2 text-sm" onClick={() => toggle(tag)}>{tag}</Badge>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **TravelStyleSelect.tsx**

```tsx
import { Label } from '@/components/ui/label'

const STYLES = [
  { value: 'relaxed', label: '轻松休闲', desc: '每天 2-3 个景点' },
  { value: 'balanced', label: '适中平衡', desc: '有玩有闲' },
  { value: 'compact', label: '紧凑充实', desc: '打卡更多景点' },
]

export function TravelStyleSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="space-y-2">
      <Label>旅行节奏</Label>
      <div className="grid grid-cols-3 gap-2">
        {STYLES.map((s) => (
          <button key={s.value} type="button"
            className={`rounded-lg border p-3 text-left transition ${value === s.value ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'hover:border-muted-foreground/30'}`}
            onClick={() => onChange(s.value)}>
            <div className="text-sm font-medium">{s.label}</div>
            <div className="text-xs text-muted-foreground">{s.desc}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
```

---

### Task 5.3: 规划进度页

**创建**: `frontend/src/features/planning/PlanningPage.tsx` + 3 个子组件

- [ ] **PlanningPage.tsx**

```tsx
import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { tripApi } from '@/shared/api/tripApi'
import { queryKeys } from '@/shared/api/queryKeys'
import { useTripStore } from '@/shared/stores/useTripStore'
import { ProgressIndicator } from './components/ProgressIndicator'
import { AgentStatusCard } from './components/AgentStatusCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, XCircle } from 'lucide-react'

export default function PlanningPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const reset = useTripStore((s) => s.reset)

  const { data, error } = useQuery({
    queryKey: queryKeys.planningTask(taskId!),
    queryFn: () => tripApi.getPlanningStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'completed' || status === 'failed') return false
      return 2000
    },
  })

  const cancelMutation = useMutation({ mutationFn: () => tripApi.cancelTask(taskId!) })

  useEffect(() => {
    if (data?.status === 'completed' && data?.trip_id) {
      setTimeout(() => navigate(`/trip/${data.trip_id}`), 1500)
    }
  }, [data?.status, data?.trip_id, navigate])

  const handleCancel = () => { cancelMutation.mutate(); reset(); navigate('/plan') }

  if (error) {
    return (
      <div className="container mx-auto max-w-lg px-4 py-16 text-center">
        <XCircle className="mx-auto h-12 w-12 text-destructive" />
        <h2 className="mt-4 text-xl font-semibold">规划失败</h2>
        <p className="mt-2 text-muted-foreground">请稍后重试</p>
        <Button className="mt-6" onClick={() => navigate('/plan')}>重新规划</Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto max-w-lg px-4 py-12">
      <Card>
        <CardHeader><CardTitle className="text-center">AI 正在为你规划行程</CardTitle></CardHeader>
        <CardContent className="space-y-6">
          {data?.status === 'completed' && <p className="text-center text-sm text-green-600">规划完成，即将跳转...</p>}
          <ProgressIndicator progress={data?.progress ?? 0} />
          <div className="grid grid-cols-2 gap-3">
            {data?.agents?.map((agent) => <AgentStatusCard key={agent.name} agent={agent} />)}
          </div>
          <Button variant="outline" className="w-full" onClick={handleCancel} disabled={cancelMutation.isPending}>
            {cancelMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            取消规划
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
```

- [ ] **ProgressIndicator.tsx**

```tsx
export function ProgressIndicator({ progress }: { progress: number }) {
  return (
    <div className="space-y-2">
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary transition-all duration-500" style={{ width: `${progress}%` }} />
      </div>
      <p className="text-center text-xs text-muted-foreground">
        {progress < 30 && '正在分析你的需求...'}
        {progress >= 30 && progress < 60 && '各 Agent 并行规划中...'}
        {progress >= 60 && progress < 90 && '优化整合行程方案...'}
        {progress >= 90 && '即将完成...'}
      </p>
    </div>
  )
}
```

- [ ] **AgentStatusCard.tsx**

```tsx
import { Card } from '@/components/ui/card'
import { Loader2, CheckCircle2, Circle, AlertCircle } from 'lucide-react'
import type { AgentInfo } from '@/types/api'

const AGENT_LABELS: Record<string, string> = {
  coordinator: '协调分析', transport: '交通出行', accommodation: '住宿选择',
  attraction: '景点规划', dining: '美食推荐', strategy: '策略优化',
}

const icons: Record<string, React.ReactNode> = {
  working: <Loader2 className="h-4 w-4 animate-spin text-primary" />,
  done: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  error: <AlertCircle className="h-4 w-4 text-destructive" />,
  idle: <Circle className="h-4 w-4 text-muted-foreground" />,
}

export function AgentStatusCard({ agent }: { agent: AgentInfo }) {
  return (
    <Card className="flex items-center gap-3 p-3">
      {icons[agent.status]}
      <div>
        <p className="text-sm font-medium">{AGENT_LABELS[agent.name] || agent.name}</p>
        <p className="text-xs text-muted-foreground">
          {agent.status === 'working' && '规划中...'}
          {agent.status === 'done' && '已完成'}
          {agent.status === 'idle' && '等待中'}
          {agent.status === 'error' && '出错'}
        </p>
      </div>
    </Card>
  )
}
```

---

### Task 5.4: 行程结果页

**创建**: `frontend/src/features/trip-result/TripResultPage.tsx` + 7 个子组件

- [ ] **TripResultPage.tsx**

```tsx
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { tripApi } from '@/shared/api/tripApi'
import { queryKeys } from '@/shared/api/queryKeys'
import { useTripStore } from '@/shared/stores/useTripStore'
import { TripHeader } from './components/TripHeader'
import { DayTabs } from './components/DayTabs'
import { DayTimeline } from './components/DayTimeline'
import { TripActions } from './components/TripActions'
import { TripSidebar } from './components/TripSidebar'
import { Button } from '@/components/ui/button'
import { LoadingPage } from '@/shared/components/ui/LoadingPage'
import { AlertCircle } from 'lucide-react'

export default function TripResultPage() {
  const { tripId } = useParams<{ tripId: string }>()
  const navigate = useNavigate()
  const setTrip = useTripStore((s) => s.setTrip)
  const [activeDay, setActiveDay] = useState(0)

  const { data: trip, isLoading, error } = useQuery({
    queryKey: queryKeys.tripResult(tripId!),
    queryFn: async () => { const d = await tripApi.getTrip(tripId!); setTrip(d); return d },
    enabled: !!tripId,
  })

  if (isLoading) return <LoadingPage />

  if (error || !trip) {
    return (
      <div className="container mx-auto max-w-lg px-4 py-16 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
        <h2 className="mt-4 text-xl font-semibold">加载失败</h2>
        <Button className="mt-6" onClick={() => navigate('/plan')}>重新规划</Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <TripHeader trip={trip} />
      <div className="mt-8 flex gap-8">
        <div className="flex-1">
          <DayTabs days={trip.days} activeDay={activeDay} onSelect={setActiveDay} />
          <DayTimeline day={trip.days[activeDay]} />
        </div>
        <TripSidebar trip={trip} />
      </div>
      <TripActions onReplan={() => { useTripStore.getState().reset(); navigate('/plan') }} />
    </div>
  )
}
```

- [ ] **TripHeader.tsx**

```tsx
import { Calendar, MapPin, Wallet } from 'lucide-react'
import type { Trip } from '@/types/api'

export function TripHeader({ trip }: { trip: Trip }) {
  return (
    <div>
      <h1 className="text-3xl font-bold">{trip.destination}</h1>
      <div className="mt-3 flex flex-wrap gap-4 text-sm text-muted-foreground">
        <span className="flex items-center gap-1"><Calendar className="h-4 w-4" />{trip.dates.start} — {trip.dates.end}</span>
        <span className="flex items-center gap-1"><Wallet className="h-4 w-4" />¥{trip.summary.total_cost?.toLocaleString()}</span>
        <span className="flex items-center gap-1"><MapPin className="h-4 w-4" />{trip.summary.attraction_count} 个景点</span>
      </div>
    </div>
  )
}
```

- [ ] **DayTabs.tsx**

```tsx
import type { DayPlan } from '@/types/api'

export function DayTabs({ days, activeDay, onSelect }: { days: DayPlan[]; activeDay: number; onSelect: (i: number) => void }) {
  return (
    <div className="flex gap-2 border-b pb-4">
      {days.map((day, i) => (
        <button key={i} className={`rounded-md px-4 py-2 text-sm font-medium transition ${i === activeDay ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted'}`}
          onClick={() => onSelect(i)}>第 {day.day_index} 天</button>
      ))}
    </div>
  )
}
```

- [ ] **DayTimeline.tsx**

```tsx
import { TimelineItem } from './TimelineItem'
import type { DayPlan } from '@/types/api'

export function DayTimeline({ day }: { day: DayPlan }) {
  if (!day) return null
  return (
    <div className="relative mt-6 space-y-0">
      {day.activities?.map((activity, i) => (
        <TimelineItem key={activity.id || i} activity={activity} isLast={i === day.activities.length - 1} />
      ))}
    </div>
  )
}
```

- [ ] **TimelineItem.tsx**

```tsx
import { ActivityCard } from './ActivityCard'
import type { Activity } from '@/types/api'

export function TimelineItem({ activity, isLast }: { activity: Activity; isLast: boolean }) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
          {activity.start_time}
        </div>
        {!isLast && <div className="w-0.5 flex-1 bg-border" />}
      </div>
      <div className={isLast ? '' : 'pb-8'}>
        <ActivityCard activity={activity} />
      </div>
    </div>
  )
}
```

- [ ] **ActivityCard.tsx**

```tsx
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Clock } from 'lucide-react'
import type { Activity } from '@/types/api'

const TYPE_LABELS: Record<string, string> = { attraction: '景点', dining: '餐饮', transport: '交通', hotel: '住宿' }

export function ActivityCard({ activity }: { activity: Activity }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <h4 className="font-semibold">{activity.name}</h4>
            <div className="mt-2 flex flex-wrap gap-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{activity.start_time} - {activity.end_time}</span>
              {activity.description && <span>{activity.description}</span>}
            </div>
            {activity.tips && <p className="mt-2 text-xs text-muted-foreground">Tip: {activity.tips}</p>}
          </div>
          <Badge variant="secondary">{TYPE_LABELS[activity.type] || activity.type}</Badge>
        </div>
      </CardContent>
    </Card>
  )
}
```

- [ ] **TripActions.tsx**

```tsx
import { Button } from '@/components/ui/button'
import { Download, Share2, RotateCcw } from 'lucide-react'

export function TripActions({ onReplan }: { onReplan: () => void }) {
  return (
    <div className="mt-8 flex justify-center gap-4 border-t pt-8">
      <Button variant="outline" disabled><Download className="mr-2 h-4 w-4" />导出 PDF</Button>
      <Button variant="outline" disabled><Share2 className="mr-2 h-4 w-4" />分享行程</Button>
      <Button variant="outline" onClick={onReplan}><RotateCcw className="mr-2 h-4 w-4" />重新规划</Button>
    </div>
  )
}
```

- [ ] **TripSidebar.tsx**

```tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Trip } from '@/types/api'

const styleLabel: Record<string, string> = { relaxed: '轻松', balanced: '适中', compact: '紧凑' }

export function TripSidebar({ trip }: { trip: Trip }) {
  return (
    <aside className="hidden w-72 shrink-0 lg:block">
      <Card>
        <CardHeader><CardTitle className="text-lg">行程概览</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between"><span className="text-muted-foreground">目的地</span><span className="font-medium">{trip.destination}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">天数</span><span className="font-medium">{trip.days.length} 天</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">景点数</span><span className="font-medium">{trip.summary.attraction_count}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">预算</span><span className="font-medium">¥{trip.summary.total_cost?.toLocaleString()}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">风格</span><span className="font-medium">{styleLabel[trip.travel_style] || trip.travel_style}</span></div>
        </CardContent>
      </Card>
    </aside>
  )
}
```

---

## Phase 6: 集成收尾

### Task 6.1: Agent 结果写入数据库

**修改**: `backend/app/tasks/planning_task.py`

在 `run_trip_planning` 的 try 块中，`extract_trip_from_final_plan` 成功后，异步写入 DB：

```python
# 在 trip_data = extract_trip_from_final_plan(result["final_plan"]) 之后追加:
import asyncio
from app.core.database import async_session
from app.services.trip_service import create_trip
from app.services.task_service import get_task as svc_get_task, update_task_status
from app.models.task import TaskStatus as TStatus

async def save_trip_to_db():
    async with async_session() as db:
        task = await svc_get_task(db, uuid.UUID(task_id))
        trip = await create_trip(db, uuid.UUID(task_id), trip_data)
        await update_task_status(db, task, TStatus.completed)
        return trip.id

trip_uuid = asyncio.run(save_trip_to_db())
redis.hset(f"task:{task_id}", "trip_id", str(trip_uuid))
```

### Task 6.2: 验证前端构建

```bash
cd frontend && npm run build
```

确认 TypeScript 编译无报错。

### Task 6.3: 验证后端启动

```bash
cd backend
docker compose up -d postgres redis
pip install -r requirements.txt
cp .env.example .env  # 填入 DEEPSEEK_API_KEY
uvicorn main:app --reload
```

确认 `GET /api/health` 返回 `{"status": "ok"}`。

---

## 实现统计

| Phase | 文件数 | 说明 |
|-------|--------|------|
| Phase 0 | ~15 | 两个项目脚手架 |
| Phase 1 | 9 | 后端核心链路 |
| Phase 2 | 9 | Agent 引擎（6 Agent + graph + celery） |
| Phase 3 | 2 | API 端点 |
| Phase 4 | 12 | 前端核心（router/api/store/layout） |
| Phase 5 | 25+ | 4 个页面组件 |
| Phase 6 | 3 | 集成验证 |
| **总计** | **~75 文件** | |

**并行建议**: Phase 1-3（后端）和 Phase 4（前端核心）可同时开工，Phase 5 前端页面在前端核心完成后顺序构建。
