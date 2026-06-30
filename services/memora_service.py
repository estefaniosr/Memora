"""Reusable business orchestration for CLI and web interfaces."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.config import Settings, load_settings
from connectors.confluence_client import ConfluenceClient
from extractors.html_cleaner import clean_confluence_html
from indexing.embeddings import EmbeddingModel
from indexing.indexer import DocumentIndexer
from indexing.vector_store import VectorStore
from llm import LLMProvider, create_llm_provider
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

    @staticmethod
    def _page_identity(search_result: dict[str, Any]) -> tuple[str, str]:
        page = search_result.get("content") or search_result
        return str(page.get("id", "")), str(page.get("title", "Sem título"))

    def _build_page_url(self, page_id: str) -> str:
        return (
            f"{self.settings.confluence_base_url.rstrip('/')}"
            f"/pages/viewpage.action?pageId={quote(page_id)}"
        )

    def _source_document(
        self, page: dict[str, Any], fallback_title: str
    ) -> SourceDocument:
        page_id = str(page.get("id", ""))
        return SourceDocument(
            source="confluence",
            source_id=page_id,
            title=str(page.get("title") or fallback_title),
            url=self._build_page_url(page_id),
            content=clean_confluence_html(
                str(page.get("body", {}).get("storage", {}).get("value", ""))
            ),
            space_key=page.get("space", {}).get("key"),
            version=page.get("version", {}).get("number"),
            metadata={"content_type": page.get("type")},
        )

    def sync_confluence(self, limit: int = 50) -> dict[str, int]:
        if limit < 1:
            raise ValueError("O limite de páginas deve ser maior que zero.")

        client = ConfluenceClient(
            base_url=self.settings.confluence_base_url,
            email=self.settings.confluence_email,
            api_token=self.settings.confluence_api_token,
        )
        payload = client.search_pages(
            self.settings.confluence_space_key, limit=limit
        )
        search_results = payload.get("results", [])
        if not isinstance(search_results, list):
            raise MemoraServiceError(
                "O Confluence retornou um formato inesperado para as páginas."
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
