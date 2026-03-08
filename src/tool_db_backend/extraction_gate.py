from typing import Any, Dict, List


class ExtractionGate:
    def assess(self, packet_kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        source_type = (payload.get("source_document") or {}).get("source_type")
        supported_item_types = {"toolkit_item", "workflow_template"}
        entity_candidates = payload.get("entity_candidates", [])
        entity_types_by_local_id = {
            entity.get("local_id"): entity.get("candidate_type")
            for entity in entity_candidates
            if entity.get("local_id")
        }

        unsupported_types = sorted(
            {
                entity_type
                for entity_type in entity_types_by_local_id.values()
                if entity_type not in supported_item_types
            }
        )
        if packet_kind in {"primary_paper_extract_v1", "review_extract_v1"} and unsupported_types:
            issues.append(
                "Literature packet includes unsupported entity candidate types: "
                + ", ".join(unsupported_types)
                + "."
            )

        if packet_kind == "primary_paper_extract_v1":
            if source_type == "review":
                issues.append("Primary-paper packet is carrying a review source type.")
            if (
                not payload.get("entity_candidates")
                and not payload.get("claims")
                and not payload.get("validation_observations")
                and not payload.get("workflow_stage_observations")
            ):
                issues.append(
                    "Primary-paper packet is metadata-only with no extracted entities, claims, validation observations, or workflow stages."
                )

        if packet_kind == "review_extract_v1":
            if (
                not payload.get("entity_candidates")
                and not payload.get("claims")
                and not payload.get("workflow_stage_observations")
            ):
                issues.append(
                    "Review packet is metadata-only with no extracted entities, claims, or workflow stages."
                )

        if packet_kind in {"primary_paper_extract_v1", "review_extract_v1"}:
            issues.extend(self._check_claim_links(payload.get("claims", []), entity_types_by_local_id))
            issues.extend(
                self._check_validation_links(
                    payload.get("validation_observations", []),
                    entity_types_by_local_id,
                )
            )
            issues.extend(
                self._check_workflow_links(
                    payload.get("workflow_stage_observations", []),
                    entity_types_by_local_id,
                )
            )

        if packet_kind == "database_entry_extract_v1":
            if not payload.get("entity_candidates") and not payload.get("claims"):
                issues.append("Database entry packet is empty.")

        return {
            "is_ready": not issues,
            "issues": issues,
        }

    @staticmethod
    def _check_claim_links(claims: List[Dict[str, Any]], entity_types_by_local_id: Dict[str, Any]) -> List[str]:
        issues: List[str] = []
        for claim in claims:
            claim_local_id = claim.get("local_id", "<unknown>")
            for subject_local_id in claim.get("subject_local_ids", []):
                entity_type = entity_types_by_local_id.get(subject_local_id)
                if entity_type is None:
                    issues.append(
                        f"Claim {claim_local_id} references missing subject_local_id {subject_local_id}."
                    )
                elif entity_type != "toolkit_item":
                    issues.append(
                        f"Claim {claim_local_id} references subject_local_id {subject_local_id} with unsupported type {entity_type}."
                    )
        return issues

    @staticmethod
    def _check_validation_links(
        validations: List[Dict[str, Any]],
        entity_types_by_local_id: Dict[str, Any],
    ) -> List[str]:
        issues: List[str] = []
        for observation in validations:
            item_local_id = observation.get("item_local_id")
            if not item_local_id:
                continue
            entity_type = entity_types_by_local_id.get(item_local_id)
            if entity_type is None:
                issues.append(
                    f"Validation observation references missing item_local_id {item_local_id}."
                )
            elif entity_type != "toolkit_item":
                issues.append(
                    f"Validation observation references item_local_id {item_local_id} with unsupported type {entity_type}."
                )
        return issues

    @staticmethod
    def _check_workflow_links(
        workflow_stage_observations: List[Dict[str, Any]],
        entity_types_by_local_id: Dict[str, Any],
    ) -> List[str]:
        issues: List[str] = []
        for stage in workflow_stage_observations:
            workflow_local_id = stage.get("workflow_local_id")
            if not workflow_local_id:
                continue
            entity_type = entity_types_by_local_id.get(workflow_local_id)
            if entity_type is None:
                issues.append(
                    f"Workflow stage {stage.get('local_id', '<unknown>')} references missing workflow_local_id {workflow_local_id}."
                )
            elif entity_type != "workflow_template":
                issues.append(
                    f"Workflow stage {stage.get('local_id', '<unknown>')} references workflow_local_id {workflow_local_id} with unsupported type {entity_type}."
                )
        return issues
