from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.budget_optimizer import optimize_budget
from app.agent.state import AgentState
from app.core.llm import get_llm

COORDINATOR_PROMPT = """你是行程规划协调员。分析用户需求，用一句话总结本次行程的核心要点。"""


async def coordinator_node(state: AgentState) -> dict:
    budget_total = float(state.get("budget_max", state.get("budget_min", 10000)))

    # ── compute trip days ───────────────────────────────────────
    try:
        s = date.fromisoformat(state["start_date"])
        e = date.fromisoformat(state["end_date"])
        num_days = max(1, (e - s).days + 1)
    except (ValueError, KeyError):
        num_days = 3

    # ── count distinct destinations ─────────────────────────────
    dest_raw = state.get("destination", "")
    num_destinations = 1
    if dest_raw:
        parts = dest_raw.replace("，", ",").replace("/", ",").replace("、", ",").split(",")
        parts = [p.strip() for p in parts if p.strip()]
        num_destinations = max(1, len(parts))

    # ── GA-optimised budget split ───────────────────────────────
    budget_constraints = optimize_budget(
        budget_total=budget_total,
        num_days=num_days,
        preferences=state.get("preferences", []),
        travel_style=state.get("travel_style", "balanced"),
        num_destinations=num_destinations,
    )

    # ── LLM summary ─────────────────────────────────────────────
    llm = get_llm(temperature=0.3)
    user_input = (
        f"出发地: {state.get('start_location', '')}\n"
        f"目的地: {state['destination']}\n"
        f"日期: {state['start_date']} 至 {state['end_date']}\n"
        f"预算: {state['budget_min']}-{int(budget_total)} {state['currency']}\n"
        f"偏好: {', '.join(state['preferences'])}\n"
        f"旅行风格: {state['travel_style']}\n"
        f"天数: {num_days}\n"
        f"预算分配: 交通{budget_constraints['transport']} / "
        f"住宿{budget_constraints['accommodation']} / "
        f"景点{budget_constraints['attraction']} / "
        f"餐饮{budget_constraints['dining']}"
    )
    messages = [
        SystemMessage(content=COORDINATOR_PROMPT),
        HumanMessage(content=user_input),
    ]
    response = await llm.ainvoke(messages)

    return {
        "constraints": budget_constraints,
        "messages": [
            HumanMessage(content=f"协调分析: {response.content}", name="coordinator")
        ],
    }
