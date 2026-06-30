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


def test_gemini_uses_google_genai_client(monkeypatch: Any) -> None:
    from llm import gemini_provider as module

    calls: dict[str, Any] = {}

    class FakeModels:
        def generate_content(self, *, model: str, contents: str) -> Any:
            calls.update(model=model, contents=contents)
            return SimpleNamespace(text="Resposta do Gemini")

    class FakeClient:
        def __init__(self, *, api_key: str) -> None:
            calls["api_key"] = api_key
            self.models = FakeModels()

    monkeypatch.setattr(module.genai, "Client", FakeClient)
    provider = module.GeminiProvider("secret", "gemini-test")

    assert provider.generate("prompt") == "Resposta do Gemini"
    assert calls == {
        "api_key": "secret",
        "model": "gemini-test",
        "contents": "prompt",
    }


def test_gemini_rejects_empty_response(monkeypatch: Any) -> None:
    from llm import gemini_provider as module

    class FakeClient:
        def __init__(self, *, api_key: str) -> None:
            self.models = SimpleNamespace(
                generate_content=lambda **kwargs: SimpleNamespace(text=None)
            )

    monkeypatch.setattr(module.genai, "Client", FakeClient)
    provider = module.GeminiProvider("secret", "gemini-test")

    with pytest.raises(LLMProviderError, match="resposta vazia"):
        provider.generate("prompt")
