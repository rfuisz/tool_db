import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from tool_db_backend.clients.gap_map import GapMapClient
from tool_db_backend.clients.openalex import OpenAlexClient
from tool_db_backend.clients.optobase import OptoBaseClient
from tool_db_backend.clients.semantic_scholar import SemanticScholarClient
from tool_db_backend.config import Settings
from tool_db_backend.raw_store import RawPayloadStore


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "query"


class RealDataSmokeTester:
    def __init__(
        self,
        settings: Settings,
        openalex_client: Optional[OpenAlexClient] = None,
        semantic_scholar_client: Optional[SemanticScholarClient] = None,
        gap_map_client: Optional[GapMapClient] = None,
        optobase_client: Optional[OptoBaseClient] = None,
        raw_store: Optional[RawPayloadStore] = None,
    ) -> None:
        self.settings = settings
        self.openalex_client = openalex_client or OpenAlexClient(settings)
        self.semantic_scholar_client = semantic_scholar_client or SemanticScholarClient(settings)
        self.gap_map_client = gap_map_client or GapMapClient(settings)
        self.optobase_client = optobase_client or OptoBaseClient(settings)
        self.raw_store = raw_store or RawPayloadStore(settings)

    def close(self) -> None:
        self.openalex_client.close()
        self.semantic_scholar_client.close()
        self.gap_map_client.close()
        self.optobase_client.close()

    def run(self, artifact_dir: Optional[Path] = None) -> Dict[str, Any]:
        artifact_root = artifact_dir or (self.settings.pipeline_artifact_root / "real-data-smoke-test")
        artifact_root.mkdir(parents=True, exist_ok=True)

        gap_map_summary = self._safe_fetch(self._fetch_gap_map, "gap_map")
        openalex_summary = self._safe_fetch(self._fetch_openalex, "openalex")
        semantic_scholar_summary = self._safe_fetch(self._fetch_semantic_scholar, "semantic_scholar")
        optobase_summary = self._safe_fetch(self._fetch_optobase, "optobase")

        total_entries = (
            gap_map_summary["entry_count"]
            + openalex_summary["entry_count"]
            + semantic_scholar_summary["entry_count"]
        )

        manifest = {
            "manifest_type": "real_data_smoke_test_v1",
            "sources": {
                "gap_map": gap_map_summary,
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

    def _fetch_openalex(self) -> Dict[str, Any]:
        queries = [
            "\"optogenetic tools\"",
            "\"optogenetic switch\"",
            "AsLOV2 OR LOV2",
            "CRY2 CIB1",
            "PhyB PIF",
            "\"optogenetic protein clustering\"",
            "\"light-controlled gene expression\"",
            "\"photoactivatable CRISPR\"",
        ]
        seen_ids = set()
        counts: Dict[str, int] = {}
        raw_paths: Dict[str, str] = {}
        for query in queries:
            payload = self.openalex_client.search_works(query=query, per_page=25, page=1)
            results = payload.get("results", [])
            counts[query] = len(results)
            for result in results:
                result_id = result.get("id")
                if result_id:
                    seen_ids.add(result_id)
            raw_path = self.raw_store.write_json_payload(
                source_key="openalex",
                resource_type="work_search",
                external_id=_slugify(query),
                payload=payload,
            )
            raw_paths[query] = str(raw_path)
        return {
            "queries": counts,
            "entry_count": len(seen_ids),
            "raw_paths": raw_paths,
        }

    def _fetch_semantic_scholar(self) -> Dict[str, Any]:
        query = "optogenetic switch"
        fields = "paperId,title,year,citationCount,externalIds"
        payload = self.semantic_scholar_client.search_papers(
            query=query,
            limit=25,
            offset=0,
            fields=fields,
        )
        results = payload.get("data", [])
        raw_path = self.raw_store.write_json_payload(
            source_key="semantic_scholar",
            resource_type="paper_search",
            external_id=_slugify(query),
            payload=payload,
        )
        return {
            "queries": {query: len(results)},
            "entry_count": len(results),
            "raw_paths": {query: str(raw_path)},
        }

    def _fetch_optobase(self) -> Dict[str, Any]:
        queries = ["AsLOV2", "CRY2"]
        raw_paths: Dict[str, str] = {}
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
        return {
            "queries": queries,
            "entry_count": 0,
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
