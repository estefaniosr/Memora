"""Semantic retrieval normalized for the RAG pipeline."""

from __future__ import annotations

from typing import Any

from indexing.embeddings import EmbeddingModel
from indexing.vector_store import VectorStore


class RagRetriever:
    def __init__(
        self, embedding_model: EmbeddingModel, vector_store: VectorStore
    ) -> None:
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    @staticmethod
    def _first_list(results: dict[str, Any], key: str) -> list[Any]:
        values = results.get(key) or []
        return values[0] if values and isinstance(values[0], list) else []

    def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("As anotações da reunião não podem estar vazias.")

        raw_results = self.vector_store.search(
            self.embedding_model.embed_query(query), top_k=top_k
        )
        documents = self._first_list(raw_results, "documents")
        metadatas = self._first_list(raw_results, "metadatas")
        distances = self._first_list(raw_results, "distances")

        normalized: list[dict[str, Any]] = []
        for index, content in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else 0.0
            normalized.append(
                {
                    "rank": index + 1,
                    "title": str(metadata.get("title") or "Sem título"),
                    "source_id": str(metadata.get("source_id") or ""),
                    "chunk_index": int(metadata.get("chunk_index", 0)),
                    "distance": float(distance),
                    "content": str(content or ""),
                    "url": str(metadata.get("url") or ""),
                }
            )
        return normalized
