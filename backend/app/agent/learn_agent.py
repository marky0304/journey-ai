import json

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

SYSTEM_PROMPT = """你是旅行知识提取专家。从抓取的网页内容中提取结构化的旅行知识。

## 输出格式
严格返回JSON（不要markdown代码块）:
{
  "title": "优化后标题（最多50字）",
  "summary": "3-5句关键信息摘要，突出最实用的旅行建议",
  "knowledge_points": [
    {"point": "具体知识点", "category": "交通/景点/美食/住宿/购物/文化/安全/预算/季节/其他"}
  ],
  "tags": ["标签1", "标签2", "标签3"],
  "location": "涉及的主要城市或景点名称，无则填null",
  "practical_info": {
    "transport": "交通建议，无则填null",
    "tickets": "门票信息，无则填null",
    "hours": "开放时间，无则填null",
    "tips": "注意事项，无则填null"
  },
  "quality_score": 0.0到1.0之间的质量评分
}

## 评分标准
- 0.8-1.0: 信息丰富具体，有明确的时间/价格/路线
- 0.6-0.8: 有实用价值但部分信息模糊
- 0.4-0.6: 内容笼统，缺乏具体细节
- 0.0-0.4: 内容稀薄或与旅行无关

## 重要
- 只提取可复用的旅行知识，不要复述原文
- knowledge_points每个point控制在30字以内
- 信息不明确时宁缺毋滥
"""


async def digest_content(url: str, scraped: dict) -> dict:
    user_content = f"""网址: {url}
平台: {scraped.get('platform', 'unknown')}

标题: {scraped.get('title', '')}

正文:
{scraped.get('text', '')[:4000]}
"""

    resp = await _get_client().chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
        max_tokens=1500,
    )

    raw = resp.choices[0].message.content or "{}"
    return _parse_response(raw, url, scraped)


def _parse_response(raw: str, url: str, scraped: dict) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        return _fallback_result(url, scraped)

    quality = result.get("quality_score", 0.5)
    if isinstance(quality, (int, float)):
        quality = max(0.0, min(1.0, float(quality)))
    else:
        quality = 0.5

    return {
        "title": str(result.get("title", scraped.get("title", "")))[:500],
        "summary": str(result.get("summary", ""))[:2000],
        "knowledge_points": result.get("knowledge_points", []),
        "tags": result.get("tags", []),
        "location": result.get("location"),
        "practical_info": result.get("practical_info"),
        "quality_score": quality,
    }


def _fallback_result(url: str, scraped: dict) -> dict:
    title = scraped.get("title", "")
    text = scraped.get("text", "")
    summary = text[:300] if text else ""
    return {
        "title": title,
        "summary": summary,
        "knowledge_points": [],
        "tags": [],
        "location": None,
        "practical_info": None,
        "quality_score": 0.3,
    }
