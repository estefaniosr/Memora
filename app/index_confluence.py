"""Index Confluence pages into the local ChromaDB collection."""

from __future__ import annotations

from rich.console import Console

from app.config import ConfigurationError, load_settings
from connectors.confluence_client import ConfluenceAPIError
from services.memora_service import MemoraService, MemoraServiceError

console = Console()


def run() -> None:
    settings = load_settings(require_confluence=True)
    console.print(
        f"[bold green]Memora[/bold green] — indexando o espaço "
        f"[cyan]{settings.confluence_space_key}[/cyan]"
    )
    result = MemoraService(settings=settings).sync_confluence(limit=50)
    if result["pages_found"] == 0:
        console.print("[yellow]Nenhuma página encontrada para indexação.[/yellow]")


def main() -> None:
    try:
        run()
    except (
        ConfigurationError,
        ConfluenceAPIError,
        MemoraServiceError,
        ValueError,
    ) as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
