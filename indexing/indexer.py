"""Orchestration for document chunking, embedding, and persistence."""

from __future__ import annotations

from rich.console import Console

from indexing.chunker import chunk_text
from indexing.embeddings import EmbeddingModel
from indexing.vector_store import VectorStore
from models.source_document import SourceDocument


class DocumentIndexer:
    def __init__(
        self,
        embedding_model: EmbeddingModel,
        vector_store: VectorStore,
        console: Console | None = None,
    ) -> None:
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.console = console or Console()

    def index_documents(self, documents: list[SourceDocument]) -> None:
        total_chunks = 0

        for position, document in enumerate(documents, start=1):
            self.console.print(
                f"[cyan][{position}/{len(documents)}][/cyan] Processando "
                f"[bold]{document.title}[/bold]"
            )
            metadata = {
                **document.metadata,
                "source": document.source,
                "source_id": document.source_id,
                "title": document.title,
                "url": document.url,
                "space_key": document.space_key,
                "version": document.version,
            }
            chunks = chunk_text(
                source_id=document.source_id,
                title=document.title,
                content=document.content,
                metadata=metadata,
            )
            if not chunks:
                self.console.print("  [yellow]Documento vazio; nenhum chunk criado.[/yellow]")
                continue

            embeddings = self.embedding_model.embed_texts(
                [chunk.content for chunk in chunks]
            )
            self.vector_store.upsert_chunks(chunks, embeddings)
            total_chunks += len(chunks)
            self.console.print(f"  [green]{len(chunks)} chunk(s) indexado(s).[/green]")

        self.console.print("\n[bold green]Indexação concluída.[/bold green]")
        self.console.print(f"Documentos processados: [bold]{len(documents)}[/bold]")
        self.console.print(f"Chunks criados nesta execução: [bold]{total_chunks}[/bold]")
        self.console.print(
            f"Registros atuais no ChromaDB: [bold]{self.vector_store.count()}[/bold]"
        )
