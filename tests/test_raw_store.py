import json

from tool_db_backend.config import get_settings
from tool_db_backend.raw_store import RawPayloadStore


def test_raw_payload_store_writes_wrapped_payload(tmp_path) -> None:
    settings = get_settings().model_copy(update={"repo_root": tmp_path})
    store = RawPayloadStore(settings)

    path = store.write_json_payload(
        source_key="openalex",
        resource_type="work",
        external_id="https://openalex.org/W123",
        payload={"id": "https://openalex.org/W123"},
    )

    data = json.loads(path.read_text())
    assert data["source_key"] == "openalex"
    assert data["resource_type"] == "work"
    assert data["external_id"] == "https://openalex.org/W123"
    assert data["payload"]["id"] == "https://openalex.org/W123"


def test_raw_payload_store_reads_cached_payloads(tmp_path) -> None:
    settings = get_settings().model_copy(update={"repo_root": tmp_path})
    store = RawPayloadStore(settings)

    store.write_json_payload(
        source_key="openalex",
        resource_type="work_search",
        external_id="query-page-1",
        payload={"results": [{"id": "W1"}]},
    )
    store.write_text_payload(
        source_key="optobase",
        resource_type="search_html",
        external_id="aslov2",
        payload_text="<html>cached</html>",
    )

    assert store.read_json_payload("openalex", "work_search", "query-page-1") == {
        "results": [{"id": "W1"}]
    }
    assert store.read_text_payload("optobase", "search_html", "aslov2") == "<html>cached</html>"
