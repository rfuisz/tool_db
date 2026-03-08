import httpx

from tool_db_backend.clients.clinicaltrials import ClinicalTrialsClient
from tool_db_backend.config import get_settings


def test_fetch_study_normalizes_nct_id() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["format"] = request.url.params.get("format")
        return httpx.Response(200, json={"studies": [{"protocolSection": {"identificationModule": {"nctId": "NCT04280705"}}}]})

    transport = httpx.MockTransport(handler)
    settings = get_settings()
    client = ClinicalTrialsClient(
        settings,
        client=httpx.Client(base_url=settings.clinicaltrials_base_url, transport=transport),
    )

    payload = client.fetch_study("nct04280705")
    client.close()

    assert payload["studies"][0]["protocolSection"]["identificationModule"]["nctId"] == "NCT04280705"
    assert captured["path"].endswith("/studies/NCT04280705")
    assert captured["format"] == "json"
