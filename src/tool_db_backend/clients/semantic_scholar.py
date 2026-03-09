import logging
import time
from typing import Any, Dict, Optional

import httpx

from tool_db_backend.config import Settings

logger = logging.getLogger(__name__)


class SemanticScholarClient:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        self._api_key = settings.semantic_scholar_api_key or None
        self._key_disabled = False
        headers = self._build_headers()
        self._client = client or httpx.Client(
            base_url=self.settings.semantic_scholar_base_url,
            headers=headers,
            timeout=30.0,
        )
        self._client.headers.update(headers)

    def _build_headers(self, use_key: bool = True) -> Dict[str, str]:
        headers = {
            "User-Agent": "tool-db-backend/0.1.0",
            "Accept": "application/json",
        }
        if use_key and self._api_key and not self._key_disabled:
            headers["x-api-key"] = self._api_key
        return headers

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        for attempt in range(3):
            response = self._client.request(method, url, **kwargs)
            if response.status_code == 403 and self._api_key and not self._key_disabled:
                logger.warning(
                    "Semantic Scholar returned 403 with API key; retrying without key. "
                    "The key may be expired or blocked."
                )
                self._key_disabled = True
                self._client.headers.pop("x-api-key", None)
                continue
            if response.status_code == 429:
                wait = min(2 ** attempt * 3, 30)
                logger.debug("Semantic Scholar 429; waiting %ds before retry.", wait)
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response
        response.raise_for_status()
        return response

    def fetch_paper(self, paper_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if fields:
            params["fields"] = fields
        response = self._request("GET", f"/paper/{paper_id.strip()}", params=params)
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
        response = self._request("GET", "/paper/search", params=params)
        return response.json()

    def close(self) -> None:
        self._client.close()
