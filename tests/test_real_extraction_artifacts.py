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
                "abstractText": "Europe PMC abstract with enough detail to prefer over a short OpenAlex reconstruction.",
                "journalTitle": "Example Journal",
                "pubType": "journal article",
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
                        {"infons": {"section_type": "ABSTRACT"}, "text": "Abstract passage."},
                        {"infons": {"section_type": "RESULTS"}, "text": "Results passage."},
                        {"infons": {"section_type": "DISCUSSION"}, "text": "Discussion passage."},
                    ]
                }
            ]
        }

    def close(self):
        return None


def test_real_extraction_artifact_builder_writes_packets_and_jobs(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    gap_raw_path = tmp_path / "gaps.json"
    capability_raw_path = tmp_path / "capabilities.json"
    resource_raw_path = tmp_path / "resources.json"
    openalex_raw_path = tmp_path / "openalex.json"

    gap_raw_path.write_text(
        json.dumps(
            {
                "payload": [
                    {
                        "id": "gap-1",
                        "name": "Example Gap",
                        "slug": "example-gap",
                        "description": "A real problem statement.",
                        "field": {"id": "field-1", "name": "Biology"},
                        "foundationalCapabilities": [],
                        "tags": [],
                    }
                ]
            }
        )
    )
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
                        },
                        {
                            "id": "https://openalex.org/W2",
                            "display_name": "Example Review",
                            "title": "Example Review",
                            "doi": "https://doi.org/10.1000/review",
                            "publication_year": 2023,
                            "ids": {},
                            "primary_location": {"source": {"display_name": "Review Journal"}},
                            "abstract_inverted_index": {"Review": [0], "abstract": [1]},
                            "type": "review",
                            "cited_by_count": 5,
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
    )
    result = builder.build_from_smoke_test_manifest(manifest_path, tmp_path / "out", gap_limit=1, openalex_limit=2)

    assert result["gap_map_packet_count"] == 1
    assert result["openalex_packet_count"] == 2
    assert result["openalex_job_count"] == 2
    assert Path(result["manifest_path"]).exists()
    review_job = Path(tmp_path / "out" / "openalex" / "jobs" / "example-review.llm_extraction_job_v1.json")
    review_packet = Path(tmp_path / "out" / "openalex" / "packets" / "example-review.review_extract_v1.json")
    article_job = Path(tmp_path / "out" / "openalex" / "jobs" / "example-paper.llm_extraction_job_v1.json")
    assert review_job.exists()
    assert review_packet.exists()
    article_payload = json.loads(article_job.read_text())
    assert article_payload["input_context"]["abstract_text"].startswith("Europe PMC abstract")
    assert article_payload["input_context"]["enrichment_metadata"]["source"] == "openalex_enrichment"
    assert article_payload["input_context"]["pmc_bioc_available"] is True
    assert "[RESULTS]" in article_payload["input_context"]["pmc_bioc_preview_text"]
    assert article_payload["source_document"]["fulltext_license_status"] == "open_access"
