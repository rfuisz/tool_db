from pathlib import Path

from tool_db_backend.config import get_settings
from tool_db_backend.source_smoke_test import RealDataSmokeTester, build_first_pass_query_sets


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
        if query in {"\"optogenetic tools\"", "AsLOV2 OR LOV2", "CRY2 CIB1", "PhyB PIF"}:
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


class _FakeEuropePMCClient:
    def search(self, query, page_size=25, page=1, result_type="core"):
        return {"resultList": {"result": []}}

    def close(self):
        return None


class _FakePMCClient:
    def fetch_bioc_fulltext(self, pmcid):
        return {}

    def close(self):
        return None


class _FakeWebResearchClient:
    def expand_seed_queries(self, *, seed_terms, max_related_items=24):
        assert "AsLOV2" in seed_terms
        return {
            "related_item_candidates": [
                {
                    "name": "Rapid blue-light-mediated induction of protein interactions in living cells",
                    "relation": "paper_title_noise",
                    "why_relevant": "Should be filtered because this is a paper title, not a tool name.",
                },
                {
                    "name": "Am1_c0023g2",
                    "relation": "adjacent_tool",
                    "why_relevant": "Frequently appears in cyanobacteriochrome optogenetics literature.",
                }
            ],
            "literature_queries": [
                "\"Am1_c0023g2\" optogenetic",
                "\"AsLOV2\" versus iLID",
            ],
            "optobase_queries": ["Am1_c0023g2"],
        }


def test_real_data_smoke_test_writes_manifest(tmp_path: Path) -> None:
    tester = RealDataSmokeTester(
        get_settings(),
        europe_pmc_client=_FakeEuropePMCClient(),
        pmc_client=_FakePMCClient(),
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


def test_build_first_pass_query_sets_includes_web_research_expansion() -> None:
    query_sets = build_first_pass_query_sets(
        get_settings().model_copy(update={"llm_web_research_enabled": True}),
        seed_query_limit=8,
        web_research_client=_FakeWebResearchClient(),
    )

    assert "\"Am1_c0023g2\" optogenetic" in query_sets["openalex"]
    assert "\"AsLOV2\" versus iLID" in query_sets["semantic_scholar"]
    assert "Am1_c0023g2" in query_sets["optobase"]
    assert query_sets["web_research"]["related_item_candidates"][0]["name"] == "Am1_c0023g2"
    assert all(
        candidate["name"] != "Rapid blue-light-mediated induction of protein interactions in living cells"
        for candidate in query_sets["web_research"]["related_item_candidates"]
    )
