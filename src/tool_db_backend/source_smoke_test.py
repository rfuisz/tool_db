import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from tool_db_backend.llm_web_research import LLMWebResearchClient, LLMWebResearchError
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


def _prepend_unique(values: List[str], candidate: Optional[str]) -> None:
    if candidate is None:
        return
    normalized = candidate.strip()
    if not normalized:
        return
    existing = [value for value in values if value != normalized]
    values[:] = [normalized, *existing]


def _looks_like_tool_name(candidate: Optional[str]) -> bool:
    if candidate is None:
        return False
    cleaned = candidate.strip()
    if not cleaned:
        return False
    if len(cleaned) > 80:
        return False
    tokens = cleaned.split()
    if len(tokens) > 8:
        return False
    if cleaned.endswith(".") or ":" in cleaned:
        return False
    return True


def build_first_pass_query_sets(
    settings: Settings,
    seed_query_limit: int = 24,
    web_research_client: Optional[LLMWebResearchClient] = None,
) -> Dict[str, Any]:
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

    web_research_summary: Dict[str, Any] = {}
    owns_web_research_client = False
    if settings.llm_web_research_enabled:
        client = web_research_client
        if client is None:
            client = LLMWebResearchClient(settings)
            owns_web_research_client = True
        try:
            seed_window = seed_terms[: min(seed_query_limit, 12)]
            web_research_summary = client.expand_seed_queries(seed_terms=seed_window)
            filtered_related_candidates = []
            for related in web_research_summary.get("related_item_candidates", []):
                related_name = str(related.get("name") or "").strip()
                if not _looks_like_tool_name(related_name):
                    continue
                filtered_related_candidates.append(related)
                _append_unique(seed_terms, related_name)
                _prepend_unique(optobase_terms, related_name)
            web_research_summary["related_item_candidates"] = filtered_related_candidates
            for query in web_research_summary.get("literature_queries", []):
                _append_unique(literature_queries, str(query))
                _append_unique(semantic_scholar_queries, str(query))
            for query in web_research_summary.get("optobase_queries", []):
                _prepend_unique(optobase_terms, str(query))
        except LLMWebResearchError:
            web_research_summary = {}
        finally:
            if owns_web_research_client:
                client.close()

    return {
        "europe_pmc": literature_queries,
        "openalex": literature_queries,
        "semantic_scholar": semantic_scholar_queries,
        "optobase": optobase_terms[:seed_query_limit],
        "web_research": web_research_summary,
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
        max_workers = self.settings.llm_max_concurrency

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            gap_map_future = pool.submit(self._safe_fetch, self._fetch_gap_map, "gap_map")
            europe_pmc_future = pool.submit(
                self._safe_fetch,
                lambda: self._fetch_europe_pmc(
                    queries=europe_pmc_queries,
                    page_size=europe_pmc_page_size,
                    pages=europe_pmc_pages,
                ),
                "europe_pmc",
            )
            openalex_future = pool.submit(
                self._safe_fetch,
                lambda: self._fetch_openalex(
                    queries=openalex_queries,
                    per_page=openalex_per_page,
                    pages=openalex_pages,
                ),
                "openalex",
            )
            semantic_scholar_future = pool.submit(
                self._safe_fetch,
                lambda: self._fetch_semantic_scholar(
                    queries=semantic_scholar_queries,
                    limit=semantic_scholar_limit,
                    pages=semantic_scholar_pages,
                ),
                "semantic_scholar",
            )
            optobase_future = pool.submit(
                self._safe_fetch,
                lambda: self._fetch_optobase(optobase_queries),
                "optobase",
            )

            gap_map_summary = gap_map_future.result()
            europe_pmc_summary = europe_pmc_future.result()
            openalex_summary = openalex_future.result()
            semantic_scholar_summary = semantic_scholar_future.result()
            optobase_summary = optobase_future.result()

        pmc_summary = self._safe_fetch(
            lambda: self._fetch_pmc_fulltexts(
                europe_pmc_summary.get("raw_paths", {}),
                limit=pmc_fulltext_limit,
            ),
            "pmc",
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

    def _read_cached_json_payload(
        self,
        *,
        source_key: str,
        resource_type: str,
        external_id: str,
    ) -> Optional[Any]:
        reader = getattr(self.raw_store, "read_json_payload", None)
        if reader is None:
            return None
        return reader(source_key, resource_type, external_id)

    def _read_cached_text_payload(
        self,
        *,
        source_key: str,
        resource_type: str,
        external_id: str,
    ) -> Optional[str]:
        reader = getattr(self.raw_store, "read_text_payload", None)
        if reader is None:
            return None
        payload = reader(source_key, resource_type, external_id)
        return payload if isinstance(payload, str) else None

    def _fetch_gap_map(self) -> Dict[str, Any]:
        dataset_names = ["gaps", "capabilities", "resources", "fields"]
        counts: Dict[str, int] = {}
        raw_paths: Dict[str, str] = {}
        total = 0
        cache_hits = 0
        for dataset_name in dataset_names:
            payload = self._read_cached_json_payload(
                source_key="gap_map",
                resource_type=dataset_name,
                external_id=dataset_name,
            )
            if payload is None:
                payload = self.gap_map_client.fetch_dataset(dataset_name)
            else:
                cache_hits += 1
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
            "cache_hits": cache_hits,
        }

    def _fetch_single_europe_pmc_page(self, query: str, page_size: int, page: int) -> Dict[str, Any]:
        external_id = f"{_slugify(query)}-page-{page}"
        payload = self._read_cached_json_payload(
            source_key="europe_pmc", resource_type="search", external_id=external_id,
        )
        cached = payload is not None
        if payload is None:
            payload = self.europe_pmc_client.search(
                query=query, page_size=page_size, page=page, result_type="core",
            )
        results = ((payload.get("resultList") or {}).get("result") or [])
        raw_path = self.raw_store.write_json_payload(
            source_key="europe_pmc", resource_type="search", external_id=external_id, payload=payload,
        )
        result_ids = [
            str(r.get("id") or r.get("pmid") or r.get("doi"))
            for r in results if r.get("id") or r.get("pmid") or r.get("doi")
        ]
        return {"query": query, "page": page, "count": len(results), "ids": result_ids,
                "raw_path": str(raw_path), "cached": cached}

    def _fetch_europe_pmc(self, queries: List[str], page_size: int, pages: int) -> Dict[str, Any]:
        seen_ids: set = set()
        counts: Dict[str, int] = {}
        raw_paths: Dict[str, str] = {}
        cache_hits = 0
        tasks = [(q, p) for q in queries for p in range(1, pages + 1)]
        with ThreadPoolExecutor(max_workers=self.settings.llm_max_concurrency) as pool:
            futures = {
                pool.submit(self._fetch_single_europe_pmc_page, q, page_size, p): (q, p)
                for q, p in tasks
            }
            for future in as_completed(futures):
                result = future.result()
                q, p = result["query"], result["page"]
                counts[f"{q} [page {p}]"] = result["count"]
                seen_ids.update(result["ids"])
                raw_paths[f"{q} [page {p}]"] = result["raw_path"]
                if result["cached"]:
                    cache_hits += 1
        for query in queries:
            counts[query] = sum(counts.get(f"{query} [page {p}]", 0) for p in range(1, pages + 1))
        return {
            "queries": counts,
            "entry_count": len(seen_ids),
            "raw_paths": raw_paths,
            "cache_hits": cache_hits,
        }

    def _fetch_single_pmc_fulltext(self, pmcid: str) -> Dict[str, Any]:
        payload = self._read_cached_json_payload(
            source_key="pmc", resource_type="bioc_fulltext", external_id=pmcid,
        )
        cached = payload is not None
        if payload is None:
            try:
                payload = self.pmc_client.fetch_bioc_fulltext(pmcid)
            except (httpx.HTTPError, ValueError) as exc:
                return {"pmcid": pmcid, "error": str(exc), "cached": False}
        raw_path = self.raw_store.write_json_payload(
            source_key="pmc", resource_type="bioc_fulltext", external_id=pmcid, payload=payload,
        )
        return {"pmcid": pmcid, "raw_path": str(raw_path), "cached": cached}

    def _fetch_pmc_fulltexts(self, europe_pmc_raw_paths: Dict[str, str], limit: int) -> Dict[str, Any]:
        raw_paths: Dict[str, str] = {}
        errors: Dict[str, str] = {}
        pmcids: List[str] = []
        cache_hits = 0
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

        with ThreadPoolExecutor(max_workers=self.settings.llm_max_concurrency) as pool:
            futures = {pool.submit(self._fetch_single_pmc_fulltext, pmcid): pmcid for pmcid in pmcids}
            for future in as_completed(futures):
                result = future.result()
                if "error" in result:
                    errors[result["pmcid"]] = result["error"]
                else:
                    raw_paths[result["pmcid"]] = result["raw_path"]
                    if result["cached"]:
                        cache_hits += 1
        return {
            "entry_count": len(raw_paths),
            "requested_pmcids": pmcids,
            "raw_paths": raw_paths,
            "errors": errors,
            "cache_hits": cache_hits,
        }

    def _fetch_single_openalex_page(
        self, query: str, per_page: int, page: int, api_semaphore: threading.Semaphore,
    ) -> Dict[str, Any]:
        external_id = f"{_slugify(query)}-page-{page}"
        payload = self._read_cached_json_payload(
            source_key="openalex", resource_type="work_search", external_id=external_id,
        )
        cached = payload is not None
        if payload is None:
            with api_semaphore:
                payload = self.openalex_client.search_works(query=query, per_page=per_page, page=page)
        results = payload.get("results", [])
        raw_path = self.raw_store.write_json_payload(
            source_key="openalex", resource_type="work_search", external_id=external_id, payload=payload,
        )
        result_ids = [r.get("id") for r in results if r.get("id")]
        return {"query": query, "page": page, "count": len(results), "ids": result_ids,
                "raw_path": str(raw_path), "cached": cached}

    def _fetch_openalex(self, queries: List[str], per_page: int, pages: int) -> Dict[str, Any]:
        seen_ids: set = set()
        counts: Dict[str, int] = {}
        raw_paths: Dict[str, str] = {}
        cache_hits = 0
        api_semaphore = threading.Semaphore(self.settings.openalex_max_concurrency)
        tasks = [(q, p) for q in queries for p in range(1, pages + 1)]
        with ThreadPoolExecutor(max_workers=self.settings.llm_max_concurrency) as pool:
            futures = {
                pool.submit(self._fetch_single_openalex_page, q, per_page, p, api_semaphore): (q, p)
                for q, p in tasks
            }
            for future in as_completed(futures):
                result = future.result()
                q, p = result["query"], result["page"]
                counts[f"{q} [page {p}]"] = result["count"]
                seen_ids.update(result["ids"])
                raw_paths[f"{q} [page {p}]"] = result["raw_path"]
                if result["cached"]:
                    cache_hits += 1
        for query in queries:
            counts[query] = sum(counts.get(f"{query} [page {p}]", 0) for p in range(1, pages + 1))
        return {
            "queries": counts,
            "entry_count": len(seen_ids),
            "raw_paths": raw_paths,
            "cache_hits": cache_hits,
        }

    def _fetch_single_semantic_scholar_page(self, query: str, limit: int, page: int) -> Dict[str, Any]:
        offset = page * limit
        external_id = f"{_slugify(query)}-page-{page + 1}"
        payload = self._read_cached_json_payload(
            source_key="semantic_scholar", resource_type="paper_search", external_id=external_id,
        )
        cached = payload is not None
        if payload is None:
            payload = self.semantic_scholar_client.search_papers(
                query=query, limit=limit, offset=offset, fields=self.DEFAULT_SEMANTIC_SCHOLAR_FIELDS,
            )
        results = payload.get("data", [])
        raw_path = self.raw_store.write_json_payload(
            source_key="semantic_scholar", resource_type="paper_search", external_id=external_id, payload=payload,
        )
        paper_ids = [r.get("paperId") for r in results if r.get("paperId")]
        return {"query": query, "page": page, "count": len(results), "ids": paper_ids,
                "raw_path": str(raw_path), "cached": cached}

    def _fetch_semantic_scholar(self, queries: List[str], limit: int, pages: int) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        raw_paths: Dict[str, str] = {}
        seen_ids: set = set()
        cache_hits = 0
        tasks = [(q, p) for q in queries for p in range(pages)]
        with ThreadPoolExecutor(max_workers=self.settings.llm_max_concurrency) as pool:
            futures = {
                pool.submit(self._fetch_single_semantic_scholar_page, q, limit, p): (q, p)
                for q, p in tasks
            }
            for future in as_completed(futures):
                result = future.result()
                q, p = result["query"], result["page"]
                counts[f"{q} [page {p + 1}]"] = result["count"]
                seen_ids.update(result["ids"])
                raw_paths[f"{q} [page {p + 1}]"] = result["raw_path"]
                if result["cached"]:
                    cache_hits += 1
        for query in queries:
            counts[query] = sum(counts.get(f"{query} [page {p + 1}]", 0) for p in range(pages))
        return {
            "queries": counts,
            "entry_count": len(seen_ids),
            "raw_paths": raw_paths,
            "cache_hits": cache_hits,
        }

    def _fetch_single_optobase(self, query: str) -> Dict[str, Any]:
        external_id = _slugify(query)
        payload_text = self._read_cached_text_payload(
            source_key="optobase", resource_type="search_html", external_id=external_id,
        )
        cached = payload_text is not None
        if payload_text is None:
            payload_text = self.optobase_client.fetch_search_page(query=query)
        raw_path = self.raw_store.write_text_payload(
            source_key="optobase", resource_type="search_html", external_id=external_id,
            payload_text=payload_text, content_type="text/html",
        )
        count = self.optobase_parser.parse_html(payload_text, query=query).get("result_count", 0)
        return {"query": query, "raw_path": str(raw_path), "count": count, "cached": cached}

    def _fetch_optobase(self, queries: List[str]) -> Dict[str, Any]:
        raw_paths: Dict[str, str] = {}
        parsed_result_counts: Dict[str, int] = {}
        cache_hits = 0
        with ThreadPoolExecutor(max_workers=self.settings.llm_max_concurrency) as pool:
            futures = {pool.submit(self._fetch_single_optobase, q): q for q in queries}
            for future in as_completed(futures):
                result = future.result()
                raw_paths[result["query"]] = result["raw_path"]
                parsed_result_counts[result["query"]] = result["count"]
                if result["cached"]:
                    cache_hits += 1
        return {
            "queries": queries,
            "entry_count": sum(parsed_result_counts.values()),
            "parsed_result_counts": parsed_result_counts,
            "raw_paths": raw_paths,
            "cache_hits": cache_hits,
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
