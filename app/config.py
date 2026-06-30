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
    )
