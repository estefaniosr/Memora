from typing import Any

from connectors.confluence_client import ConfluenceClient


def test_get_all_pages_follows_pagination(monkeypatch: Any) -> None:
    client = ConfluenceClient("https://example.atlassian.net/wiki", "email", "token")
    calls: list[str] = []

    def fake_search(space_key: str, limit: int = 10, start: int = 0) -> dict[str, Any]:
        return {
            "results": [{"content": {"id": "0"}}, {"content": {"id": "1"}}],
            "_links": {"next": "/next-1"},
        }

    def fake_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        calls.append(path)
        batches = {
            "/next-1": {
                "results": [{"content": {"id": "2"}}, {"content": {"id": "3"}}],
                "_links": {"next": "/next-2"},
            },
            "/next-2": {
                "results": [{"content": {"id": "4"}}],
                "_links": {},
            },
        }
        return batches[path]

    monkeypatch.setattr(client, "search_pages", fake_search)
    monkeypatch.setattr(client, "_get", fake_get)

    pages = client.get_all_pages("SPACE", page_size=2)

    assert [page["content"]["id"] for page in pages] == ["0", "1", "2", "3", "4"]
    assert calls == ["/next-1", "/next-2"]


def test_get_all_pages_ignores_duplicate_ids(monkeypatch: Any) -> None:
    client = ConfluenceClient("https://example.atlassian.net/wiki", "email", "token")

    def fake_search(space_key: str, limit: int = 10, start: int = 0) -> dict[str, Any]:
        return {
            "results": [{"content": {"id": "1"}}, {"content": {"id": "2"}}],
            "_links": {"next": "/next"},
        }

    def fake_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "results": [{"content": {"id": "2"}}, {"content": {"id": "3"}}],
            "_links": {},
        }

    monkeypatch.setattr(client, "search_pages", fake_search)
    monkeypatch.setattr(client, "_get", fake_get)

    pages = client.get_all_pages("SPACE", page_size=2)

    assert [page["content"]["id"] for page in pages] == ["1", "2", "3"]


def test_get_all_pages_honors_total_limit(monkeypatch: Any) -> None:
    client = ConfluenceClient("https://example.atlassian.net/wiki", "email", "token")
    monkeypatch.setattr(
        client,
        "search_pages",
        lambda space_key, limit=10, start=0: {
            "results": [{"content": {"id": str(index)}} for index in range(5)],
            "_links": {"next": "/next"},
        },
    )

    pages = client.get_all_pages("SPACE", page_size=5, max_pages=3)

    assert [page["content"]["id"] for page in pages] == ["0", "1", "2"]
