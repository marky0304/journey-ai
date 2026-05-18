from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.core.llm import get_llm

ATTRACTION_PROMPT = """你是景点规划专家。设计每日游览路线。输出 JSON:
{"days": [{"day_index": 1, "date": "", "attractions": [{"name": "", "duration_min": 0, "ticket_price": 0}]}], "total_tickets": 0}
"""


async def attraction_node(state: AgentState) -> dict:
    llm = get_llm()
    context = (
        f"目的地: {state['destination']}, "
        f"日期: {state['start_date']} 至 {state['end_date']}, "
        f"偏好: {state['preferences']}, "
        f"风格: {state['travel_style']}"
    )
    messages = [
        SystemMessage(content=ATTRACTION_PROMPT),
        HumanMessage(content=context),
    ]
    response = await llm.ainvoke(messages)
    return {
        "attraction_plan": {"raw": response.content},
        "messages": [
            HumanMessage(content=f"景点方案: {response.content}", name="attraction")
        ],
    }
