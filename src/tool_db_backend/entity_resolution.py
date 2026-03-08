import re
import unicodedata
from typing import Any, Dict, List

import yaml

from tool_db_backend.config import Settings


def _norm(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


class EntityResolver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._existing_items = self._load_existing_items()
        self._existing_workflows = self._load_existing_workflows()

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

    def resolve_workflow_candidates(
        self,
        canonical_workflow_candidates: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        resolutions = {}
        for local_id, candidate in canonical_workflow_candidates.items():
            matches = self._match_workflow_candidate(candidate)
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
        matches_by_slug: Dict[str, Dict[str, str]] = {}
        candidate_slug = _norm(candidate["slug"])
        candidate_name = _norm(candidate["canonical_name"])
        candidate_aliases = {_norm(alias) for alias in candidate.get("aliases", [])}
        candidate_item_type = candidate.get("item_type")
        candidate_external_ids = _normalize_external_ids(candidate.get("external_ids", {}))

        for item in self._existing_items:
            item_slug = _norm(item["slug"])
            item_name = _norm(item["canonical_name"])
            item_synonyms = {
                _norm(alias) for alias in (item.get("synonyms", []) + item.get("aliases", []))
            }
            item_external_ids = _normalize_external_ids(item.get("external_ids", {}))
            item_type = item.get("item_type")

            if candidate_external_ids and item_external_ids:
                for key, value in candidate_external_ids.items():
                    if item_external_ids.get(key) == value:
                        matches_by_slug[item["slug"]] = {"slug": item["slug"], "matched_by": f"external_id:{key}"}
                        break
                if item["slug"] in matches_by_slug:
                    continue

            if candidate_item_type and item_type and candidate_item_type != item_type:
                continue

            if item_slug == candidate_slug:
                matches_by_slug[item["slug"]] = {"slug": item["slug"], "matched_by": "slug"}
                continue
            if item_name == candidate_name:
                matches_by_slug[item["slug"]] = {"slug": item["slug"], "matched_by": "canonical_name"}
                continue
            if candidate_name and candidate_name in item_synonyms:
                matches_by_slug[item["slug"]] = {"slug": item["slug"], "matched_by": "synonym"}
                continue
            if item_name and item_name in candidate_aliases:
                matches_by_slug[item["slug"]] = {"slug": item["slug"], "matched_by": "candidate_alias"}
                continue
            if candidate_aliases.intersection(item_synonyms):
                matches_by_slug[item["slug"]] = {"slug": item["slug"], "matched_by": "synonym"}
        return list(matches_by_slug.values())

    def _match_workflow_candidate(self, candidate: Dict[str, Any]) -> List[Dict[str, str]]:
        matches = []
        candidate_slug = _norm(candidate["slug"])
        candidate_name = _norm(candidate["canonical_name"])
        candidate_aliases = {_norm(alias) for alias in candidate.get("aliases", [])}

        for workflow in self._existing_workflows:
            workflow_aliases = {_norm(alias) for alias in workflow.get("aliases", [])}
            if _norm(workflow["slug"]) == candidate_slug:
                matches.append({"slug": workflow["slug"], "matched_by": "slug"})
                continue
            if _norm(workflow["canonical_name"]) == candidate_name:
                matches.append({"slug": workflow["slug"], "matched_by": "canonical_name"})
                continue
            if candidate_aliases.intersection(workflow_aliases):
                matches.append({"slug": workflow["slug"], "matched_by": "alias"})
        return matches

    def _load_existing_items(self) -> List[Dict[str, Any]]:
        items = []
        items_root = self.settings.knowledge_root / "items"
        for structured_path in sorted(items_root.glob("*/structured.yaml")):
            data = yaml.safe_load(structured_path.read_text())
            if isinstance(data, dict):
                items.append(
                    {
                        **data,
                        "canonical_name": data.get("canonical_name", structured_path.parent.name),
                        "aliases": data.get("aliases", []),
                    }
                )
        return items

    def _load_existing_workflows(self) -> List[Dict[str, Any]]:
        workflows = []
        workflows_root = self.settings.knowledge_root / "workflows"
        for structured_path in sorted(workflows_root.glob("*/structured.yaml")):
            data = yaml.safe_load(structured_path.read_text())
            if isinstance(data, dict):
                workflows.append(
                    {
                        "slug": data.get("slug", structured_path.parent.name),
                        "canonical_name": data.get("name", structured_path.parent.name),
                        "aliases": data.get("aliases", []),
                    }
                )
        return workflows


def _normalize_external_ids(external_ids: Dict[str, Any]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for key, value in (external_ids or {}).items():
        if value is None:
            continue
        normalized[str(key)] = _norm(str(value))
    return normalized
