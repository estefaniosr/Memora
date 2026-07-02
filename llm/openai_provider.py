"""OpenAI Responses API provider."""

from __future__ import annotations

from openai import OpenAI, OpenAIError

from llm.base import LLMProvider, LLMProviderError


def _friendly_openai_error(exc: OpenAIError) -> str:
    """Map SDK failures to safe messages without exposing provider payloads."""
    body = getattr(exc, "body", None)
    error = body.get("error", body) if isinstance(body, dict) else {}
    code = str(
        getattr(exc, "code", "")
        or (error.get("code", "") if isinstance(error, dict) else "")
    ).lower()
    status_code = getattr(exc, "status_code", None)

    if code == "insufficient_quota":
        return (
            "A cota da OpenAI foi esgotada. Verifique o plano e o faturamento "
            "da conta ou selecione outro provider."
        )
    if status_code == 429:
        return "A OpenAI limitou temporariamente as requisições. Tente novamente em instantes."
    if status_code in {401, 403}:
        return "A OpenAI recusou a credencial configurada. Verifique a OPENAI_API_KEY."
    if status_code == 404:
        return "O modelo configurado não está disponível para esta conta da OpenAI."
    if status_code is not None and status_code >= 500:
        return "A OpenAI está temporariamente indisponível. Tente novamente mais tarde."
    return "Não foi possível gerar a resposta com a OpenAI. Tente novamente."


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
            raise LLMProviderError(_friendly_openai_error(exc)) from exc

        answer = response.output_text
        if not answer or not answer.strip():
            raise LLMProviderError("A OpenAI retornou uma resposta vazia.")
        return answer.strip()
