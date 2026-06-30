"""Persistent ChromaDB vector store."""

from __future__ import annotations

from typing import Any

import chromadb

from indexing.chunker import TextChunk

ChromaMetadata = dict[str, str | int | float | bool]


class VectorStore:
    def __init__(self, db_path: str, collection_name: str) -> None:
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=None,
        )

    @staticmethod
    def _metadata_for_chroma(chunk: TextChunk) -> ChromaMetadata:
        metadata = chunk.metadata
        version = metadata.get("version")
        if not isinstance(version, (str, int, float, bool)):
            version = "unknown"
        normalized = {
            key: value
            for key, value in metadata.items()
            if isinstance(value, (str, int, float, bool))
        }
        normalized.update({
            "source": str(metadata.get("source") or ""),
            "source_id": str(metadata.get("source_id") or chunk.source_id),
            "title": str(metadata.get("title") or chunk.title),
            "url": str(metadata.get("url") or ""),
            "space_key": str(metadata.get("space_key") or ""),
            "version": version,
            "chunk_index": int(metadata.get("chunk_index", chunk.chunk_index)),
        })
        return normalized

    def delete_source(self, source_id: str) -> None:
        if source_id:
            self.collection.delete(where={"source_id": source_id})

    def replace_source_chunks(
        self, chunks: list[TextChunk], embeddings: list[list[float]]
    ) -> None:
        if not chunks:
            return
        self.delete_source(chunks[0].source_id)
        self.upsert_chunks(chunks, embeddings)

    def upsert_chunks(
        self, chunks: list[TextChunk], embeddings: list[list[float]]
    ) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("A quantidade de chunks e embeddings deve ser igual.")

        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=embeddings,
            metadatas=[self._metadata_for_chroma(chunk) for chunk in chunks],
        )

    def search(self, query_embedding: list[float], top_k: int = 10) -> dict[str, Any]:
        if top_k < 1:
            raise ValueError("top_k deve ser maior que zero.")
        if not query_embedding:
            raise ValueError("O embedding da consulta não pode estar vazio.")
        if self.count() == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"],
        )

    def count(self) -> int:
        return self.collection.count()
