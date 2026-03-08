from typing import Optional

import httpx

from tool_db_backend.config import Settings


class OptoBaseClient:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        default_headers = {"User-Agent": "tool-db-backend/0.1.0"}
        self._client = client or httpx.Client(
            base_url=self.settings.optobase_base_url,
            headers=default_headers,
            timeout=30.0,
        )
        self._client.headers.update(default_headers)

    def fetch_search_page(self, query: str = "") -> str:
        params = {}
        cleaned = query.strip()
        if cleaned:
            params["q"] = cleaned
        response = self._client.get("/search/", params=params)
        response.raise_for_status()
        return response.text

    def close(self) -> None:
        self._client.close()
