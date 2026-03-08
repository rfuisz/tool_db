import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from tool_db_backend.config import Settings
from tool_db_backend.entity_resolution import EntityResolver


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class LoadPlanBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.resolver = EntityResolver(settings)

    def build_from_normalized_file(self, normalized_path: Path) -> Dict[str, Any]:
        payload = json.loads(normalized_path.read_text())
        return self.build_from_normalized_payload(payload)

    def build_from_normalized_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        candidates = payload.get("canonical_item_candidates", {})
        resolutions = self.resolver.resolve_item_candidates(candidates)
        actions = self._build_item_actions(candidates, resolutions)
        candidate_key_to_local_id = {
            candidate["candidate_key"]: local_id
            for local_id, candidate in candidates.items()
        }
        claim_actions = self._build_claim_actions(
            payload.get("claims", []),
            resolutions,
            candidate_key_to_local_id,
        )

        return {
            "load_plan_type": "canonical_load_plan_v1",
            "generated_at": _utc_now_iso(),
            "source_document": payload.get("source_document", {}),
            "item_resolutions": resolutions,
            "actions": {
                "toolkit_items": actions,
                "claims": claim_actions,
            },
        }

    def write_load_plan(self, normalized_path: Path, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.build_from_normalized_file(normalized_path), indent=2) + "\n")
        return output_path

    @staticmethod
    def _build_item_actions(
        candidates: Dict[str, Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        actions = []
        for local_id, candidate in candidates.items():
            resolution = resolutions[local_id]
            status = resolution["resolution_status"]
            if status == "matched_existing":
                actions.append(
                    {
                        "action": "attach_evidence_to_existing_item",
                        "local_id": local_id,
                        "target_slug": resolution["matched_slug"],
                        "canonical_name": candidate["canonical_name"],
                        "item_type": candidate.get("item_type"),
                        "aliases": candidate.get("aliases", []),
                        "external_ids": candidate.get("external_ids", {}),
                    }
                )
            elif status == "new_candidate":
                actions.append(
                    {
                        "action": "manual_candidate_review_required",
                        "local_id": local_id,
                        "proposed_slug": resolution["proposed_slug"],
                        "canonical_name": candidate["canonical_name"],
                        "item_type": candidate.get("item_type"),
                        "aliases": candidate.get("aliases", []),
                        "external_ids": candidate.get("external_ids", {}),
                    }
                )
            else:
                actions.append(
                    {
                        "action": "manual_resolution_required",
                        "local_id": local_id,
                        "candidate_matches": resolution["candidate_matches"],
                    }
                )
        return actions

    @staticmethod
    def _build_claim_actions(
        claims: List[Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
        candidate_key_to_local_id: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        actions = []
        for claim in claims:
            subject_targets = []
            unresolved_subject_candidates = []
            for subject_key in claim.get("subject_candidate_keys", []):
                local_id = candidate_key_to_local_id.get(subject_key)
                resolution = resolutions.get(local_id) if local_id else None
                if not resolution:
                    continue
                if resolution["resolution_status"] == "matched_existing":
                    subject_targets.append(
                        {
                            "target_kind": "existing_item",
                            "target_slug": resolution["matched_slug"],
                        }
                    )
                elif resolution["resolution_status"] == "new_candidate":
                    unresolved_subject_candidates.append(
                        {
                            "target_kind": "item_candidate",
                            "proposed_slug": resolution["proposed_slug"],
                            "local_id": local_id,
                        }
                    )
            actions.append(
                {
                    "action": "insert_extracted_claim",
                    "claim_local_id": claim["claim_local_id"],
                    "claim_type": claim["claim_type"],
                    "claim_text_normalized": claim["claim_text_normalized"],
                    "polarity": claim["polarity"],
                    "subject_targets": subject_targets,
                    "unresolved_subject_candidates": unresolved_subject_candidates,
                    "context": claim.get("context"),
                    "metrics": claim.get("metrics", []),
                    "citation_role_suggestion": claim.get("citation_role_suggestion"),
                    "source_locator": claim.get("source_locator"),
                    "unresolved_ambiguities": claim.get("unresolved_ambiguities", []),
                }
            )
        return actions
