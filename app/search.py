"""Search the local Memora vector collection from the terminal."""

from __future__ import annotations

import sys
from typing import Any

from rich.console import Console
from rich.table import Table

from app.config import ConfigurationError, load_settings
from indexing.embeddings import EmbeddingModel
from indexing.vector_store import VectorStore

console = Console()


def _first_result_list(results: dict[str, Any], key: str) -> list[Any]:
    value = results.get(key) or []
    return value[0] if value and isinstance(value[0], list) else []


def run(query: str) -> None:
    settings = load_settings()
    vector_store = VectorStore(
        db_path=settings.chroma_db_path,
        collection_name=settings.chroma_collection_name,
    )
    if vector_store.count() == 0:
        console.print(
            "[yellow]A base vetorial está vazia. Execute primeiro:[/yellow] "
            "[bold]python -m app.index_confluence[/bold]"
        )
        return

    console.print(
        f"Carregando modelo de embeddings [cyan]{settings.embedding_model}[/cyan]..."
    )
    embedding_model = EmbeddingModel(settings.embedding_model)
    results = vector_store.search(embedding_model.embed_query(query), top_k=8)

    documents = _first_result_list(results, "documents")
    metadatas = _first_result_list(results, "metadatas")
    distances = _first_result_list(results, "distances")

    table = Table(title=f'Resultados para: "{query}"', show_lines=True)
    table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
    table.add_column("Título", style="bold")
    table.add_column("Chunk", justify="right")
    table.add_column("Distância", justify="right")
    table.add_column("Trecho", max_width=70)

    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None
        excerpt = " ".join(str(document).split())[:280]
        if len(" ".join(str(document).split())) > 280:
            excerpt += "…"
        table.add_row(
            str(index + 1),
            str(metadata.get("title", "Sem título")),
            str(metadata.get("chunk_index", "-")),
            f"{float(distance):.4f}" if distance is not None else "-",
            excerpt,
        )

    console.print(table)


def main() -> None:
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        console.print(
            '[yellow]Uso:[/yellow] python -m app.search "portal com login dashboard e permissões"'
        )
        raise SystemExit(1)

    try:
        run(query)
    except (ConfigurationError, ValueError) as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
