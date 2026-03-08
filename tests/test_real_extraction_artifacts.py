import json
from pathlib import Path

from tool_db_backend.config import get_settings
from tool_db_backend.real_extraction_artifacts import RealExtractionArtifactBuilder


def test_real_extraction_artifact_builder_writes_packets_and_jobs(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    gap_raw_path = tmp_path / "gaps.json"
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
                    "gap_map": {"raw_paths": {"gaps": str(gap_raw_path)}},
                    "openalex": {"raw_paths": {"optogenetic": str(openalex_raw_path)}},
                }
            }
        )
    )

    builder = RealExtractionArtifactBuilder(get_settings())
    result = builder.build_from_smoke_test_manifest(manifest_path, tmp_path / "out", gap_limit=1, openalex_limit=1)

    assert result["gap_map_packet_count"] == 1
    assert result["openalex_packet_count"] == 1
    assert result["openalex_job_count"] == 1
    assert Path(result["manifest_path"]).exists()
