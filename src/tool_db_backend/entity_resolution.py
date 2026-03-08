from typing import Any, Dict, List

import yaml

from tool_db_backend.config import Settings


def _norm(value: str) -> str:
    return value.strip().casefold()


class EntityResolver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._existing_items = self._load_existing_items()

    def resolve_item_candidates(
        self,
        canonical_item_candidates: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        resolutions = {}
        for local_id, candidate in canonical_item_candidates.items():
            matches = self._match_item_candidate(candidate)
            if len(matches) == 1:
                resolutions[local_id] = {
                    "resolution_status": "matched_existing",
                    "matched_slug": matches[0]["slug"],
                    "matched_by": matches[0]["matched_by"],
                }
            elif len(matches) > 1:
                resolutions[local_id] = {
                    "resolution_status": "ambiguous_existing",
                    "candidate_matches": matches,
                }
            else:
                resolutions[local_id] = {
                    "resolution_status": "new_candidate",
                    "proposed_slug": candidate["slug"],
                }
        return resolutions

    def _match_item_candidate(self, candidate: Dict[str, Any]) -> List[Dict[str, str]]:
        matches = []
        candidate_slug = _norm(candidate["slug"])
        candidate_name = _norm(candidate["canonical_name"])
        candidate_aliases = {_norm(alias) for alias in candidate.get("aliases", [])}

        for item in self._existing_items:
            if _norm(item["slug"]) == candidate_slug:
                matches.append({"slug": item["slug"], "matched_by": "slug"})
                continue
            if _norm(item["canonical_name"]) == candidate_name:
                matches.append({"slug": item["slug"], "matched_by": "canonical_name"})
                continue
            if candidate_aliases.intersection({_norm(alias) for alias in item.get("synonyms", [])}):
                matches.append({"slug": item["slug"], "matched_by": "synonym"})
        return matches

    def _load_existing_items(self) -> List[Dict[str, Any]]:
        items = []
        items_root = self.settings.knowledge_root / "items"
        for structured_path in sorted(items_root.glob("*/structured.yaml")):
            data = yaml.safe_load(structured_path.read_text())
            if isinstance(data, dict):
                items.append(data)
        return items
