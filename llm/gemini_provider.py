"""Gemini provider using the google-generativeai SDK required by this phase."""

from __future__ import annotations

import google.generativeai as genai

from llm.base import LLMProvider, LLMProviderError


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key.strip():
            raise ValueError("GEMINI_API_KEY é obrigatória para o provider Gemini.")
        if not model.strip():
            raise ValueError("GEMINI_MODEL é obrigatório para o provider Gemini.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            answer = response.text
        except Exception as exc:
            raise LLMProviderError("Falha ao gerar resposta com Gemini.") from exc
        if not answer or not answer.strip():
            raise LLMProviderError("O Gemini retornou uma resposta vazia.")
        return answer.strip()
