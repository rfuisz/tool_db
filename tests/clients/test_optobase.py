import httpx

from tool_db_backend.clients.optobase import OptoBaseClient
from tool_db_backend.config import get_settings


def test_fetch_optobase_search_page_passes_query() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["query"] = request.url.params.get("q")
        return httpx.Response(200, text="<html>result</html>")

    transport = httpx.MockTransport(handler)
    settings = get_settings()
    client = OptoBaseClient(
        settings,
        client=httpx.Client(base_url=settings.optobase_base_url, transport=transport),
    )

    payload = client.fetch_search_page("AsLOV2")
    client.close()

    assert payload == "<html>result</html>"
    assert captured["path"].endswith("/search/")
    assert captured["query"] == "AsLOV2"
