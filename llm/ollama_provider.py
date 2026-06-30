"""Ollama local HTTP provider."""

from __future__ import annotations

import requests

from llm.base import LLMProvider, LLMProviderError


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, timeout: float = 180.0) -> None:
        if not model.strip():
            raise ValueError("OLLAMA_MODEL não pode estar vazio.")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except (requests.ConnectionError, requests.Timeout) as exc:
            raise LLMProviderError(
                "Não foi possível conectar ao Ollama. Verifique se o Ollama está rodando."
            ) from exc
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "desconhecido"
            raise LLMProviderError(
                f"O Ollama retornou HTTP {status}. Verifique se o modelo '{self.model}' está instalado."
            ) from exc
        except requests.RequestException as exc:
            raise LLMProviderError("Falha ao consultar o Ollama.") from exc

        try:
            answer = response.json().get("response", "")
        except (requests.JSONDecodeError, AttributeError) as exc:
            raise LLMProviderError("O Ollama retornou uma resposta inválida.") from exc
        if not isinstance(answer, str) or not answer.strip():
            raise LLMProviderError("O Ollama retornou uma resposta vazia.")
        return answer.strip()
