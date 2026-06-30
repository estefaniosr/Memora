"""Generate a grounded technical-reuse analysis from meeting notes."""

from __future__ import annotations

import sys
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from app.config import ConfigurationError, load_settings
from indexing.embeddings import EmbeddingModel
from indexing.vector_store import VectorStore
from llm import LLMProviderError, create_llm_provider
from rag.answer_generator import AnswerGenerator
from rag.retriever import RagRetriever

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
        f"[bold green]Memora[/bold green] — análise RAG com provider "
        f"[cyan]{settings.llm_provider}[/cyan]"
    )
    console.print(
        f"Carregando modelo de embeddings [cyan]{settings.embedding_model}[/cyan]..."
    )
    embedding_model = EmbeddingModel(settings.embedding_model)
    retriever = RagRetriever(embedding_model, vector_store)
    llm_provider = create_llm_provider(settings)
    generator = AnswerGenerator(
        retriever,
        llm_provider,
        max_context_chars=settings.rag_max_context_chars,
    )

    with console.status("Recuperando documentos e gerando análise..."):
        result = generator.generate_answer(meeting_notes, top_k=settings.rag_top_k)

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
    except (ConfigurationError, LLMProviderError, ValueError) as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
