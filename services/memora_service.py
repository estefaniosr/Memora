"""Reusable business orchestration for CLI and web interfaces."""

from __future__ import annotations

from typing import Any
from app.config import ConfigurationError, Settings, load_settings
from connectors.confluence_client import ConfluenceClient
from indexing.embeddings import EmbeddingModel
from indexing.indexer import DocumentIndexer
from indexing.vector_store import VectorStore
from llm import LLMProvider, create_llm_provider
from models.confluence_document import build_confluence_document
from models.source_document import SourceDocument
from rag.answer_generator import AnswerGenerator
from rag.retriever import RagRetriever


class MemoraServiceError(RuntimeError):
    """Raised when a Memora workflow cannot be completed."""


class MemoraService:
    def __init__(
        self,
        settings: Settings | None = None,
        embedding_model: EmbeddingModel | None = None,
        vector_store: VectorStore | None = None,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self._embedding_model = embedding_model
        self._vector_store = vector_store
        self._llm_provider = llm_provider

    @property
    def embedding_model(self) -> EmbeddingModel:
        if self._embedding_model is None:
            self._embedding_model = EmbeddingModel(self.settings.embedding_model)
        return self._embedding_model

    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = VectorStore(
                db_path=self.settings.chroma_db_path,
                collection_name=self.settings.chroma_collection_name,
            )
        return self._vector_store

    @property
    def llm_provider(self) -> LLMProvider:
        if self._llm_provider is None:
            self._llm_provider = create_llm_provider(self.settings)
        return self._llm_provider

    def get_config_status(self) -> dict[str, str | bool]:
        model_by_provider = {
            "ollama": self.settings.ollama_model,
            "openai": self.settings.openai_model,
            "gemini": self.settings.gemini_model,
        }
        return {
            "confluence_base_url_configured": bool(
                self.settings.confluence_base_url
            ),
            "confluence_email_configured": bool(self.settings.confluence_email),
            "confluence_space_key": self.settings.confluence_space_key,
            "embedding_model": self.settings.embedding_model,
            "chroma_collection_name": self.settings.chroma_collection_name,
            "llm_provider": self.settings.llm_provider,
            "llm_model": model_by_provider[self.settings.llm_provider],
        }

    def get_vector_count(self) -> int:
        return self.vector_store.count()

    def get_document_count(self) -> int:
        return self.vector_store.document_count()

    @staticmethod
    def _page_identity(search_result: dict[str, Any]) -> tuple[str, str]:
        page = search_result.get("content") or search_result
        return str(page.get("id", "")), str(page.get("title", "Sem título"))

    def _source_document(
        self, page: dict[str, Any], fallback_title: str
    ) -> SourceDocument:
        return build_confluence_document(
            page,
            base_url=self.settings.confluence_base_url,
            fallback_title=fallback_title,
        )

    def sync_confluence(self, limit: int = 50) -> dict[str, int]:
        if limit < 1:
            raise ValueError("O limite de páginas deve ser maior que zero.")
        missing = [
            name
            for name, value in (
                ("CONFLUENCE_BASE_URL", self.settings.confluence_base_url),
                ("CONFLUENCE_EMAIL", self.settings.confluence_email),
                ("CONFLUENCE_API_TOKEN", self.settings.confluence_api_token),
                ("CONFLUENCE_SPACE_KEY", self.settings.confluence_space_key),
            )
            if not value
        ]
        if missing:
            raise ConfigurationError(
                "Variáveis de ambiente obrigatórias para sincronizar o Confluence "
                "ausentes: " + ", ".join(missing)
            )

        client = ConfluenceClient(
            base_url=self.settings.confluence_base_url,
            email=self.settings.confluence_email,
            api_token=self.settings.confluence_api_token,
        )
        search_results = client.get_all_pages(
            self.settings.confluence_space_key,
            page_size=min(25, limit),
            max_pages=limit,
        )
        if not search_results:
            return {
                "pages_found": 0,
                "documents_processed": 0,
                "chunks_indexed": 0,
                "total_chunks": self.get_vector_count(),
            }

        documents: list[SourceDocument] = []
        for search_result in search_results:
            page_id, title = self._page_identity(search_result)
            if not page_id:
                continue
            page = client.get_page_content(page_id)
            documents.append(self._source_document(page, fallback_title=title))

        stats = DocumentIndexer(
            self.embedding_model, self.vector_store
        ).index_documents(documents)
        return {
            "pages_found": len(search_results),
            "documents_processed": stats.documents_processed,
            "chunks_indexed": stats.chunks_indexed,
            "total_chunks": stats.total_chunks,
        }

    def _ensure_indexed(self) -> None:
        if self.get_vector_count() == 0:
            raise MemoraServiceError(
                "A base vetorial está vazia. Sincronize o Confluence ou execute "
                "python -m app.index_confluence."
            )

    def semantic_search(
        self, query: str, top_k: int = 8
    ) -> list[dict[str, Any]]:
        self._ensure_indexed()
        return RagRetriever(self.embedding_model, self.vector_store).retrieve(
            query, top_k=top_k
        )

    def analyze_meeting_notes(
        self, meeting_notes: str, top_k: int = 8
    ) -> dict[str, Any]:
        self._ensure_indexed()
        generator = AnswerGenerator(
            RagRetriever(self.embedding_model, self.vector_store),
            self.llm_provider,
            max_context_chars=self.settings.rag_max_context_chars,
        )
        return generator.generate_answer(meeting_notes, top_k=top_k)
