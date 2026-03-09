import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from tool_db_backend.config import Settings


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(token: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", token.strip())
    normalized = normalized.strip("._-")
    return normalized or "unknown"


class RawPayloadStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def json_payload_path(self, source_key: str, resource_type: str, external_id: str) -> Path:
        target_dir = (
            self.settings.raw_payload_root
            / _slugify(source_key)
            / _slugify(resource_type)
        )
        return target_dir / f"{_slugify(external_id)}.json"

    def text_payload_path(self, source_key: str, resource_type: str, external_id: str) -> Path:
        target_dir = (
            self.settings.raw_payload_root
            / _slugify(source_key)
            / _slugify(resource_type)
        )
        return target_dir / f"{_slugify(external_id)}.json"

    def write_json_payload(
        self,
        source_key: str,
        resource_type: str,
        external_id: str,
        payload: Dict[str, Any],
    ) -> Path:
        target_path = self.json_payload_path(source_key, resource_type, external_id)
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        wrapped_payload = {
            "source_key": source_key,
            "resource_type": resource_type,
            "external_id": external_id,
            "fetched_at": _utc_now_iso(),
            "payload": payload,
        }
        target_path.write_text(json.dumps(wrapped_payload, indent=2) + "\n")
        return target_path

    def write_text_payload(
        self,
        source_key: str,
        resource_type: str,
        external_id: str,
        payload_text: str,
        content_type: str = "text/plain",
    ) -> Path:
        target_path = self.text_payload_path(source_key, resource_type, external_id)
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        wrapped_payload = {
            "source_key": source_key,
            "resource_type": resource_type,
            "external_id": external_id,
            "fetched_at": _utc_now_iso(),
            "content_type": content_type,
            "payload_text": payload_text,
        }
        target_path.write_text(json.dumps(wrapped_payload, indent=2) + "\n")
        return target_path

    def read_json_payload(
        self,
        source_key: str,
        resource_type: str,
        external_id: str,
    ) -> Dict[str, Any] | None:
        target_path = self.json_payload_path(source_key, resource_type, external_id)
        if not target_path.exists():
            return None
        try:
            wrapped_payload = json.loads(target_path.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        payload = wrapped_payload.get("payload")
        return payload if isinstance(payload, dict) else None

    def read_text_payload(
        self,
        source_key: str,
        resource_type: str,
        external_id: str,
    ) -> str | None:
        target_path = self.text_payload_path(source_key, resource_type, external_id)
        if not target_path.exists():
            return None
        try:
            wrapped_payload = json.loads(target_path.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        payload_text = wrapped_payload.get("payload_text")
        return payload_text if isinstance(payload_text, str) else None
