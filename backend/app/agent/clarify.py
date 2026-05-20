import json
import re
from datetime import date, timedelta

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm

CLARIFY_PROMPT = """你是旅行规划顾问。用户提供了部分旅行计划信息，你的任务是：
1. 判断信息是否足够启动详细规划
2. 如果不够，生成一个友好的追问（每次只问一个关键问题）
3. 如果够了或已达追问上限，输出完整的结构化计划

关键信息优先级（从高到低）:
- 出行人数/同伴（几人？家庭/情侣/朋友/独自？）
- 游玩天数（如果日期范围缺少）
- 兴趣偏好（美食/文化/自然/购物/休闲？）
- 预算范围
- 旅行节奏（悠闲/适中/紧凑）

追问规则:
- 每次只问一个问题，用轻松的口吻
- 如果用户已提供某信息，不要重复问
- 最多追问 5 轮，第 5 轮必须 done=true
- 根据用户每轮回答动态调整下一个问题

输出纯 JSON（不要 markdown 代码块）:
{
  "done": false,
  "message": "追问内容（15-50字，轻松口语化）",
  "questions_asked": 1,
  "destination": null,
  "start_date": null,
  "end_date": null,
  "budget_min": null,
  "budget_max": null,
  "currency": null,
  "preferences": null,
  "travel_style": null
}

当 done=true 时，补齐所有已知字段（destination/start_date/end_date/budget_min/budget_max/currency/preferences/travel_style），preferences 为字符串数组。
"""

MAX_QUESTIONS = 5


async def clarify_node(req: dict) -> dict:
    llm = get_llm(temperature=0.6)

    questions_asked = req.get("questions_asked", 0)
    messages_history = req.get("messages", [])

    if questions_asked >= MAX_QUESTIONS:
        today = date.today()
        default_start = req.get("start_date") or today.isoformat()
        default_end = req.get("end_date") or (today + timedelta(days=3)).isoformat()
        return {
            "done": True,
            "message": "好的，我已了解你的需求，正在为你规划行程...",
            "questions_asked": questions_asked,
            "destination": req.get("destination"),
            "start_date": default_start,
            "end_date": default_end,
            "budget_min": req.get("budget_min", 0),
            "budget_max": req.get("budget_max", 100000),
            "currency": req.get("currency", "CNY"),
            "preferences": req.get("preferences", []),
            "travel_style": req.get("travel_style", "balanced"),
        }

    context = f"""当前已提供信息:
- 目的地: {req.get('destination') or '未提供'}
- 日期: {req.get('start_date') or '未提供'} 至 {req.get('end_date') or '未提供'}
- 预算: {req.get('budget_min', 0)} - {req.get('budget_max', 100000)} {req.get('currency', 'CNY')}
- 偏好: {', '.join(req.get('preferences', [])) if req.get('preferences') else '未提供'}
- 旅行风格: {req.get('travel_style', 'balanced')}
- 已追问次数: {questions_asked}/{MAX_QUESTIONS}
"""

    llm_messages = [SystemMessage(content=CLARIFY_PROMPT), HumanMessage(content=context)]

    if messages_history:
        for msg in messages_history:
            if msg.get("role") == "user":
                llm_messages.append(HumanMessage(content=msg["content"]))
            else:
                llm_messages.append(HumanMessage(content=f"AI: {msg['content']}"))

    response = await llm.ainvoke(llm_messages)
    raw = response.content

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError(f"无法解析 clarify agent 输出: {raw[:200]}")

    result["questions_asked"] = questions_asked + (0 if result.get("done") else 1)

    if result.get("done"):
        today = date.today()
        if not result.get("start_date"):
            result["start_date"] = today.isoformat()
        if not result.get("end_date"):
            result["end_date"] = (today + timedelta(days=3)).isoformat()

    return result
