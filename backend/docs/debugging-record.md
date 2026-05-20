# AI 旅行规划系统排错记录

## 时间线总览

```
阶段1: Agent 规划超时 → 阶段2: 模型幻觉问题 → 阶段3: RAG 策略优化
    → 阶段4: chromadb C 扩展崩溃 → 阶段5: 聊天 500 错误修复
    → 阶段6: 完整集成测试通过
```

---

## 阶段1: 4个 AI Agent 规划超时导致死锁

### 现象

调用 `/api/v1/trip/plan` 时，Coordinator Agent 分配任务给 4 个子 Agent（transport、accommodation、attraction、dining）后，进度卡在 25%，子 Agent 全部处于 `working` 状态但永远不返回结果。前端显示规划超时。

### 根因分析

6 个文件中 `AsyncOpenAI` 客户端实例化时没有设置 `timeout` 参数：

```python
# 问题代码
import httpx
_client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
    http_client=httpx.AsyncClient(proxy=None, trust_env=False),  # 无 timeout!
)
```

`httpx.AsyncClient` 默认 `timeout=5.0` 仅适用于连接阶段，而 `AsyncOpenAI` 包装后未正确传递读取超时。在大模型推理延迟较高（>30s）时，请求会无限期阻塞，导致 Agent 永久挂起。

### 受影响文件（6 个）

| 文件 | 角色 |
|------|------|
| `app/agent/context_engine.py` | 聊天上下文引擎 |
| `app/agent/chat_agent.py` | AI 伴侣对话 |
| `app/agent/inspire.py` | 灵感推荐 |
| `app/agent/learn_agent.py` | 偏好学习 |
| `app/services/preference_service.py` | 偏好提取服务 |
| `app/services/summarize.py` | 摘要服务 |

### 修复方案

1. 在 `app/core/llm.py` 中创建共享 HTTP 客户端工厂：

```python
LLM_TIMEOUT = httpx.Timeout(60.0, connect=10.0, read=50.0)
LLM_MAX_RETRIES = 2

def _get_http_client() -> httpx.AsyncClient:
    global _shared_http_client
    if _shared_http_client is None:
        _shared_http_client = httpx.AsyncClient(
            proxy=None, trust_env=False, timeout=LLM_TIMEOUT,
        )
    return _shared_http_client
```

2. 所有 6 个文件统一使用延迟初始化模式：

```python
_client: Optional[object] = None

def _get_client():
    global _client
    if _client is None:
        from openai import AsyncOpenAI
        _client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            max_retries=LLM_MAX_RETRIES,
            timeout=LLM_TIMEOUT,
            http_client=_get_http_client(),
        )
    return _client
```

### 额外发现：双重 await 错误

```python
# 错误代码
response = await (await _get_client()).chat.completions.create(...)

# 正确代码
response = await _get_client().chat.completions.create(...)
```

`_get_client()` 是同步函数，不能 `await`。虽然这个语法错误在 Python 中会被运行时拦截，但在某些执行路径下会被静默跳过（因为 `AsyncOpenAI` 对象恰好不是 awaitable），导致走到不同的错误分支。修正时需要注意不同缩进层级的替换。

---

## 阶段2: 模型切换 — 降低幻觉与编造

### 现象

原始模型 `deepseek-chat` 生成的行程包含大量虚构数据：
- 编造不存在的航班号（如 "CA4194 北京→成都"）
- 虚构餐厅价格（如 "人均 500 元"）
- 编造具体的门票价格、营业时间

### 根因分析

1. **System Prompt 自身命令模型编造**：
   ```python
   # 问题 Prompt
   "包含具体信息（价格、时间、地址）"  # 直接要求模型编造！
   ```

2. **温度过高**：用户聊天 0.7、Agent 0.7，随机性过高，增加幻觉概率。

3. **`deepseek-chat` 模型幻觉率较高**：该模型在缺乏 grounding 数据时倾向于自信地编造。

### 修复方案

**A. 模型切换**: `deepseek-chat` → `deepseek-v4-flash`

**B. 温度调低**:
| 场景 | 修改前 | 修改后 |
|------|--------|--------|
| 用户聊天 (chat_with_context) | 0.7 | 0.3 |
| 灵感推荐 (inspire) | 0.8 | 0.4 |
| JSON 结构化输出 | 0.3 | 0.2 |
| Agent 规划 | 0.7 | 0.3 |

**C. 反幻觉 System Prompt 重写**:
```python
SYSTEM_PROMPT = """你是"小智"，一位AI旅行伙伴。
## 回答规范
- 简洁实用，优先使用已学知识和当前行程中的真实信息
- 可以给出旅行建议和方向性指导，但绝对禁止编造具体的价格、时间、地址、电话
- 不确定的信息必须诚实说明"建议出发前查询最新信息"，不要装作知道
- 适当使用emoji
"""
```

关键改动：从 "包含具体信息" 变为 "绝对禁止编造具体信息"。

**D. 关键踩坑**: pydantic-settings 的 `.env` 文件优先级高于 `config.py` 默认值。只改 `config.py` 中 `deepseek_model: str = "deepseek-v4-flash"` 无效，因为 `.env` 中 `DEEPSEEK_MODEL=deepseek-chat` 会覆盖。必须同步更新 `.env`。

---

## 阶段3: RAG 策略优化

### 背景

单纯依赖模型降温和 prompt 约束无法完全消除幻觉。需要为模型提供真实的旅行知识作为回答依据。

### RAG 架构设计

```
用户消息 → 查询重写(含目的地) → BM25 混合检索 → Top-N 文档
    → 注入 System Prompt → DeepSeek 生成回答 → 用户
```

### 实现细节

**A. 嵌入模型**: ModelScope BGE-small-zh-v1.5
- 维度: 512
- 针对中文检索优化
- 本地运行，无需外部 API

**B. 文本分块策略**:
- 块大小: 512 字符
- 基于句子边界的重叠分块（避免切断语义）
- 块重叠: ~100 字符

**C. 检索策略**: BM25 + 向量相似度混合检索
- BM25 用于关键词精确匹配（中文二元组分词）
- 向量相似度用于语义匹配
- 两阶段检索: 先按 user_id 过滤，无结果则放宽到全局搜索

**D. 上下文注入**: 在 `context_engine.py` 的 `build_context()` 中作为 P4 优先级层：
```
P1 当前行程 > P2 已学偏好 > P3 对话历史 > P4 RAG 知识
```

### 核心代码

```python
async def _retrieve_knowledge(query: str, user_id: str, destination: str) -> str:
    store = get_vector_store()
    search_query = f"{destination} {query}" if destination not in query else query

    # 优先用户相关
    results = store.search(search_query, n_results=3, where={"user_id": user_id})
    # 回退到全局搜索
    if not results:
        results = store.search(search_query, n_results=2)

    if not results:
        return ""
    return "## 相关知识\n" + "\n".join(
        f"{i}. {r['document'][:200]}" for i, r in enumerate(results, 1)
    )
```

---

## 阶段4: chromadb C 扩展 Windows 崩溃 → 纯 Python 向量数据库

### 现象

```
onnxruntime DLL load failed
chromadb PersistentClient segfault (exit code 139)
```

chromadb 内部依赖 onnxruntime，onnxruntime 的 C 扩展在 Windows 环境下与 Python 3.12 存在 DLL 兼容性问题，导致进程直接崩溃（segfault），无 Python 异常堆栈。

### 根因

chromadb 的以下组件依赖原生 C 扩展：
- `onnxruntime` — 用于默认嵌入模型 (all-MiniLM-L6-v2)
- `hnswlib` — 用于 HNSW 索引
- 两者在 Windows + Python 3.12 组合下均有兼容性报告

### 修复方案: 完全替换为纯 Python 实现

**A. 向量存储** (`app/services/vector_store.py`):
- 使用 `numpy` 进行向量相似度计算（余弦相似度）
- JSON 文件持久化（无需任何 C 扩展或数据库服务）
- 数据结构: `{"documents": [...], "embeddings": [...], "metadata": [...]}`

**B. 嵌入模型** (`app/services/embedding_service.py`):
- 主模型: ModelScope BGE-small-zh-v1.5
- 降级链: ModelScope → HuggingFace BGE → MiniLM → SimpleChinese
- 全部为纯 Python/transformers 实现

**C. 检索**:
- 向量检索: cosine_similarity + numpy top-k
- BM25 混合检索: Python 标准库实现的 TF-IDF 评分
- 中文分词: 二元组 (bigram) 分词器，纯 Python

### 影响

- 无需任何 C 扩展或外部数据库服务
- 内存占用 <100MB（512 维 x 少量文档）
- 适合中小规模向量库（<10K 文档）
- Windows/Linux/macOS 全平台兼容

---

## 阶段5: 聊天 500 错误修复链

### 现象

前端 AI 对话返回 `POST /api/v1/chat/send 500 (Internal Server Error)`。

### 根因链（4 个独立问题叠加）

**问题1: timezone 导入缺失** (`app/models/chat.py:19`)

```python
# 错误
from datetime import datetime  # 缺少 timezone

# 修复
from datetime import datetime, timezone
```

`ChatSession.started_at` 默认值使用 `datetime.now(timezone.utc)`，`timezone` 未导入导致 `NameError`，ChatSession INSERT 时崩溃 → 聊天接口 500。

**问题2: 双重 await 错误** — 见阶段1，`await (await _get_client())` 在聊天执行路径中触发 TypeError。

**问题3: .env 模型名覆盖** — `config.py` 已改为 `deepseek-v4-flash` 但 `.env` 仍为 `deepseek-chat`，导致聊天使用错误模型、返回格式异常。

**问题4: 端口残留旧进程** — 前端 Vite 代理 → `localhost:8001`，该端口上运行的是旧代码进程 (PID 11072)，修复后的代码未生效。需要 `taskkill` 旧进程后重启。

### 端口配置

| 组件 | 端口 |
|------|------|
| 后端 (FastAPI) | 8001 |
| 前端 (Vite Dev Server) | 5173 → 代理到 8001 |

---

## 阶段6: 完整集成测试验证

### 测试流程

```
1. 登录 (POST /api/v1/auth/login) → 200 OK
2. 行程规划 (POST /api/v1/trip/plan) → 200 OK
   - 6 个 Agent 协作完成:
     coordinator → transport → accommodation → attraction → dining → strategy
   - 进度: 10% → 25% → 60% → 90% → 100%
3. AI 对话 (POST /api/v1/chat/send) → 200 OK
   - 回复中包含诚实声明: "建议出发前查询最新信息"
   - 未编造具体价格、时间、地址
4. 偏好学习 → 向量存储 → RAG 检索 → 200 OK
```

### 最终配置

| 配置项 | 值 |
|--------|-----|
| 模型 | `deepseek-v4-flash` |
| 用户聊天温度 | 0.3 |
| JSON 输出温度 | 0.2 |
| HTTP 超时 | 连接 10s, 读取 50s, 总计 60s |
| 最大重试 | 2 |
| 向量维度 | 512 (BGE-small-zh) |
| 检索 Top-N | 3 (用户范围), 2 (全局) |

---

## 经验教训

1. **httpx.AsyncClient 超时是必选项**：不设超时意味着无限阻塞，在分布式 Agent 系统中会导致级联死锁。
2. **pydantic-settings .env 优先级**：`.env` 覆盖代码默认值，改配置时必须同步检查 `.env` 文件。
3. **System Prompt 是双刃剑**：要求模型"包含具体信息"等同于命令它编造，应改为"绝对禁止编造不确定信息"。
4. **Windows + C 扩展组合需谨慎**：chromadb/onnxruntime 在 Windows 下有已知兼容性问题，纯 Python 实现虽慢但可靠。
5. **端口残留进程**：重启服务前先检查旧进程是否存活，避免修改代码在旧进程上不生效的调试陷阱。
6. **RAG 是反幻觉的有效手段**：为模型提供真实知识比单纯 prompt 约束更可靠。
