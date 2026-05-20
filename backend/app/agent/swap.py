import json
import re
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm

SWAP_PROMPT = """你是旅行推荐专家。用户对当前安排不满意，请推荐一个同类型、同区域的替代方案。

规则:
1. 替换方案必须与当前活动类型相同（景点→景点，餐饮→餐饮）
2. 尽量推荐同一城市/区域内的替代，不要跨城市推荐
3. 保持与原活动相近的时间段和时长
4. 给出1-2句推荐理由

输出纯 JSON（不要 markdown 代码块）:
{"name": "", "type": "", "start_time": "", "end_time": "", "duration": 0, "description": "", "tips": "", "reason": ""}
"""


async def swap_activity(
    destination: str,
    day_index: int,
    activity_type: str,
    activity_name: str,
    preferences: Optional[List[str]] = None,
    context: Optional[str] = None,
) -> dict:
    llm = get_llm(temperature=0.8)

    user_context = f"目的地: {destination}, 第{day_index + 1}天\n"
    user_context += f"当前{activity_type}: {activity_name}\n"
    if preferences:
        user_context += f"用户偏好: {', '.join(preferences)}\n"
    if context:
        user_context += f"当日上下文: {context}\n"
    user_context += "请推荐一个替代方案。"

    messages = [
        SystemMessage(content=SWAP_PROMPT),
        HumanMessage(content=user_context),
    ]
    response = await llm.ainvoke(messages)
    raw = response.content

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())
        raise ValueError(f"无法解析 swap agent 输出: {raw[:200]}")
