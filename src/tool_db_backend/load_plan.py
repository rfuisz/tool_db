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
        if payload.get("normalized_packet_type") == "database_entry_extract_normalized_v1":
            return self._build_database_entry_load_plan(payload)

        candidates = payload.get("canonical_item_candidates", {})
        workflow_candidates = payload.get("canonical_workflow_candidates", {})
        resolutions = self.resolver.resolve_item_candidates(candidates)
        workflow_resolutions = self.resolver.resolve_workflow_candidates(workflow_candidates)
        actions = self._build_item_actions(candidates, resolutions)
        workflow_actions = self._build_workflow_actions(
            workflow_candidates,
            workflow_resolutions,
            payload.get("workflow_stage_observations", []),
        )
        candidate_key_to_local_id = {
            candidate["candidate_key"]: local_id
            for local_id, candidate in candidates.items()
        }
        claim_actions = self._build_claim_actions(
            payload.get("claims", []),
            resolutions,
            candidate_key_to_local_id,
        )
        validation_actions = self._build_validation_actions(
            payload.get("validation_observations", []),
            resolutions,
            candidate_key_to_local_id,
        )
        replication_actions = self._build_replication_actions(
            payload.get("replication_signals", {}),
            candidates,
            resolutions,
        )

        return {
            "load_plan_type": "canonical_load_plan_v1",
            "generated_at": _utc_now_iso(),
            "packet_kind": payload.get("packet_kind"),
            "schema_version": payload.get("schema_version"),
            "source_document": payload.get("source_document", {}),
            "item_resolutions": resolutions,
            "workflow_resolutions": workflow_resolutions,
            "actions": {
                "toolkit_items": actions,
                "claims": claim_actions,
                "validation_observations": validation_actions,
                "replication": replication_actions,
                "workflows": workflow_actions,
            },
        }

    @staticmethod
    def _build_database_entry_load_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
        gap_actions = []
        for local_id, candidate in payload.get("gap_candidates", {}).items():
            related_claims = [
                claim
                for claim in payload.get("claims", [])
                if candidate["candidate_key"] in claim.get("subject_candidate_keys", [])
            ]
            gap_actions.append(
                {
                    "action": "upsert_gap_item_from_database_entry",
                    "local_id": local_id,
                    "external_gap_item_id": candidate["external_gap_item_id"],
                    "canonical_name": candidate["canonical_name"],
                    "external_ids": candidate.get("external_ids", {}),
                    "evidence_text": candidate.get("evidence_text"),
                    "database_name": payload.get("database_name"),
                    "entry_url": payload.get("entry_url"),
                    "database_fields": payload.get("database_fields", {}),
                    "claims": related_claims,
                    "unresolved_ambiguities": payload.get("unresolved_ambiguities", []),
                }
            )

        return {
            "load_plan_type": "canonical_load_plan_v1",
            "generated_at": _utc_now_iso(),
            "packet_kind": payload.get("packet_kind", "database_entry_extract_v1"),
            "schema_version": payload.get("schema_version", "v1"),
            "source_document": payload.get("source_document", {}),
            "item_resolutions": {},
            "actions": {
                "toolkit_items": [],
                "claims": [],
                "validation_observations": [],
                "replication": [],
                "gap_items": gap_actions,
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
                elif resolution["resolution_status"] == "ambiguous_existing":
                    unresolved_subject_candidates.append(
                        {
                            "target_kind": "existing_item",
                            "candidate_matches": resolution.get("candidate_matches", []),
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

    @staticmethod
    def _build_validation_actions(
        validation_observations: List[Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
        candidate_key_to_local_id: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        actions = []
        for observation in validation_observations:
            candidate_key = observation.get("item_candidate_key")
            local_id = candidate_key_to_local_id.get(candidate_key) if candidate_key else None
            resolution = resolutions.get(local_id) if local_id else None
            subject_targets = []
            unresolved_subject_candidates = []

            if resolution:
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
                elif resolution["resolution_status"] == "ambiguous_existing":
                    unresolved_subject_candidates.append(
                        {
                            "target_kind": "existing_item",
                            "candidate_matches": resolution.get("candidate_matches", []),
                            "local_id": local_id,
                        }
                    )

            actions.append(
                {
                    "action": "insert_validation_observation",
                    "observation_local_id": observation.get("local_id"),
                    "subject_targets": subject_targets,
                    "unresolved_subject_candidates": unresolved_subject_candidates,
                    "observation_type": observation.get("observation_type"),
                    "biological_system_level": observation.get("biological_system_level"),
                    "species": observation.get("species"),
                    "strain_or_model": observation.get("strain_or_model"),
                    "cell_type": observation.get("cell_type"),
                    "tissue": observation.get("tissue"),
                    "subcellular_target": observation.get("subcellular_target"),
                    "delivery_mode": observation.get("delivery_mode"),
                    "cargo_or_effector": observation.get("cargo_or_effector"),
                    "construct_name": observation.get("construct_name"),
                    "assay_description": observation.get("assay_description"),
                    "success_outcome": observation.get("success_outcome"),
                    "independent_lab_cluster_id": observation.get("independent_lab_cluster_id"),
                    "institution_cluster_id": observation.get("institution_cluster_id"),
                    "metrics": observation.get("metrics", []),
                    "notes": observation.get("notes"),
                    "source_locator": observation.get("source_locator"),
                    "derived_from_claim_local_id": observation.get("derived_from_claim_local_id"),
                }
            )
        return actions

    @staticmethod
    def _build_replication_actions(
        replication_signals: Dict[str, Any],
        candidates: Dict[str, Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not replication_signals:
            return []

        citation_roles = []
        if replication_signals.get("is_foundational_paper"):
            citation_roles.append("foundational")
        if replication_signals.get("is_independent_follow_up"):
            citation_roles.append("independent_validation")
        if replication_signals.get("negative_or_mixed_follow_up"):
            citation_roles.append("negative_result")
        if not citation_roles:
            return []

        actions = []
        for local_id, candidate in candidates.items():
            resolution = resolutions.get(local_id)
            if not resolution or resolution["resolution_status"] != "matched_existing":
                continue
            actions.append(
                {
                    "action": "attach_replication_signal_citation",
                    "local_id": local_id,
                    "target_slug": resolution["matched_slug"],
                    "canonical_name": candidate.get("canonical_name"),
                    "citation_roles": citation_roles,
                    "replication_signals": replication_signals,
                }
            )
        return actions

    @staticmethod
    def _build_workflow_actions(
        candidates: Dict[str, Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
        workflow_stage_observations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        grouped_stages: Dict[str, List[Dict[str, Any]]] = {}
        orphan_stages: List[Dict[str, Any]] = []

        for observation in workflow_stage_observations:
            workflow_candidate_key = observation.get("workflow_candidate_key")
            if not workflow_candidate_key:
                orphan_stages.append(observation)
                continue
            grouped_stages.setdefault(workflow_candidate_key, []).append(observation)

        actions = []
        for local_id, candidate in candidates.items():
            resolution = resolutions[local_id]
            candidate_key = candidate["candidate_key"]
            stages = sorted(
                grouped_stages.get(candidate_key, []),
                key=lambda stage: (stage.get("stage_order", 999999), stage.get("local_id", "")),
            )
            status = resolution["resolution_status"]

            if status == "matched_existing":
                actions.append(
                    {
                        "action": "upsert_workflow_stages_for_existing_workflow",
                        "local_id": local_id,
                        "target_slug": resolution["matched_slug"],
                        "canonical_name": candidate["canonical_name"],
                        "stages": stages,
                    }
                )
            elif status == "new_candidate":
                actions.append(
                    {
                        "action": "manual_workflow_candidate_review_required",
                        "local_id": local_id,
                        "proposed_slug": resolution["proposed_slug"],
                        "canonical_name": candidate["canonical_name"],
                        "stages": stages,
                    }
                )
            else:
                actions.append(
                    {
                        "action": "manual_workflow_resolution_required",
                        "local_id": local_id,
                        "candidate_matches": resolution["candidate_matches"],
                        "stages": stages,
                    }
                )

        if orphan_stages:
            actions.append(
                {
                    "action": "manual_workflow_stage_review_required",
                    "reason": "Workflow stages were extracted without a resolvable workflow candidate.",
                    "stages": sorted(
                        orphan_stages,
                        key=lambda stage: (stage.get("stage_order", 999999), stage.get("local_id", "")),
                    ),
                }
            )

        return actions
