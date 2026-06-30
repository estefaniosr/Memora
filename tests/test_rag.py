from typing import Any

from llm.base import LLMProvider
from rag.answer_generator import AnswerGenerator
from rag.prompt_builder import build_reuse_prompt
from rag.retriever import RagRetriever


class FakeEmbeddingModel:
    def embed_query(self, query: str) -> list[float]:
        return [0.1, 0.2]


class FakeVectorStore:
    def search(self, query_embedding: list[float], top_k: int) -> dict[str, Any]:
        return {
            "documents": [["Login com autenticação por e-mail."]],
            "metadatas": [[{
                "title": "Portal B2B",
                "source_id": "page-1",
                "chunk_index": 2,
                "url": "https://example.test/page-1",
            }]],
            "distances": [[0.25]],
        }


class FakeLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self.prompt = ""

    def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return "1. Resumo da nova demanda\nAnálise baseada no Portal B2B."


def test_retriever_normalizes_chroma_results() -> None:
    retriever = RagRetriever(FakeEmbeddingModel(), FakeVectorStore())  # type: ignore[arg-type]

    results = retriever.retrieve("portal com login", top_k=8)

    assert results == [{
        "rank": 1,
        "title": "Portal B2B",
        "source_id": "page-1",
        "chunk_index": 2,
        "distance": 0.25,
        "content": "Login com autenticação por e-mail.",
        "url": "https://example.test/page-1",
    }]


def test_prompt_has_required_sections_and_limits_context() -> None:
    chunks = [{
        "title": "Projeto antigo",
        "chunk_index": 1,
        "distance": 0.2,
        "content": "evidência " * 100,
    }]

    prompt = build_reuse_prompt("Nova demanda", chunks, max_context_chars=180)
    context = prompt.split("CONTEXTO RECUPERADO:\n", 1)[1]

    assert len(context) <= 180
    assert "1. Resumo da nova demanda" in prompt
    assert "9. Fontes consultadas" in prompt
    assert "somente com base nos documentos recuperados" in prompt


def test_answer_generator_returns_answer_and_sources() -> None:
    retriever = RagRetriever(FakeEmbeddingModel(), FakeVectorStore())  # type: ignore[arg-type]
    llm = FakeLLMProvider()
    generator = AnswerGenerator(retriever, llm, max_context_chars=1000)

    result = generator.generate_answer("portal com login", top_k=4)

    assert result["answer"].startswith("1. Resumo")
    assert result["sources"][0]["title"] == "Portal B2B"
    assert "Login com autenticação" in llm.prompt
