from typing import Any, Dict, Optional

import httpx

from tool_db_backend.config import Settings


class OpenAlexClient:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        default_headers = {"User-Agent": "tool-db-backend/0.1.0"}
        self._client = client or httpx.Client(
            base_url=self.settings.openalex_base_url,
            headers=default_headers,
            timeout=30.0,
        )
        self._client.headers.update(default_headers)

    def fetch_work(self, work_id: str) -> Dict[str, Any]:
        normalized_id = self._normalize_work_id(work_id)
        params = {}
        if self.settings.openalex_mailto:
            params["mailto"] = self.settings.openalex_mailto

        response = self._client.get(f"/works/{normalized_id}", params=params)
        response.raise_for_status()
        return response.json()

    def search_works(
        self,
        query: str,
        per_page: int = 25,
        page: int = 1,
        filter_expr: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "search": query.strip(),
            "per-page": per_page,
            "page": page,
        }
        if filter_expr:
            params["filter"] = filter_expr
        if self.settings.openalex_mailto:
            params["mailto"] = self.settings.openalex_mailto

        response = self._client.get("/works", params=params)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _normalize_work_id(work_id: str) -> str:
        work_id = work_id.strip()
        if work_id.startswith("https://openalex.org/"):
            return work_id.rsplit("/", 1)[-1]
        if work_id.startswith("W"):
            return work_id
        return work_id
