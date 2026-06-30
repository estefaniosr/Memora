"""Normalized source document model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceDocument:
    source: str
    source_id: str
    title: str
    url: str | None
    content: str
    space_key: str | None
    version: int | None
    metadata: dict[str, Any] = field(default_factory=dict)
