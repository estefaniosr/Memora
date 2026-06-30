from typing import Any

from indexing.vector_store import VectorStore


class FakeCollection:
    def count(self) -> int:
        return 4

    def get(self, *, include: list[str]) -> dict[str, Any]:
        assert include == ["metadatas"]
        return {
            "metadatas": [
                {"source_id": "page-1"},
                {"source_id": "page-1"},
                {"source_id": "page-2"},
                {},
            ]
        }


def test_document_count_counts_distinct_indexed_sources() -> None:
    store = object.__new__(VectorStore)
    store.collection = FakeCollection()  # type: ignore[assignment]

    assert store.document_count() == 2
