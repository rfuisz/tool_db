from typing import Any, Dict, Optional

import httpx

from tool_db_backend.config import Settings


class EuropePMCClient:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        default_headers = {"User-Agent": "tool-db-backend/0.1.0", "Accept": "application/json"}
        self._client = client or httpx.Client(
            base_url=self.settings.europe_pmc_base_url,
            headers=default_headers,
            timeout=30.0,
        )
        self._client.headers.update(default_headers)

    def search(self, query: str, page_size: int = 25, page: int = 1, result_type: str = "core") -> Dict[str, Any]:
        response = self._client.get(
            "/search",
            params={
                "query": query,
                "format": "json",
                "pageSize": page_size,
                "page": page,
                "resultType": result_type,
            },
        )
        response.raise_for_status()
        return response.json()

    def fetch_by_doi_or_pmid(self, doi: Optional[str] = None, pmid: Optional[str] = None) -> Optional[Dict[str, Any]]:
        queries = []
        if doi:
            queries.append(f'DOI:"{doi}"')
        if pmid:
            queries.append(f'EXT_ID:{pmid} AND SRC:MED')

        for query in queries:
            payload = self.search(query=query, page_size=1)
            results = ((payload.get("resultList") or {}).get("result") or [])
            if results:
                return results[0]
        return None

    def close(self) -> None:
        self._client.close()
