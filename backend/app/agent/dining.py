from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.core.llm import get_llm

DINING_PROMPT = """你是美食推荐专家。推荐每日餐厅。输出 JSON:
{"meals": [{"day_index": 1, "restaurants": [{"name": "", "meal": "lunch/dinner", "cuisine": "", "price_per_person": 0}]}], "total_cost": 0}
"""


async def dining_node(state: AgentState) -> dict:
    llm = get_llm()
    context = (
        f"目的地: {state['destination']}, "
        f"日期: {state['start_date']} 至 {state['end_date']}, "
        f"偏好: {state['preferences']}"
    )
    messages = [
        SystemMessage(content=DINING_PROMPT),
        HumanMessage(content=context),
    ]
    response = await llm.ainvoke(messages)
    return {
        "dining_plan": {"raw": response.content},
        "messages": [
            HumanMessage(content=f"餐饮方案: {response.content}", name="dining")
        ],
    }
