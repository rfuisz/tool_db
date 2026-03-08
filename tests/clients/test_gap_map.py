import httpx

from tool_db_backend.clients.gap_map import GapMapClient
from tool_db_backend.config import get_settings


def test_fetch_gapmap_dataset_uses_expected_path() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(200, json={"items": []})

    transport = httpx.MockTransport(handler)
    settings = get_settings()
    client = GapMapClient(
        settings,
        client=httpx.Client(base_url=settings.gap_map_base_url, transport=transport),
    )

    payload = client.fetch_dataset("gaps")
    client.close()

    assert payload == {"items": []}
    assert captured["path"].endswith("/data/gaps.json")
