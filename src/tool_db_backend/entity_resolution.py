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

            if item_slug == candidate_slug:
                matches_by_slug[item["slug"]] = {"slug": item["slug"], "matched_by": "slug"}
                continue
            if item_name == candidate_name:
                matches_by_slug[item["slug"]] = {"slug": item["slug"], "matched_by": "canonical_name"}
                continue

            if candidate_item_type and item_type and not self._item_types_compatible(candidate_item_type, item_type):
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

    @staticmethod
    def _item_types_compatible(candidate_item_type: str, item_type: str) -> bool:
        if candidate_item_type == item_type:
            return True
        switchish_types = {"construct_pattern", "protein_domain", "multi_component_switch"}
        if candidate_item_type in switchish_types and item_type in switchish_types:
            return True
        return False

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
        items_by_slug: Dict[str, Dict[str, Any]] = {}
        items_root = self.settings.knowledge_root / "items"
        for structured_path in sorted(items_root.glob("*/structured.yaml")):
            data = yaml.safe_load(structured_path.read_text())
            if isinstance(data, dict):
                slug = data.get("slug", structured_path.parent.name)
                items_by_slug[slug] = {
                    **data,
                    "slug": slug,
                    "canonical_name": data.get("canonical_name", structured_path.parent.name),
                    "aliases": data.get("aliases", []),
                    "synonyms": data.get("synonyms", []),
                }

        if self.settings.database_url:
            try:
                import psycopg

                with psycopg.connect(self.settings.database_url) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            select
                              ti.slug,
                              ti.canonical_name,
                              ti.item_type::text,
                              ti.external_ids,
                              coalesce(
                                array_agg(distinct s.synonym)
                                filter (where s.synonym is not null and s.synonym <> ''),
                                '{}'::text[]
                              ) as synonyms
                            from toolkit_item ti
                            left join item_synonym s on s.item_id = ti.id
                            group by ti.id
                            order by ti.slug asc
                            """
                        )
                        for slug, canonical_name, item_type, external_ids, synonyms in cursor.fetchall():
                            existing = items_by_slug.get(slug, {})
                            items_by_slug[slug] = {
                                **existing,
                                "slug": slug,
                                "canonical_name": canonical_name or existing.get("canonical_name") or slug,
                                "item_type": item_type or existing.get("item_type"),
                                "external_ids": external_ids or existing.get("external_ids", {}),
                                "aliases": _dedupe_preserving_order(
                                    list(existing.get("aliases", []))
                                ),
                                "synonyms": _dedupe_preserving_order(
                                    list(existing.get("synonyms", [])) + list(synonyms or [])
                                ),
                            }
            except Exception:
                pass

        return list(items_by_slug.values())

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


def _dedupe_preserving_order(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result
