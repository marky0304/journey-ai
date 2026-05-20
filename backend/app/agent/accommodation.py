from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.core.llm import get_json_llm

ACCOMMODATION_PROMPT = """推荐酒店，total_cost接近预算目标。输出JSON:
{"hotels":[{"name":"","area":"","price_per_night":0,"rating":0}],"total_cost":0}"""


async def accommodation_node(state: AgentState, budget_target: int = 0) -> dict:
    llm = get_json_llm()
    target = budget_target or state.get("budget_max", 10000)
    context = (
        f"目的地: {state['destination']}, "
        f"住宿预算目标: {target} {state.get('currency', 'CNY')}（请尽量用满此预算）, "
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
