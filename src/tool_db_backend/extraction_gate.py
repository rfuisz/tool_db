from typing import Any, Dict, List


class ExtractionGate:
    def assess(self, packet_kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        source_type = (payload.get("source_document") or {}).get("source_type")

        if packet_kind == "primary_paper_extract_v1":
            if source_type == "review":
                issues.append("Primary-paper packet is carrying a review source type.")
            if not payload.get("entity_candidates") and not payload.get("claims") and not payload.get("validation_observations"):
                issues.append("Primary-paper packet is metadata-only with no extracted entities, claims, or validation observations.")

        if packet_kind == "review_extract_v1":
            if not payload.get("entity_candidates") and not payload.get("claims"):
                issues.append("Review packet is metadata-only with no extracted entities or claims.")

        if packet_kind == "database_entry_extract_v1":
            if not payload.get("entity_candidates") and not payload.get("claims"):
                issues.append("Database entry packet is empty.")

        return {
            "is_ready": not issues,
            "issues": issues,
        }
