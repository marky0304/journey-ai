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
    context = (
        f"交通方案: {state.get('transport_plan', {})}\n"
        f"住宿方案: {state.get('accommodation_plan', {})}\n"
        f"景点方案: {state.get('attraction_plan', {})}\n"
        f"餐饮方案: {state.get('dining_plan', {})}\n"
        f"偏好: {state['preferences']}\n"
        f"风格: {state['travel_style']}\n"
        f"预算: {state['budget_min']}-{state['budget_max']}"
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
