import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from tool_db_backend.clients.europe_pmc import EuropePMCClient
from tool_db_backend.clients.semantic_scholar import SemanticScholarClient
from tool_db_backend.config import Settings
from tool_db_backend.schema_validation import validate_packet
from tool_db_backend.source_staging import OptoBaseSearchParser


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
    def __init__(
        self,
        settings: Settings,
        europe_pmc_client: Optional[EuropePMCClient] = None,
        semantic_scholar_client: Optional[SemanticScholarClient] = None,
    ) -> None:
        self.settings = settings
        self.europe_pmc_client = europe_pmc_client or EuropePMCClient(settings)
        self.semantic_scholar_client = semantic_scholar_client or SemanticScholarClient(settings)
        self.optobase_parser = OptoBaseSearchParser()
        self.enrichment_cache_dir = self.settings.pipeline_artifact_root / "openalex-enrichment-cache"

    def close(self) -> None:
        self.europe_pmc_client.close()
        self.semantic_scholar_client.close()

    def build_from_smoke_test_manifest(
        self,
        manifest_path: Path,
        output_dir: Path,
        gap_limit: int = 80,
        europe_pmc_limit: int = 200,
        openalex_limit: int = 200,
        semantic_scholar_limit: int = 200,
    ) -> Dict[str, Any]:
        manifest = json.loads(manifest_path.read_text())
        output_dir.mkdir(parents=True, exist_ok=True)
        seen_document_keys = set()

        gap_packets = self._build_gap_packets(
            gaps_raw_path=Path(manifest["sources"]["gap_map"]["raw_paths"]["gaps"]),
            capabilities_raw_path=Path(manifest["sources"]["gap_map"]["raw_paths"]["capabilities"]),
            resources_raw_path=Path(manifest["sources"]["gap_map"]["raw_paths"]["resources"]),
            output_dir=output_dir / "gap_map",
            limit=gap_limit,
        )
        europe_pmc_outputs = self._build_europe_pmc_packets_and_jobs(
            raw_search_paths=[
                Path(path)
                for path in manifest["sources"].get("europe_pmc", {}).get("raw_paths", {}).values()
            ],
            pmc_raw_paths=manifest["sources"].get("pmc", {}).get("raw_paths", {}),
            output_dir=output_dir / "europe_pmc",
            limit=europe_pmc_limit,
            seen_document_keys=seen_document_keys,
        )
        openalex_outputs = self._build_openalex_packets_and_jobs(
            raw_search_paths=[
                Path(path)
                for path in manifest["sources"]["openalex"]["raw_paths"].values()
            ],
            output_dir=output_dir / "openalex",
            limit=openalex_limit,
            seen_document_keys=seen_document_keys,
        )
        semantic_scholar_outputs = self._build_semantic_scholar_packets_and_jobs(
            raw_search_paths=[
                Path(path)
                for path in manifest["sources"].get("semantic_scholar", {}).get("raw_paths", {}).values()
            ],
            output_dir=output_dir / "semantic_scholar",
            limit=semantic_scholar_limit,
            seen_document_keys=seen_document_keys,
        )
        semantic_scholar_summaries = self._build_semantic_scholar_summaries(
            raw_search_paths=[
                Path(path)
                for path in manifest["sources"].get("semantic_scholar", {}).get("raw_paths", {}).values()
            ],
            output_dir=output_dir / "semantic_scholar",
            limit=openalex_limit,
        )
        optobase_summaries = self._build_optobase_summaries(
            raw_search_paths=[
                Path(path)
                for path in manifest["sources"].get("optobase", {}).get("raw_paths", {}).values()
            ],
            output_dir=output_dir / "optobase",
        )

        result = {
            "artifact_type": "real_extraction_seed_v1",
            "gap_map_packet_count": len(gap_packets),
            "europe_pmc_packet_count": len(europe_pmc_outputs["packets"]),
            "europe_pmc_job_count": len(europe_pmc_outputs["jobs"]),
            "openalex_packet_count": len(openalex_outputs["packets"]),
            "openalex_job_count": len(openalex_outputs["jobs"]),
            "semantic_scholar_packet_count": len(semantic_scholar_outputs["packets"]),
            "semantic_scholar_job_count": len(semantic_scholar_outputs["jobs"]),
            "semantic_scholar_summary_count": len(semantic_scholar_summaries),
            "optobase_summary_count": len(optobase_summaries),
            "gap_map_packets": [str(path) for path in gap_packets],
            "europe_pmc_packets": [str(path) for path in europe_pmc_outputs["packets"]],
            "europe_pmc_jobs": [str(path) for path in europe_pmc_outputs["jobs"]],
            "openalex_packets": [str(path) for path in openalex_outputs["packets"]],
            "openalex_jobs": [str(path) for path in openalex_outputs["jobs"]],
            "semantic_scholar_packets": [str(path) for path in semantic_scholar_outputs["packets"]],
            "semantic_scholar_jobs": [str(path) for path in semantic_scholar_outputs["jobs"]],
            "semantic_scholar_summaries": [str(path) for path in semantic_scholar_summaries],
            "optobase_summaries": [str(path) for path in optobase_summaries],
        }
        manifest_out = output_dir / "manifest.json"
        manifest_out.write_text(json.dumps(result, indent=2) + "\n")
        result["manifest_path"] = str(manifest_out)
        return result

    def _build_gap_packets(
        self,
        gaps_raw_path: Path,
        capabilities_raw_path: Path,
        resources_raw_path: Path,
        output_dir: Path,
        limit: int,
    ) -> List[Path]:
        gaps_wrapper = json.loads(gaps_raw_path.read_text())
        capabilities_wrapper = json.loads(capabilities_raw_path.read_text())
        resources_wrapper = json.loads(resources_raw_path.read_text())
        entries = gaps_wrapper["payload"][:limit]
        capability_by_id = {
            entry["id"]: entry for entry in capabilities_wrapper["payload"] if entry.get("id")
        }
        resource_by_id = {
            entry["id"]: entry for entry in resources_wrapper["payload"] if entry.get("id")
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        self._clear_json_outputs(output_dir)
        written_paths = []
        for entry in entries:
            local_id = f"gap_{entry['id']}"
            capabilities = [
                capability_by_id[capability_id]
                for capability_id in entry.get("foundationalCapabilities", [])
                if capability_id in capability_by_id
            ]
            resource_ids = {
                resource_id
                for capability in capabilities
                for resource_id in capability.get("resources", [])
                if resource_id in resource_by_id
            }
            resources = [resource_by_id[resource_id] for resource_id in sorted(resource_ids)]
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
                    "capabilities": capabilities,
                    "resources": resources,
                    "tags": entry.get("tags", []),
                },
                "unresolved_ambiguities": [],
            }
            validate_packet("database_entry_extract_v1", packet, self.settings)
            path = output_dir / f"{entry['slug']}.database_entry_extract_v1.json"
            path.write_text(json.dumps(packet, indent=2) + "\n")
            written_paths.append(path)
        return written_paths

    def _build_semantic_scholar_summaries(
        self,
        raw_search_paths: List[Path],
        output_dir: Path,
        limit: int,
    ) -> List[Path]:
        if not raw_search_paths:
            return []
        output_dir.mkdir(parents=True, exist_ok=True)
        self._clear_json_outputs(output_dir)
        written_paths: List[Path] = []
        seen_ids = set()
        for raw_path in raw_search_paths:
            raw_wrapper = json.loads(raw_path.read_text())
            for result in raw_wrapper.get("payload", {}).get("data", []):
                paper_id = result.get("paperId")
                if not paper_id or paper_id in seen_ids:
                    continue
                seen_ids.add(paper_id)
                summary = {
                    "artifact_type": "semantic_scholar_paper_summary_v1",
                    "paper_id": paper_id,
                    "title": result.get("title"),
                    "year": result.get("year"),
                    "citation_count": result.get("citationCount"),
                    "external_ids": result.get("externalIds", {}),
                    "raw_payload_ref": str(raw_path),
                }
                out_path = self._unique_output_path(
                    output_dir,
                    slug=_slugify(result.get("title") or paper_id),
                    suffix=".semantic_scholar_summary_v1.json",
                    external_id=paper_id,
                )
                out_path.write_text(json.dumps(_compact_dict(summary), indent=2) + "\n")
                written_paths.append(out_path)
                if len(written_paths) >= limit:
                    return written_paths
        return written_paths

    def _build_optobase_summaries(self, raw_search_paths: List[Path], output_dir: Path) -> List[Path]:
        if not raw_search_paths:
            return []
        output_dir.mkdir(parents=True, exist_ok=True)
        self._clear_json_outputs(output_dir)
        written_paths: List[Path] = []
        for raw_path in raw_search_paths:
            summary = self.optobase_parser.parse_raw_file(raw_path)
            out_path = self._unique_output_path(
                output_dir,
                slug=_slugify(summary.get("query") or raw_path.stem),
                suffix=".optobase_search_summary_v1.json",
                external_id=raw_path.stem,
            )
            out_path.write_text(json.dumps(summary, indent=2) + "\n")
            written_paths.append(out_path)
        return written_paths

    def _build_openalex_packets_and_jobs(
        self,
        raw_search_paths: List[Path],
        output_dir: Path,
        limit: int,
        seen_document_keys: Optional[set[str]] = None,
    ) -> Dict[str, List[Path]]:
        packets_dir = output_dir / "packets"
        jobs_dir = output_dir / "jobs"
        packets_dir.mkdir(parents=True, exist_ok=True)
        jobs_dir.mkdir(parents=True, exist_ok=True)
        self._clear_json_outputs(packets_dir)
        self._clear_json_outputs(jobs_dir)

        seen_ids = set()
        seen_document_keys = seen_document_keys if seen_document_keys is not None else set()
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
                title = work.get("display_name") or work.get("title") or openalex_id
                enrichment: Dict[str, Any] = {"source": "openalex_enrichment_skipped"}
                if len(abstract_text.strip()) < 80:
                    enrichment = self._enrich_openalex_work(
                        title=title,
                        doi=doi,
                        pmid=pmid,
                    )
                    if enrichment.get("abstract_text"):
                        abstract_text = enrichment["abstract_text"]
                slug = _slugify(work.get("display_name") or work.get("title") or openalex_id)
                work_type = (work.get("type") or "").strip().lower()
                is_review = work_type == "review"
                source_type = "review" if is_review else "primary_paper"
                source_document = _compact_dict({
                    "source_type": source_type,
                    "title": title,
                    "doi": doi,
                    "openalex_id": openalex_id,
                    "pmid": pmid,
                    "semantic_scholar_id": enrichment.get("semantic_scholar_id"),
                    "publication_year": work.get("publication_year"),
                    "journal_or_source": self._extract_source_name(work),
                    "abstract_text": abstract_text or None,
                    "fulltext_license_status": self._license_status(enrichment),
                    "is_retracted": False,
                    "retraction_metadata": {},
                    "raw_payload_ref": str(raw_path),
                })
                document_key = self._document_key_from_fields(
                    title=source_document["title"],
                    doi=doi,
                    pmid=pmid,
                    provider_id=openalex_id,
                    provider_name="openalex",
                )
                if document_key in seen_document_keys:
                    continue
                seen_document_keys.add(document_key)

                packet_path, job_path = self._write_literature_packet_and_job(
                    packets_dir=packets_dir,
                    jobs_dir=jobs_dir,
                    slug=slug,
                    external_id=openalex_id,
                    source_document=source_document,
                    abstract_text=abstract_text,
                    is_review=is_review,
                    unresolved_detail="Prepared from OpenAlex search results for later LLM extraction.",
                    input_context={
                        "title": source_document["title"],
                        "abstract_text": abstract_text,
                        "openalex_metadata": {
                            "type": work.get("type"),
                            "cited_by_count": work.get("cited_by_count"),
                            "concepts": work.get("concepts", []),
                        },
                        "semantic_scholar_metadata": enrichment.get("semantic_scholar"),
                        "enrichment_metadata": enrichment,
                    },
                )
                packet_paths.append(packet_path)
                job_paths.append(job_path)

            if len(packet_paths) >= limit:
                break

        return {"packets": packet_paths, "jobs": job_paths}

    def _build_europe_pmc_packets_and_jobs(
        self,
        raw_search_paths: List[Path],
        pmc_raw_paths: Dict[str, str],
        output_dir: Path,
        limit: int,
        seen_document_keys: Optional[set[str]] = None,
    ) -> Dict[str, List[Path]]:
        packets_dir = output_dir / "packets"
        jobs_dir = output_dir / "jobs"
        packets_dir.mkdir(parents=True, exist_ok=True)
        jobs_dir.mkdir(parents=True, exist_ok=True)
        self._clear_json_outputs(packets_dir)
        self._clear_json_outputs(jobs_dir)

        pmc_lookup = self._load_pmc_bioc_lookup(pmc_raw_paths)
        seen_ids = set()
        seen_document_keys = seen_document_keys if seen_document_keys is not None else set()
        packet_paths: List[Path] = []
        job_paths: List[Path] = []

        for raw_path in raw_search_paths:
            raw_wrapper = json.loads(raw_path.read_text())
            for result in ((raw_wrapper.get("payload") or {}).get("resultList") or {}).get("result", []):
                paper_id = str(result.get("id") or result.get("pmid") or result.get("doi") or "").strip()
                if not paper_id or paper_id in seen_ids:
                    continue
                seen_ids.add(paper_id)
                if len(packet_paths) >= limit:
                    break

                pmcid = str(result.get("pmcid") or "").strip() or None
                doi = self._normalize_doi(result.get("doi"))
                pmid = str(result.get("pmid") or "").strip() or None
                title = result.get("title") or result.get("titleText") or paper_id
                source_document = _compact_dict(
                    {
                        "source_type": "review" if self._is_europe_pmc_review(result) else "primary_paper",
                        "title": title,
                        "doi": doi,
                        "pmid": pmid,
                        "pmcid": pmcid,
                        "publication_year": self._coerce_int(result.get("pubYear")),
                        "journal_or_source": self._extract_europe_pmc_source_name(result),
                        "abstract_text": result.get("abstractText"),
                        "fulltext_license_status": "open_access" if result.get("isOpenAccess") == "Y" else None,
                        "raw_payload_ref": str(raw_path),
                    }
                )
                document_key = self._document_key_from_fields(
                    title=title,
                    doi=doi,
                    pmid=pmid,
                    provider_id=paper_id,
                    provider_name="europe_pmc",
                )
                if document_key in seen_document_keys:
                    continue
                seen_document_keys.add(document_key)

                pmc_bioc_payload = pmc_lookup.get((pmcid or "").strip().upper())
                slug = _slugify(title)
                packet_path, job_path = self._write_literature_packet_and_job(
                    packets_dir=packets_dir,
                    jobs_dir=jobs_dir,
                    slug=slug,
                    external_id=pmcid or pmid or doi or paper_id,
                    source_document=source_document,
                    abstract_text=result.get("abstractText") or "",
                    is_review=source_document["source_type"] == "review",
                    unresolved_detail="Prepared from Europe PMC search results for later LLM extraction.",
                    input_context={
                        "title": title,
                        "abstract_text": result.get("abstractText"),
                        "europe_pmc_metadata": {
                            "id": result.get("id"),
                            "source": result.get("source"),
                            "pmid": pmid,
                            "pmcid": pmcid,
                            "doi": doi,
                            "pubType": result.get("pubType"),
                            "journalTitle": result.get("journalTitle"),
                            "authorString": result.get("authorString"),
                            "citedByCount": self._coerce_int(result.get("citedByCount")),
                            "isOpenAccess": result.get("isOpenAccess"),
                        },
                        "pmc_bioc_preview_text": self._summarize_pmc_bioc_payload(pmc_bioc_payload),
                        "pmc_bioc_available": pmc_bioc_payload is not None,
                    },
                )
                packet_paths.append(packet_path)
                job_paths.append(job_path)

            if len(packet_paths) >= limit:
                break

        return {"packets": packet_paths, "jobs": job_paths}

    def _build_semantic_scholar_packets_and_jobs(
        self,
        raw_search_paths: List[Path],
        output_dir: Path,
        limit: int,
        seen_document_keys: Optional[set[str]] = None,
    ) -> Dict[str, List[Path]]:
        packets_dir = output_dir / "packets"
        jobs_dir = output_dir / "jobs"
        packets_dir.mkdir(parents=True, exist_ok=True)
        jobs_dir.mkdir(parents=True, exist_ok=True)
        self._clear_json_outputs(packets_dir)
        self._clear_json_outputs(jobs_dir)

        seen_ids = set()
        seen_document_keys = seen_document_keys if seen_document_keys is not None else set()
        packet_paths: List[Path] = []
        job_paths: List[Path] = []

        for raw_path in raw_search_paths:
            raw_wrapper = json.loads(raw_path.read_text())
            for result in raw_wrapper.get("payload", {}).get("data", []):
                paper_id = result.get("paperId")
                if not paper_id or paper_id in seen_ids:
                    continue
                seen_ids.add(paper_id)
                if len(packet_paths) >= limit:
                    break

                title = result.get("title") or paper_id
                doi = self._normalize_doi((result.get("externalIds") or {}).get("DOI"))
                pmid = str((result.get("externalIds") or {}).get("PubMed") or "").strip() or None
                source_document = _compact_dict({
                    "source_type": "review" if self._is_semantic_scholar_review(result) else "primary_paper",
                    "title": title,
                    "doi": doi,
                    "pmid": pmid,
                    "semantic_scholar_id": paper_id,
                    "publication_year": result.get("year"),
                    "journal_or_source": self._extract_semantic_scholar_source_name(result),
                    "abstract_text": result.get("abstract"),
                    "raw_payload_ref": str(raw_path),
                })
                document_key = self._document_key_from_fields(
                    title=title,
                    doi=doi,
                    pmid=pmid,
                    provider_id=paper_id,
                    provider_name="semantic_scholar",
                )
                if document_key in seen_document_keys:
                    continue
                seen_document_keys.add(document_key)

                slug = _slugify(title)
                packet_path, job_path = self._write_literature_packet_and_job(
                    packets_dir=packets_dir,
                    jobs_dir=jobs_dir,
                    slug=slug,
                    external_id=paper_id,
                    source_document=source_document,
                    abstract_text=result.get("abstract") or "",
                    is_review=source_document["source_type"] == "review",
                    unresolved_detail="Prepared from Semantic Scholar search results for later LLM extraction.",
                    input_context={
                        "title": title,
                        "abstract_text": result.get("abstract"),
                        "semantic_scholar_metadata": {
                            "paperId": paper_id,
                            "year": result.get("year"),
                            "citationCount": result.get("citationCount"),
                            "externalIds": result.get("externalIds", {}),
                            "publicationTypes": result.get("publicationTypes", []),
                            "journal": result.get("journal"),
                            "venue": result.get("venue"),
                        },
                    },
                )
                packet_paths.append(packet_path)
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
    def _extract_europe_pmc_source_name(result: Dict[str, Any]) -> Optional[str]:
        return result.get("journalTitle") or result.get("journal") or result.get("source")

    @staticmethod
    def _extract_semantic_scholar_source_name(result: Dict[str, Any]) -> Optional[str]:
        journal = result.get("journal") or {}
        if isinstance(journal, dict):
            name = journal.get("name")
            if name:
                return name
        venue = result.get("venue")
        return venue if isinstance(venue, str) and venue.strip() else None

    @staticmethod
    def _is_semantic_scholar_review(result: Dict[str, Any]) -> bool:
        publication_types = [str(value).strip().casefold() for value in (result.get("publicationTypes") or [])]
        return any("review" in value for value in publication_types)

    @staticmethod
    def _is_europe_pmc_review(result: Dict[str, Any]) -> bool:
        pub_type = str(result.get("pubType") or "").casefold()
        title = str(result.get("title") or "").casefold()
        return "review" in pub_type or "review" in title

    @staticmethod
    def _load_pmc_bioc_lookup(raw_paths: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        lookup: Dict[str, Dict[str, Any]] = {}
        for pmcid, raw_path in raw_paths.items():
            try:
                raw_wrapper = json.loads(Path(raw_path).read_text())
            except (OSError, json.JSONDecodeError):
                continue
            payload = raw_wrapper.get("payload")
            if isinstance(payload, dict):
                lookup[pmcid.strip().upper()] = payload
        return lookup

    @staticmethod
    def _coerce_int(value: Any) -> Optional[int]:
        try:
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _summarize_pmc_bioc_payload(payload: Optional[Dict[str, Any]], max_chars: int = 12000) -> Optional[str]:
        if not payload:
            return None
        passages: List[str] = []
        for document in payload.get("documents", []):
            for passage in document.get("passages", []):
                text = str(passage.get("text") or "").strip()
                if text:
                    passages.append(text)
                if sum(len(chunk) for chunk in passages) >= max_chars:
                    break
            if sum(len(chunk) for chunk in passages) >= max_chars:
                break
        if not passages:
            return None
        joined = "\n\n".join(passages)
        if len(joined) <= max_chars:
            return joined
        return joined[: max_chars - 20].rstrip() + "\n\n[truncated]"

    @staticmethod
    def _clear_json_outputs(directory: Path) -> None:
        for path in directory.glob("*.json"):
            path.unlink()

    @staticmethod
    def _unique_output_path(directory: Path, slug: str, suffix: str, external_id: str) -> Path:
        safe_slug = RealExtractionArtifactBuilder._safe_output_stem(slug, suffix)
        candidate = directory / f"{safe_slug}{suffix}"
        if not candidate.exists():
            return candidate
        safe_external = _slugify(external_id.rsplit("/", 1)[-1])
        safe_external_slug = RealExtractionArtifactBuilder._safe_output_stem(
            f"{safe_slug}-{safe_external}",
            suffix,
        )
        return directory / f"{safe_external_slug}{suffix}"

    @staticmethod
    def _safe_output_stem(stem: str, suffix: str, max_name_length: int = 240) -> str:
        candidate_name = f"{stem}{suffix}"
        if len(candidate_name) <= max_name_length:
            return stem

        digest = hashlib.sha256(stem.encode("utf-8")).hexdigest()[:12]
        max_stem_length = max(32, max_name_length - len(suffix) - len(digest) - 1)
        trimmed = stem[:max_stem_length].rstrip("-._")
        if not trimmed:
            trimmed = "artifact"
        return f"{trimmed}-{digest}"

    @staticmethod
    def _document_key_from_fields(
        *,
        title: str,
        doi: Optional[str],
        pmid: Optional[str],
        provider_id: str,
        provider_name: str,
    ) -> str:
        if doi:
            return f"doi:{doi.casefold()}"
        if pmid:
            return f"pmid:{pmid}"
        normalized_title = title.strip().casefold()
        if normalized_title:
            return f"title:{normalized_title}"
        return f"{provider_name}:{provider_id}"

    def _write_literature_packet_and_job(
        self,
        *,
        packets_dir: Path,
        jobs_dir: Path,
        slug: str,
        external_id: str,
        source_document: Dict[str, Any],
        abstract_text: str,
        is_review: bool,
        unresolved_detail: str,
        input_context: Dict[str, Any],
    ) -> tuple[Path, Path]:
        if is_review:
            packet = {
                "packet_type": "review_extract_v1",
                "schema_version": "v1",
                "source_document": source_document,
                "review_scope": "Metadata scaffold from literature search result.",
                "entity_candidates": [],
                "claims": [],
                "workflow_observations": [],
                "workflow_stage_observations": [],
                "workflow_step_observations": [],
                "recommended_seed_item_local_ids": [],
                "unresolved_ambiguities": [
                    {
                        "issue": "Metadata scaffold only; title and abstract still need review-level extraction.",
                        "detail": unresolved_detail,
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
                "workflow_observations": [],
                "workflow_stage_observations": [],
                "workflow_step_observations": [],
                "replication_signals": {},
                "unresolved_ambiguities": [
                    {
                        "issue": "Metadata scaffold only; title and abstract still need claim extraction.",
                        "detail": unresolved_detail,
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
            external_id=external_id,
        )
        packet_path.write_text(json.dumps(packet, indent=2) + "\n")

        job = {
            "job_type": "llm_extraction_job_v1",
            "target_packet_type": packet_kind,
            "prompt_template": prompt_template,
            "schema_path": schema_path,
            "source_document": source_document,
            "input_context": input_context,
            "notes": [
                "LLM extraction should populate packet content conservatively from available evidence.",
                "Do not invent canonical item IDs or merges.",
                "Preserve source_document identifiers and metadata from the job payload when they are already supplied.",
            ],
        }
        if "title" not in job["input_context"]:
            job["input_context"]["title"] = source_document["title"]
        if "abstract_text" not in job["input_context"]:
            job["input_context"]["abstract_text"] = abstract_text
        job_path = self._unique_output_path(
            jobs_dir,
            slug=slug,
            suffix=".llm_extraction_job_v1.json",
            external_id=external_id,
        )
        job_path.write_text(json.dumps(job, indent=2) + "\n")
        return packet_path, job_path

    def _enrich_openalex_work(self, title: str, doi: Optional[str], pmid: Optional[str]) -> Dict[str, Any]:
        cache_path = self._enrichment_cache_path(title=title, doi=doi, pmid=pmid)
        cached = self._read_json_cache(cache_path)
        if cached is not None:
            return cached

        europe_pmc_result = self.europe_pmc_client.fetch_by_doi_or_pmid(doi=doi, pmid=pmid)
        semantic_scholar_result = self._find_semantic_scholar_match(title=title, doi=doi, pmid=pmid)
        enrichment = {
            "source": "openalex_enrichment",
        }
        if europe_pmc_result:
            enrichment.update(
                _compact_dict(
                    {
                        "doi": europe_pmc_result.get("doi"),
                        "pmid": europe_pmc_result.get("pmid"),
                        "pmcid": europe_pmc_result.get("pmcid"),
                        "abstract_text": europe_pmc_result.get("abstractText"),
                        "journal": europe_pmc_result.get("journalTitle"),
                        "pub_type": europe_pmc_result.get("pubType"),
                        "is_open_access": europe_pmc_result.get("isOpenAccess"),
                    }
                )
            )
        if semantic_scholar_result:
            enrichment["semantic_scholar_id"] = semantic_scholar_result.get("paperId")
            enrichment["semantic_scholar"] = _compact_dict(
                {
                    "paperId": semantic_scholar_result.get("paperId"),
                    "title": semantic_scholar_result.get("title"),
                    "year": semantic_scholar_result.get("year"),
                    "citationCount": semantic_scholar_result.get("citationCount"),
                    "externalIds": semantic_scholar_result.get("externalIds"),
                }
            )
        compact_enrichment = _compact_dict(enrichment)
        self._write_json_cache(cache_path, compact_enrichment)
        return compact_enrichment

    def _enrichment_cache_path(self, *, title: str, doi: Optional[str], pmid: Optional[str]) -> Path:
        identity = doi or pmid or title.strip().casefold() or "unknown"
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        return self.enrichment_cache_dir / f"{digest}.json"

    @staticmethod
    def _read_json_cache(path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _write_json_cache(path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")

    def _find_semantic_scholar_match(
        self,
        *,
        title: str,
        doi: Optional[str],
        pmid: Optional[str],
    ) -> Dict[str, Any]:
        try:
            payload = self.semantic_scholar_client.search_papers(
                query=title,
                limit=5,
                offset=0,
                fields="paperId,title,year,citationCount,externalIds",
            )
        except Exception:
            return {}
        for result in payload.get("data", []):
            external_ids = result.get("externalIds") or {}
            result_doi = self._normalize_doi(external_ids.get("DOI"))
            result_pmid = str(external_ids.get("PubMed") or "").strip() or None
            if doi and result_doi and result_doi.casefold() == doi.casefold():
                return result
            if pmid and result_pmid == pmid:
                return result
        for result in payload.get("data", []):
            if (result.get("title") or "").strip().casefold() == title.strip().casefold():
                return result
        return {}

    @staticmethod
    def _license_status(enrichment: Dict[str, Any]) -> Optional[str]:
        if enrichment.get("is_open_access") is True:
            return "open_access"
        if enrichment.get("is_open_access") is False:
            return "closed_or_unknown"
        return None
