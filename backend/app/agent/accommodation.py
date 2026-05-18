from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.core.llm import get_llm

ACCOMMODATION_PROMPT = """你是住宿推荐专家。推荐酒店。输出 JSON:
{"hotels": [{"name": "", "area": "", "price_per_night": 0, "rating": 0}], "total_cost": 0}
"""


async def accommodation_node(state: AgentState) -> dict:
    llm = get_llm()
    context = (
        f"目的地: {state['destination']}, "
        f"预算: {state['budget_min']}-{state['budget_max']}, "
        f"偏好: {state['preferences']}"
    )
    messages = [
        SystemMessage(content=ACCOMMODATION_PROMPT),
        HumanMessage(content=context),
    ]
    response = await llm.ainvoke(messages)
    return {
        "accommodation_plan": {"raw": response.content},
        "messages": [
            HumanMessage(content=f"住宿方案: {response.content}", name="accommodation")
        ],
    }
