"""LLM provider factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from llm.base import LLMProvider, LLMProviderError

if TYPE_CHECKING:
    from app.config import Settings


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Create only the selected provider, keeping other SDKs out of its path."""
    if settings.llm_provider == "ollama":
        from llm.ollama_provider import OllamaProvider

        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    if settings.llm_provider == "openai":
        from llm.openai_provider import OpenAIProvider

        return OpenAIProvider(settings.openai_api_key, settings.openai_model)
    if settings.llm_provider == "gemini":
        from llm.gemini_provider import GeminiProvider

        return GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    raise ValueError(
        f"LLM_PROVIDER inválido: '{settings.llm_provider}'. "
        "Use ollama, openai ou gemini."
    )


__all__ = ["LLMProvider", "LLMProviderError", "create_llm_provider"]
