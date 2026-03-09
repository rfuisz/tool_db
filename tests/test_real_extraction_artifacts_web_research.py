import json
from pathlib import Path

from tool_db_backend.config import get_settings
from tool_db_backend.real_extraction_artifacts import RealExtractionArtifactBuilder


class _FakeEuropePMCClient:
    def fetch_by_doi_or_pmid(self, doi=None, pmid=None):
        if doi == "10.1000/example":
            return {
                "doi": doi,
                "pmid": pmid,
                "pmcid": "PMC1234567",
                "abstractText": "Europe PMC abstract with richer details.",
                "journalTitle": "Example Journal",
                "pubType": "Journal Article",
                "isOpenAccess": "Y",
            }
        return None

    def close(self):
        return None


class _FakePMCClient:
    def fetch_bioc_fulltext(self, pmcid):
        assert pmcid == "PMC1234567"
        return {
            "documents": [
                {
                    "passages": [
                        {"infons": {"section_type": "RESULTS"}, "text": "Results text about optogenetic switching."}
                    ]
                }
            ]
        }

    def close(self):
        return None


class _FakeSemanticScholarClient:
    def search_papers(self, **kwargs):
        return {"data": []}

    def close(self):
        return None


class _FakeWebResearchClient:
    def research_source_document(self, *, source_document, abstract_text=""):
        return {
            "summary": "Compiled from browsing-backed source review.",
            "high_signal_sources": [
                {
                    "title": "Green, orange, red, and far-red optogenetic tools derived from cyanobacteriochromes",
                    "url": "https://example.test/cbcr-paper",
                    "source_type": "preprint",
                    "publication_year": 2019,
                    "doi": "10.1101/769422",
                    "pmid": None,
                    "why_relevant": "Provides optogenetic application context and adjacent tool names.",
                }
            ],
            "related_item_candidates": [
                {
                    "name": "Amg2",
                    "relation": "engineered_variant",
                    "why_relevant": "An engineered cyanobacteriochrome-derived switch component.",
                }
            ],
            "open_questions": [],
        }

    def close(self):
        return None


def test_real_extraction_artifact_builder_adds_web_research_summary(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    gap_raw_path = tmp_path / "gaps.json"
    capability_raw_path = tmp_path / "capabilities.json"
    resource_raw_path = tmp_path / "resources.json"
    openalex_raw_path = tmp_path / "openalex.json"

    gap_raw_path.write_text(json.dumps({"payload": []}))
    capability_raw_path.write_text(json.dumps({"payload": []}))
    resource_raw_path.write_text(json.dumps({"payload": []}))
    openalex_raw_path.write_text(
        json.dumps(
            {
                "payload": {
                    "results": [
                        {
                            "id": "https://openalex.org/W1",
                            "display_name": "Example Paper",
                            "title": "Example Paper",
                            "doi": "https://doi.org/10.1000/example",
                            "publication_year": 2024,
                            "ids": {"pmid": "https://pubmed.ncbi.nlm.nih.gov/12345678"},
                            "primary_location": {"source": {"display_name": "Example Journal"}},
                            "abstract_inverted_index": {"Example": [0], "abstract": [1]},
                            "type": "article",
                            "cited_by_count": 10,
                            "concepts": [],
                        }
                    ]
                }
            }
        )
    )
    manifest_path.write_text(
        json.dumps(
            {
                "sources": {
                    "gap_map": {
                        "raw_paths": {
                            "gaps": str(gap_raw_path),
                            "capabilities": str(capability_raw_path),
                            "resources": str(resource_raw_path),
                        }
                    },
                    "openalex": {"raw_paths": {"optogenetic": str(openalex_raw_path)}},
                }
            }
        )
    )

    builder = RealExtractionArtifactBuilder(
        get_settings(),
        europe_pmc_client=_FakeEuropePMCClient(),
        pmc_client=_FakePMCClient(),
        semantic_scholar_client=_FakeSemanticScholarClient(),
        web_research_client=_FakeWebResearchClient(),
    )
    builder.build_from_smoke_test_manifest(manifest_path, tmp_path / "out", gap_limit=0, openalex_limit=1)

    article_job = Path(tmp_path / "out" / "openalex" / "jobs" / "example-paper.llm_extraction_job_v1.json")
    article_payload = json.loads(article_job.read_text())

    assert article_payload["input_context"]["web_research_summary"]["summary"] == (
        "Compiled from browsing-backed source review."
    )
    assert article_payload["input_context"]["web_research_summary"]["related_item_candidates"][0]["name"] == "Amg2"
