from fastapi.testclient import TestClient

from tool_db_backend.api import app


client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app_name"] == "BioControl Toolkit API"


def test_list_items() -> None:
    response = client.get("/api/v1/items")

    assert response.status_code == 200
    payload = response.json()
    slugs = {item["slug"] for item in payload}
    assert {"aslov2", "cry2-cib1"}.issubset(slugs)


def test_get_item_detail() -> None:
    response = client.get("/api/v1/items/aslov2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["canonical_name"] == "AsLOV2"
    assert "Seed dossier" in payload["summary"]
    assert "AsLOV2" in payload["index_markdown"]


def test_get_unknown_item_returns_404() -> None:
    response = client.get("/api/v1/items/does-not-exist")

    assert response.status_code == 404


def test_get_vocabularies() -> None:
    response = client.get("/api/v1/vocabularies")

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "v1"
    assert "item_types" in payload["data"]


def test_get_source_registry() -> None:
    response = client.get("/api/v1/source-registry")

    assert response.status_code == 200
    payload = response.json()
    keys = {entry["source_key"] for entry in payload}
    assert {"openalex", "semantic_scholar", "clinicaltrials_gov", "gap_map", "optobase"} == keys


def test_get_workflow() -> None:
    response = client.get("/api/v1/workflows/fast-no-cloning-screen")

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_family"] == "fast_screen"
    assert len(payload["step_templates"]) == 4
