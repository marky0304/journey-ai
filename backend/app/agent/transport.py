from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.core.llm import get_json_llm

TRANSPORT_PROMPT = """推荐往返交通方案，total_cost接近预算目标。输出JSON:
{"type":"flight/train/car","options":[{"name":"","price":0,"duration":"","departure":"","arrival":""}],"total_cost":0}"""


async def transport_node(state: AgentState, budget_target: int = 0) -> dict:
    llm = get_json_llm()
    start = state.get("start_location", "")
    target = budget_target or state.get("budget_max", 10000)
    context = (
        f"出发地: {start}, "
        f"目的地: {state['destination']}, "
        f"日期: {state['start_date']} 至 {state['end_date']}, "
        f"交通预算目标: {target} {state.get('currency', 'CNY')}（请尽量用满此预算）"
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
