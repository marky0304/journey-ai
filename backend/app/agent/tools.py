import json

from langchain_core.tools import tool


@tool
def validate_plan_schema(plan_json: str) -> str:
    """验证行程 JSON Schema"""
    try:
        plan = json.loads(plan_json)
        for field in ["destination", "dates", "days"]:
            if field not in plan:
                return f"缺少必要字段: {field}"
        return "Schema 验证通过"
    except json.JSONDecodeError as e:
        return f"JSON 解析失败: {e}"
