import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from tool_db_backend.config import Settings
from tool_db_backend.schema_validation import validate_packet


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unnamed"


def _dedupe_strings(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


class PacketNormalizer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def normalize_packet_file(self, packet_kind: str, packet_path: Path) -> Dict[str, Any]:
        payload = json.loads(packet_path.read_text())
        return self.normalize_packet(packet_kind, payload)

    def normalize_packet(self, packet_kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        validate_packet(packet_kind, payload, self.settings)

        if packet_kind == "review_extract_v1":
            return self._normalize_review_packet(payload)
        if packet_kind == "primary_paper_extract_v1":
            return self._normalize_primary_paper_packet(payload)

        raise ValueError(f"Normalization not implemented for {packet_kind}")

    def write_normalized_packet(
        self,
        packet_kind: str,
        packet_path: Path,
        output_path: Path,
    ) -> Path:
        normalized = self.normalize_packet_file(packet_kind, packet_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(normalized, indent=2) + "\n")
        return output_path

    def _normalize_review_packet(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        item_candidates = self._normalize_item_candidates(payload.get("entity_candidates", []))
        claim_index = self._normalize_claims(payload.get("claims", []), item_candidates)
        return {
            "normalized_packet_type": "review_extract_normalized_v1",
            "normalized_at": _utc_now_iso(),
            "source_document": payload["source_document"],
            "canonical_item_candidates": item_candidates,
            "claims": claim_index,
            "recommended_seed_item_keys": self._map_local_ids(
                payload.get("recommended_seed_item_local_ids", []),
                item_candidates,
            ),
            "unresolved_ambiguities": payload.get("unresolved_ambiguities", []),
        }

    def _normalize_primary_paper_packet(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        item_candidates = self._normalize_item_candidates(payload.get("entity_candidates", []))
        claims = self._normalize_claims(payload.get("claims", []), item_candidates)
        validations = []
        for observation in payload.get("validation_observations", []):
            local_id = observation["item_local_id"]
            mapped_key = item_candidates.get(local_id, {}).get("candidate_key")
            validations.append(
                {
                    **observation,
                    "item_candidate_key": mapped_key,
                }
            )
        return {
            "normalized_packet_type": "primary_paper_extract_normalized_v1",
            "normalized_at": _utc_now_iso(),
            "source_document": payload["source_document"],
            "canonical_item_candidates": item_candidates,
            "claims": claims,
            "validation_observations": validations,
            "replication_signals": payload.get("replication_signals", {}),
            "unresolved_ambiguities": payload.get("unresolved_ambiguities", []),
        }

    def _normalize_item_candidates(self, entity_candidates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        normalized = {}
        for entity in entity_candidates:
            if entity.get("candidate_type") != "toolkit_item":
                continue
            canonical_name = entity["canonical_name"].strip()
            slug = _slugify(canonical_name)
            aliases = _dedupe_strings(entity.get("aliases", []))
            normalized[entity["local_id"]] = {
                "candidate_key": f"item/{slug}",
                "slug": slug,
                "canonical_name": canonical_name,
                "item_type": entity.get("item_type"),
                "aliases": aliases,
                "external_ids": entity.get("external_ids", {}),
                "evidence_text": entity.get("evidence_text"),
            }
        return normalized

    def _normalize_claims(
        self,
        claims: List[Dict[str, Any]],
        item_candidates: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        normalized_claims = []
        for claim in claims:
            normalized_claims.append(
                {
                    "claim_local_id": claim["local_id"],
                    "claim_type": claim["claim_type"].strip(),
                    "claim_text_normalized": claim["claim_text_normalized"].strip(),
                    "polarity": claim["polarity"],
                    "subject_candidate_keys": self._map_local_ids(
                        claim.get("subject_local_ids", []),
                        item_candidates,
                    ),
                    "context": claim.get("context"),
                    "metrics": claim.get("metrics", []),
                    "citation_role_suggestion": claim.get("citation_role_suggestion"),
                    "source_locator": claim.get("source_locator"),
                    "unresolved_ambiguities": claim.get("unresolved_ambiguities", []),
                }
            )
        return normalized_claims

    @staticmethod
    def _map_local_ids(
        local_ids: List[str],
        item_candidates: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        mapped = []
        for local_id in local_ids:
            candidate_key = item_candidates.get(local_id, {}).get("candidate_key")
            if candidate_key:
                mapped.append(candidate_key)
        return mapped
