"""HTTP entry point for the Alpine.js interface."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import Settings, load_settings
from rag.answer_parser import parse_answer_sections
from services.memora_service import MemoraService

ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "ui" / "index.html"

app = FastAPI(title="Memora", docs_url="/api/docs", redoc_url=None)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)
    top_k: int = Field(default=8, ge=1, le=50)


class AnalysisRequest(SearchRequest):
    provider: Literal["ollama", "openai", "gemini"] | None = None
    model: str | None = Field(default=None, max_length=200)


class SyncRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)


@lru_cache(maxsize=1)
def get_service() -> MemoraService:
    return MemoraService()


def _settings_for_model(
    settings: Settings, provider: str | None, model: str | None
) -> Settings:
    if not provider or not model:
        return settings
    model = model.strip()
    if not model:
        raise HTTPException(422, "Selecione um modelo válido.")
    changes: dict[str, str] = {"llm_provider": provider}
    changes[f"{provider}_model"] = model
    return replace(settings, **changes)


def _configured_model(settings: Settings, provider: str) -> str:
    return str(getattr(settings, f"{provider}_model", "") or "")


def _is_generation_model(
    provider: str, model_name: str, family: str = ""
) -> bool:
    name = model_name.removeprefix("models/").lower()
    if provider == "openai":
        return name.startswith(("gpt-", "chatgpt-", "o1", "o3", "o4"))
    if provider == "gemini":
        return name.startswith("gemini-")
    if provider == "ollama":
        return "embed" not in name and family.lower() not in {"bert", "nomic-bert"}
    return False


def _available_models(settings: Settings, provider: str) -> list[str]:
    configured = _configured_model(settings, provider)
    try:
        if provider == "ollama":
            response = requests.get(
                f"{settings.ollama_base_url}/api/tags", timeout=4
            )
            response.raise_for_status()
            models = [
                str(item.get("name", ""))
                for item in response.json().get("models", [])
                if item.get("name")
                and _is_generation_model(
                    provider,
                    str(item.get("name", "")),
                    str((item.get("details") or {}).get("family", "")),
                )
            ]
        elif provider == "openai" and settings.openai_api_key:
            from openai import OpenAI

            models = sorted(
                item.id
                for item in OpenAI(api_key=settings.openai_api_key).models.list()
                if _is_generation_model(provider, item.id)
            )
        elif provider == "gemini" and settings.gemini_api_key:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
            models = sorted(
                model.name.removeprefix("models/")
                for model in client.models.list()
                if model.name
                and _is_generation_model(provider, model.name)
                and "generateContent" in (model.supported_actions or [])
            )
        else:
            models = []
    except Exception:
        models = []
    if configured and _is_generation_model(provider, configured) and configured not in models:
        models.insert(0, configured)
    return models


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(INDEX_FILE)


@app.get("/api/status")
def status() -> dict[str, Any]:
    service = get_service()
    vector_count = service.get_vector_count()
    settings = service.settings
    provider_ready = {
        "ollama": bool(settings.ollama_base_url and settings.ollama_model),
        "openai": bool(settings.openai_api_key and settings.openai_model),
        "gemini": bool(settings.gemini_api_key and settings.gemini_model),
    }
    return {
        "ready": vector_count > 0,
        "document_count": service.get_document_count(),
        "vector_count": vector_count,
        "provider": settings.llm_provider,
        "confluence_configured": all(
            (
                settings.confluence_base_url,
                settings.confluence_email,
                settings.confluence_api_token,
                settings.confluence_space_key,
            )
        ),
        "vector_store_ready": vector_count > 0,
        "embedding_configured": bool(settings.embedding_model),
        "llm_configured": provider_ready[settings.llm_provider],
    }


@app.get("/api/models")
def models(
    provider: Literal["ollama", "openai", "gemini"] = Query(...)
) -> dict[str, Any]:
    settings = get_service().settings
    available = _available_models(settings, provider)
    return {"provider": provider, "models": available}


@app.post("/api/search")
def search(payload: SearchRequest) -> dict[str, Any]:
    try:
        results = get_service().semantic_search(payload.query, payload.top_k)
        return {"results": results}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/analyze")
def analyze(payload: AnalysisRequest) -> dict[str, Any]:
    base = get_service()
    try:
        if payload.provider and payload.model:
            if not _is_generation_model(payload.provider, payload.model):
                raise HTTPException(
                    422,
                    "O modelo selecionado não está disponível para este provider.",
                )
        settings = _settings_for_model(
            base.settings, payload.provider, payload.model
        )
        service = MemoraService(
            settings=settings,
            embedding_model=base.embedding_model,
            vector_store=base.vector_store,
        )
        result = service.analyze_meeting_notes(payload.query, payload.top_k)
        return {
            **result,
            "sections": parse_answer_sections(str(result.get("answer", ""))),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/sync")
def sync(payload: SyncRequest) -> dict[str, int]:
    try:
        return get_service().sync_confluence(payload.limit)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
