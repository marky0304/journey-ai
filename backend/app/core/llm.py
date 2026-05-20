import httpx
from langchain_openai import ChatOpenAI

from app.config import settings

LLM_TIMEOUT = httpx.Timeout(60.0, connect=10.0, read=50.0)
LLM_MAX_RETRIES = 2

_shared_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _shared_http_client
    if _shared_http_client is None:
        _shared_http_client = httpx.AsyncClient(
            proxy=None,
            trust_env=False,
            timeout=LLM_TIMEOUT,
        )
    return _shared_http_client


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """LLM for planning agents. Add json_object mode only when prompt contains 'json'."""
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=temperature,
        max_retries=LLM_MAX_RETRIES,
        http_async_client=_get_http_client(),
    )


def get_json_llm(temperature: float = 0.2) -> ChatOpenAI:
    """LLM with JSON mode enforced — use for agents that output JSON."""
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=temperature,
        max_retries=LLM_MAX_RETRIES,
        http_async_client=_get_http_client(),
        model_kwargs={"response_format": {"type": "json_object"}},
    )
