import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tool_db_backend.candidate_filtering import assess_toolkit_item_candidate, load_controlled_vocabularies
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


def _compact_dict(values: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


_VALIDATION_CONTEXT_FIELDS = (
    "biological_system_level",
    "species",
    "strain_or_model",
    "cell_type",
    "tissue",
    "delivery_mode",
    "cargo_or_effector",
)


def _compact_dict(value: Dict[str, Any]) -> Dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


class PacketNormalizer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._controlled_vocabularies = load_controlled_vocabularies(settings)

    def normalize_packet_file(self, packet_kind: str, packet_path: Path) -> Dict[str, Any]:
        payload = json.loads(packet_path.read_text())
        return self.normalize_packet(packet_kind, payload)

    def normalize_packet(self, packet_kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        validate_packet(packet_kind, payload, self.settings)

        if packet_kind == "review_extract_v1":
            return self._normalize_review_packet(payload)
        if packet_kind == "primary_paper_extract_v1":
            return self._normalize_primary_paper_packet(payload)
        if packet_kind == "database_entry_extract_v1":
            return self._normalize_database_entry_packet(payload)

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
        item_candidates, rejected_item_candidates = self._normalize_item_candidates(payload.get("entity_candidates", []))
        workflow_candidates = self._normalize_workflow_candidates(payload.get("entity_candidates", []))
        claim_index = self._normalize_claims(payload.get("claims", []), item_candidates)
        workflow_stage_observations = self._normalize_workflow_stage_observations(
            payload.get("workflow_stage_observations", []),
            workflow_candidates,
        )
        return {
            "normalized_packet_type": "review_extract_normalized_v1",
            "packet_kind": payload["packet_type"],
            "schema_version": payload.get("schema_version", "v1"),
            "normalized_at": _utc_now_iso(),
            "source_document": self._normalize_source_document(payload["source_document"]),
            "canonical_item_candidates": item_candidates,
            "canonical_workflow_candidates": workflow_candidates,
            "claims": claim_index,
            "workflow_stage_observations": workflow_stage_observations,
            "recommended_seed_item_keys": self._map_local_ids(
                payload.get("recommended_seed_item_local_ids", []),
                item_candidates,
            ),
            "rejected_item_candidates": rejected_item_candidates,
            "unresolved_ambiguities": payload.get("unresolved_ambiguities", []),
        }

    def _normalize_primary_paper_packet(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        item_candidates, rejected_item_candidates = self._normalize_item_candidates(payload.get("entity_candidates", []))
        workflow_candidates = self._normalize_workflow_candidates(payload.get("entity_candidates", []))
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
        validations.extend(self._infer_validation_observations(payload.get("claims", []), item_candidates, validations))
        workflow_stage_observations = self._normalize_workflow_stage_observations(
            payload.get("workflow_stage_observations", []),
            workflow_candidates,
        )
        return {
            "normalized_packet_type": "primary_paper_extract_normalized_v1",
            "packet_kind": payload["packet_type"],
            "schema_version": payload.get("schema_version", "v1"),
            "normalized_at": _utc_now_iso(),
            "source_document": self._normalize_source_document(payload["source_document"]),
            "canonical_item_candidates": item_candidates,
            "canonical_workflow_candidates": workflow_candidates,
            "claims": claims,
            "validation_observations": validations,
            "workflow_stage_observations": workflow_stage_observations,
            "replication_signals": self._normalize_replication_signals(payload.get("replication_signals", {})),
            "rejected_item_candidates": rejected_item_candidates,
            "unresolved_ambiguities": payload.get("unresolved_ambiguities", []),
        }

    def _normalize_database_entry_packet(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        gap_candidates = self._normalize_gap_candidates(payload.get("entity_candidates", []))
        claims = self._normalize_claims(payload.get("claims", []), gap_candidates)
        return {
            "normalized_packet_type": "database_entry_extract_normalized_v1",
            "packet_kind": payload["packet_type"],
            "schema_version": payload.get("schema_version", "v1"),
            "normalized_at": _utc_now_iso(),
            "source_document": self._normalize_source_document(payload["source_document"]),
            "database_name": payload.get("database_name"),
            "entry_url": payload.get("entry_url"),
            "gap_candidates": gap_candidates,
            "claims": claims,
            "database_fields": payload.get("database_fields", {}),
            "unresolved_ambiguities": payload.get("unresolved_ambiguities", []),
        }

    def _normalize_source_document(self, source_document: Dict[str, Any]) -> Dict[str, Any]:
        return _compact_dict(
            {
                "source_type": source_document.get("source_type"),
                "title": source_document.get("title"),
                "doi": source_document.get("doi"),
                "pmid": source_document.get("pmid"),
                "openalex_id": source_document.get("openalex_id"),
                "semantic_scholar_id": source_document.get("semantic_scholar_id"),
                "nct_id": source_document.get("nct_id"),
                "publication_year": source_document.get("publication_year"),
                "journal_or_source": source_document.get("journal_or_source"),
                "abstract_text": self._normalize_optional_text(source_document.get("abstract_text")),
                "fulltext_license_status": source_document.get("fulltext_license_status"),
                "is_retracted": source_document.get("is_retracted"),
                "retraction_metadata": source_document.get("retraction_metadata"),
                "raw_payload_ref": source_document.get("raw_payload_ref"),
            }
        )

    def _normalize_item_candidates(
        self,
        entity_candidates: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        normalized = {}
        rejected = []
        allowed_item_types = set(self._controlled_vocabularies.get("item_types", []))
        for entity in entity_candidates:
            if entity.get("candidate_type") != "toolkit_item":
                continue
            assessment = assess_toolkit_item_candidate(entity, allowed_item_types=allowed_item_types)
            if not assessment["keep"]:
                rejected.append(
                    {
                        "local_id": entity.get("local_id"),
                        "canonical_name": str(entity.get("canonical_name") or "").strip(),
                        "reason": assessment["reason"],
                    }
                )
                continue
            canonical_name = entity["canonical_name"].strip()
            slug = _slugify(canonical_name)
            aliases = _dedupe_strings(entity.get("aliases", []))
            normalized[entity["local_id"]] = {
                "candidate_key": f"item/{slug}",
                "slug": slug,
                "canonical_name": canonical_name,
                "item_type": assessment["item_type"],
                "aliases": aliases,
                "external_ids": entity.get("external_ids", {}),
                "evidence_text": entity.get("evidence_text"),
            }
        return normalized, rejected

    def _normalize_gap_candidates(self, entity_candidates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        normalized = {}
        for entity in entity_candidates:
            if entity.get("candidate_type") != "gap_item":
                continue
            canonical_name = entity["canonical_name"].strip()
            external_ids = entity.get("external_ids", {})
            external_gap_item_id = str(external_ids.get("gap_map_id") or _slugify(canonical_name))
            normalized[entity["local_id"]] = {
                "candidate_key": f"gap/{external_gap_item_id}",
                "external_gap_item_id": external_gap_item_id,
                "canonical_name": canonical_name,
                "aliases": _dedupe_strings(entity.get("aliases", [])),
                "external_ids": external_ids,
                "evidence_text": entity.get("evidence_text"),
            }
        return normalized

    def _normalize_workflow_candidates(self, entity_candidates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        normalized = {}
        for entity in entity_candidates:
            if entity.get("candidate_type") != "workflow_template":
                continue
            canonical_name = entity["canonical_name"].strip()
            slug = _slugify(canonical_name)
            aliases = _dedupe_strings(entity.get("aliases", []))
            normalized[entity["local_id"]] = {
                "candidate_key": f"workflow/{slug}",
                "slug": slug,
                "canonical_name": canonical_name,
                "aliases": aliases,
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

    def _infer_validation_observations(
        self,
        claims: List[Dict[str, Any]],
        item_candidates: Dict[str, Dict[str, Any]],
        existing_observations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        seen = {
            self._validation_observation_key(observation)
            for observation in existing_observations
            if observation.get("item_candidate_key")
        }
        inferred: List[Dict[str, Any]] = []

        for claim in claims:
            context = claim.get("context") or {}
            biological_system_level = context.get("biological_system_level")
            success_outcome = context.get("success_outcome")
            if not biological_system_level or not success_outcome:
                continue
            if not any(context.get(field) for field in _VALIDATION_CONTEXT_FIELDS) and not context.get("assay_type"):
                continue

            observation_type = self._infer_observation_type_from_claim(claim, context)
            notes_parts = [f"Inferred from claim {claim['local_id']} during normalization."]
            if claim.get("claim_text_normalized"):
                notes_parts.append(claim["claim_text_normalized"].strip())

            for subject_local_id in claim.get("subject_local_ids", []):
                mapped_key = item_candidates.get(subject_local_id, {}).get("candidate_key")
                if not mapped_key:
                    continue
                observation = _compact_dict(
                    {
                        "local_id": f"inferred-{claim['local_id']}-{subject_local_id}",
                        "item_local_id": subject_local_id,
                        "item_candidate_key": mapped_key,
                        "observation_type": observation_type,
                        "biological_system_level": biological_system_level,
                        "species": context.get("species"),
                        "strain_or_model": context.get("strain_or_model"),
                        "cell_type": context.get("cell_type"),
                        "tissue": context.get("tissue"),
                        "delivery_mode": context.get("delivery_mode"),
                        "cargo_or_effector": context.get("cargo_or_effector"),
                        "construct_name": context.get("construct_name"),
                        "assay_description": context.get("assay_type"),
                        "success_outcome": success_outcome,
                        "metrics": claim.get("metrics", []),
                        "notes": " ".join(notes_parts),
                        "source_locator": claim.get("source_locator"),
                        "derived_from_claim_local_id": claim.get("local_id"),
                    }
                )
                key = self._validation_observation_key(observation)
                if key in seen:
                    continue
                seen.add(key)
                inferred.append(observation)

        return inferred

    @staticmethod
    def _infer_observation_type_from_claim(claim: Dict[str, Any], context: Dict[str, Any]) -> str:
        claim_type = (claim.get("claim_type") or "").strip().casefold()
        biological_system_level = (context.get("biological_system_level") or "").strip().casefold()
        success_outcome = (context.get("success_outcome") or "").strip().casefold()

        if success_outcome == "failed":
            return "failed_attempt"
        if claim_type == "benchmark":
            return "benchmark"
        if claim_type.startswith("mechan") or "mechan" in claim_type:
            return "mechanistic_demo"
        if biological_system_level == "human_clinical" or "therapeutic" in claim_type:
            return "therapeutic_use"
        return "application_demo"

    @staticmethod
    def _validation_observation_key(observation: Dict[str, Any]) -> str:
        locator = observation.get("source_locator") or {}
        return "|".join(
            [
                str(observation.get("item_candidate_key") or observation.get("item_local_id") or ""),
                str(observation.get("observation_type") or ""),
                str(observation.get("biological_system_level") or ""),
                str(observation.get("species") or ""),
                str(observation.get("cell_type") or ""),
                str(observation.get("tissue") or ""),
                str(observation.get("cargo_or_effector") or ""),
                str(observation.get("success_outcome") or ""),
                str(locator.get("section_label") or ""),
                str(locator.get("quoted_text") or ""),
            ]
        )

    def _normalize_workflow_stage_observations(
        self,
        observations: List[Dict[str, Any]],
        workflow_candidates: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        normalized = []
        for observation in observations:
            workflow_local_id = observation.get("workflow_local_id")
            workflow_candidate_key = (
                workflow_candidates.get(workflow_local_id, {}).get("candidate_key")
                if workflow_local_id
                else None
            )
            normalized.append(
                {
                    **observation,
                    "workflow_candidate_key": workflow_candidate_key,
                }
            )
        return normalized

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

    @staticmethod
    def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @staticmethod
    def _normalize_replication_signals(replication_signals: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(replication_signals, dict):
            return {}
        return {
            "is_foundational_paper": bool(replication_signals.get("is_foundational_paper", False)),
            "is_independent_follow_up": bool(replication_signals.get("is_independent_follow_up", False)),
            "last_author_cluster_hint": (replication_signals.get("last_author_cluster_hint") or "").strip(),
            "institution_cluster_hint": (replication_signals.get("institution_cluster_hint") or "").strip(),
            "negative_or_mixed_follow_up": bool(replication_signals.get("negative_or_mixed_follow_up", False)),
            "practicality_penalties": _dedupe_strings(replication_signals.get("practicality_penalties", [])),
        }
