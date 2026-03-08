import httpx

from tool_db_backend.clients.semantic_scholar import SemanticScholarClient
from tool_db_backend.config import get_settings


def test_fetch_paper_passes_fields_and_api_key() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["fields"] = request.url.params.get("fields")
        captured["api_key"] = request.headers.get("x-api-key")
        return httpx.Response(200, json={"paperId": "abc123"})

    transport = httpx.MockTransport(handler)
    settings = get_settings().model_copy(update={"semantic_scholar_api_key": "secret-key"})
    client = SemanticScholarClient(
        settings,
        client=httpx.Client(base_url=settings.semantic_scholar_base_url, transport=transport),
    )

    payload = client.fetch_paper("10.1038/nature12373", fields="title,year")
    client.close()

    assert payload["paperId"] == "abc123"
    assert captured["path"].endswith("/paper/10.1038/nature12373")
    assert captured["fields"] == "title,year"
    assert captured["api_key"] == "secret-key"


def test_search_papers_passes_query_and_limit() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["query"] = request.url.params.get("query")
        captured["limit"] = request.url.params.get("limit")
        captured["offset"] = request.url.params.get("offset")
        return httpx.Response(200, json={"data": []})

    transport = httpx.MockTransport(handler)
    settings = get_settings()
    client = SemanticScholarClient(
        settings,
        client=httpx.Client(base_url=settings.semantic_scholar_base_url, transport=transport),
    )

    payload = client.search_papers("optogenetic switch", limit=25, offset=5, fields="title")
    client.close()

    assert payload == {"data": []}
    assert captured["path"].endswith("/paper/search")
    assert captured["query"] == "optogenetic switch"
    assert captured["limit"] == "25"
    assert captured["offset"] == "5"
