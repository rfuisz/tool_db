import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from tool_db_backend.config import Settings


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ReviewQueueWriter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def write_tasks(
        self,
        source_document: Dict[str, Any],
        tasks: List[Dict[str, Any]],
        output_path: Optional[Path] = None,
    ) -> Path:
        target_path = output_path or self._default_path(source_document)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "review_queue_type": "curation_review_queue_v1",
            "generated_at": _utc_now_iso(),
            "source_document": source_document,
            "tasks": tasks,
        }
        target_path.write_text(json.dumps(payload, indent=2) + "\n")
        return target_path

    def _default_path(self, source_document: Dict[str, Any]) -> Path:
        identifier = (
            source_document.get("doi")
            or source_document.get("openalex_id")
            or source_document.get("nct_id")
            or source_document.get("title")
            or "source-document"
        )
        safe_identifier = "".join(ch if ch.isalnum() else "_" for ch in identifier).strip("_") or "source_document"
        return self.settings.review_queue_root / f"{safe_identifier}.review.json"
