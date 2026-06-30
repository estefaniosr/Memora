"""Search the local Memora vector collection from the terminal."""

from __future__ import annotations

import sys
from rich.console import Console
from rich.table import Table

from app.config import ConfigurationError, load_settings
from services.memora_service import MemoraService, MemoraServiceError

console = Console()


def run(query: str) -> None:
    settings = load_settings()
    service = MemoraService(settings=settings)
    console.print(
        f"Carregando modelo de embeddings [cyan]{settings.embedding_model}[/cyan]..."
    )
    results = service.semantic_search(query, top_k=settings.rag_top_k)

    table = Table(title=f'Resultados para: "{query}"', show_lines=True)
    table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
    table.add_column("Título", style="bold")
    table.add_column("Chunk", justify="right")
    table.add_column("Distância", justify="right")
    table.add_column("Trecho", max_width=70)

    for result in results:
        document = result["content"]
        distance = result["distance"]
        excerpt = " ".join(str(document).split())[:280]
        if len(" ".join(str(document).split())) > 280:
            excerpt += "…"
        table.add_row(
            str(result["rank"]),
            str(result["title"]),
            str(result["chunk_index"]),
            f"{float(distance):.4f}",
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
    except (ConfigurationError, MemoraServiceError, ValueError) as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
