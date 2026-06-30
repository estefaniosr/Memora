"""Index Confluence pages into the local ChromaDB collection."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from rich.console import Console

from app.config import ConfigurationError, load_settings
from connectors.confluence_client import ConfluenceAPIError, ConfluenceClient
from extractors.html_cleaner import clean_confluence_html
from indexing.embeddings import EmbeddingModel
from indexing.indexer import DocumentIndexer
from indexing.vector_store import VectorStore
from models.source_document import SourceDocument

console = Console()


def build_page_url(base_url: str, page_id: str) -> str:
    """Build a stable Confluence reference URL from a page ID."""
    return f"{base_url.rstrip('/')}/pages/viewpage.action?pageId={quote(page_id)}"


def _page_identity(search_result: dict[str, Any]) -> tuple[str, str]:
    page = search_result.get("content") or search_result
    return str(page.get("id", "")), str(page.get("title", "Sem título"))


def _source_document(
    page: dict[str, Any], *, base_url: str, fallback_title: str
) -> SourceDocument:
    page_id = str(page.get("id", ""))
    version = page.get("version", {}).get("number")
    space_key = page.get("space", {}).get("key")
    return SourceDocument(
        source="confluence",
        source_id=page_id,
        title=str(page.get("title") or fallback_title),
        url=build_page_url(base_url, page_id),
        content=clean_confluence_html(
            str(page.get("body", {}).get("storage", {}).get("value", ""))
        ),
        space_key=space_key,
        version=version,
        metadata={"content_type": page.get("type")},
    )


def run() -> None:
    settings = load_settings()
    client = ConfluenceClient(
        base_url=settings.confluence_base_url,
        email=settings.confluence_email,
        api_token=settings.confluence_api_token,
    )

    console.print(
        f"[bold green]Memora[/bold green] — indexando o espaço "
        f"[cyan]{settings.confluence_space_key}[/cyan]"
    )
    search_results = client.get_all_pages(
        settings.confluence_space_key, page_size=50
    )
    if not search_results:
        console.print("[yellow]Nenhuma página encontrada para indexação.[/yellow]")
        return

    documents: list[SourceDocument] = []
    for search_result in search_results:
        page_id, title = _page_identity(search_result)
        if not page_id:
            console.print("[yellow]Página sem ID ignorada.[/yellow]")
            continue
        page = client.get_page_content(page_id)
        documents.append(
            _source_document(
                page,
                base_url=settings.confluence_base_url,
                fallback_title=title,
            )
        )

    console.print(f"[green]{len(documents)} documento(s) preparado(s).[/green]")
    console.print(
        f"Carregando modelo de embeddings [cyan]{settings.embedding_model}[/cyan]..."
    )
    embedding_model = EmbeddingModel(settings.embedding_model)
    vector_store = VectorStore(
        db_path=settings.chroma_db_path,
        collection_name=settings.chroma_collection_name,
    )
    DocumentIndexer(embedding_model, vector_store, console).index_documents(documents)


def main() -> None:
    try:
        run()
    except (ConfigurationError, ConfluenceAPIError, ValueError) as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
