"""Reusable presentation components for the Streamlit interface."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_header() -> None:
    st.title("Memora")
    st.caption(
        "Assistente de IA para reaproveitamento de conhecimento em projetos corporativos."
    )


def render_sidebar_config(
    status: dict[str, str | bool], vector_count: int
) -> None:
    with st.sidebar:
        st.header("Status da configuração")
        if status["confluence_base_url_configured"]:
            st.success("Confluence URL configurada")
        else:
            st.error("Confluence URL não configurada")

        if status["confluence_email_configured"]:
            st.success("E-mail do Confluence configurado")
        else:
            st.error("E-mail do Confluence não configurado")

        st.text(f"Espaço: {status['confluence_space_key']}")
        st.text(f"LLM: {status['llm_provider']}")
        st.text(f"Modelo LLM: {status['llm_model']}")
        st.text(f"Coleção: {status['chroma_collection_name']}")
        st.metric("Chunks indexados", vector_count)

        with st.expander("Modelo de embeddings"):
            st.code(str(status["embedding_model"]), language=None)

        st.caption("Credenciais e tokens nunca são exibidos nesta interface.")


def render_sources_table(sources: list[dict[str, Any]]) -> None:
    st.subheader("Fontes usadas")
    if not sources:
        st.warning("Nenhuma fonte foi recuperada.")
        return

    rows = [
        {
            "Rank": source["rank"],
            "Título": source["title"],
            "Chunk": source["chunk_index"],
            "Distância": source["distance"],
            "Similaridade": 100
            * max(0.0, min(1.0, 1.0 - source["distance"])),
            "URL": source.get("url") or "",
        }
        for source in sources
    ]
    st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
        column_config={
            "Distância": st.column_config.NumberColumn(format="%.4f"),
            "Similaridade": st.column_config.ProgressColumn(
                min_value=0.0, max_value=100.0, format="%.1f%%"
            ),
            "URL": st.column_config.LinkColumn("Confluence", display_text="Abrir"),
        },
    )


def render_search_results(
    results: list[dict[str, Any]], heading: str = "Projetos e documentos semelhantes"
) -> None:
    st.subheader(heading)
    if not results:
        st.warning("Nenhum resultado semelhante foi encontrado.")
        return

    for result in results:
        distance = float(result["distance"])
        similarity = max(0.0, min(1.0, 1.0 - distance))
        label = (
            f"#{result['rank']} — {result['title']} "
            f"(distância {distance:.4f})"
        )
        with st.expander(label, expanded=result["rank"] == 1):
            first, second, third = st.columns(3)
            first.metric("Chunk", result["chunk_index"])
            second.metric("Distância", f"{distance:.4f}")
            third.metric("Similaridade", f"{similarity:.1%}")
            if result.get("url"):
                st.link_button("Abrir no Confluence", result["url"])
            st.markdown("**Trecho recuperado**")
            st.write(result.get("content") or "Trecho indisponível.")


def render_footer() -> None:
    st.divider()
    st.caption(
        "Memora · conhecimento corporativo recuperável, rastreável e reutilizável."
    )
