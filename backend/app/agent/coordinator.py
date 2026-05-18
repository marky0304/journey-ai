from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.core.llm import get_llm

COORDINATOR_PROMPT = """你是行程规划协调员。分析用户需求，分解为交通、住宿、景点、餐饮四个子任务。输出 JSON:
{"summary": "需求摘要", "constraints": {"transport": {"budget_share": 0.3}, "accommodation": {"budget_share": 0.3}, "attraction": {"budget_share": 0.25}, "dining": {"budget_share": 0.15}}}
"""


async def coordinator_node(state: AgentState) -> dict:
    llm = get_llm(temperature=0.3)
    user_input = (
        f"目的地: {state['destination']}\n"
        f"日期: {state['start_date']} 至 {state['end_date']}\n"
        f"预算: {state['budget_min']}-{state['budget_max']} {state['currency']}\n"
        f"偏好: {', '.join(state['preferences'])}\n"
        f"旅行风格: {state['travel_style']}"
    )
    messages = [
        SystemMessage(content=COORDINATOR_PROMPT),
        HumanMessage(content=user_input),
    ]
    response = await llm.ainvoke(messages)
    return {
        "messages": [
            HumanMessage(content=f"协调分析: {response.content}", name="coordinator")
        ]
    }
