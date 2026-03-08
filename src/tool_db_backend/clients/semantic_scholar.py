from typing import Any, Dict, Optional

import httpx

from tool_db_backend.config import Settings


class SemanticScholarClient:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        if self.settings.semantic_scholar_api_key:
            headers["x-api-key"] = self.settings.semantic_scholar_api_key

        self._client = client or httpx.Client(
            base_url=self.settings.semantic_scholar_base_url,
            headers=headers,
            timeout=30.0,
        )
        self._client.headers.update(headers)

    def fetch_paper(self, paper_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if fields:
            params["fields"] = fields

        response = self._client.get(f"/paper/{paper_id.strip()}", params=params)
        response.raise_for_status()
        return response.json()

    def search_papers(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "query": query.strip(),
            "limit": limit,
            "offset": offset,
        }
        if fields:
            params["fields"] = fields

        response = self._client.get("/paper/search", params=params)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()
