from dataclasses import replace
from typing import Any

import pytest

import services.memora_service as service_module
from app.config import ConfigurationError, Settings
from llm.base import LLMProvider
from services.memora_service import MemoraService


def make_settings() -> Settings:
    return Settings(
        confluence_base_url="https://example.atlassian.net/wiki",
        confluence_email="user@example.com",
        confluence_api_token="secret-token",
        confluence_space_key="SPACE",
        embedding_model="fake-model",
        chroma_db_path="./fake-db",
        chroma_collection_name="test_collection",
        llm_provider="ollama",
        openai_api_key="",
        openai_model="",
        gemini_api_key="",
        gemini_model="",
        ollama_base_url="http://localhost:11434",
        ollama_model="test-model",
        rag_top_k=8,
        rag_max_context_chars=12000,
    )


class FakeEmbeddingModel:
    def embed_query(self, query: str) -> list[float]:
        return [0.1, 0.2]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]


class FakeVectorStore:
    def __init__(self, count: int = 1) -> None:
        self.current_count = count

    def count(self) -> int:
        return self.current_count

    def search(self, query_embedding: list[float], top_k: int) -> dict[str, Any]:
        return {
            "documents": [["Login e dashboard por perfil."]],
            "metadatas": [[{
                "title": "Portal B2B",
                "source_id": "10",
                "chunk_index": 1,
                "url": "https://example.test/10",
            }]],
            "distances": [[0.2]],
        }

    def upsert_chunks(self, chunks: list[Any], embeddings: list[list[float]]) -> None:
        self.current_count += len(chunks)

    def delete_source(self, source_id: str) -> None:
        self.current_count = 0

    def replace_source_chunks(
        self, chunks: list[Any], embeddings: list[list[float]]
    ) -> None:
        self.delete_source(chunks[0].source_id)
        self.upsert_chunks(chunks, embeddings)


class FakeLLM(LLMProvider):
    def generate(self, prompt: str) -> str:
        return "1. Resumo da nova demanda\nResposta baseada nas fontes."


class FakeConfluenceClient:
    def __init__(self, **kwargs: Any) -> None:
        pass

    def get_all_pages(
        self, space_key: str, page_size: int = 25, max_pages: int | None = None
    ) -> list[dict[str, Any]]:
        return [{"content": {"id": "10", "title": "Portal B2B"}}]

    def get_page_content(self, page_id: str) -> dict[str, Any]:
        return {
            "id": page_id,
            "title": "Portal B2B",
            "type": "page",
            "body": {"storage": {"value": "<p>Login e dashboard por perfil.</p>"}},
            "space": {"key": "SPACE"},
            "version": {"number": 2},
        }


def test_config_status_never_contains_credentials() -> None:
    service = MemoraService(
        settings=make_settings(),
        embedding_model=FakeEmbeddingModel(),  # type: ignore[arg-type]
        vector_store=FakeVectorStore(),  # type: ignore[arg-type]
        llm_provider=FakeLLM(),
    )

    status = service.get_config_status()

    assert "confluence_api_token" not in status
    assert "openai_api_key" not in status
    assert "gemini_api_key" not in status
    assert "secret-token" not in status.values()


def test_service_search_and_analysis_use_existing_pipeline() -> None:
    service = MemoraService(
        settings=make_settings(),
        embedding_model=FakeEmbeddingModel(),  # type: ignore[arg-type]
        vector_store=FakeVectorStore(),  # type: ignore[arg-type]
        llm_provider=FakeLLM(),
    )

    results = service.semantic_search("portal com login", top_k=5)
    analysis = service.analyze_meeting_notes("portal com login", top_k=5)

    assert results[0]["title"] == "Portal B2B"
    assert analysis["sources"][0]["source_id"] == "10"
    assert analysis["answer"].startswith("1. Resumo")


def test_sync_confluence_returns_indexing_metrics(monkeypatch: Any) -> None:
    monkeypatch.setattr(service_module, "ConfluenceClient", FakeConfluenceClient)
    vector_store = FakeVectorStore(count=0)
    service = MemoraService(
        settings=make_settings(),
        embedding_model=FakeEmbeddingModel(),  # type: ignore[arg-type]
        vector_store=vector_store,  # type: ignore[arg-type]
        llm_provider=FakeLLM(),
    )

    result = service.sync_confluence(limit=50)

    assert result["pages_found"] == 1
    assert result["documents_processed"] == 1
    assert result["chunks_indexed"] == 1
    assert result["total_chunks"] == 1


def test_sync_confluence_requires_credentials(monkeypatch: Any) -> None:
    settings = replace(make_settings(), confluence_api_token="")
    service = MemoraService(settings=settings, vector_store=FakeVectorStore())  # type: ignore[arg-type]

    with pytest.raises(ConfigurationError, match="CONFLUENCE_API_TOKEN"):
        service.sync_confluence()
