import json
import re

from app.config import settings
from app.core.llm import LLM_MAX_RETRIES, LLM_TIMEOUT, _get_http_client

_client: object | None = None


def _get_client():
    global _client
    if _client is None:
        from openai import AsyncOpenAI

        _client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            max_retries=LLM_MAX_RETRIES,
            timeout=LLM_TIMEOUT,
            http_client=_get_http_client(),
        )
    return _client

SYSTEM_PROMPT = """你是小智，一位专业的旅行目的地推荐师。
根据用户的偏好，推荐 3 个适合的中国国内旅行目的地。

返回严格的 JSON 数组，每个元素格式如下：
{
  "name": "目的地名称",
  "reason": "推荐理由 (80字以内)",
  "season": "最佳季节",
  "budget_estimate": 人均预算(整数，单位人民币元),
  "highlights": ["亮点1", "亮点2", "亮点3"],
  "tags": ["标签1", "标签2"]
}

要求：
- 推荐真实、可旅行的中国目的地
- 3 个目的地风格尽量不同
- reason 要具体、有吸引力
- budget_estimate 要合理（含交通/住宿/餐饮大致估算）
- 返回纯 JSON 数组，不要 markdown 代码块"""


async def inspire_destinations(
    preferences: str = "",
    budget_min: int = 0,
    budget_max: int = 10000,
    days: int = 3,
) -> list[dict]:
    user_prompt = f"帮我推荐 3 个目的地。"
    if preferences:
        user_prompt += f" 偏好：{preferences}。"
    if budget_max:
        user_prompt += f" 人均预算控制在 {budget_max} 元以内。"
    user_prompt += f" 计划旅行 {days} 天。"

    resp = await _get_client().chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=1500,
    )

    content = resp.choices[0].message.content or "[]"
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", content)
        if match:
            return json.loads(match.group())
        return []
