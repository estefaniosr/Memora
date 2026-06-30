"""High-level RAG answer generation orchestration."""

from __future__ import annotations

from typing import Any

from llm.base import LLMProvider
from rag.prompt_builder import build_reuse_prompt
from rag.retriever import RagRetriever


class AnswerGenerator:
    def __init__(
        self,
        retriever: RagRetriever,
        llm_provider: LLMProvider,
        max_context_chars: int,
    ) -> None:
        self.retriever = retriever
        self.llm_provider = llm_provider
        self.max_context_chars = max_context_chars

    def generate_answer(
        self, meeting_notes: str, top_k: int = 8
    ) -> dict[str, Any]:
        sources = self.retriever.retrieve(meeting_notes, top_k=top_k)
        prompt = build_reuse_prompt(
            meeting_notes,
            sources,
            max_context_chars=self.max_context_chars,
        )
        return {"answer": self.llm_provider.generate(prompt), "sources": sources}
