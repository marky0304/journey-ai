import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.core.llm import get_json_llm

STRATEGY_PROMPT = """整合各方案为完整每日行程。输出JSON:
{"destination":"","dates":{"start":"","end":""},"budget":{"min":0,"max":0,"currency":"CNY"},"preferences":[],"travel_style":"","days":[{"day_index":1,"date":"","activities":[{"id":"","type":"attraction/meal/transport/hotel","name":"","start_time":"HH:MM","end_time":"HH:MM","duration":120,"description":"","tips":""}]}],"summary":{"total_cost":0,"attraction_count":0}}
total_cost=活动费用总和, attraction_count=景点数量。
"""


def _summarize_plan(plan: dict, max_len: int = 600) -> str:
    raw = plan.get("raw", "") if plan else ""
    if len(raw) <= max_len:
        return raw
    return raw[:max_len] + "…"


async def strategy_node(state: AgentState) -> dict:
    llm = get_json_llm(temperature=0.3)
    context = (
        f"目的地: {state['destination']}, "
        f"日期: {state['start_date']}~{state['end_date']}, "
        f"天数: {state.get('num_days', 3)}\n"
        f"预算范围: {state['budget_min']}-{state['budget_max']} {state.get('currency', 'CNY')}\n"
        f"偏好: {state['preferences']}, 风格: {state['travel_style']}\n"
        f"交通: {_summarize_plan(state.get('transport_plan', {}))}\n"
        f"住宿: {_summarize_plan(state.get('accommodation_plan', {}))}\n"
        f"景点: {_summarize_plan(state.get('attraction_plan', {}))}\n"
        f"餐饮: {_summarize_plan(state.get('dining_plan', {}))}\n"
        f"total_cost 接近 {state['budget_max']}"
    )
    messages = [
        SystemMessage(content=STRATEGY_PROMPT),
        HumanMessage(content=context),
    ]
    response = await llm.ainvoke(messages)
    return {
        "final_plan": {"raw": response.content},
        "messages": [
            HumanMessage(content=f"最终方案: {response.content}", name="strategy")
        ],
    }
