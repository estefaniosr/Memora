"""Generate a grounded technical-reuse analysis from meeting notes."""

from __future__ import annotations

import sys
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from app.config import ConfigurationError, load_settings
from llm import LLMProviderError
from services.memora_service import MemoraService, MemoraServiceError

console = Console()


def _print_sources(sources: list[dict[str, Any]]) -> None:
    table = Table(title="Fontes usadas", show_lines=True)
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Título", style="bold")
    table.add_column("Chunk", justify="right")
    table.add_column("Distância", justify="right")
    table.add_column("URL", overflow="fold")

    for source in sources:
        table.add_row(
            str(source["rank"]),
            str(source["title"]),
            str(source["chunk_index"]),
            f"{source['distance']:.4f}",
            str(source["url"] or "-"),
        )
    console.print(table)


def run(meeting_notes: str) -> None:
    settings = load_settings()
    service = MemoraService(settings=settings)

    console.print(
        f"[bold green]Memora[/bold green] — análise RAG com provider "
        f"[cyan]{settings.llm_provider}[/cyan]"
    )
    console.print(
        f"Carregando modelo de embeddings [cyan]{settings.embedding_model}[/cyan]..."
    )
    with console.status("Recuperando documentos e gerando análise..."):
        result = service.analyze_meeting_notes(
            meeting_notes, top_k=settings.rag_top_k
        )

    console.print("\n[bold green]Análise[/bold green]")
    console.print(Markdown(result["answer"]))
    console.print()
    _print_sources(result["sources"])


def main() -> None:
    meeting_notes = " ".join(sys.argv[1:]).strip()
    if not meeting_notes:
        console.print(
            '[yellow]Uso:[/yellow] python -m app.analyze '
            '"portal com login dashboard permissões"'
        )
        raise SystemExit(1)

    try:
        run(meeting_notes)
    except (
        ConfigurationError,
        LLMProviderError,
        MemoraServiceError,
        ValueError,
    ) as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
