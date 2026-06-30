"""Gemini provider using Google's current Gen AI SDK."""

from __future__ import annotations

from google import genai

from llm.base import LLMProvider, LLMProviderError


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY é obrigatória para o provider Gemini.")
        if not model.strip():
            raise ValueError("GEMINI_MODEL é obrigatório para o provider Gemini.")
        self.model = model
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            answer = response.text
        except Exception as exc:
            raise LLMProviderError("Falha ao gerar resposta com Gemini.") from exc
        if not answer or not answer.strip():
            raise LLMProviderError("O Gemini retornou uma resposta vazia.")
        return answer.strip()
