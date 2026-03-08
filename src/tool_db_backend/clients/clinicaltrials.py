from typing import Any, Dict, Optional

import httpx

from tool_db_backend.config import Settings


class ClinicalTrialsClient:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        default_headers = {"User-Agent": "tool-db-backend/0.1.0"}
        self._client = client or httpx.Client(
            base_url=self.settings.clinicaltrials_base_url,
            headers=default_headers,
            timeout=30.0,
        )
        self._client.headers.update(default_headers)

    def fetch_study(self, nct_id: str) -> Dict[str, Any]:
        normalized_id = nct_id.strip().upper()
        response = self._client.get(f"/studies/{normalized_id}", params={"format": "json"})
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()
