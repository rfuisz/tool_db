from pathlib import Path

from tool_db_backend.config import get_settings
from tool_db_backend.source_smoke_test import RealDataSmokeTester


class _FakeRawStore:
    def __init__(self):
        self.writes = []

    def write_json_payload(self, source_key, resource_type, external_id, payload):
        self.writes.append((source_key, resource_type, external_id, payload))
        return Path(f"/tmp/{source_key}-{resource_type}-{external_id}.json")

    def write_text_payload(self, source_key, resource_type, external_id, payload_text, content_type="text/plain"):
        self.writes.append((source_key, resource_type, external_id, payload_text, content_type))
        return Path(f"/tmp/{source_key}-{resource_type}-{external_id}.json")


class _FakeOpenAlexClient:
    def search_works(self, query, per_page=25, page=1, filter_expr=None):
        if query == "optogenetic":
            return {"results": [{"id": "W1"}, {"id": "W2"}]}
        return {"results": [{"id": "W2"}, {"id": "W3"}]}

    def close(self):
        return None


class _FakeSemanticScholarClient:
    def search_papers(self, query, limit=25, offset=0, fields=None):
        return {"data": [{"paperId": "P1"}, {"paperId": "P2"}]}

    def close(self):
        return None


class _FakeGapMapClient:
    def fetch_dataset(self, dataset_name):
        return [{"id": f"{dataset_name}-1"}, {"id": f"{dataset_name}-2"}]

    def close(self):
        return None


class _FakeOptoBaseClient:
    def fetch_search_page(self, query=""):
        return f"<html>{query}</html>"

    def close(self):
        return None


def test_real_data_smoke_test_writes_manifest(tmp_path: Path) -> None:
    tester = RealDataSmokeTester(
        get_settings(),
        openalex_client=_FakeOpenAlexClient(),
        semantic_scholar_client=_FakeSemanticScholarClient(),
        gap_map_client=_FakeGapMapClient(),
        optobase_client=_FakeOptoBaseClient(),
        raw_store=_FakeRawStore(),
    )

    manifest = tester.run(tmp_path)

    assert manifest["total_entry_count"] == 13
    assert Path(manifest["manifest_path"]).exists()
    assert manifest["sources"]["openalex"]["entry_count"] == 3
    assert manifest["sources"]["semantic_scholar"]["entry_count"] == 2
    assert manifest["sources"]["gap_map"]["entry_count"] == 8
