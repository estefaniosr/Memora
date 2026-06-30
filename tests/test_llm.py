from types import SimpleNamespace
from typing import Any

import pytest
import requests

from llm import create_llm_provider
from llm.base import LLMProviderError
from llm.ollama_provider import OllamaProvider


def test_factory_creates_ollama_provider() -> None:
    settings = SimpleNamespace(
        llm_provider="ollama",
        ollama_base_url="http://localhost:11434",
        ollama_model="llama3.1:8b",
    )

    provider = create_llm_provider(settings)  # type: ignore[arg-type]

    assert isinstance(provider, OllamaProvider)


def test_ollama_connection_error_is_friendly(monkeypatch: Any) -> None:
    def fail(*args: Any, **kwargs: Any) -> None:
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(requests, "post", fail)
    provider = OllamaProvider("http://localhost:11434", "llama3.1:8b")

    with pytest.raises(LLMProviderError, match="Verifique se o Ollama está rodando"):
        provider.generate("prompt")
