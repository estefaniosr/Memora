"""Command-line entry point for testing the Confluence integration."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.config import ConfigurationError, load_settings
from connectors.confluence_client import ConfluenceAPIError, ConfluenceClient
from extractors.html_cleaner import clean_confluence_html
from models.source_document import SourceDocument

console = Console()


def _print_spaces(payload: dict[str, Any]) -> None:
    table = Table(title="Espaços disponíveis")
    table.add_column("Chave", style="cyan")
    table.add_column("Nome")

    spaces = payload.get("results", [])
    for space in spaces:
        table.add_row(str(space.get("key", "-")), str(space.get("name", "-")))

    if spaces:
        console.print(table)
    else:
        console.print("[yellow]Nenhum espaço encontrado.[/yellow]")


def _page_summary(page: dict[str, Any]) -> tuple[str, str]:
    content = page.get("content") or page
    return str(content.get("id", "")), str(content.get("title", "Sem título"))


def _build_document(
    page: dict[str, Any], *, base_url: str, fallback_title: str
) -> SourceDocument:
    page_id = str(page.get("id", ""))
    links = page.get("_links") or {}
    web_ui_path = links.get("webui")
    return SourceDocument(
        source="confluence",
        source_id=page_id,
        title=str(page.get("title") or fallback_title),
        url=f"{base_url}{web_ui_path}" if web_ui_path else None,
        content=clean_confluence_html(
            str(page.get("body", {}).get("storage", {}).get("value", ""))
        ),
        space_key=page.get("space", {}).get("key"),
        version=page.get("version", {}).get("number"),
        metadata={
            "content_type": page.get("type"),
            "created_by": page.get("history", {})
            .get("createdBy", {})
            .get("displayName"),
        },
    )


def run() -> None:
    """Run a small end-to-end Confluence API smoke test."""
    settings = load_settings()
    client = ConfluenceClient(
        base_url=settings.confluence_base_url,
        email=settings.confluence_email,
        api_token=settings.confluence_api_token,
    )

    console.print("[bold green]Memora[/bold green] — teste de conexão com o Confluence")
    _print_spaces(client.list_spaces())

    console.print(
        f"\nBuscando páginas no espaço [bold cyan]{settings.confluence_space_key}[/bold cyan]..."
    )
    results = client.search_pages(settings.confluence_space_key).get("results", [])
    if not results:
        console.print("[yellow]Nenhuma página encontrada nesse espaço.[/yellow]")
        return

    for search_result in results[:3]:
        page_id, search_title = _page_summary(search_result)
        if not page_id:
            console.print("[yellow]Resultado ignorado: página sem ID.[/yellow]")
            continue

        page = client.get_page_content(page_id)
        document = _build_document(
            page,
            base_url=settings.confluence_base_url,
            fallback_title=search_title,
        )
        preview = document.content[:800]
        if len(document.content) > 800:
            preview += "…"

        console.print(
            Panel(
                preview or "[dim]Página sem conteúdo textual.[/dim]",
                title=document.title,
                subtitle=f"ID: {document.source_id} | Versão: {document.version or '-'}",
                border_style="blue",
            )
        )


def main() -> None:
    try:
        run()
    except (ConfigurationError, ConfluenceAPIError) as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
