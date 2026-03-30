from __future__ import annotations

import httpx
from langchain_core.language_models import BaseChatModel

from app.config import settings


def _make_http_clients() -> tuple[httpx.Client, httpx.AsyncClient]:
    """Create httpx clients with HTTP/2 disabled.

    Some internal API proxies do not handle HTTP/2 upgrade negotiation correctly,
    causing async reads to hang indefinitely. Forcing HTTP/1.1 avoids this.
    """
    sync_client = httpx.Client(
        transport=httpx.HTTPTransport(http2=False),
        timeout=httpx.Timeout(120.0, connect=10.0),
    )
    async_client = httpx.AsyncClient(
        transport=httpx.AsyncHTTPTransport(http2=False),
        timeout=httpx.Timeout(120.0, connect=10.0),
    )
    return sync_client, async_client


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    **kwargs,
) -> BaseChatModel:
    """Factory function to create an LLM instance based on configuration.

    Supports OpenAI, Anthropic Claude, and local models (via Ollama/vLLM).
    """
    provider = provider or settings.LLM_PROVIDER

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        sync_client, async_client = _make_http_clients()
        return ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            temperature=temperature,
            http_client=sync_client,
            http_async_client=async_client,
            **kwargs,
        )

    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model or settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            anthropic_api_url=settings.ANTHROPIC_BASE_URL,
            temperature=temperature,
            **kwargs,
        )

    elif provider == "local":
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            model=model or settings.LOCAL_LLM_MODEL,
            base_url=settings.LOCAL_LLM_BASE_URL,
            temperature=temperature,
            **kwargs,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_vision_llm(
    provider: str | None = None,
    **kwargs,
) -> BaseChatModel:
    """Get an LLM with vision capabilities for screenshot analysis."""
    provider = provider or settings.LLM_PROVIDER

    if provider == "openai":
        return get_llm(provider="openai", model=settings.OPENAI_MODEL, **kwargs)
    elif provider == "claude":
        return get_llm(provider="claude", model=settings.ANTHROPIC_MODEL, **kwargs)
    else:
        return get_llm(provider=provider, **kwargs)
