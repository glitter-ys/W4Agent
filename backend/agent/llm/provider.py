from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from app.config import settings


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

        return ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            temperature=temperature,
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
        return get_llm(provider="openai", model="gpt-4o", **kwargs)
    elif provider == "claude":
        return get_llm(provider="claude", model=settings.ANTHROPIC_MODEL, **kwargs)
    else:
        return get_llm(provider=provider, **kwargs)
