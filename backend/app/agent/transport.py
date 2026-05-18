from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.core.llm import get_llm

TRANSPORT_PROMPT = """你是交通规划专家。推荐往返大交通方案。输出 JSON:
{"type": "flight/train/car", "options": [{"name": "", "price": 0, "duration": "", "departure": "", "arrival": ""}], "total_cost": 0}
"""


async def transport_node(state: AgentState) -> dict:
    llm = get_llm()
    context = (
        f"目的地: {state['destination']}, "
        f"日期: {state['start_date']} 至 {state['end_date']}, "
        f"预算: {state['budget_min']}-{state['budget_max']}"
    )
    messages = [
        SystemMessage(content=TRANSPORT_PROMPT),
        HumanMessage(content=context),
    ]
    response = await llm.ainvoke(messages)
    return {
        "transport_plan": {"raw": response.content},
        "messages": [
            HumanMessage(content=f"交通方案: {response.content}", name="transport")
        ],
    }
