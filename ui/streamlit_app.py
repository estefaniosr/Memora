"""Local Streamlit application for Memora."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

import streamlit as st

from app.config import ConfigurationError
from connectors.confluence_client import ConfluenceAPIError
from llm import LLMProviderError
from services.memora_service import MemoraService, MemoraServiceError
from ui.components import (
    render_footer,
    render_header,
    render_search_results,
    render_sidebar_config,
    render_sources_table,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")
EXPECTED_ERRORS = (
    ConfigurationError,
    ConfluenceAPIError,
    LLMProviderError,
    MemoraServiceError,
    ValueError,
)

st.set_page_config(
    page_title="Memora",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(scope="session", show_spinner=False)
def get_service() -> MemoraService:
    """Keep heavyweight models and the vector client within one browser session."""
    return MemoraService()


def execute_action(action: Callable[[], T], spinner_text: str) -> T | None:
    try:
        with st.spinner(spinner_text):
            return action()
    except EXPECTED_ERRORS as exc:
        logger.warning("Memora action failed: %s", type(exc).__name__)
        st.error(str(exc))
    except Exception:
        logger.exception("Unexpected Memora UI failure")
        st.error("Ocorreu um erro inesperado. Consulte o terminal para mais detalhes.")
    return None


render_header()

try:
    service = get_service()
    config_status = service.get_config_status()
    vector_count = service.get_vector_count()
except EXPECTED_ERRORS as exc:
    logger.warning("Memora configuration failed: %s", type(exc).__name__)
    st.error(f"Não foi possível carregar a configuração: {exc}")
    st.info("Revise o arquivo .env e reinicie a aplicação.")
    st.stop()
except Exception:
    logger.exception("Unexpected Memora startup failure")
    st.error("Não foi possível iniciar o Memora. Consulte o terminal.")
    st.stop()

render_sidebar_config(config_status, vector_count)

analyze_tab, search_tab, sync_tab, about_tab = st.tabs(
    [
        "Analisar reunião",
        "Busca semântica",
        "Sincronizar Confluence",
        "Sobre o projeto",
    ]
)

with analyze_tab:
    st.header("Analisar nova demanda")
    meeting_notes = st.text_area(
        "Cole aqui as anotações da reunião ou os requisitos iniciais da nova demanda",
        value=(
            "Cliente precisa de um portal web B2B com login, dashboard, cadastro "
            "de clientes, permissões por perfil e integração com API externa para "
            "consultar status de solicitações."
        ),
        height=190,
    )
    analyze_top_k = st.number_input(
        "Quantidade de trechos para análise",
        min_value=3,
        max_value=15,
        value=min(15, max(3, service.settings.rag_top_k)),
        step=1,
        key="analyze_top_k",
    )
    if st.button("Analisar demanda", type="primary", use_container_width=True):
        if not meeting_notes.strip():
            st.warning("Cole as anotações da reunião antes de analisar.")
        else:
            analysis = execute_action(
                lambda: service.analyze_meeting_notes(
                    meeting_notes, top_k=int(analyze_top_k)
                ),
                "Recuperando projetos semelhantes e gerando a análise...",
            )
            if analysis is not None:
                st.subheader("Análise de reaproveitamento")
                st.markdown(analysis["answer"])
                render_sources_table(analysis["sources"])
                render_search_results(
                    analysis["sources"], heading="Trechos recuperados"
                )

with search_tab:
    st.header("Busca semântica")
    query = st.text_area(
        "Descreva o projeto, requisito ou problema que deseja localizar",
        placeholder="Ex.: sistema de chamados com SLA, status e histórico",
        height=120,
    )
    search_top_k = st.number_input(
        "Quantidade de resultados",
        min_value=3,
        max_value=15,
        value=min(15, max(3, service.settings.rag_top_k)),
        step=1,
        key="search_top_k",
    )
    if st.button("Buscar projetos semelhantes", use_container_width=True):
        if not query.strip():
            st.warning("Digite uma descrição antes de buscar.")
        else:
            search_results = execute_action(
                lambda: service.semantic_search(query, top_k=int(search_top_k)),
                "Buscando conhecimento semelhante...",
            )
            if search_results is not None:
                render_search_results(search_results)

with sync_tab:
    st.header("Sincronizar Confluence")
    first, second = st.columns(2)
    first.metric("Espaço configurado", service.settings.confluence_space_key)
    second.metric("Chunks atuais", service.get_vector_count())
    page_limit = st.number_input(
        "Limite de páginas nesta sincronização",
        min_value=1,
        max_value=100,
        value=50,
        step=1,
    )
    st.info(
        "Essa operação pode demorar na primeira execução porque o modelo de "
        "embeddings pode ser baixado localmente."
    )
    if st.button("Sincronizar agora", type="primary", use_container_width=True):
        sync_result = execute_action(
            lambda: service.sync_confluence(limit=int(page_limit)),
            "Buscando e indexando páginas do Confluence...",
        )
        if sync_result is not None:
            if sync_result["pages_found"] == 0:
                st.warning("Nenhuma página foi encontrada no espaço configurado.")
            else:
                st.success("Sincronização concluída.")
                columns = st.columns(4)
                columns[0].metric("Páginas encontradas", sync_result["pages_found"])
                columns[1].metric(
                    "Documentos processados", sync_result["documents_processed"]
                )
                columns[2].metric("Chunks indexados", sync_result["chunks_indexed"])
                columns[3].metric("Total de chunks", sync_result["total_chunks"])

with about_tab:
    st.header("Sobre o Memora")
    st.write(
        "Memora é uma aplicação de IA baseada em RAG para recuperar conhecimento "
        "de documentações antigas e sugerir reaproveitamento técnico em novas "
        "demandas de software."
    )
    st.subheader("Arquitetura")
    st.code(
        "Confluence\n"
        "→ API\n"
        "→ Extração de conteúdo\n"
        "→ Limpeza HTML\n"
        "→ Chunks\n"
        "→ Embeddings\n"
        "→ ChromaDB\n"
        "→ Busca semântica\n"
        "→ LLM\n"
        "→ Análise de reaproveitamento",
        language=None,
    )
    st.subheader("Próximos passos")
    st.markdown(
        "- Leitura de anexos PDF/DOCX\n"
        "- OCR\n"
        "- Integração com Azure DevOps\n"
        "- Integração com Jira\n"
        "- Autenticação\n"
        "- Deploy\n"
        "- Avaliação da qualidade das respostas"
    )

render_footer()
