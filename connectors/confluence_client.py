"""Small client for the Confluence Cloud REST API."""

from __future__ import annotations

from typing import Any

import requests
from requests.auth import HTTPBasicAuth


class ConfluenceAPIError(RuntimeError):
    """Raised when the Confluence API cannot fulfill a request."""


class ConfluenceClient:
    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        timeout: float = 20.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(email, api_token)
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except requests.Timeout as exc:
            raise ConfluenceAPIError(
                f"A API do Confluence excedeu o tempo limite de {self.timeout:g}s."
            ) from exc
        except requests.ConnectionError as exc:
            raise ConfluenceAPIError(
                "Não foi possível conectar à API do Confluence. Verifique a URL e a rede."
            ) from exc
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "desconhecido"
            detail = self._error_detail(exc.response)
            raise ConfluenceAPIError(
                f"A API do Confluence retornou HTTP {status}: {detail}"
            ) from exc
        except requests.RequestException as exc:
            raise ConfluenceAPIError(f"Falha ao consultar o Confluence: {exc}") from exc

        try:
            payload = response.json()
        except requests.JSONDecodeError as exc:
            raise ConfluenceAPIError(
                "A API do Confluence retornou uma resposta que não é JSON válido."
            ) from exc

        if not isinstance(payload, dict):
            raise ConfluenceAPIError("A API do Confluence retornou um formato inesperado.")
        return payload

    @staticmethod
    def _error_detail(response: requests.Response | None) -> str:
        if response is None:
            return "erro sem detalhes"
        try:
            payload = response.json()
            return str(payload.get("message") or payload.get("errorMessage") or response.reason)
        except (ValueError, AttributeError):
            return response.reason or "erro sem detalhes"

    def list_spaces(self) -> dict[str, Any]:
        return self._get("/rest/api/space")

    def search_pages(
        self, space_key: str, limit: int = 10, start: int = 0
    ) -> dict[str, Any]:
        if limit < 1:
            raise ValueError("O limite deve ser maior que zero.")
        if start < 0:
            raise ValueError("A posição inicial não pode ser negativa.")
        # Stable ordering prevents records from moving between pagination batches.
        cql = f'space="{space_key}" AND type=page ORDER BY id'
        return self._get(
            "/rest/api/search",
            params={"cql": cql, "limit": limit, "start": start},
        )

    def get_all_pages(
        self, space_key: str, page_size: int = 25, max_pages: int | None = None
    ) -> list[dict[str, Any]]:
        """Fetch every page from a space, following cursor pagination."""
        if page_size < 1:
            raise ValueError("O tamanho da página deve ser maior que zero.")
        if max_pages is not None and max_pages < 1:
            raise ValueError("O limite de páginas deve ser maior que zero.")

        pages: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        seen_next_links: set[str] = set()
        payload = self.search_pages(space_key, limit=page_size)

        while True:
            batch = payload.get("results", [])
            if not isinstance(batch, list) or not batch:
                break

            for result in batch:
                content = result.get("content") or result
                content_id = str(content.get("id", ""))
                if content_id and content_id in seen_ids:
                    continue
                if content_id:
                    seen_ids.add(content_id)
                pages.append(result)
                if max_pages is not None and len(pages) >= max_pages:
                    return pages

            next_link = (payload.get("_links") or {}).get("next")
            if not next_link or next_link in seen_next_links:
                break
            seen_next_links.add(next_link)
            payload = self._get(next_link)

        return pages

    def get_page_content(self, page_id: str) -> dict[str, Any]:
        return self._get(
            f"/rest/api/content/{page_id}",
            params={"expand": "body.storage,version,space,history"},
        )
