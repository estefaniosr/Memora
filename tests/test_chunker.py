from indexing.chunker import chunk_text


def test_chunk_text_returns_chunks_for_valid_content() -> None:
    chunks = chunk_text("page-1", "Projeto", "conteúdo útil " * 200, {"version": 3})

    assert chunks
    assert all(chunk.content for chunk in chunks)


def test_chunk_text_returns_empty_list_for_empty_content() -> None:
    assert chunk_text("page-1", "Projeto", "  ", {"version": 3}) == []


def test_chunk_id_contains_source_id_and_version() -> None:
    chunks = chunk_text("page-42", "Projeto", "texto principal", {"version": 7})

    assert chunks[0].chunk_id == "page-42:v7:chunk:0"


def test_chunk_text_uses_overlap() -> None:
    content = "0123456789" * 30
    chunks = chunk_text("page-1", "Projeto", content, {}, chunk_size=100, overlap=20)

    assert len(chunks) > 1
    assert chunks[0].content[-20:] == chunks[1].content[:20]


def test_chunk_text_always_advances_with_large_overlap() -> None:
    chunks = chunk_text(
        "page-1", "Projeto", "abcdefg hijabcdefghij", {}, chunk_size=10, overlap=9
    )

    assert chunks
    assert len(chunks) <= len("abcdefg hijabcdefghij")


def test_chunk_text_preserves_scalar_custom_metadata() -> None:
    chunks = chunk_text(
        "page-1", "Projeto", "conteúdo", {"version": 1, "content_type": "page"}
    )

    assert chunks[0].metadata["content_type"] == "page"
