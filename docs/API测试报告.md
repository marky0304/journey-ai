# 智旅平台 API 测试报告

**测试日期:** 2026-05-21
**测试环境:** FastAPI + SQLite + DeepSeek V4 Flash
**测试账号:** test / 123456

---

## Auth 模块

| 接口 | 方法 | 认证 | 结果 | 说明 |
|------|------|------|------|------|
| `/api/health` | GET | ❌ | ✅ 200 | 健康检查 |
| `/api/auth/register` | POST | ❌ | ✅ 409 | 重复注册正确拒绝 |
| `/api/auth/login` | POST | ❌ | ✅ 200 | 返回 JWT token |
| `/api/auth/me` | GET | ✅ | ✅ 200 | 返回用户信息 |

## Trip 模块

| 接口 | 方法 | 认证 | 结果 | 说明 |
|------|------|------|------|------|
| `/api/trip/inspire` | POST | ❌ | ✅ 200 | AI 推荐 3 个目的地 |
| `/api/trip/clarify` | POST | ❌ | ✅ 200 | AI 追问澄清需求 |
| `/api/trip/plan` | POST | ❌ | ✅ 200 | 创建规划任务 |
| `/api/trip/planning/{task_id}` | GET | ❌ | ✅ 200 | 轮询进度(含 6 agent 状态) |
| `/api/trip/{trip_id}` | GET | ❌ | ✅ 200 | 完整行程(交通/住宿/景点/餐饮) |
| `/api/trip/{trip_id}/weather` | GET | ❌ | ✅ 200 | 天气 + LLM 穿搭建议 |
| `/api/trip/{trip_id}/chat` | POST | ✅ | ✅ 200 | 行程上下文 AI 对话 |
| `/api/trip/{trip_id}/swap` | POST | ❌ | ✅ 200 | 替换活动 |
| `/api/trip/{task_id}/cancel` | POST | ❌ | ✅ 200 | 取消任务 |

## Chat 模块 (`/api/v1/chat`)

| 接口 | 方法 | 认证 | 结果 | 说明 |
|------|------|------|------|------|
| `/context` | GET | ✅ | ✅ 200 | 行程元数据 + 推荐问题 |
| `/send` | POST | ✅ | ✅ 200 | 多轮对话(Redis 会话) |
| `/history` | GET | ✅ | ✅ 200 | 按行程分组会话列表 |
| `/session/{id}` | GET | ✅ | ✅ 200 | 会话消息历史 |
| `/session/{id}` | DELETE | ✅ | ✅ 200 | 软删除会话 |
| `/preferences` | GET | ✅ | ✅ 200 | 用户偏好列表 |

## Learn 模块 (`/api/learn`)

| 接口 | 方法 | 认证 | 结果 | 说明 |
|------|------|------|------|------|
| `/analyze` | POST | ✅ | ✅ 200 | 抓取 URL → AI 摘要 |
| `/recent` | GET | ✅ | ✅ 200 | 最近学习记录 |
| `/history` | GET | ✅ | ✅ 200 | 分页学习历史 |
| `/search` | POST | ✅ | ✅ 200 | 向量检索知识库 |
| `/global` | GET | ❌ | ✅ 200 | 全局知识库 |

---

> **总计: 24 个接口全部通过。**
>
> **已知问题:** inspire 接口旧版服务器进程返回 500，重启后恢复正常。
