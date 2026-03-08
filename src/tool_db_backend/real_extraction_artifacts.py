import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from tool_db_backend.clients.europe_pmc import EuropePMCClient
from tool_db_backend.config import Settings
from tool_db_backend.schema_validation import validate_packet


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "entry"


def _compact_dict(values: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _reconstruct_openalex_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    if not inverted_index:
        return ""
    words = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words.append((pos, word))
    words.sort(key=lambda pair: pair[0])
    return " ".join(word for _, word in words)


class RealExtractionArtifactBuilder:
    def __init__(self, settings: Settings, europe_pmc_client: Optional[EuropePMCClient] = None) -> None:
        self.settings = settings
        self.europe_pmc_client = europe_pmc_client or EuropePMCClient(settings)

    def close(self) -> None:
        self.europe_pmc_client.close()

    def build_from_smoke_test_manifest(
        self,
        manifest_path: Path,
        output_dir: Path,
        gap_limit: int = 80,
        openalex_limit: int = 40,
    ) -> Dict[str, Any]:
        manifest = json.loads(manifest_path.read_text())
        output_dir.mkdir(parents=True, exist_ok=True)

        gap_packets = self._build_gap_packets(
            Path(manifest["sources"]["gap_map"]["raw_paths"]["gaps"]),
            output_dir / "gap_map",
            limit=gap_limit,
        )
        openalex_outputs = self._build_openalex_packets_and_jobs(
            raw_search_paths=[
                Path(path)
                for path in manifest["sources"]["openalex"]["raw_paths"].values()
            ],
            output_dir=output_dir / "openalex",
            limit=openalex_limit,
        )

        result = {
            "artifact_type": "real_extraction_seed_v1",
            "gap_map_packet_count": len(gap_packets),
            "openalex_packet_count": len(openalex_outputs["packets"]),
            "openalex_job_count": len(openalex_outputs["jobs"]),
            "gap_map_packets": [str(path) for path in gap_packets],
            "openalex_packets": [str(path) for path in openalex_outputs["packets"]],
            "openalex_jobs": [str(path) for path in openalex_outputs["jobs"]],
        }
        manifest_out = output_dir / "manifest.json"
        manifest_out.write_text(json.dumps(result, indent=2) + "\n")
        result["manifest_path"] = str(manifest_out)
        return result

    def _build_gap_packets(self, raw_path: Path, output_dir: Path, limit: int) -> List[Path]:
        raw_wrapper = json.loads(raw_path.read_text())
        entries = raw_wrapper["payload"][:limit]
        output_dir.mkdir(parents=True, exist_ok=True)
        self._clear_json_outputs(output_dir)
        written_paths = []
        for entry in entries:
            local_id = f"gap_{entry['id']}"
            packet = {
                "packet_type": "database_entry_extract_v1",
                "schema_version": "v1",
                "source_document": {
                    "source_type": "database_entry",
                    "title": entry["name"],
                    "journal_or_source": "Gap Map",
                },
                "database_name": "Gap Map",
                "entry_url": f"https://www.gap-map.org/gaps/{entry['slug']}",
                "entity_candidates": [
                    {
                        "local_id": local_id,
                        "candidate_type": "gap_item",
                        "canonical_name": entry["name"],
                        "aliases": [],
                        "external_ids": {
                            "gap_map_id": entry["id"],
                            "gap_map_slug": entry["slug"],
                        },
                        "evidence_text": entry.get("description", ""),
                    }
                ],
                "claims": [
                    {
                        "local_id": f"{local_id}_claim_problem_statement",
                        "claim_type": "problem_statement",
                        "claim_text_normalized": entry.get("description", "").strip() or entry["name"],
                        "polarity": "supports",
                        "subject_local_ids": [local_id],
                        "source_locator": {
                            "section_label": "description",
                            "quoted_text": entry.get("description", ""),
                        },
                        "unresolved_ambiguities": [],
                    }
                ],
                "database_fields": {
                    "field": entry.get("field"),
                    "foundationalCapabilities": entry.get("foundationalCapabilities", []),
                    "tags": entry.get("tags", []),
                },
                "unresolved_ambiguities": [],
            }
            validate_packet("database_entry_extract_v1", packet, self.settings)
            path = output_dir / f"{entry['slug']}.database_entry_extract_v1.json"
            path.write_text(json.dumps(packet, indent=2) + "\n")
            written_paths.append(path)
        return written_paths

    def _build_openalex_packets_and_jobs(
        self,
        raw_search_paths: List[Path],
        output_dir: Path,
        limit: int,
    ) -> Dict[str, List[Path]]:
        packets_dir = output_dir / "packets"
        jobs_dir = output_dir / "jobs"
        packets_dir.mkdir(parents=True, exist_ok=True)
        jobs_dir.mkdir(parents=True, exist_ok=True)
        self._clear_json_outputs(packets_dir)
        self._clear_json_outputs(jobs_dir)

        seen_ids = set()
        packet_paths: List[Path] = []
        job_paths: List[Path] = []

        for raw_path in raw_search_paths:
            raw_wrapper = json.loads(raw_path.read_text())
            for work in raw_wrapper["payload"].get("results", []):
                work_id = work.get("id")
                if not work_id or work_id in seen_ids:
                    continue
                seen_ids.add(work_id)
                if len(packet_paths) >= limit:
                    break

                openalex_id = work_id
                doi = self._normalize_doi(work.get("doi"))
                pmid = self._extract_pmid(work.get("ids", {}))
                abstract_text = _reconstruct_openalex_abstract(work.get("abstract_inverted_index"))
                enrichment = self._enrich_openalex_work(doi=doi, pmid=pmid)
                if len(abstract_text.strip()) < 80 and enrichment.get("abstract_text"):
                    abstract_text = enrichment["abstract_text"]
                slug = _slugify(work.get("display_name") or work.get("title") or openalex_id)
                work_type = (work.get("type") or "").strip().lower()
                is_review = work_type == "review"
                source_type = "review" if is_review else "primary_paper"
                source_document = _compact_dict({
                    "source_type": source_type,
                    "title": work.get("display_name") or work.get("title") or openalex_id,
                    "doi": doi,
                    "openalex_id": openalex_id,
                    "pmid": pmid,
                    "publication_year": work.get("publication_year"),
                    "journal_or_source": self._extract_source_name(work),
                })
                if is_review:
                    packet = {
                        "packet_type": "review_extract_v1",
                        "schema_version": "v1",
                        "source_document": source_document,
                        "review_scope": "Metadata scaffold from OpenAlex review search result.",
                        "entity_candidates": [],
                        "claims": [],
                        "recommended_seed_item_local_ids": [],
                        "unresolved_ambiguities": [
                            {
                                "issue": "Metadata scaffold only; title and abstract still need review-level extraction.",
                                "detail": "Prepared from OpenAlex search results for later LLM extraction.",
                                "severity": "medium",
                            }
                        ],
                    }
                    packet_kind = "review_extract_v1"
                    prompt_template = "prompts/extraction/review_extract_v1.md"
                    schema_path = "schemas/extraction/review_extract.v1.schema.json"
                else:
                    packet = {
                        "packet_type": "primary_paper_extract_v1",
                        "schema_version": "v1",
                        "source_document": source_document,
                        "entity_candidates": [],
                        "claims": [],
                        "validation_observations": [],
                        "replication_signals": {},
                        "unresolved_ambiguities": [
                            {
                                "issue": "Metadata scaffold only; title and abstract still need claim extraction.",
                                "detail": "Prepared from OpenAlex search results for later LLM extraction.",
                                "severity": "medium",
                            }
                        ],
                    }
                    packet_kind = "primary_paper_extract_v1"
                    prompt_template = "prompts/extraction/primary_paper_extract_v1.md"
                    schema_path = "schemas/extraction/primary_paper_extract.v1.schema.json"

                validate_packet(packet_kind, packet, self.settings)
                packet_path = self._unique_output_path(
                    packets_dir,
                    slug=slug,
                    suffix=f".{packet_kind}.json",
                    external_id=openalex_id,
                )
                packet_path.write_text(json.dumps(packet, indent=2) + "\n")
                packet_paths.append(packet_path)

                job = {
                    "job_type": "llm_extraction_job_v1",
                    "target_packet_type": packet_kind,
                    "prompt_template": prompt_template,
                    "schema_path": schema_path,
                    "source_document": source_document,
                    "input_context": {
                        "title": source_document["title"],
                        "abstract_text": abstract_text,
                        "openalex_metadata": {
                            "type": work.get("type"),
                            "cited_by_count": work.get("cited_by_count"),
                            "concepts": work.get("concepts", []),
                        },
                        "enrichment_metadata": enrichment,
                    },
                    "notes": [
                        "LLM extraction should populate packet content conservatively from available evidence.",
                        "Do not invent canonical item IDs or merges.",
                    ],
                }
                job_path = self._unique_output_path(
                    jobs_dir,
                    slug=slug,
                    suffix=".llm_extraction_job_v1.json",
                    external_id=openalex_id,
                )
                job_path.write_text(json.dumps(job, indent=2) + "\n")
                job_paths.append(job_path)

            if len(packet_paths) >= limit:
                break

        return {"packets": packet_paths, "jobs": job_paths}

    @staticmethod
    def _normalize_doi(doi: Optional[str]) -> Optional[str]:
        if not doi:
            return None
        normalized = doi.strip()
        for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
            if normalized.startswith(prefix):
                return normalized[len(prefix) :]
        return normalized

    @staticmethod
    def _extract_pmid(ids: Dict[str, Any]) -> Optional[str]:
        pmid = ids.get("pmid")
        if not pmid:
            return None
        return pmid.rsplit("/", 1)[-1]

    @staticmethod
    def _extract_source_name(work: Dict[str, Any]) -> Optional[str]:
        primary_location = work.get("primary_location") or {}
        source = primary_location.get("source") or {}
        return source.get("display_name")

    @staticmethod
    def _clear_json_outputs(directory: Path) -> None:
        for path in directory.glob("*.json"):
            path.unlink()

    @staticmethod
    def _unique_output_path(directory: Path, slug: str, suffix: str, external_id: str) -> Path:
        candidate = directory / f"{slug}{suffix}"
        if not candidate.exists():
            return candidate
        safe_external = _slugify(external_id.rsplit("/", 1)[-1])
        return directory / f"{slug}-{safe_external}{suffix}"

    def _enrich_openalex_work(self, doi: Optional[str], pmid: Optional[str]) -> Dict[str, Any]:
        result = self.europe_pmc_client.fetch_by_doi_or_pmid(doi=doi, pmid=pmid)
        if not result:
            return {}
        return _compact_dict(
            {
                "source": "europe_pmc",
                "doi": result.get("doi"),
                "pmid": result.get("pmid"),
                "pmcid": result.get("pmcid"),
                "abstract_text": result.get("abstractText"),
                "journal": result.get("journalTitle"),
                "pub_type": result.get("pubType"),
                "is_open_access": result.get("isOpenAccess"),
            }
        )
