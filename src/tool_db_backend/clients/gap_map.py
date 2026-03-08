from typing import Any, Dict, Optional

import httpx

from tool_db_backend.config import Settings


DATASET_PATHS = {
    "gaps": "/data/gaps.json",
    "capabilities": "/data/capabilities.json",
    "fields": "/data/fields.json",
    "resources": "/data/resources.json",
    "gapmap-data": "/data/gapmap-data.json",
    "schema": "/data/schema.json",
}


class GapMapClient:
    def __init__(self, settings: Settings, client: Optional[httpx.Client] = None) -> None:
        self.settings = settings
        default_headers = {"User-Agent": "tool-db-backend/0.1.0"}
        self._client = client or httpx.Client(
            base_url=self.settings.gap_map_base_url,
            headers=default_headers,
            timeout=30.0,
        )
        self._client.headers.update(default_headers)

    def fetch_dataset(self, dataset_name: str) -> Dict[str, Any]:
        dataset_key = dataset_name.strip().lower()
        path = DATASET_PATHS.get(dataset_key)
        if path is None:
            raise ValueError(f"Unsupported Gap Map dataset: {dataset_name}")
        response = self._client.get(path)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()
