import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from tool_db_backend.config import Settings
from tool_db_backend.entity_resolution import EntityResolver


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _strip_inline_markup(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "")


def _normalize_summary_text(value: Optional[str]) -> str:
    return " ".join(_strip_inline_markup(value or "").split()).strip()


def _summary_is_low_information(summary: Optional[str], canonical_name: Optional[str] = None) -> bool:
    cleaned = _normalize_summary_text(summary)
    if not cleaned:
        return True
    normalized_summary = re.sub(r"[^a-z0-9]+", " ", cleaned.casefold()).strip()
    if not normalized_summary:
        return True
    normalized_name = re.sub(r"[^a-z0-9]+", " ", (canonical_name or "").casefold()).strip()
    summary_tokens = normalized_summary.split()
    if normalized_name:
        normalized_variants = {
            normalized_name,
            f"the {normalized_name}",
            f"a {normalized_name}",
            f"an {normalized_name}",
        }
        if normalized_summary in normalized_variants:
            return True
        name_tokens = set(normalized_name.split())
        has_action_verb = any(
            token in {
                "is",
                "are",
                "was",
                "were",
                "enables",
                "enable",
                "allows",
                "allow",
                "binds",
                "bind",
                "controls",
                "control",
                "provides",
                "provide",
                "requires",
                "require",
                "serves",
                "serve",
                "acts",
                "act",
                "uses",
                "use",
                "forms",
                "form",
                "works",
                "work",
                "derived",
            }
            for token in summary_tokens
        )
        if len(summary_tokens) <= len(name_tokens) + 2 and not has_action_verb:
            non_article_tokens = {token for token in summary_tokens if token not in {"the", "a", "an"}}
            if non_article_tokens and non_article_tokens.issubset(name_tokens):
                return True
        if normalized_summary.endswith(normalized_name) and len(summary_tokens) <= len(name_tokens) + 3 and not has_action_verb:
            return True
    return False


class LoadPlanBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.resolver = EntityResolver(settings)
        self._controlled_vocabularies = self._load_controlled_vocabularies()

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
        candidate_key_to_local_ids = self._map_candidate_keys_to_local_ids(candidates)
        auto_promotions = self._build_auto_promotions(
            payload,
            candidates,
            resolutions,
            candidate_key_to_local_ids,
        )
        actions = self._build_item_actions(candidates, resolutions, auto_promotions)
        claim_actions = self._build_claim_actions(
            payload.get("claims", []),
            resolutions,
            candidate_key_to_local_ids,
            auto_promotions,
        )
        validation_actions = self._build_validation_actions(
            payload.get("validation_observations", []),
            resolutions,
            candidate_key_to_local_ids,
            auto_promotions,
        )
        replication_actions = self._build_replication_actions(
            payload.get("replication_signals", {}),
            candidates,
            resolutions,
            auto_promotions,
        )
        workflow_actions = self._build_workflow_actions(
            workflow_candidates,
            workflow_resolutions,
            payload.get("workflow_observations", []),
            payload.get("workflow_stage_observations", []),
            payload.get("workflow_step_observations", []),
            resolutions,
            candidate_key_to_local_ids,
            auto_promotions,
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
    def _map_candidate_keys_to_local_ids(candidates: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {}
        for local_id, candidate in candidates.items():
            candidate_key = candidate.get("candidate_key")
            if not candidate_key:
                continue
            mapping.setdefault(candidate_key, []).append(local_id)
        return mapping

    def _build_item_actions(
        self,
        candidates: Dict[str, Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
        auto_promotions: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        actions = []
        for local_id, candidate in candidates.items():
            resolution = resolutions[local_id]
            status = resolution["resolution_status"]
            if status == "matched_existing":
                promotion = auto_promotions.get(local_id, {})
                actions.append(
                    {
                        "action": "attach_evidence_to_existing_item",
                        "local_id": local_id,
                        "target_slug": resolution["matched_slug"],
                        "canonical_name": candidate["canonical_name"],
                        "item_type": promotion.get("item_type") or candidate.get("item_type"),
                        "aliases": candidate.get("aliases", []),
                        "external_ids": candidate.get("external_ids", {}),
                        "summary": promotion.get("summary"),
                        "mechanisms": promotion.get("mechanisms", []),
                        "techniques": promotion.get("techniques", []),
                        "target_processes": promotion.get("target_processes", []),
                        "primary_input_modality": promotion.get("primary_input_modality"),
                        "primary_output_modality": promotion.get("primary_output_modality"),
                        "item_facets": promotion.get("item_facets", []),
                        "classification_notes": promotion.get("classification_notes", []),
                    }
                )
            elif status == "new_candidate":
                if local_id in auto_promotions:
                    promotion = auto_promotions[local_id]
                    actions.append(
                        {
                            "action": "create_normalized_item",
                            "local_id": local_id,
                            "proposed_slug": resolution["proposed_slug"],
                            "canonical_name": candidate["canonical_name"],
                            "item_type": promotion.get("item_type") or candidate.get("item_type"),
                            "aliases": candidate.get("aliases", []),
                            "external_ids": candidate.get("external_ids", {}),
                            "summary": promotion.get("summary"),
                            "mechanisms": promotion.get("mechanisms", []),
                            "techniques": promotion.get("techniques", []),
                            "target_processes": promotion.get("target_processes", []),
                            "primary_input_modality": promotion.get("primary_input_modality"),
                            "primary_output_modality": promotion.get("primary_output_modality"),
                            "item_facets": promotion.get("item_facets", []),
                            "classification_notes": promotion.get("classification_notes", []),
                        }
                    )
                else:
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

    def _build_claim_actions(
        self,
        claims: List[Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
        candidate_key_to_local_ids: Dict[str, List[str]],
        auto_promotions: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        actions = []
        for claim in claims:
            subject_targets = []
            unresolved_subject_candidates = []
            seen_targets = set()
            for subject_key in claim.get("subject_candidate_keys", []):
                for local_id in candidate_key_to_local_ids.get(subject_key, []):
                    resolution = resolutions.get(local_id)
                    if not resolution:
                        continue
                    if resolution["resolution_status"] == "matched_existing":
                        key = ("existing_item", resolution["matched_slug"])
                        if key in seen_targets:
                            continue
                        subject_targets.append(
                            {
                                "target_kind": "existing_item",
                                "target_slug": resolution["matched_slug"],
                            }
                        )
                        seen_targets.add(key)
                    elif resolution["resolution_status"] == "new_candidate":
                        if local_id in auto_promotions:
                            key = ("new_item", resolution["proposed_slug"])
                            if key in seen_targets:
                                continue
                            subject_targets.append(
                                {
                                    "target_kind": "new_item",
                                    "proposed_slug": resolution["proposed_slug"],
                                }
                            )
                            seen_targets.add(key)
                        else:
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

    def _build_validation_actions(
        self,
        validation_observations: List[Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
        candidate_key_to_local_ids: Dict[str, List[str]],
        auto_promotions: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        actions = []
        for observation in validation_observations:
            candidate_key = observation.get("item_candidate_key")
            subject_targets = []
            unresolved_subject_candidates = []
            seen_targets = set()

            for local_id in candidate_key_to_local_ids.get(candidate_key, []) if candidate_key else []:
                resolution = resolutions.get(local_id)
                if not resolution:
                    continue
                if resolution["resolution_status"] == "matched_existing":
                    key = ("existing_item", resolution["matched_slug"])
                    if key in seen_targets:
                        continue
                    subject_targets.append(
                        {
                            "target_kind": "existing_item",
                            "target_slug": resolution["matched_slug"],
                        }
                    )
                    seen_targets.add(key)
                elif resolution["resolution_status"] == "new_candidate":
                    if local_id in auto_promotions:
                        key = ("new_item", resolution["proposed_slug"])
                        if key in seen_targets:
                            continue
                        subject_targets.append(
                            {
                                "target_kind": "new_item",
                                "proposed_slug": resolution["proposed_slug"],
                            }
                        )
                        seen_targets.add(key)
                    else:
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

    def _build_replication_actions(
        self,
        replication_signals: Dict[str, Any],
        candidates: Dict[str, Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
        auto_promotions: Dict[str, Dict[str, Any]],
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
            if not resolution:
                continue
            if resolution["resolution_status"] == "matched_existing":
                target_slug = resolution["matched_slug"]
            elif resolution["resolution_status"] == "new_candidate" and local_id in auto_promotions:
                target_slug = resolution["proposed_slug"]
            else:
                continue
            actions.append(
                {
                    "action": "attach_replication_signal_citation",
                    "local_id": local_id,
                    "target_slug": target_slug,
                    "canonical_name": candidate.get("canonical_name"),
                    "citation_roles": citation_roles,
                    "replication_signals": replication_signals,
                }
            )
        return actions

    def _build_auto_promotions(
        self,
        payload: Dict[str, Any],
        candidates: Dict[str, Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
        candidate_key_to_local_ids: Dict[str, List[str]],
    ) -> Dict[str, Dict[str, Any]]:
        recommended_keys = set(payload.get("recommended_seed_item_keys", []))
        duplicate_slugs = self._duplicate_new_candidate_slugs(resolutions)
        claims_by_local_id = self._group_claims_by_candidate(payload.get("claims", []), candidate_key_to_local_ids)
        validations_by_local_id = self._group_validations_by_candidate(
            payload.get("validation_observations", []),
            candidate_key_to_local_ids,
        )
        promotions: Dict[str, Dict[str, Any]] = {}

        for local_id, candidate in candidates.items():
            resolution = resolutions.get(local_id)
            if not resolution:
                continue
            resolution_status = resolution.get("resolution_status")
            if resolution_status not in {"new_candidate", "matched_existing"}:
                continue
            if resolution_status == "new_candidate":
                proposed_slug = resolution.get("proposed_slug")
                if not proposed_slug or proposed_slug in duplicate_slugs:
                    continue
            combined_text = self._collect_candidate_text(candidate, claims_by_local_id.get(local_id, []), validations_by_local_id.get(local_id, []))
            item_type, _ = self._derive_item_type(candidate, combined_text)
            if item_type not in set(self._controlled_vocabularies.get("item_types", [])):
                continue

            related_claims = claims_by_local_id.get(local_id, [])
            related_validations = validations_by_local_id.get(local_id, [])
            is_recommended = candidate["candidate_key"] in recommended_keys
            if not self._should_auto_promote_candidate(
                candidate=candidate,
                related_claims=related_claims,
                related_validations=related_validations,
                is_recommended=is_recommended,
            ):
                continue

            promotions[local_id] = self._derive_item_metadata(candidate, related_claims, related_validations)

        return promotions

    def _should_auto_promote_candidate(
        self,
        *,
        candidate: Dict[str, Any],
        related_claims: List[Dict[str, Any]],
        related_validations: List[Dict[str, Any]],
        is_recommended: bool,
    ) -> bool:
        if self._looks_like_generic_class(candidate):
            return False
        if is_recommended:
            return True
        return bool(related_claims or related_validations)

    @staticmethod
    def _duplicate_new_candidate_slugs(resolutions: Dict[str, Dict[str, Any]]) -> Set[str]:
        counts: Dict[str, int] = {}
        for resolution in resolutions.values():
            if resolution.get("resolution_status") != "new_candidate":
                continue
            proposed_slug = resolution.get("proposed_slug")
            if not proposed_slug:
                continue
            counts[proposed_slug] = counts.get(proposed_slug, 0) + 1
        return {slug for slug, count in counts.items() if count > 1}

    @staticmethod
    def _group_claims_by_candidate(
        claims: List[Dict[str, Any]],
        candidate_key_to_local_ids: Dict[str, List[str]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for claim in claims:
            for subject_key in claim.get("subject_candidate_keys", []):
                for local_id in candidate_key_to_local_ids.get(subject_key, []):
                    grouped.setdefault(local_id, []).append(claim)
        return grouped

    @staticmethod
    def _group_validations_by_candidate(
        validations: List[Dict[str, Any]],
        candidate_key_to_local_ids: Dict[str, List[str]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for observation in validations:
            candidate_key = observation.get("item_candidate_key")
            for local_id in candidate_key_to_local_ids.get(candidate_key, []) if candidate_key else []:
                grouped.setdefault(local_id, []).append(observation)
        return grouped

    def _derive_item_metadata(
        self,
        candidate: Dict[str, Any],
        related_claims: List[Dict[str, Any]],
        related_validations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        combined_text = self._collect_candidate_text(candidate, related_claims, related_validations)
        summary = self._derive_summary(candidate, related_claims)
        item_type, classification_notes = self._derive_item_type(candidate, combined_text)
        normalized_candidate = {**candidate, "item_type": item_type}
        target_processes = self._derive_target_processes(normalized_candidate, combined_text)
        primary_output_modality = self._derive_primary_output_modality(target_processes)
        return {
            "summary": summary,
            "item_type": item_type,
            "mechanisms": self._derive_mechanisms(combined_text),
            "techniques": self._derive_techniques(normalized_candidate, combined_text),
            "target_processes": target_processes,
            "primary_input_modality": self._derive_primary_input_modality(combined_text),
            "primary_output_modality": primary_output_modality,
            "item_facets": self._derive_item_facets(normalized_candidate, combined_text, related_validations),
            "classification_notes": classification_notes,
        }

    @staticmethod
    def _collect_candidate_text(
        candidate: Dict[str, Any],
        related_claims: List[Dict[str, Any]],
        related_validations: List[Dict[str, Any]],
    ) -> str:
        parts = [candidate.get("canonical_name"), candidate.get("evidence_text")]
        for claim in related_claims:
            parts.append(claim.get("claim_text_normalized"))
            locator = claim.get("source_locator") or {}
            parts.append(locator.get("quoted_text"))
        for observation in related_validations:
            parts.append(observation.get("notes"))
            locator = observation.get("source_locator") or {}
            parts.append(locator.get("quoted_text"))
        return " ".join(part for part in parts if part).casefold()

    @staticmethod
    def _derive_summary(candidate: Dict[str, Any], related_claims: List[Dict[str, Any]]) -> Optional[str]:
        canonical_name = str(candidate.get("canonical_name") or "").strip()
        evidence_text = _normalize_summary_text(candidate.get("evidence_text"))
        if evidence_text and not _summary_is_low_information(evidence_text, canonical_name):
            return evidence_text
        freeform_explainers = candidate.get("freeform_explainers") or {}
        if isinstance(freeform_explainers, dict):
            for key in ("what_it_does", "problem_it_solves", "resources_required"):
                value = _normalize_summary_text(freeform_explainers.get(key))
                if value and not _summary_is_low_information(value, canonical_name):
                    return value
        for key in ("useful_for", "problem_solved"):
            values = candidate.get(key) or []
            if values:
                cleaned_values = [str(value).strip() for value in values if str(value).strip()]
                if cleaned_values:
                    return "; ".join(cleaned_values)
        preferred_claim_types = (
            "application_result",
            "mechanism_summary",
            "engineering_result",
            "application_potential",
        )
        for claim_type in preferred_claim_types:
            for claim in related_claims:
                if claim.get("claim_type") != claim_type:
                    continue
                claim_text = _normalize_summary_text(claim.get("claim_text_normalized"))
                if claim_text and not _summary_is_low_information(claim_text, canonical_name):
                    return claim_text
        for claim in related_claims:
            claim_text = _normalize_summary_text(claim.get("claim_text_normalized"))
            if claim_text:
                return claim_text
        if evidence_text:
            return evidence_text
        return None

    def _derive_mechanisms(self, combined_text: str) -> List[str]:
        signals = {
            "heterodimerization": ("heterodimer", "dimer", "binding partner", "bind sspb"),
            "oligomerization": ("oligomer", "multimer"),
            "conformational_uncaging": ("conformational", "allosteric", "undock", "sterically blocked", "uncag"),
            "membrane_recruitment": ("membrane recruitment", "membrane-localized", "subcellular localization"),
            "photocleavage": ("photocleavage", "cleav"),
            "dna_binding": ("dna binding", "bind dna"),
            "rna_binding": ("rna binding", "bind rna"),
            "degradation": ("degradation", "degrade", "proteolysis"),
            "translation_control": ("translation", "translational"),
        }
        return self._match_vocab_signals(combined_text, signals, "mechanism_families")

    def _derive_techniques(self, candidate: Dict[str, Any], combined_text: str) -> List[str]:
        signals = {
            "computational_design": ("computational design", "protein design", "in silico", "design"),
            "selection_enrichment": ("selection", "enrichment", "phage display", "screen"),
            "directed_evolution": ("directed evolution", "evolution"),
            "sequence_verification": ("sequence verification", "sequencing"),
            "functional_assay": ("assay", "screen"),
            "structural_characterization": ("crystal structure", "structural", "x-ray", "cryo-em"),
        }
        labels = self._match_vocab_signals(combined_text, signals, "technique_families")
        item_type = candidate.get("item_type")
        if item_type == "computation_method" and "computational_design" not in labels:
            labels.append("computational_design")
        if item_type == "assay_method" and "functional_assay" not in labels:
            labels.append("functional_assay")
        return self._filter_to_vocab(labels, "technique_families")

    def _derive_target_processes(self, candidate: Dict[str, Any], combined_text: str) -> List[str]:
        signals = {
            "transcription": ("transcription", "transcriptional"),
            "translation": ("translation", "translational"),
            "localization": ("localization", "recruitment", "translocation"),
            "degradation": ("degradation", "degrade", "proteolysis"),
            "signaling": ("signaling", "gtpase", "kinase"),
            "recombination": ("recombination", "recombinase", "cre", "lox"),
            "editing": ("editing", "editase", "crispr"),
            "selection": ("selection", "screen", "enrichment"),
            "manufacturing": ("manufacturing",),
            "diagnostic": ("diagnostic",),
        }
        labels = self._match_vocab_signals(combined_text, signals, "target_processes")
        if candidate.get("item_type") == "assay_method" and "selection" not in labels and "screen" in combined_text:
            labels.append("selection")
        return self._filter_to_vocab(labels, "target_processes")

    @staticmethod
    def _derive_primary_input_modality(combined_text: str) -> Optional[str]:
        if any(term in combined_text for term in (" blue light", " light", "photo", "optogen")):
            return "light"
        if any(term in combined_text for term in ("chemical", "ligand", "drug")):
            return "chemical"
        if "thermal" in combined_text:
            return "thermal"
        if "magnetic" in combined_text:
            return "magnetic"
        if "electrical" in combined_text:
            return "electrical"
        return None

    def _derive_primary_output_modality(self, target_processes: List[str]) -> Optional[str]:
        allowed_modalities = set(self._controlled_vocabularies.get("modalities", []))
        for target_process in target_processes:
            if target_process in allowed_modalities:
                return target_process
        return None

    def _derive_item_type(self, candidate: Dict[str, Any], combined_text: str) -> tuple[Optional[str], List[str]]:
        original = candidate.get("item_type")
        notes: List[str] = []
        plain_name = _strip_inline_markup(str(candidate.get("canonical_name") or "")).casefold()
        if original == "construct_pattern":
            if any(term in combined_text for term in ("binding partner", "heterodimer", "recruitment", "two-component")):
                notes.append("Remapped construct_pattern to multi_component_switch from interaction/split cues.")
                return "multi_component_switch", notes
            if any(term in combined_text for term in ("lov2", "photoswitch", "photosensor", "photoreceptor", "flavin-containing")) and not any(
                term in combined_text for term in ("binding partner", "heterodimer", "recruitment", "two-component")
            ):
                notes.append("Remapped construct_pattern to protein_domain from LOV/photoswitch cues.")
                return "protein_domain", notes
            if any(term in plain_name for term in ("lov2", "photoswitch", "photosensor")):
                notes.append("Remapped construct_pattern to protein_domain from domain/photosensor cues.")
                return "protein_domain", notes
        if original == "engineering_method":
            if self._looks_like_delivery_architecture(plain_name, combined_text):
                notes.append("Remapped engineering_method to delivery_harness from delivery/package/vector cues.")
                return "delivery_harness", notes
            if self._looks_like_architecture_candidate(plain_name, combined_text):
                if self._looks_like_switch_architecture(plain_name, combined_text):
                    notes.append("Remapped engineering_method to multi_component_switch from engineered system/switch cues.")
                    return "multi_component_switch", notes
                notes.append("Remapped engineering_method to construct_pattern from engineered system/circuit/module cues.")
                return "construct_pattern", notes
        if original:
            notes.append(f"Retained extracted item_type: {original}.")
        return original, notes

    @staticmethod
    def _looks_like_delivery_architecture(plain_name: str, combined_text: str) -> bool:
        delivery_heads = (
            "delivery",
            "packaging",
            "transduction",
            "capsid",
            "vector",
            "vectors",
            "viral vector",
            "vehicle",
            "vehicles",
            "particle",
            "particles",
            "electroporation",
        )
        carrier_terms = (
            "aav",
            "adeno-associated virus",
            "lnp",
            "lentivirus",
            "adenovirus",
            "viral",
        )
        method_heads = (
            "method",
            "methods",
            "protocol",
            "approach",
            "assay",
            "analysis",
            "optimization",
        )
        has_delivery_head = any(term in plain_name for term in delivery_heads)
        has_carrier = any(term in plain_name for term in carrier_terms)
        mentions_delivery_context = any(term in combined_text for term in delivery_heads)
        has_method_head = any(term in plain_name for term in method_heads)
        if has_method_head:
            return False
        return has_delivery_head or (has_carrier and mentions_delivery_context)

    @staticmethod
    def _looks_like_architecture_candidate(plain_name: str, combined_text: str) -> bool:
        architecture_heads = ("system", "circuit", "construct", "module", "platform")
        method_heads = (
            "method",
            "methods",
            "methodology",
            "approach",
            "approaches",
            "protocol",
            "workflow",
            "algorithm",
            "framework",
            "analysis",
            "optimization",
            "assay",
            "screening",
        )
        has_architecture_head = any(
            plain_name.endswith(f" {head}") or f" {head} " in f" {plain_name} "
            for head in architecture_heads
        )
        has_method_head = any(
            plain_name.endswith(f" {head}") or f" {head} " in f" {plain_name} "
            for head in method_heads
        )
        if not has_architecture_head or has_method_head:
            return False
        return any(
            cue in combined_text
            for cue in (
                "engineered",
                "synthetic",
                "optogenetic",
                "light-inducible",
                "light inducible",
                "genetic rewiring",
                "transgene expression",
                "control of gene expression",
                "gene expression system",
            )
        ) or has_architecture_head

    @staticmethod
    def _looks_like_switch_architecture(plain_name: str, combined_text: str) -> bool:
        return any(
            cue in plain_name or cue in combined_text
            for cue in (
                "switch",
                "inducible",
                "two-component",
                "two component",
                "binding partner",
                "heterodimer",
                "recruitment",
                "split ",
                "transgene expression system",
                "signaling circuit",
            )
        )

    def _derive_item_facets(
        self,
        candidate: Dict[str, Any],
        combined_text: str,
        related_validations: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        facets: List[Dict[str, str]] = []

        role = self._derive_operating_role(candidate, combined_text)
        if role:
            facets.append({"facet_name": "operating_role", "facet_value": role})

        for architecture in self._derive_switch_architecture_facets(candidate, combined_text):
            facets.append({"facet_name": "switch_architecture", "facet_value": architecture})

        encoding_mode = self._derive_encoding_mode_facet(candidate, combined_text)
        if encoding_mode:
            facets.append({"facet_name": "encoding_mode", "facet_value": encoding_mode})

        cofactor_dependency = self._derive_cofactor_dependency_facet(combined_text)
        if cofactor_dependency:
            facets.append({"facet_name": "cofactor_dependency", "facet_value": cofactor_dependency})

        if candidate.get("item_type") == "multi_component_switch":
            facets.append(
                {
                    "facet_name": "implementation_constraint",
                    "facet_value": "multi_component_delivery_burden",
                }
            )
        if "aav" in combined_text or "payload" in combined_text or "packaging" in combined_text:
            facets.append(
                {
                    "facet_name": "implementation_constraint",
                    "facet_value": "payload_burden",
                }
            )
        if self._derive_primary_input_modality(combined_text) == "light":
            facets.append(
                {
                    "facet_name": "implementation_constraint",
                    "facet_value": "spectral_hardware_requirement",
                }
            )
        if len({obs.get("biological_system_level") for obs in related_validations if obs.get("biological_system_level")}) <= 1:
            facets.append(
                {
                    "facet_name": "implementation_constraint",
                    "facet_value": "context_specific_validation",
                }
            )

        merged = []
        seen = set()
        for facet in facets:
            key = (facet["facet_name"], facet["facet_value"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(facet)
        for name, value in (candidate.get("facet_hints") or {}).items():
            if (name, value) not in seen:
                merged.append({"facet_name": str(name), "facet_value": str(value)})
                seen.add((name, value))
        return merged

    @staticmethod
    def _derive_operating_role(candidate: Dict[str, Any], combined_text: str) -> Optional[str]:
        item_type = candidate.get("item_type")
        if item_type == "delivery_harness":
            return "delivery"
        if item_type in {"engineering_method", "computation_method"}:
            return "builder"
        if item_type == "assay_method" or any(term in combined_text for term in ("sensor", "readout", "diagnostic", "reporter")):
            return "sensor"
        if any(term in combined_text for term in ("transcription", "translation", "signaling", "recombination", "editing")):
            return "regulator"
        if item_type in {"protein_domain", "multi_component_switch", "construct_pattern"}:
            return "actuator"
        return None

    @staticmethod
    def _derive_switch_architecture_facets(candidate: Dict[str, Any], combined_text: str) -> List[str]:
        facets = []
        plain_name = _strip_inline_markup(str(candidate.get("canonical_name") or "")).casefold()
        if candidate.get("item_type") == "multi_component_switch" or ("/" in plain_name) or any(
            term in combined_text for term in ("binding partner", "heterodimer", "two-component", "multi-component")
        ):
            facets.append("multi_component")
        if any(term in combined_text for term in ("single-chain", "single chain", "single flavin-containing")):
            facets.append("single_chain")
        if "split " in combined_text:
            facets.append("split")
        if any(term in combined_text for term in ("recruitment", "heterodimer")):
            facets.append("recruitment")
        if any(term in combined_text for term in ("uncag", "allosteric", "undock")):
            facets.append("uncaging")
        if "photocleav" in combined_text:
            facets.append("cleavage")
        return facets

    @staticmethod
    def _derive_encoding_mode_facet(candidate: Dict[str, Any], combined_text: str) -> Optional[str]:
        if any(term in combined_text for term in ("exogenous ligand", "externally supplied", "small molecule addition")):
            return "hybrid"
        if candidate.get("item_type") in {"protein_domain", "multi_component_switch", "rna_element", "construct_pattern"}:
            return "genetically_encoded"
        if candidate.get("item_type") == "delivery_harness":
            return "externally_supplied"
        return None

    @staticmethod
    def _derive_cofactor_dependency_facet(combined_text: str) -> Optional[str]:
        if any(term in combined_text for term in ("without exogenous", "no exogenous chromophore", "endogenous flavin")):
            return "compatible_with_endogenous_cofactor"
        if any(
            term in combined_text
            for term in ("5-deazafmn", "phycocyanobilin", "biliverdin", "retinal", "exogenous cofactor", "exogenous chromophore")
        ):
            return "requires_exogenous_cofactor"
        return "cofactor_requirement_unknown"

    @staticmethod
    def _looks_like_generic_class(candidate: Dict[str, Any]) -> bool:
        canonical_name = str(candidate.get("canonical_name") or "").strip().casefold()
        aliases = [str(alias).strip() for alias in candidate.get("aliases", []) if str(alias).strip()]
        external_ids = candidate.get("external_ids") or {}
        tokens = [token for token in re.split(r"[^a-z0-9]+", canonical_name) if token]
        if not tokens:
            return True
        if canonical_name in {"optogenetics", "synthetic biology", "protein engineering"}:
            return True
        generic_plural_heads = {
            "tools",
            "proteins",
            "domains",
            "methods",
            "techniques",
            "systems",
            "applications",
            "approaches",
            "constructs",
            "switches",
        }
        if tokens[-1] in generic_plural_heads:
            return True
        if not aliases and not external_ids and len(tokens) <= 2 and tokens[-1] in {"tool", "protein", "domain"}:
            return True
        return False

    def _match_vocab_signals(
        self,
        combined_text: str,
        signals: Dict[str, tuple[str, ...]],
        vocab_key: str,
    ) -> List[str]:
        matches = []
        for label, terms in signals.items():
            if any(term in combined_text for term in terms):
                matches.append(label)
        return self._filter_to_vocab(matches, vocab_key)

    def _filter_to_vocab(self, values: List[str], vocab_key: str) -> List[str]:
        allowed = set(self._controlled_vocabularies.get(vocab_key, []))
        result = []
        seen = set()
        for value in values:
            if value not in allowed or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    def _load_controlled_vocabularies(self) -> Dict[str, Any]:
        vocab_path = self.settings.schema_root / "canonical" / "controlled_vocabularies.v1.json"
        try:
            return json.loads(vocab_path.read_text())
        except Exception:
            return {}

    def _build_workflow_actions(
        self,
        candidates: Dict[str, Dict[str, Any]],
        resolutions: Dict[str, Dict[str, Any]],
        workflow_observations: List[Dict[str, Any]],
        workflow_stage_observations: List[Dict[str, Any]],
        workflow_step_observations: List[Dict[str, Any]],
        item_resolutions: Dict[str, Dict[str, Any]],
        item_candidate_key_to_local_ids: Dict[str, List[str]],
        auto_promotions: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        grouped_observations: Dict[str, List[Dict[str, Any]]] = {}
        grouped_stages: Dict[str, List[Dict[str, Any]]] = {}
        grouped_steps: Dict[str, List[Dict[str, Any]]] = {}
        orphan_observations: List[Dict[str, Any]] = []
        orphan_stages: List[Dict[str, Any]] = []
        orphan_steps: List[Dict[str, Any]] = []

        for observation in workflow_observations:
            workflow_candidate_key = observation.get("workflow_candidate_key")
            if not workflow_candidate_key:
                orphan_observations.append(observation)
                continue
            grouped_observations.setdefault(workflow_candidate_key, []).append(observation)

        for observation in workflow_stage_observations:
            workflow_candidate_key = observation.get("workflow_candidate_key")
            if not workflow_candidate_key:
                orphan_stages.append(observation)
                continue
            grouped_stages.setdefault(workflow_candidate_key, []).append(observation)

        for observation in workflow_step_observations:
            workflow_candidate_key = observation.get("workflow_candidate_key")
            if not workflow_candidate_key:
                orphan_steps.append(observation)
                continue
            grouped_steps.setdefault(workflow_candidate_key, []).append(observation)

        actions = []
        for local_id, candidate in candidates.items():
            resolution = resolutions[local_id]
            candidate_key = candidate["candidate_key"]
            observations = grouped_observations.get(candidate_key, [])
            stages = sorted(
                grouped_stages.get(candidate_key, []),
                key=lambda stage: (stage.get("stage_order", 999999), stage.get("local_id", "")),
            )
            steps = sorted(
                grouped_steps.get(candidate_key, []),
                key=lambda step: (step.get("step_order", 999999), step.get("local_id", "")),
            )
            status = resolution["resolution_status"]
            workflow_mechanisms = self._filter_to_vocab(
                self._collect_workflow_tags(observations, steps, "target_mechanisms"),
                "mechanism_families",
            )
            workflow_techniques = self._filter_to_vocab(
                self._collect_workflow_tags(observations, steps, "target_techniques"),
                "technique_families",
            )
            design_goals = self._build_workflow_design_goals(observations, steps)
            item_roles = self._build_workflow_item_roles(
                steps,
                item_resolutions,
                item_candidate_key_to_local_ids,
                auto_promotions,
            )

            if status == "matched_existing":
                actions.append(
                    {
                        "action": "upsert_workflow_for_existing_workflow",
                        "local_id": local_id,
                        "target_slug": resolution["matched_slug"],
                        "canonical_name": candidate["canonical_name"],
                        "workflow_observations": observations,
                        "stages": stages,
                        "steps": steps,
                        "workflow_mechanisms": workflow_mechanisms,
                        "workflow_techniques": workflow_techniques,
                        "design_goals": design_goals,
                        "item_roles": item_roles,
                    }
                )
            elif status == "new_candidate":
                actions.append(
                    {
                        "action": "manual_workflow_candidate_review_required",
                        "local_id": local_id,
                        "proposed_slug": resolution["proposed_slug"],
                        "canonical_name": candidate["canonical_name"],
                        "workflow_observations": observations,
                        "stages": stages,
                        "steps": steps,
                        "workflow_mechanisms": workflow_mechanisms,
                        "workflow_techniques": workflow_techniques,
                        "design_goals": design_goals,
                        "item_roles": item_roles,
                    }
                )
            else:
                actions.append(
                    {
                        "action": "manual_workflow_resolution_required",
                        "local_id": local_id,
                        "candidate_matches": resolution["candidate_matches"],
                        "workflow_observations": observations,
                        "stages": stages,
                        "steps": steps,
                        "workflow_mechanisms": workflow_mechanisms,
                        "workflow_techniques": workflow_techniques,
                        "design_goals": design_goals,
                        "item_roles": item_roles,
                    }
                )

        if orphan_observations:
            actions.append(
                {
                    "action": "manual_workflow_observation_review_required",
                    "reason": "Workflow observations were extracted without a resolvable workflow candidate.",
                    "workflow_observations": orphan_observations,
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
        if orphan_steps:
            actions.append(
                {
                    "action": "manual_workflow_step_review_required",
                    "reason": "Workflow steps were extracted without a resolvable workflow candidate.",
                    "steps": sorted(
                        orphan_steps,
                        key=lambda step: (step.get("step_order", 999999), step.get("local_id", "")),
                    ),
                }
            )

        return actions

    @staticmethod
    def _collect_workflow_tags(
        workflow_observations: List[Dict[str, Any]],
        workflow_steps: List[Dict[str, Any]],
        field_name: str,
    ) -> List[str]:
        values: List[str] = []
        seen: Set[str] = set()
        for record in [*workflow_observations, *workflow_steps]:
            for value in record.get(field_name, []) or []:
                if not value or value in seen:
                    continue
                seen.add(value)
                values.append(value)
        return values

    @staticmethod
    def _build_workflow_design_goals(
        workflow_observations: List[Dict[str, Any]],
        workflow_steps: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        goals: List[Dict[str, Any]] = []
        seen: Set[tuple[str, str]] = set()
        for observation in workflow_observations:
            rationale = observation.get("why_workflow_works") or observation.get("workflow_priority_logic")
            for goal_name in observation.get("target_property_axes", []) or []:
                key = ("property_axis", goal_name)
                if key in seen:
                    continue
                seen.add(key)
                goals.append(
                    {
                        "goal_kind": "property_axis",
                        "goal_name": goal_name,
                        "rationale": rationale,
                    }
                )
        for step in workflow_steps:
            rationale = step.get("purpose") or step.get("why_this_step_now") or step.get("validation_focus")
            for goal_name in step.get("target_property_axes", []) or []:
                key = ("property_axis", goal_name)
                if key in seen:
                    continue
                seen.add(key)
                goals.append(
                    {
                        "goal_kind": "property_axis",
                        "goal_name": goal_name,
                        "rationale": rationale,
                    }
                )
        return goals

    @staticmethod
    def _build_workflow_item_roles(
        workflow_steps: List[Dict[str, Any]],
        item_resolutions: Dict[str, Dict[str, Any]],
        item_candidate_key_to_local_ids: Dict[str, List[str]],
        auto_promotions: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        roles: List[Dict[str, Any]] = []
        seen: Set[tuple[str, str, str, str]] = set()
        for step in workflow_steps:
            role_name = str(step.get("item_role") or step.get("step_type") or "referenced_item").strip()
            note = step.get("purpose") or step.get("validation_focus") or step.get("why_this_step_now")
            for candidate_key in step.get("item_candidate_keys", []) or []:
                for local_id in item_candidate_key_to_local_ids.get(candidate_key, []):
                    resolution = item_resolutions.get(local_id)
                    if not resolution:
                        continue
                    target_slug: Optional[str] = None
                    if resolution.get("resolution_status") == "matched_existing":
                        target_slug = resolution.get("matched_slug")
                    elif resolution.get("resolution_status") == "new_candidate" and local_id in auto_promotions:
                        target_slug = resolution.get("proposed_slug")
                    if not target_slug:
                        continue
                    key = (
                        target_slug,
                        role_name,
                        str(step.get("stage_name") or ""),
                        str(step.get("step_name") or ""),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    roles.append(
                        {
                            "target_slug": target_slug,
                            "role_name": role_name,
                            "stage_name": step.get("stage_name"),
                            "step_name": step.get("step_name"),
                            "notes": note,
                        }
                    )
        return roles
