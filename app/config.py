"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
DEFAULT_CHROMA_DB_PATH = "./chroma_db"
DEFAULT_CHROMA_COLLECTION_NAME = "memora_projects"
DEFAULT_LLM_PROVIDER = "ollama"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_RAG_TOP_K = 8
DEFAULT_RAG_MAX_CONTEXT_CHARS = 12000
SUPPORTED_LLM_PROVIDERS = {"ollama", "openai", "gemini"}


class ConfigurationError(ValueError):
    """Raised when required application configuration is missing."""


@dataclass(frozen=True, slots=True)
class Settings:
    confluence_base_url: str
    confluence_email: str
    confluence_api_token: str
    confluence_space_key: str
    embedding_model: str
    chroma_db_path: str
    chroma_collection_name: str
    llm_provider: str
    openai_api_key: str
    openai_model: str
    gemini_api_key: str
    gemini_model: str
    ollama_base_url: str
    ollama_model: str
    rag_top_k: int
    rag_max_context_chars: int


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} deve ser um número inteiro positivo.") from exc
    if value < 1:
        raise ConfigurationError(f"{name} deve ser maior que zero.")
    return value


def load_settings() -> Settings:
    """Load and validate settings from a local .env file or the environment."""
    load_dotenv()

    variable_names = (
        "CONFLUENCE_BASE_URL",
        "CONFLUENCE_EMAIL",
        "CONFLUENCE_API_TOKEN",
        "CONFLUENCE_SPACE_KEY",
    )
    values = {name: os.getenv(name, "").strip() for name in variable_names}
    missing = [name for name, value in values.items() if not value]

    if missing:
        raise ConfigurationError(
            "Variáveis de ambiente obrigatórias ausentes: " + ", ".join(missing)
        )

    llm_provider = os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower()
    if llm_provider not in SUPPORTED_LLM_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_LLM_PROVIDERS))
        raise ConfigurationError(
            f"LLM_PROVIDER inválido: '{llm_provider}'. Use um destes valores: {supported}."
        )

    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model = os.getenv("OPENAI_MODEL", "").strip()
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "").strip()

    if llm_provider == "openai":
        missing_openai = []
        if not openai_api_key:
            missing_openai.append("OPENAI_API_KEY")
        if not openai_model:
            missing_openai.append("OPENAI_MODEL")
        if missing_openai:
            raise ConfigurationError(
                "Configuração obrigatória para OpenAI ausente: "
                + ", ".join(missing_openai)
            )

    if llm_provider == "gemini":
        missing_gemini = []
        if not gemini_api_key:
            missing_gemini.append("GEMINI_API_KEY")
        if not gemini_model:
            missing_gemini.append("GEMINI_MODEL")
        if missing_gemini:
            raise ConfigurationError(
                "Configuração obrigatória para Gemini ausente: "
                + ", ".join(missing_gemini)
            )

    return Settings(
        confluence_base_url=values["CONFLUENCE_BASE_URL"].rstrip("/"),
        confluence_email=values["CONFLUENCE_EMAIL"],
        confluence_api_token=values["CONFLUENCE_API_TOKEN"],
        confluence_space_key=values["CONFLUENCE_SPACE_KEY"],
        embedding_model=os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL).strip()
        or DEFAULT_EMBEDDING_MODEL,
        chroma_db_path=os.getenv("CHROMA_DB_PATH", DEFAULT_CHROMA_DB_PATH).strip()
        or DEFAULT_CHROMA_DB_PATH,
        chroma_collection_name=os.getenv(
            "CHROMA_COLLECTION_NAME", DEFAULT_CHROMA_COLLECTION_NAME
        ).strip()
        or DEFAULT_CHROMA_COLLECTION_NAME,
        llm_provider=llm_provider,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        ollama_base_url=os.getenv(
            "OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL
        ).strip().rstrip("/")
        or DEFAULT_OLLAMA_BASE_URL,
        ollama_model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()
        or DEFAULT_OLLAMA_MODEL,
        rag_top_k=_positive_int("RAG_TOP_K", DEFAULT_RAG_TOP_K),
        rag_max_context_chars=_positive_int(
            "RAG_MAX_CONTEXT_CHARS", DEFAULT_RAG_MAX_CONTEXT_CHARS
        ),
    )
