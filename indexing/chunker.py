"""Text chunking with stable identifiers and overlap."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TextChunk:
    chunk_id: str
    source_id: str
    title: str
    content: str
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)


def chunk_text(
    source_id: str,
    title: str,
    content: str,
    metadata: dict[str, Any],
    chunk_size: int = 1400,
    overlap: int = 250,
) -> list[TextChunk]:
    """Split text into overlapping chunks, preferring natural boundaries."""
    if not content or not content.strip():
        return []
    if chunk_size < 1:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between zero and chunk_size - 1")

    normalized_content = content.strip()
    version = metadata.get("version", "unknown")
    if version is None:
        version = "unknown"

    chunks: list[TextChunk] = []
    start = 0

    while start < len(normalized_content):
        proposed_end = min(start + chunk_size, len(normalized_content))
        end = proposed_end

        if proposed_end < len(normalized_content):
            boundary_floor = start + int(chunk_size * 0.7)
            newline = normalized_content.rfind("\n", boundary_floor, proposed_end)
            space = normalized_content.rfind(" ", boundary_floor, proposed_end)
            natural_boundary = max(newline, space)
            if natural_boundary > start:
                end = natural_boundary

        chunk_content = normalized_content[start:end].strip()
        if chunk_content:
            chunk_index = len(chunks)
            chunk_metadata = {
                "source": metadata.get("source", ""),
                "source_id": source_id,
                "title": title,
                "url": metadata.get("url"),
                "space_key": metadata.get("space_key"),
                "version": version,
                "chunk_index": chunk_index,
            }
            chunks.append(
                TextChunk(
                    chunk_id=f"{source_id}:v{version}:chunk:{chunk_index}",
                    source_id=source_id,
                    title=title,
                    content=chunk_content,
                    chunk_index=chunk_index,
                    metadata=chunk_metadata,
                )
            )

        if end >= len(normalized_content):
            break
        start = end - overlap

    return chunks
