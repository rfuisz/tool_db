import httpx

from tool_db_backend.clients.openalex import OpenAlexClient
from tool_db_backend.config import get_settings


def test_fetch_work_normalizes_identifier_and_passes_mailto() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["mailto"] = request.url.params.get("mailto")
        return httpx.Response(200, json={"id": "https://openalex.org/W2741809807"})

    transport = httpx.MockTransport(handler)
    settings = get_settings().model_copy(update={"openalex_mailto": "test@example.com"})
    client = OpenAlexClient(settings, client=httpx.Client(base_url=settings.openalex_base_url, transport=transport))

    payload = client.fetch_work("https://openalex.org/W2741809807")
    client.close()

    assert payload["id"] == "https://openalex.org/W2741809807"
    assert captured["path"] == "/works/W2741809807"
    assert captured["mailto"] == "test@example.com"
