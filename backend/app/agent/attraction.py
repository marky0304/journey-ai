from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.core.llm import get_json_llm

ATTRACTION_PROMPT = """设计每日景点路线，total_tickets接近预算目标。输出JSON:
{"days":[{"day_index":1,"date":"","attractions":[{"name":"","duration_min":0,"ticket_price":0}]}],"total_tickets":0}"""


async def attraction_node(state: AgentState, budget_target: int = 0) -> dict:
    llm = get_json_llm()
    target = budget_target or state.get("budget_max", 10000)
    context = (
        f"目的地: {state['destination']}, "
        f"日期: {state['start_date']} 至 {state['end_date']}, "
        f"景点预算目标: {target} {state.get('currency', 'CNY')}（请尽量用满此预算）, "
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
