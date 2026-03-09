from typing import Any, Dict, Optional

import httpx

from tool_db_backend.config import Settings


class PMCClient:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        default_headers = {"User-Agent": "tool-db-backend/0.1.0", "Accept": "application/json"}
        self._client = client or httpx.Client(
            base_url=self.settings.pmc_bioc_base_url,
            headers=default_headers,
            timeout=30.0,
        )
        self._client.headers.update(default_headers)

    def fetch_bioc_fulltext(self, pmcid: str) -> Dict[str, Any]:
        normalized = self._normalize_pmcid(pmcid)
        response = self._client.get(f"/pmcoa.cgi/BioC_json/{normalized}/unicode")
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _normalize_pmcid(pmcid: str) -> str:
        cleaned = pmcid.strip().upper()
        if not cleaned.startswith("PMC"):
            cleaned = f"PMC{cleaned}"
        return cleaned

    def close(self) -> None:
        self._client.close()
