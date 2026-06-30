"""OpenAI Responses API provider."""

from __future__ import annotations

from openai import OpenAI, OpenAIError

from llm.base import LLMProvider, LLMProviderError


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key.strip():
            raise ValueError("OPENAI_API_KEY é obrigatória para o provider OpenAI.")
        if not model.strip():
            raise ValueError("OPENAI_MODEL é obrigatório para o provider OpenAI.")
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.responses.create(model=self.model, input=prompt)
        except OpenAIError as exc:
            raise LLMProviderError(f"Falha ao gerar resposta com OpenAI: {exc}") from exc

        answer = response.output_text
        if not answer or not answer.strip():
            raise LLMProviderError("A OpenAI retornou uma resposta vazia.")
        return answer.strip()
