# 旅程AI — 智能旅行规划平台

基于多智能体协作的 AI 旅行规划平台。输入目的地、日期、预算和偏好，AI 自动生成完整的每日行程（交通、住宿、景点、餐饮），并配有交互式地图、智能旅行伙伴和知识学习系统。

## 技术栈

| 层 | 后端 | 前端 |
|---|------|------|
| 框架 | FastAPI (Python) | React 18 + TypeScript |
| 数据 | SQLAlchemy 2.0 + PostgreSQL/SQLite | TanStack React Query |
| 缓存/队列 | Redis + Celery | Zustand |
| AI | DeepSeek + LangChain | — |
| 向量库 | ChromaDB + BGE 嵌入 | — |
| UI | — | shadcn/ui + Tailwind CSS |
| 地图 | 高德地图 API | @amap/amap-jsapi-loader |
| 构建 | — | Vite 6 |

## 功能

- **AI 行程规划** — 多智能体并行协作：协调 → (交通 ‖ 住宿 ‖ 景点 ‖ 餐饮) → 策略整合
- **智能澄清** — 信息不足时以对话方式追问
- **目的地灵感** — 根据偏好和预算推荐旅行目的地
- **活动替换** — 点击「换一个」AI 实时生成替代方案
- **天气 + 穿搭建议** — 集成和风天气 API，AI 生成每日穿搭
- **地图可视化** — 高德地图展示行程路线和 POI 标记
- **旅行伙伴「小智」** — Live2D/SVG 角色，随目的地换装，可对话
- **知识学习** — 提交小红书/马蜂窝等链接，AI 抓取摘要并索引到向量库
- **多会话聊天** — 按行程分组的独立对话，自动提取偏好

## 项目结构

```
├── backend/                  # Python FastAPI 后端
│   ├── app/
│   │   ├── agent/            # AI 智能体（协调、交通、住宿、景点、餐饮、策略）
│   │   ├── api/              # REST API 路由
│   │   ├── core/             # 基础设施（数据库、LLM、认证、Redis）
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── schemas/          # Pydantic 请求/响应模型
│   │   ├── services/         # 业务逻辑（地理编码、天气、抓取、嵌入）
│   │   └── tasks/            # Celery 异步任务
│   ├── main.py               # 应用入口
│   └── requirements.txt
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── features/         # 功能模块（首页、行程输入、结果、知识库等）
│   │   ├── shared/           # 共享层（API 客户端、状态管理、布局组件）
│   │   ├── components/ui/    # shadcn/ui 组件
│   │   └── router/           # 路由配置 + 懒加载
│   ├── vite.config.ts
│   └── package.json
├── docs/                     # 产品文档
└── docker-compose.yml        # PostgreSQL + Redis
```

## 快速开始

### 要求

- Python 3.11+
- Node.js 18+
- Docker（可选，用于 PostgreSQL + Redis）

### 后端

```bash
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 等密钥

# 创建测试用户
python seed.py

# 启动服务 (http://localhost:8000)
python main.py
```

### 前端

```bash
cd frontend
npm install

# 启动开发服务器 (http://localhost:5173)
npm run dev
```

### 基础设施（可选，生产模式）

```bash
docker-compose up -d    # 启动 PostgreSQL + Redis
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

### 测试账号

- 用户名：`test`
- 密码：`123456`

## 环境变量

### 后端 (`backend/.env`)

| 变量 | 说明 | 必需 |
|------|------|------|
| `DATABASE_URL` | 数据库连接字符串 | 是 |
| `REDIS_URL` | Redis 连接字符串 | 否（开发模式） |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 是 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | 是 |
| `DEEPSEEK_MODEL` | 模型名称 | 是 |
| `SENIVERSE_API_KEY` | 和风天气 API 密钥 | 否 |
| `AMAP_API_KEY` | 高德地图 API 密钥 | 否 |
| `SECRET_KEY` | JWT 签名密钥 | 是 |

### 前端 (`frontend/.env`)

| 变量 | 说明 |
|------|------|
| `VITE_AMAP_KEY` | 高德地图 JS API 密钥 |
| `VITE_AMAP_VERSION` | 高德地图 API 版本 |

## API 文档

启动后端后访问 http://localhost:8000/docs 查看 Swagger UI。
<img width="1860" height="915" alt="3a9110614c30f85809ea94639da64d8e" src="https://github.com/user-attachments/assets/4aaf315f-d57a-4740-b28d-2e98f2b2d9b9" />

<img width="1369" height="810" alt="aeba8d7a2f663fd5081a0bf10e02ac2e" src="https://github.com/user-attachments/assets/f8588083-448d-4d00-9fdd-dcfb2b6c05e1" />
<img width="1860" height="915" alt="de2fe1286ead96a1ff4a2b61bff79b00" src="https://github.com/user-attachments/assets/99c6baa9-d467-45bb-a14c-6346b660eb24" />
<img width="1860" height="915" alt="98ca3037c27a094b8280631b6ffdd70c" src="https://github.com/user-attachments/assets/f39cc06f-472c-4e3a-b91d-1027e3aab913" />
<img width="1860" height="915" alt="3cf339e0d41b3e447556555b0466d1d3" src="https://github.com/user-attachments/assets/12ab9cd9-0136-4e32-986d-54b4650cc1e6" />


