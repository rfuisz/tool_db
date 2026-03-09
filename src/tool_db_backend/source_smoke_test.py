import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from tool_db_backend.clients.europe_pmc import EuropePMCClient
from tool_db_backend.clients.gap_map import GapMapClient
from tool_db_backend.clients.openalex import OpenAlexClient
from tool_db_backend.clients.optobase import OptoBaseClient
from tool_db_backend.clients.pmc import PMCClient
from tool_db_backend.clients.semantic_scholar import SemanticScholarClient
from tool_db_backend.config import Settings
from tool_db_backend.raw_store import RawPayloadStore
from tool_db_backend.source_staging import OptoBaseSearchParser


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "query"


def _append_unique(values: List[str], candidate: Optional[str]) -> None:
    if candidate is None:
        return
    normalized = candidate.strip()
    if not normalized or normalized in values:
        return
    values.append(normalized)


def build_first_pass_query_sets(settings: Settings, seed_query_limit: int = 24) -> Dict[str, List[str]]:
    seed_bundle_path = settings.repo_root / "db" / "seeds" / "knowledge_seed_bundle.v1.json"
    vocabulary_path = settings.schema_root / "canonical" / "controlled_vocabularies.v1.json"
    seed_bundle = json.loads(seed_bundle_path.read_text())
    vocabulary = json.loads(vocabulary_path.read_text())

    generic_literature_queries = [
        "\"optogenetic tools\"",
        "\"optogenetic switch\"",
        "\"light inducible\" protein",
        "\"light-controlled\" gene expression",
        "\"photoactivatable CRISPR\"",
        "\"optogenetic protein clustering\"",
        "\"light-inducible dimer\"",
        "\"light-controlled signaling\"",
        "\"optogenetic transcription\"",
        "\"light-gated enzyme\"",
        "\"optogenetic benchmark\"",
        "\"optogenetic comparison\"",
        "\"comparative optogenetics\"",
        "\"optogenetic limitations\"",
        "\"head-to-head\" optogenetic",
    ]
    seed_terms: List[str] = []
    optobase_terms: List[str] = []

    for item in seed_bundle.get("items", []):
        structured = item.get("structured", {})
        _append_unique(seed_terms, structured.get("canonical_name"))
        for synonym in structured.get("synonyms", []):
            _append_unique(seed_terms, synonym)
        for component in structured.get("components", []):
            _append_unique(seed_terms, component)

        canonical_name = str(structured.get("canonical_name", "")).strip()
        if canonical_name:
            _append_unique(optobase_terms, canonical_name)
        for synonym in structured.get("synonyms", []):
            synonym_text = str(synonym).strip()
            if 2 <= len(synonym_text) <= 48:
                _append_unique(optobase_terms, synonym_text)

    mechanism_queries: List[str] = []
    for mechanism in vocabulary.get("mechanism_families", []):
        label = str(mechanism).replace("_", " ").strip()
        if label:
            _append_unique(mechanism_queries, f"optogenetic {label}")

    process_queries: List[str] = []
    for process in vocabulary.get("target_processes", []):
        label = str(process).replace("_", " ").strip()
        if label:
            _append_unique(process_queries, f"light controlled {label}")

    literature_queries: List[str] = []
    for query in generic_literature_queries:
        _append_unique(literature_queries, query)
    for query in seed_terms[:seed_query_limit]:
        _append_unique(literature_queries, query)
    for query in seed_terms[: min(seed_query_limit, 12)]:
        _append_unique(literature_queries, f"\"{query}\" benchmark")
        _append_unique(literature_queries, f"\"{query}\" comparison")
    for query in mechanism_queries:
        _append_unique(literature_queries, query)
    for query in process_queries:
        _append_unique(literature_queries, query)

    semantic_scholar_queries: List[str] = []
    for query in literature_queries:
        _append_unique(semantic_scholar_queries, query)

    return {
        "europe_pmc": literature_queries,
        "openalex": literature_queries,
        "semantic_scholar": semantic_scholar_queries,
        "optobase": optobase_terms[:seed_query_limit],
    }


class RealDataHarvester:
    DEFAULT_SEMANTIC_SCHOLAR_FIELDS = (
        "paperId,title,year,citationCount,externalIds,abstract,publicationTypes,journal,venue"
    )

    def __init__(
        self,
        settings: Settings,
        europe_pmc_client: Optional[EuropePMCClient] = None,
        pmc_client: Optional[PMCClient] = None,
        openalex_client: Optional[OpenAlexClient] = None,
        semantic_scholar_client: Optional[SemanticScholarClient] = None,
        gap_map_client: Optional[GapMapClient] = None,
        optobase_client: Optional[OptoBaseClient] = None,
        raw_store: Optional[RawPayloadStore] = None,
    ) -> None:
        self.settings = settings
        self.europe_pmc_client = europe_pmc_client or EuropePMCClient(settings)
        self.pmc_client = pmc_client or PMCClient(settings)
        self.openalex_client = openalex_client or OpenAlexClient(settings)
        self.semantic_scholar_client = semantic_scholar_client or SemanticScholarClient(settings)
        self.gap_map_client = gap_map_client or GapMapClient(settings)
        self.optobase_client = optobase_client or OptoBaseClient(settings)
        self.raw_store = raw_store or RawPayloadStore(settings)
        self.optobase_parser = OptoBaseSearchParser()

    def close(self) -> None:
        self.europe_pmc_client.close()
        self.pmc_client.close()
        self.openalex_client.close()
        self.semantic_scholar_client.close()
        self.gap_map_client.close()
        self.optobase_client.close()

    def run(
        self,
        artifact_dir: Optional[Path] = None,
        *,
        europe_pmc_queries: List[str],
        europe_pmc_pages: int,
        europe_pmc_page_size: int,
        pmc_fulltext_limit: int,
        openalex_queries: List[str],
        openalex_pages: int,
        openalex_per_page: int,
        semantic_scholar_queries: List[str],
        semantic_scholar_pages: int,
        semantic_scholar_limit: int,
        optobase_queries: List[str],
    ) -> Dict[str, Any]:
        artifact_root = artifact_dir or (self.settings.pipeline_artifact_root / "real-data-harvest")
        artifact_root.mkdir(parents=True, exist_ok=True)

        gap_map_summary = self._safe_fetch(self._fetch_gap_map, "gap_map")
        europe_pmc_summary = self._safe_fetch(
            lambda: self._fetch_europe_pmc(
                queries=europe_pmc_queries,
                page_size=europe_pmc_page_size,
                pages=europe_pmc_pages,
            ),
            "europe_pmc",
        )
        pmc_summary = self._safe_fetch(
            lambda: self._fetch_pmc_fulltexts(
                europe_pmc_summary.get("raw_paths", {}),
                limit=pmc_fulltext_limit,
            ),
            "pmc",
        )
        openalex_summary = self._safe_fetch(
            lambda: self._fetch_openalex(
                queries=openalex_queries,
                per_page=openalex_per_page,
                pages=openalex_pages,
            ),
            "openalex",
        )
        semantic_scholar_summary = self._safe_fetch(
            lambda: self._fetch_semantic_scholar(
                queries=semantic_scholar_queries,
                limit=semantic_scholar_limit,
                pages=semantic_scholar_pages,
            ),
            "semantic_scholar",
        )
        optobase_summary = self._safe_fetch(
            lambda: self._fetch_optobase(optobase_queries),
            "optobase",
        )

        total_entries = (
            gap_map_summary["entry_count"]
            + europe_pmc_summary["entry_count"]
            + pmc_summary["entry_count"]
            + openalex_summary["entry_count"]
            + semantic_scholar_summary["entry_count"]
        )

        manifest = {
            "manifest_type": "real_data_harvest_v1",
            "config": {
                "europe_pmc_query_count": len(europe_pmc_queries),
                "europe_pmc_pages": europe_pmc_pages,
                "europe_pmc_page_size": europe_pmc_page_size,
                "pmc_fulltext_limit": pmc_fulltext_limit,
                "openalex_query_count": len(openalex_queries),
                "openalex_pages": openalex_pages,
                "openalex_per_page": openalex_per_page,
                "semantic_scholar_query_count": len(semantic_scholar_queries),
                "semantic_scholar_pages": semantic_scholar_pages,
                "semantic_scholar_limit": semantic_scholar_limit,
                "optobase_query_count": len(optobase_queries),
            },
            "sources": {
                "gap_map": gap_map_summary,
                "europe_pmc": europe_pmc_summary,
                "pmc": pmc_summary,
                "openalex": openalex_summary,
                "semantic_scholar": semantic_scholar_summary,
                "optobase": optobase_summary,
            },
            "total_entry_count": total_entries,
        }
        manifest_path = artifact_root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        manifest["manifest_path"] = str(manifest_path)
        return manifest

    def _safe_fetch(self, fetcher: Any, source_key: str) -> Dict[str, Any]:
        try:
            summary = fetcher()
            summary.setdefault("status", "ok")
            return summary
        except (httpx.HTTPError, ValueError) as exc:
            return {
                "status": "error",
                "entry_count": 0,
                "error": f"{source_key}: {exc}",
                "raw_paths": {},
            }

    def _fetch_gap_map(self) -> Dict[str, Any]:
        dataset_names = ["gaps", "capabilities", "resources", "fields"]
        counts: Dict[str, int] = {}
        raw_paths: Dict[str, str] = {}
        total = 0
        for dataset_name in dataset_names:
            payload = self.gap_map_client.fetch_dataset(dataset_name)
            entry_count = self._count_entries(payload)
            counts[dataset_name] = entry_count
            total += entry_count
            raw_path = self.raw_store.write_json_payload(
                source_key="gap_map",
                resource_type=dataset_name,
                external_id=dataset_name,
                payload=payload,
            )
            raw_paths[dataset_name] = str(raw_path)
        return {
            "datasets": counts,
            "entry_count": total,
            "raw_paths": raw_paths,
        }

    def _fetch_europe_pmc(self, queries: List[str], page_size: int, pages: int) -> Dict[str, Any]:
        seen_ids = set()
        counts: Dict[str, int] = {}
        raw_paths: Dict[str, str] = {}
        for query in queries:
            query_total = 0
            for page in range(1, pages + 1):
                payload = self.europe_pmc_client.search(
                    query=query,
                    page_size=page_size,
                    page=page,
                    result_type="core",
                )
                results = ((payload.get("resultList") or {}).get("result") or [])
                counts[f"{query} [page {page}]"] = len(results)
                query_total += len(results)
                for result in results:
                    result_id = result.get("id") or result.get("pmid") or result.get("doi")
                    if result_id:
                        seen_ids.add(str(result_id))
                raw_path = self.raw_store.write_json_payload(
                    source_key="europe_pmc",
                    resource_type="search",
                    external_id=f"{_slugify(query)}-page-{page}",
                    payload=payload,
                )
                raw_paths[f"{query} [page {page}]"] = str(raw_path)
                if not results:
                    break
            counts[query] = query_total
        return {
            "queries": counts,
            "entry_count": len(seen_ids),
            "raw_paths": raw_paths,
        }

    def _fetch_pmc_fulltexts(self, europe_pmc_raw_paths: Dict[str, str], limit: int) -> Dict[str, Any]:
        raw_paths: Dict[str, str] = {}
        errors: Dict[str, str] = {}
        pmcids: List[str] = []
        for raw_path in europe_pmc_raw_paths.values():
            try:
                payload = json.loads(Path(raw_path).read_text())
            except (OSError, json.JSONDecodeError):
                continue
            results = ((payload.get("payload") or {}).get("resultList") or {}).get("result") or []
            for result in results:
                pmcid = str(result.get("pmcid") or "").strip()
                if not pmcid or pmcid in pmcids:
                    continue
                pmcids.append(pmcid)
                if limit > 0 and len(pmcids) >= limit:
                    break
            if limit > 0 and len(pmcids) >= limit:
                break

        for pmcid in pmcids:
            try:
                payload = self.pmc_client.fetch_bioc_fulltext(pmcid)
            except (httpx.HTTPError, ValueError) as exc:
                errors[pmcid] = str(exc)
                continue
            raw_path = self.raw_store.write_json_payload(
                source_key="pmc",
                resource_type="bioc_fulltext",
                external_id=pmcid,
                payload=payload,
            )
            raw_paths[pmcid] = str(raw_path)
        return {
            "entry_count": len(raw_paths),
            "requested_pmcids": pmcids,
            "raw_paths": raw_paths,
            "errors": errors,
        }

    def _fetch_openalex(self, queries: List[str], per_page: int, pages: int) -> Dict[str, Any]:
        seen_ids = set()
        counts: Dict[str, int] = {}
        raw_paths: Dict[str, str] = {}
        for query in queries:
            query_total = 0
            for page in range(1, pages + 1):
                payload = self.openalex_client.search_works(query=query, per_page=per_page, page=page)
                results = payload.get("results", [])
                counts[f"{query} [page {page}]"] = len(results)
                query_total += len(results)
                for result in results:
                    result_id = result.get("id")
                    if result_id:
                        seen_ids.add(result_id)
                raw_path = self.raw_store.write_json_payload(
                    source_key="openalex",
                    resource_type="work_search",
                    external_id=f"{_slugify(query)}-page-{page}",
                    payload=payload,
                )
                raw_paths[f"{query} [page {page}]"] = str(raw_path)
                if not results:
                    break
            counts[query] = query_total
        return {
            "queries": counts,
            "entry_count": len(seen_ids),
            "raw_paths": raw_paths,
        }

    def _fetch_semantic_scholar(self, queries: List[str], limit: int, pages: int) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        raw_paths: Dict[str, str] = {}
        seen_ids = set()
        for query in queries:
            query_total = 0
            for page in range(pages):
                offset = page * limit
                payload = self.semantic_scholar_client.search_papers(
                    query=query,
                    limit=limit,
                    offset=offset,
                    fields=self.DEFAULT_SEMANTIC_SCHOLAR_FIELDS,
                )
                results = payload.get("data", [])
                counts[f"{query} [page {page + 1}]"] = len(results)
                query_total += len(results)
                for result in results:
                    paper_id = result.get("paperId")
                    if paper_id:
                        seen_ids.add(paper_id)
                raw_path = self.raw_store.write_json_payload(
                    source_key="semantic_scholar",
                    resource_type="paper_search",
                    external_id=f"{_slugify(query)}-page-{page + 1}",
                    payload=payload,
                )
                raw_paths[f"{query} [page {page + 1}]"] = str(raw_path)
                if len(results) < limit:
                    break
            counts[query] = query_total
        return {
            "queries": counts,
            "entry_count": len(seen_ids),
            "raw_paths": raw_paths,
        }

    def _fetch_optobase(self, queries: List[str]) -> Dict[str, Any]:
        raw_paths: Dict[str, str] = {}
        parsed_result_counts: Dict[str, int] = {}
        for query in queries:
            payload_text = self.optobase_client.fetch_search_page(query=query)
            raw_path = self.raw_store.write_text_payload(
                source_key="optobase",
                resource_type="search_html",
                external_id=_slugify(query),
                payload_text=payload_text,
                content_type="text/html",
            )
            raw_paths[query] = str(raw_path)
            parsed_result_counts[query] = self.optobase_parser.parse_html(payload_text, query=query).get(
                "result_count",
                0,
            )
        return {
            "queries": queries,
            "entry_count": sum(parsed_result_counts.values()),
            "parsed_result_counts": parsed_result_counts,
            "raw_paths": raw_paths,
        }

    @staticmethod
    def _count_entries(payload: Any) -> int:
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict):
            for key in ("data", "items", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return len(value)
            return len(payload)
        return 0


class RealDataSmokeTester:
    def __init__(
        self,
        settings: Settings,
        europe_pmc_client: Optional[EuropePMCClient] = None,
        pmc_client: Optional[PMCClient] = None,
        openalex_client: Optional[OpenAlexClient] = None,
        semantic_scholar_client: Optional[SemanticScholarClient] = None,
        gap_map_client: Optional[GapMapClient] = None,
        optobase_client: Optional[OptoBaseClient] = None,
        raw_store: Optional[RawPayloadStore] = None,
    ) -> None:
        self.harvester = RealDataHarvester(
            settings=settings,
            europe_pmc_client=europe_pmc_client,
            pmc_client=pmc_client,
            openalex_client=openalex_client,
            semantic_scholar_client=semantic_scholar_client,
            gap_map_client=gap_map_client,
            optobase_client=optobase_client,
            raw_store=raw_store,
        )

    def close(self) -> None:
        self.harvester.close()

    def run(self, artifact_dir: Optional[Path] = None) -> Dict[str, Any]:
        return self.harvester.run(
            artifact_dir=artifact_dir or (self.harvester.settings.pipeline_artifact_root / "real-data-smoke-test"),
            europe_pmc_queries=[
                "\"optogenetic tools\"",
                "\"optogenetic switch\"",
                "AsLOV2 OR LOV2",
                "CRY2 CIB1",
                "PhyB PIF",
                "\"optogenetic protein clustering\"",
                "\"light-controlled gene expression\"",
                "\"photoactivatable CRISPR\"",
            ],
            europe_pmc_pages=1,
            europe_pmc_page_size=25,
            pmc_fulltext_limit=10,
            openalex_queries=[
                "\"optogenetic tools\"",
                "\"optogenetic switch\"",
                "AsLOV2 OR LOV2",
                "CRY2 CIB1",
                "PhyB PIF",
                "\"optogenetic protein clustering\"",
                "\"light-controlled gene expression\"",
                "\"photoactivatable CRISPR\"",
            ],
            openalex_pages=1,
            openalex_per_page=25,
            semantic_scholar_queries=["optogenetic switch"],
            semantic_scholar_pages=1,
            semantic_scholar_limit=25,
            optobase_queries=["AsLOV2", "CRY2"],
        )
