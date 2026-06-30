"""Map Confluence API payloads to normalized source documents."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from extractors.html_cleaner import clean_confluence_html
from models.source_document import SourceDocument


def build_confluence_document(
    page: dict[str, Any], *, base_url: str, fallback_title: str
) -> SourceDocument:
    page_id = str(page.get("id", ""))
    web_ui_path = (page.get("_links") or {}).get("webui")
    url = (
        f"{base_url.rstrip('/')}{web_ui_path}"
        if web_ui_path
        else f"{base_url.rstrip('/')}/pages/viewpage.action?pageId={quote(page_id)}"
    )
    return SourceDocument(
        source="confluence",
        source_id=page_id,
        title=str(page.get("title") or fallback_title),
        url=url,
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
