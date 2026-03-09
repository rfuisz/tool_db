import json
import logging
import re
from dataclasses import dataclass
from datetime import date
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from tool_db_backend.config import Settings
from tool_db_backend.errors import LoadPlanExecutionError

logger = logging.getLogger(__name__)


def _dedupe_preserving_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
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


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 3)))


def _strip_inline_markup(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "")


@dataclass
class ExtractedItemEvidence:
    local_id: str
    source_document: Dict[str, Any]
    evidence_text: Optional[str]
    useful_for: List[str]
    problem_solved: List[str]
    strengths: List[str]
    limitations: List[str]
    implementation_constraints: List[str]
    freeform_explainers: Dict[str, str]


@dataclass
class ItemContext:
    item_id: Any
    slug: str
    canonical_name: str
    item_type: str
    summary: Optional[str]
    primary_input_modality: Optional[str]
    primary_output_modality: Optional[str]
    mechanisms: List[str]
    techniques: List[str]
    target_processes: List[str]
    synonyms: List[str]
    claims: List[Dict[str, Any]]
    validations: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    gap_links: List[Dict[str, Any]]
    extracted_evidence: List[ExtractedItemEvidence]

    @property
    def text_blob(self) -> str:
        parts: List[str] = [
            self.canonical_name,
            self.summary or "",
            " ".join(self.synonyms),
            " ".join(self.mechanisms),
            " ".join(self.techniques),
            " ".join(self.target_processes),
        ]
        for claim in self.claims:
            parts.append(claim.get("claim_text_normalized") or "")
            locator = claim.get("source_locator") or {}
            parts.append(locator.get("quoted_text") or "")
        for validation in self.validations:
            parts.append(validation.get("notes") or "")
            locator = validation.get("source_locator") or {}
            parts.append(locator.get("quoted_text") or "")
        for citation in self.citations:
            parts.append(citation.get("why_this_matters") or "")
            parts.append(citation.get("title") or "")
        for evidence in self.extracted_evidence:
            parts.append(evidence.evidence_text or "")
            parts.extend(evidence.useful_for)
            parts.extend(evidence.problem_solved)
            parts.extend(evidence.strengths)
            parts.extend(evidence.limitations)
            parts.extend(evidence.implementation_constraints)
            parts.extend(evidence.freeform_explainers.values())
        return " ".join(part for part in parts if part).casefold()


class ItemMaterializer:
    SCORE_VERSION = "v1"
    DERIVATION_VERSION = "v1"
    PROGRESS_LOG_INTERVAL = 100

    def __init__(self, settings: Settings, connection: Any = None) -> None:
        self.settings = settings
        self._connection = connection

    def refresh(self, item_slugs: Optional[Sequence[str]] = None, include_related: bool = True) -> Dict[str, Any]:
        started_at = perf_counter()
        conn, should_close = self._get_connection()
        try:
            with conn.transaction():
                with conn.cursor() as cursor:
                    requested_slug_count = len(item_slugs or [])
                    logger.info(
                        "Starting item materialization: requested_slug_count=%s include_related=%s",
                        requested_slug_count,
                        include_related,
                    )
                    item_rows = self._load_item_rows(cursor)
                    if not item_rows:
                        elapsed_seconds = round(perf_counter() - started_at, 3)
                        logger.info("Item materialization found no toolkit items to process.")
                        return {
                            "updated_item_count": 0,
                            "updated_comparison_item_count": 0,
                            "elapsed_seconds": elapsed_seconds,
                        }

                    slug_to_id = {row["slug"]: row["id"] for row in item_rows}
                    if item_slugs:
                        target_item_ids = {
                            slug_to_id[slug]
                            for slug in item_slugs
                            if slug in slug_to_id
                        }
                    else:
                        target_item_ids = {row["id"] for row in item_rows}

                    if not target_item_ids:
                        elapsed_seconds = round(perf_counter() - started_at, 3)
                        logger.info(
                            "Item materialization resolved no matching target items from %s requested slugs.",
                            requested_slug_count,
                        )
                        return {
                            "updated_item_count": 0,
                            "updated_comparison_item_count": 0,
                            "elapsed_seconds": elapsed_seconds,
                        }

                    logger.info(
                        "Loaded %s toolkit items; materializing %s target items.",
                        len(item_rows),
                        len(target_item_ids),
                    )

                    fetch_started_at = perf_counter()
                    item_contexts: Dict[Any, ItemContext] = {}
                    target_item_id_list = sorted(target_item_ids, key=str)
                    for index, item_id in enumerate(target_item_id_list, start=1):
                        item_contexts[item_id] = self._fetch_item_context(cursor, item_id)
                        self._maybe_log_progress("Fetched target item contexts", index, len(target_item_id_list))
                    fetch_target_seconds = round(perf_counter() - fetch_started_at, 3)

                    comparison_item_ids = set(target_item_ids)
                    if include_related:
                        comparison_item_ids.update(
                            self._expand_related_item_ids(item_rows, item_contexts.values())
                        )

                    additional_item_ids = sorted(
                        (item_id for item_id in comparison_item_ids if item_id not in item_contexts),
                        key=str,
                    )
                    logger.info(
                        "Preparing %s comparison items (%s additional related items).",
                        len(comparison_item_ids),
                        len(additional_item_ids),
                    )
                    related_fetch_started_at = perf_counter()
                    for index, item_id in enumerate(additional_item_ids, start=1):
                        item_contexts[item_id] = self._fetch_item_context(cursor, item_id)
                        self._maybe_log_progress(
                            "Fetched related comparison item contexts",
                            index,
                            len(additional_item_ids),
                        )
                    fetch_related_seconds = round(perf_counter() - related_fetch_started_at, 3)

                    derive_started_at = perf_counter()
                    comparison_item_id_list = sorted(comparison_item_ids, key=str)
                    for index, item_id in enumerate(comparison_item_id_list, start=1):
                        if item_id not in item_contexts:
                            item_contexts[item_id] = self._fetch_item_context(cursor, item_id)
                        context = item_contexts[item_id]
                        replication_summary = self._derive_replication_summary(context)
                        facets = self._derive_facets(context, replication_summary)
                        refined_item_type = self._refine_item_type(context, facets)
                        problem_links = self._derive_problem_links(context)
                        explainers = self._derive_explainers(
                            context,
                            replication_summary=replication_summary,
                            facets=facets,
                            problem_links=problem_links,
                        )
                        self._update_item_type(cursor, context.item_id, refined_item_type)
                        self._update_first_publication_year(cursor, context, replication_summary)
                        self._replace_item_facets(cursor, item_id, facets)
                        self._replace_item_problem_links(cursor, item_id, problem_links)
                        self._replace_item_explainers(cursor, item_id, explainers)
                        self._upsert_replication_summary(cursor, item_id, replication_summary)
                        self._maybe_log_progress("Materialized item details", index, len(comparison_item_id_list))
                    derive_seconds = round(perf_counter() - derive_started_at, 3)

                    comparison_started_at = perf_counter()
                    logger.info(
                        "Replacing item comparisons for %s items.",
                        len(comparison_item_id_list),
                    )
                    self._replace_item_comparisons(
                        cursor,
                        comparison_item_ids,
                        {item_id: item_contexts[item_id] for item_id in comparison_item_ids},
                    )
                    comparison_seconds = round(perf_counter() - comparison_started_at, 3)

        finally:
            if should_close:
                conn.close()

        elapsed_seconds = round(perf_counter() - started_at, 3)
        logger.info(
            "Finished item materialization: targets=%s comparisons=%s fetch_targets_s=%s fetch_related_s=%s derive_s=%s comparisons_s=%s total_s=%s",
            len(target_item_ids),
            len(comparison_item_ids),
            fetch_target_seconds,
            fetch_related_seconds,
            derive_seconds,
            comparison_seconds,
            elapsed_seconds,
        )
        return {
            "updated_item_count": len(target_item_ids),
            "updated_comparison_item_count": len(comparison_item_ids),
            "elapsed_seconds": elapsed_seconds,
        }

    @classmethod
    def _maybe_log_progress(cls, label: str, current: int, total: int) -> None:
        if total <= 0:
            return
        if current == total or current == 1 or current % cls.PROGRESS_LOG_INTERVAL == 0:
            logger.info("%s: %s/%s", label, current, total)

    def _get_connection(self) -> Tuple[Any, bool]:
        if self._connection is not None:
            return self._connection, False
        if not self.settings.database_url:
            raise LoadPlanExecutionError("DATABASE_URL is required to materialize item details.")

        import psycopg

        return psycopg.connect(self.settings.database_url), True

    @staticmethod
    def _load_item_rows(cursor: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              ti.id,
              ti.slug,
              ti.canonical_name,
              ti.item_type::text,
              ti.summary,
              ti.primary_input_modality::text,
              ti.primary_output_modality::text,
              coalesce(array_agg(distinct s.synonym) filter (where s.synonym is not null), '{}'::text[]) as synonyms,
              coalesce(array(
                select mechanism_name
                from item_mechanism
                where item_id = ti.id
                order by mechanism_name asc
              ), '{}'::text[]) as mechanisms,
              coalesce(array(
                select technique_name
                from item_technique
                where item_id = ti.id
                order by technique_name asc
              ), '{}'::text[]) as techniques,
              coalesce(array(
                select target_process
                from item_target_process
                where item_id = ti.id
                order by target_process asc
              ), '{}'::text[]) as target_processes
            from toolkit_item ti
            left join item_synonym s on s.item_id = ti.id
            group by ti.id
            order by ti.slug asc
            """
        )
        return [
            {
                "id": row[0],
                "slug": row[1],
                "canonical_name": row[2],
                "item_type": row[3],
                "summary": row[4],
                "primary_input_modality": row[5],
                "primary_output_modality": row[6],
                "synonyms": list(row[7] or []),
                "mechanisms": list(row[8] or []),
                "techniques": list(row[9] or []),
                "target_processes": list(row[10] or []),
            }
            for row in cursor.fetchall()
        ]

    def _fetch_item_context(self, cursor: Any, item_id: Any) -> ItemContext:
        cursor.execute(
            """
            select
              ti.id,
              ti.slug,
              ti.canonical_name,
              ti.item_type::text,
              ti.summary,
              ti.primary_input_modality::text,
              ti.primary_output_modality::text,
              coalesce(array(
                select synonym
                from item_synonym
                where item_id = ti.id
                order by synonym asc
              ), '{}'::text[]) as synonyms,
              coalesce(array(
                select mechanism_name
                from item_mechanism
                where item_id = ti.id
                order by mechanism_name asc
              ), '{}'::text[]) as mechanisms,
              coalesce(array(
                select technique_name
                from item_technique
                where item_id = ti.id
                order by technique_name asc
              ), '{}'::text[]) as techniques,
              coalesce(array(
                select target_process
                from item_target_process
                where item_id = ti.id
                order by target_process asc
              ), '{}'::text[]) as target_processes
            from toolkit_item ti
            where ti.id = %s
            """,
            (item_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise LoadPlanExecutionError(f"Unknown item id during materialization: {item_id}")

        claims = self._fetch_claims(cursor, item_id)
        validations = self._fetch_validations(cursor, item_id)
        citations = self._fetch_citations(cursor, item_id)
        gap_links = self._fetch_gap_links(cursor, item_id)
        extracted_evidence = self._fetch_extracted_evidence(cursor, item_id, row[1])

        return ItemContext(
            item_id=row[0],
            slug=row[1],
            canonical_name=row[2],
            item_type=row[3],
            summary=row[4],
            primary_input_modality=row[5],
            primary_output_modality=row[6],
            synonyms=list(row[7] or []),
            mechanisms=list(row[8] or []),
            techniques=list(row[9] or []),
            target_processes=list(row[10] or []),
            claims=claims,
            validations=validations,
            citations=citations,
            gap_links=gap_links,
            extracted_evidence=extracted_evidence,
        )

    @staticmethod
    def _fetch_claims(cursor: Any, item_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              ec.id,
              ec.claim_type,
              ec.claim_text_normalized,
              ec.polarity::text,
              ec.needs_review,
              ec.context,
              ec.source_locator,
              sd.id,
              sd.title,
              sd.source_type::text,
              sd.publication_year,
              sd.journal_or_source,
              sd.doi,
              sd.pmid,
              sd.is_retracted
            from extracted_claim ec
            join claim_subject_link csl on csl.claim_id = ec.id
            join source_document sd on sd.id = ec.source_document_id
            where csl.item_id = %s
            order by sd.publication_year desc nulls last, ec.claim_type asc, ec.claim_text_normalized asc
            """,
            (item_id,),
        )
        claim_rows = cursor.fetchall()
        claims: List[Dict[str, Any]] = []
        for row in claim_rows:
            claim_id = row[0]
            cursor.execute(
                """
                select metric_name, operator, value_num, value_text, unit, condition_text
                from claim_metric
                where claim_id = %s
                order by metric_name asc
                """,
                (claim_id,),
            )
            metrics = [
                {
                    "metric_name": metric_row[0],
                    "operator": metric_row[1],
                    "value_num": metric_row[2],
                    "value_text": metric_row[3],
                    "unit": metric_row[4],
                    "condition_text": metric_row[5],
                }
                for metric_row in cursor.fetchall()
            ]
            claims.append(
                {
                    "id": str(claim_id),
                    "claim_type": row[1],
                    "claim_text_normalized": row[2],
                    "polarity": row[3],
                    "needs_review": row[4],
                    "context": row[5] or {},
                    "source_locator": row[6] or {},
                    "source_document": {
                        "id": str(row[7]),
                        "title": row[8],
                        "source_type": row[9],
                        "publication_year": row[10],
                        "journal_or_source": row[11],
                        "doi": row[12],
                        "pmid": row[13],
                        "is_retracted": row[14],
                    },
                    "metrics": metrics,
                }
            )
        return claims

    @staticmethod
    def _fetch_validations(cursor: Any, item_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              vo.id,
              vo.observation_type::text,
              vo.biological_system_level::text,
              vo.species,
              vo.strain_or_model,
              vo.cell_type,
              vo.tissue,
              vo.delivery_mode,
              vo.cargo_or_effector,
              vo.construct_name,
              vo.assay_description,
              vo.success_outcome::text,
              vo.independent_lab_cluster_id,
              vo.institution_cluster_id,
              vo.notes,
              vo.source_locator,
              sd.id,
              sd.title,
              sd.source_type::text,
              sd.publication_year,
              sd.journal_or_source,
              sd.doi,
              sd.pmid,
              sd.is_retracted
            from validation_observation vo
            join source_document sd on sd.id = vo.source_document_id
            where vo.item_id = %s
            order by sd.publication_year desc nulls last, vo.observation_type asc
            """,
            (item_id,),
        )
        rows = cursor.fetchall()
        validations: List[Dict[str, Any]] = []
        for row in rows:
            validation_id = row[0]
            cursor.execute(
                """
                select metric_name, value_num, unit, qualifier, condition_text
                from validation_metric_value
                where validation_observation_id = %s
                order by metric_name asc
                """,
                (validation_id,),
            )
            metrics = [
                {
                    "metric_name": metric_row[0],
                    "value_num": metric_row[1],
                    "unit": metric_row[2],
                    "qualifier": metric_row[3],
                    "condition_text": metric_row[4],
                }
                for metric_row in cursor.fetchall()
            ]
            validations.append(
                {
                    "id": str(row[0]),
                    "observation_type": row[1],
                    "biological_system_level": row[2],
                    "species": row[3],
                    "strain_or_model": row[4],
                    "cell_type": row[5],
                    "tissue": row[6],
                    "delivery_mode": row[7],
                    "cargo_or_effector": row[8],
                    "construct_name": row[9],
                    "assay_description": row[10],
                    "success_outcome": row[11],
                    "independent_lab_cluster_id": row[12],
                    "institution_cluster_id": row[13],
                    "notes": row[14],
                    "source_locator": row[15] or {},
                    "metrics": metrics,
                    "source_document": {
                        "id": str(row[16]),
                        "title": row[17],
                        "source_type": row[18],
                        "publication_year": row[19],
                        "journal_or_source": row[20],
                        "doi": row[21],
                        "pmid": row[22],
                        "is_retracted": row[23],
                    },
                }
            )
        return validations

    @staticmethod
    def _fetch_citations(cursor: Any, item_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              ic.citation_role::text,
              ic.importance_rank,
              ic.why_this_matters,
              sd.id,
              sd.title,
              sd.source_type::text,
              sd.publication_year,
              sd.journal_or_source,
              sd.doi,
              sd.pmid,
              sd.is_retracted
            from item_citation ic
            join source_document sd on sd.id = ic.source_document_id
            where ic.item_id = %s
            order by ic.importance_rank asc, sd.title asc
            """,
            (item_id,),
        )
        return [
            {
                "citation_role": row[0],
                "importance_rank": row[1],
                "why_this_matters": row[2],
                "source_document_id": str(row[3]),
                "title": row[4],
                "source_type": row[5],
                "publication_year": row[6],
                "journal_or_source": row[7],
                "doi": row[8],
                "pmid": row[9],
                "is_retracted": row[10],
            }
            for row in cursor.fetchall()
        ]

    @staticmethod
    def _fetch_gap_links(cursor: Any, item_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              gi.slug,
              gi.title,
              igl.overall_gap_applicability_score,
              igl.why_it_might_help,
              igl.assumptions,
              igl.missing_evidence
            from item_gap_link igl
            join gap_item gi on gi.id = igl.gap_item_id
            where igl.item_id = %s
            order by igl.overall_gap_applicability_score desc nulls last, gi.title asc
            """,
            (item_id,),
        )
        return [
            {
                "gap_slug": row[0],
                "gap_title": row[1],
                "overall_score": float(row[2]) if row[2] is not None else None,
                "why_it_might_help": row[3],
                "assumptions": row[4],
                "missing_evidence": row[5],
            }
            for row in cursor.fetchall()
        ]

    @staticmethod
    def _fetch_extracted_evidence(cursor: Any, item_id: Any, item_slug: str) -> List[ExtractedItemEvidence]:
        cursor.execute(
            """
            select
              eic.local_id,
              eic.evidence_text,
              eic.raw_payload,
              sd.id,
              sd.title,
              sd.source_type::text,
              sd.publication_year,
              sd.journal_or_source,
              sd.doi,
              sd.pmid,
              sd.is_retracted
            from extracted_item_candidate eic
            join source_document sd on sd.id = eic.source_document_id
            where eic.candidate_type = 'toolkit_item'
              and (
                eic.matched_item_id = %s
                or eic.matched_slug = %s
                or (eic.slug = %s and eic.matched_item_id is null and coalesce(eic.matched_slug, '') = '')
              )
            order by sd.publication_year desc nulls last, eic.created_at desc
            """,
            (item_id, item_slug, item_slug),
        )
        evidence_rows = cursor.fetchall()
        results: List[ExtractedItemEvidence] = []
        seen = set()
        for row in evidence_rows:
            key = (str(row[0]), str(row[3]))
            if key in seen:
                continue
            seen.add(key)
            payload = row[2] or {}
            if not isinstance(payload, dict):
                payload = {}
            freeform_explainers = payload.get("freeform_explainers") or {}
            if not isinstance(freeform_explainers, dict):
                freeform_explainers = {}
            results.append(
                ExtractedItemEvidence(
                    local_id=str(row[0]),
                    evidence_text=row[1],
                    useful_for=_dedupe_preserving_order(payload.get("useful_for") or []),
                    problem_solved=_dedupe_preserving_order(payload.get("problem_solved") or []),
                    strengths=_dedupe_preserving_order(payload.get("strengths") or []),
                    limitations=_dedupe_preserving_order(payload.get("limitations") or []),
                    implementation_constraints=_dedupe_preserving_order(
                        payload.get("implementation_constraints") or []
                    ),
                    freeform_explainers={
                        key: str(value).strip()
                        for key, value in freeform_explainers.items()
                        if str(value).strip()
                    },
                    source_document={
                        "id": str(row[3]),
                        "title": row[4],
                        "source_type": row[5],
                        "publication_year": row[6],
                        "journal_or_source": row[7],
                        "doi": row[8],
                        "pmid": row[9],
                        "is_retracted": row[10],
                    },
                )
            )
        return results

    def _expand_related_item_ids(self, item_rows: List[Dict[str, Any]], contexts: Iterable[ItemContext]) -> set[Any]:
        related_ids: set[Any] = set()
        rows_by_id = {row["id"]: row for row in item_rows}
        for context in contexts:
            for row in item_rows:
                if row["id"] == context.item_id:
                    continue
                if self._peer_similarity(context, rows_by_id[row["id"]]) > 0:
                    related_ids.add(row["id"])
        return related_ids

    def _peer_similarity(self, context: ItemContext, row: Dict[str, Any]) -> int:
        score = 0
        if context.item_type == row["item_type"]:
            score += 1
        if context.primary_input_modality and context.primary_input_modality == row["primary_input_modality"]:
            score += 1
        if context.primary_output_modality and context.primary_output_modality == row["primary_output_modality"]:
            score += 1
        score += 2 * len(set(context.target_processes).intersection(row.get("target_processes", [])))
        score += len(set(context.mechanisms).intersection(row.get("mechanisms", [])))
        return score

    def _derive_facets(
        self,
        context: ItemContext,
        replication_summary: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        text = context.text_blob
        facets: List[Tuple[str, str, Optional[str]]] = []

        role = self._derive_role(context, text)
        facets.append(("operating_role", role, "Derived from item type, output modality, and claim language."))

        for architecture in self._derive_switch_architectures(context, text):
            facets.append(("switch_architecture", architecture, "Derived from item name, item type, and claim language."))

        facets.append(
            (
                "encoding_mode",
                self._derive_encoding_mode(context, text),
                "Derived from implementation language and item type.",
            )
        )
        facets.append(
            (
                "cofactor_dependency",
                self._derive_cofactor_dependency(text),
                "Derived from cofactor and chromophore language in the evidence.",
            )
        )

        if context.primary_input_modality == "light":
            facets.append(
                (
                    "implementation_constraint",
                    "spectral_hardware_requirement",
                    "Requires compatible illumination hardware and wavelength planning.",
                )
            )
        if "multi_component" in {value for name, value, _ in facets if name == "switch_architecture"}:
            facets.append(
                (
                    "implementation_constraint",
                    "multi_component_delivery_burden",
                    "Multiple components likely increase delivery and stoichiometry coordination burden.",
                )
            )
        if replication_summary["distinct_biological_contexts"] <= 1:
            facets.append(
                (
                    "implementation_constraint",
                    "context_specific_validation",
                    "Validation breadth is still narrow across biological contexts.",
                )
            )
        if any(term in text for term in ("viral vector", "aav", "lentiviral", "packaging", "payload")):
            facets.append(
                (
                    "implementation_constraint",
                    "payload_burden",
                    "Evidence mentions delivery or packaging burden.",
                )
            )

        deduped = []
        seen = set()
        for facet_name, facet_value, evidence_note in facets:
            key = (facet_name, facet_value)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(
                {
                    "facet_name": facet_name,
                    "facet_value": facet_value,
                    "evidence_note": evidence_note,
                }
            )
        return deduped

    @staticmethod
    def _derive_role(context: ItemContext, text: str) -> str:
        if context.item_type == "delivery_harness":
            return "delivery"
        if context.item_type in {"engineering_method", "computation_method"}:
            return "builder"
        if context.item_type == "assay_method" or any(term in text for term in ("sensor", "detect", "readout", "diagnostic")):
            return "sensor"
        if "reporter" in text:
            return "reporter"
        if context.primary_output_modality in {
            "transcription",
            "translation",
            "localization",
            "degradation",
            "signaling",
            "recombination",
            "editing",
        } or context.target_processes:
            return "regulator"
        return "actuator"

    @staticmethod
    def _derive_switch_architectures(context: ItemContext, text: str) -> List[str]:
        architectures: List[str] = []
        name = _strip_inline_markup(context.canonical_name).casefold()
        if context.item_type == "multi_component_switch" or "/" in name or any(
            term in text for term in ("binding partner", "heterodimer", "two-component", "multi-component")
        ):
            architectures.append("multi_component")
        if any(term in text for term in ("single-chain", "single chain", "single flavin-containing")):
            architectures.append("single_chain")
        if "split " in text or text.startswith("split"):
            architectures.append("split")
        if any(term in text for term in ("recruitment", "bind partner", "heterodimer")):
            architectures.append("recruitment")
        if any(term in text for term in ("uncag", "allosteric", "sterically constrained", "undock")):
            architectures.append("uncaging")
        if "photocleav" in text:
            architectures.append("cleavage")
        return architectures or (["single_chain"] if context.item_type == "protein_domain" else [])

    @staticmethod
    def _refine_item_type(context: ItemContext, facets: List[Dict[str, str]]) -> str:
        if context.item_type != "construct_pattern":
            return context.item_type
        plain_name = _strip_inline_markup(context.canonical_name).casefold()
        facet_map: Dict[str, List[str]] = {}
        for facet in facets:
            facet_map.setdefault(facet["facet_name"], []).append(facet["facet_value"])
        architectures = set(facet_map.get("switch_architecture", []))
        if "multi_component" in architectures:
            return "multi_component_switch"
        if any(term in plain_name for term in ("lov2", "photoswitch", "photosensor", "photoreceptor")):
            return "protein_domain"
        return context.item_type

    @staticmethod
    def _derive_encoding_mode(context: ItemContext, text: str) -> str:
        if any(term in text for term in ("externally supplied", "exogenous ligand", "small molecule addition")):
            return "hybrid"
        if context.item_type in {"protein_domain", "multi_component_switch", "rna_element", "construct_pattern"}:
            return "genetically_encoded"
        if context.item_type == "delivery_harness":
            return "externally_supplied"
        return "genetically_encoded"

    @staticmethod
    def _derive_cofactor_dependency(text: str) -> str:
        if any(term in text for term in ("without exogenous", "no exogenous chromophore", "endogenous flavin")):
            return "compatible_with_endogenous_cofactor"
        if any(
            term in text
            for term in (
                "5-deazafmn",
                "phycocyanobilin",
                "chromophore supply",
                "biliverdin",
                "retinal",
                "exogenous cofactor",
                "exogenous chromophore",
            )
        ):
            return "requires_exogenous_cofactor"
        return "cofactor_requirement_unknown"

    @staticmethod
    def _collect_literature_statements(
        context: ItemContext,
        *,
        freeform_key: Optional[str] = None,
        structured_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        statements: List[Dict[str, Any]] = []
        seen = set()
        for evidence in context.extracted_evidence:
            values: List[Tuple[str, str]] = []
            if freeform_key:
                freeform_value = evidence.freeform_explainers.get(freeform_key)
                if freeform_value:
                    values.append((freeform_value, freeform_key))
            if structured_key:
                for structured_value in getattr(evidence, structured_key, []):
                    cleaned_value = str(structured_value).strip()
                    if cleaned_value:
                        values.append((cleaned_value, structured_key))
            for text, extract_field in values:
                cleaned_text = str(text).strip()
                key = (cleaned_text.casefold(), evidence.source_document["id"], extract_field)
                if not cleaned_text or key in seen:
                    continue
                seen.add(key)
                statements.append(
                    {
                        "text": cleaned_text,
                        "extract_field": extract_field,
                        "source_document": evidence.source_document,
                        "evidence_text": evidence.evidence_text,
                        "local_id": evidence.local_id,
                    }
                )
        return statements

    @staticmethod
    def _collect_structured_values(context: ItemContext, attribute_name: str) -> List[str]:
        return _dedupe_preserving_order(
            value
            for evidence in context.extracted_evidence
            for value in getattr(evidence, attribute_name, [])
        )

    @staticmethod
    def _build_literature_payload(
        statements: List[Dict[str, Any]],
        *,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "source_kind": "literature_extract",
            "sources": [
                {
                    "document": statement["source_document"],
                    "support_text": statement["text"],
                    "evidence_text": statement.get("evidence_text"),
                    "extract_field": statement["extract_field"],
                    "local_id": statement["local_id"],
                }
                for statement in statements
            ],
        }
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def _build_literature_explainer(
        *,
        explainer_kind: str,
        title: str,
        statements: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not statements:
            return None
        body = "; ".join(_dedupe_preserving_order(statement["text"] for statement in statements))
        if not body:
            return None
        return {
            "explainer_kind": explainer_kind,
            "title": title,
            "body": body,
            "evidence_payload": ItemMaterializer._build_literature_payload(statements),
        }

    @staticmethod
    def _collect_claim_statements(
        context: ItemContext,
        *,
        claim_types: Optional[Sequence[str]] = None,
        keywords: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]]:
        statements: List[Dict[str, Any]] = []
        seen = set()
        allowed_claim_types = set(claim_types or [])
        keyword_tokens = [keyword.casefold() for keyword in (keywords or [])]
        for claim in context.claims:
            claim_type = str(claim.get("claim_type") or "")
            if allowed_claim_types and claim_type not in allowed_claim_types:
                continue
            quoted_text = str((claim.get("source_locator") or {}).get("quoted_text") or "").strip()
            claim_text = str(claim.get("claim_text_normalized") or "").strip()
            support_text = quoted_text or claim_text
            if not support_text:
                continue
            if keyword_tokens:
                haystack = f"{claim_text} {quoted_text}".casefold()
                if not any(token in haystack for token in keyword_tokens):
                    continue
            source_document = claim.get("source_document") or {}
            source_id = str(source_document.get("id") or "")
            if not source_id:
                continue
            key = (support_text.casefold(), source_id, claim_type)
            if key in seen:
                continue
            seen.add(key)
            statements.append(
                {
                    "text": support_text,
                    "extract_field": claim_type or "claim",
                    "source_document": source_document,
                    "claim_id": claim.get("id"),
                    "claim_text": claim_text,
                }
            )
        return statements

    @staticmethod
    def _build_claim_payload(
        statements: List[Dict[str, Any]],
        *,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "source_kind": "canonical_claim",
            "sources": [
                {
                    "document": statement["source_document"],
                    "support_text": statement["text"],
                    "extract_field": statement["extract_field"],
                    "claim_id": statement.get("claim_id"),
                    "claim_text": statement.get("claim_text"),
                }
                for statement in statements
            ],
        }
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def _build_claim_explainer(
        *,
        explainer_kind: str,
        title: str,
        statements: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not statements:
            return None
        body = " ".join(_dedupe_preserving_order(statement["text"] for statement in statements))
        if not body:
            return None
        return {
            "explainer_kind": explainer_kind,
            "title": title,
            "body": body,
            "evidence_payload": ItemMaterializer._build_claim_payload(statements),
        }

    @staticmethod
    def _build_problem_label_from_statement(statement: str) -> str:
        cleaned = statement.strip().rstrip(".")
        if len(cleaned) <= 110:
            return cleaned
        sentence = cleaned.split(". ", 1)[0].strip()
        if sentence and len(sentence) <= 110:
            return sentence
        return cleaned[:107].rstrip() + "..."

    def _derive_problem_links(self, context: ItemContext) -> List[Dict[str, Any]]:
        problems: List[Dict[str, Any]] = []
        for evidence in context.extracted_evidence:
            freeform_problem = evidence.freeform_explainers.get("problem_it_solves")
            supporting_text = (
                freeform_problem
                or evidence.freeform_explainers.get("what_it_does")
                or evidence.evidence_text
                or ""
            ).strip()
            labels = list(evidence.problem_solved)
            if freeform_problem and not labels:
                labels = [self._build_problem_label_from_statement(freeform_problem)]
            for label in labels:
                cleaned_label = str(label).strip()
                if not cleaned_label:
                    continue
                problems.append(
                    {
                        "problem_label": cleaned_label,
                        "why_this_item_helps": supporting_text or cleaned_label,
                        "source_kind": "literature_extract",
                        "gap_slug": None,
                        "overall_score": None,
                        "evidence_payload": self._build_literature_payload(
                            [
                                {
                                    "text": supporting_text or cleaned_label,
                                    "extract_field": "problem_it_solves"
                                    if freeform_problem
                                    else "problem_solved",
                                    "source_document": evidence.source_document,
                                    "evidence_text": evidence.evidence_text,
                                    "local_id": evidence.local_id,
                                }
                            ]
                        ),
                    }
                )

        for gap_link in context.gap_links:
            problems.append(
                {
                    "problem_label": gap_link["gap_title"],
                    "why_this_item_helps": gap_link.get("why_it_might_help")
                    or f"{context.canonical_name} appears relevant to this gap from current canonical linkage.",
                    "source_kind": "gap_map",
                    "gap_slug": gap_link.get("gap_slug"),
                    "overall_score": gap_link.get("overall_score"),
                    "evidence_payload": {
                        "assumptions": gap_link.get("assumptions"),
                        "missing_evidence": gap_link.get("missing_evidence"),
                    },
                }
            )

        if not problems:
            for problem_label in self._derive_generic_problem_labels(context):
                problems.append(
                    {
                        "problem_label": problem_label,
                        "why_this_item_helps": self._build_problem_help_text(context, problem_label),
                        "source_kind": "derived",
                        "gap_slug": None,
                        "overall_score": None,
                        "evidence_payload": {"target_processes": context.target_processes},
                    }
                )

        deduped: List[Dict[str, Any]] = []
        seen = set()
        for problem in problems:
            key = (problem["problem_label"].casefold(), problem["source_kind"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(problem)
        return deduped

    @staticmethod
    def _derive_generic_problem_labels(context: ItemContext) -> List[str]:
        labels: List[str] = []
        for target_process in context.target_processes:
            mapping = {
                "transcription": "Need tighter control over gene expression timing or amplitude",
                "translation": "Need tighter control over protein production",
                "localization": "Need inducible protein relocalization or recruitment",
                "degradation": "Need conditional protein clearance",
                "signaling": "Need conditional control of signaling activity",
                "recombination": "Need conditional recombination or state switching",
                "editing": "Need controllable genome or transcript editing",
                "selection": "Need better screening or enrichment leverage",
                "manufacturing": "Need manufacturable control over a production workflow",
                "diagnostic": "Need a controllable or interpretable biological readout",
            }
            if target_process in mapping:
                labels.append(mapping[target_process])
        if context.primary_input_modality == "light":
            labels.append("Need precise spatiotemporal control with light input")
        return _dedupe_preserving_order(labels)

    @staticmethod
    def _build_problem_help_text(context: ItemContext, problem_label: str) -> str:
        if context.summary:
            return context.summary
        process_list = ", ".join(context.target_processes) if context.target_processes else "the target biology"
        return f"{context.canonical_name} is positioned to help when the goal is to control {process_list}. {problem_label}."

    def _derive_explainers(
        self,
        context: ItemContext,
        *,
        replication_summary: Dict[str, Any],
        facets: List[Dict[str, str]],
        problem_links: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        facet_map: Dict[str, List[str]] = {}
        for facet in facets:
            facet_map.setdefault(facet["facet_name"], []).append(facet["facet_value"])

        usefulness = self._build_usefulness_explainer(context, problem_links)
        limitations = self._build_limitations_explainer(context, replication_summary, facet_map)
        strengths = self._build_strengths_explainer(context, replication_summary, facet_map)
        implementation = self._build_implementation_explainer(context, facet_map)
        problem_body = " ".join(link["why_this_item_helps"] for link in problem_links[:3]).strip()

        literature_explainers = [
            self._build_literature_explainer(
                explainer_kind="usefulness",
                title="Why this is useful",
                statements=self._collect_literature_statements(
                    context,
                    freeform_key="what_it_does",
                    structured_key="useful_for",
                ),
            ),
            self._build_literature_explainer(
                explainer_kind="problem_solved",
                title="What problem this helps solve",
                statements=self._collect_literature_statements(
                    context,
                    freeform_key="problem_it_solves",
                    structured_key="problem_solved",
                ),
            ),
            self._build_literature_explainer(
                explainer_kind="strengths",
                title="Strengths",
                statements=self._collect_literature_statements(
                    context,
                    structured_key="strengths",
                ),
            ),
            self._build_literature_explainer(
                explainer_kind="limitations",
                title="Limitations",
                statements=self._collect_literature_statements(
                    context,
                    freeform_key="problem_it_does_not_solve",
                    structured_key="limitations",
                ),
            ),
            self._build_literature_explainer(
                explainer_kind="implementation_constraints",
                title="Implementation constraints",
                statements=self._collect_literature_statements(
                    context,
                    freeform_key="resources_required",
                    structured_key="implementation_constraints",
                ),
            ),
            self._build_literature_explainer(
                explainer_kind="alternatives",
                title="Nearby alternatives in the literature",
                statements=self._collect_literature_statements(
                    context,
                    freeform_key="alternatives",
                ),
            ),
        ]
        claim_explainers = [
            self._build_claim_explainer(
                explainer_kind="usefulness",
                title="Why this is useful",
                statements=self._collect_claim_statements(
                    context,
                    claim_types=(
                        "application_result",
                        "application_potential",
                        "engineering_result",
                        "mechanism_summary",
                    ),
                )[:3],
            ),
            self._build_claim_explainer(
                explainer_kind="problem_solved",
                title="What problem this helps solve",
                statements=self._collect_claim_statements(
                    context,
                    claim_types=("application_result", "application_potential"),
                )[:3],
            ),
            self._build_claim_explainer(
                explainer_kind="implementation_constraints",
                title="Implementation constraints",
                statements=self._collect_claim_statements(
                    context,
                    keywords=(
                        "phycocyanobilin",
                        "biliverdin",
                        "chromophore",
                        "cofactor",
                        "illumination",
                        "light",
                    ),
                )[:3],
            ),
        ]
        explainers_by_kind = {
            explainer["explainer_kind"]: explainer
            for explainer in literature_explainers
            if explainer is not None
        }
        for explainer in claim_explainers:
            if explainer is not None:
                explainers_by_kind.setdefault(explainer["explainer_kind"], explainer)

        explainers = [
            {
                "explainer_kind": "usefulness",
                "title": "Why this is useful",
                "body": usefulness,
                "evidence_payload": {"problem_labels": [link["problem_label"] for link in problem_links]},
            },
            {
                "explainer_kind": "problem_solved",
                "title": "What problem this helps solve",
                "body": problem_body or usefulness,
                "evidence_payload": {"problem_labels": [link["problem_label"] for link in problem_links]},
            },
            {
                "explainer_kind": "strengths",
                "title": "Strengths",
                "body": strengths,
                "evidence_payload": {"replication_summary": replication_summary},
            },
            {
                "explainer_kind": "limitations",
                "title": "Limitations",
                "body": limitations,
                "evidence_payload": {"replication_summary": replication_summary},
            },
            {
                "explainer_kind": "implementation_constraints",
                "title": "Implementation constraints",
                "body": implementation,
                "evidence_payload": {"facets": facets},
            },
        ]
        for explainer in explainers:
            if explainer["body"].strip():
                explainers_by_kind.setdefault(explainer["explainer_kind"], explainer)
        ordered_kinds = [
            "usefulness",
            "problem_solved",
            "strengths",
            "alternatives",
            "limitations",
            "implementation_constraints",
        ]
        return [explainers_by_kind[kind] for kind in ordered_kinds if kind in explainers_by_kind]

    @staticmethod
    def _build_usefulness_explainer(context: ItemContext, problem_links: List[Dict[str, Any]]) -> str:
        if problem_links:
            labels = "; ".join(link["problem_label"] for link in problem_links[:3])
            return f"{context.canonical_name} is most useful when you need a concrete way to address problems like: {labels}."
        if context.summary:
            return context.summary
        target_text = ", ".join(context.target_processes) if context.target_processes else "the stated target process"
        return f"{context.canonical_name} is useful as a {context.item_type.replace('_', ' ')} for controlling {target_text}."

    @staticmethod
    def _build_strengths_explainer(
        context: ItemContext,
        replication_summary: Dict[str, Any],
        facet_map: Dict[str, List[str]],
    ) -> str:
        strengths: List[str] = []
        if replication_summary["independent_primary_paper_count"] > 0:
            strengths.append("There is at least some independent follow-up evidence rather than a single founding report.")
        if replication_summary["distinct_biological_contexts"] > 1:
            strengths.append("Evidence spans more than one biological context, which improves confidence in portability.")
        if "compatible_with_endogenous_cofactor" in facet_map.get("cofactor_dependency", []):
            strengths.append("The current evidence suggests it can operate without requiring an added exogenous cofactor.")
        if "single_chain" in facet_map.get("switch_architecture", []):
            strengths.append("Its single-chain architecture can reduce implementation complexity relative to multi-component alternatives.")
        if context.summary and not strengths:
            strengths.append(context.summary)
        return " ".join(strengths)

    @staticmethod
    def _build_limitations_explainer(
        context: ItemContext,
        replication_summary: Dict[str, Any],
        facet_map: Dict[str, List[str]],
    ) -> str:
        limitations: List[str] = []
        for penalty in replication_summary["practicality_penalties"]:
            limitations.append(penalty.rstrip(".") + ".")
        if replication_summary["orphan_tool_flag"]:
            limitations.append("Independent reuse still looks limited, so the evidence base may be fragile.")
        if "requires_exogenous_cofactor" in facet_map.get("cofactor_dependency", []):
            limitations.append("It may depend on an exogenous cofactor or chromophore supply step.")
        if "multi_component_delivery_burden" in facet_map.get("implementation_constraint", []):
            limitations.append("Multi-component delivery and stoichiometry control can make deployment harder.")
        if not context.validations:
            limitations.append("No canonical validation observations are stored yet, so context-specific performance remains under-specified.")
        return " ".join(_dedupe_preserving_order(limitations))

    @staticmethod
    def _build_implementation_explainer(context: ItemContext, facet_map: Dict[str, List[str]]) -> str:
        notes: List[str] = []
        role = ", ".join(facet_map.get("operating_role", []))
        architecture = ", ".join(facet_map.get("switch_architecture", []))
        encoding = ", ".join(facet_map.get("encoding_mode", []))
        cofactor = ", ".join(facet_map.get("cofactor_dependency", []))
        if role:
            notes.append(f"Operational role: {role.replace('_', ' ')}.")
        if architecture:
            notes.append(f"Architecture cues: {architecture.replace('_', ' ')}.")
        if encoding:
            notes.append(f"Implementation mode: {encoding.replace('_', ' ')}.")
        if cofactor:
            notes.append(f"Cofactor status: {cofactor.replace('_', ' ')}.")
        if context.primary_input_modality:
            notes.append(f"Primary input modality: {context.primary_input_modality}.")
        if context.primary_output_modality:
            notes.append(f"Primary output modality: {context.primary_output_modality}.")
        return " ".join(notes)

    def _derive_replication_summary(self, context: ItemContext) -> Dict[str, Any]:
        documents: Dict[str, Dict[str, Any]] = {}
        for claim in context.claims:
            documents[claim["source_document"]["id"]] = claim["source_document"]
        for validation in context.validations:
            documents[validation["source_document"]["id"]] = validation["source_document"]
        for citation in context.citations:
            documents[citation["source_document_id"]] = {
                "id": citation["source_document_id"],
                "title": citation["title"],
                "source_type": citation["source_type"],
                "publication_year": citation["publication_year"],
                "journal_or_source": citation["journal_or_source"],
                "doi": citation["doi"],
                "pmid": citation["pmid"],
                "is_retracted": citation["is_retracted"],
            }

        primary_docs = [
            doc
            for doc in documents.values()
            if doc["source_type"] in {"primary_paper", "preprint", "benchmark", "trial_record"}
        ]
        citation_roles = [citation["citation_role"] for citation in context.citations]
        independent_count = len(
            {
                validation["source_document"]["id"]
                for validation in context.validations
                if validation.get("independent_lab_cluster_id")
            }
        )
        independent_count = max(
            independent_count,
            len(
                {
                    citation["source_document_id"]
                    for citation in context.citations
                    if citation["citation_role"] == "independent_validation"
                }
            ),
        )
        institution_count = len(
            {
                validation["institution_cluster_id"]
                for validation in context.validations
                if validation.get("institution_cluster_id")
            }
        )
        biological_contexts = len(
            {
                (
                    validation["biological_system_level"],
                    validation.get("species"),
                    validation.get("cell_type"),
                )
                for validation in context.validations
            }
        )
        publication_years = [
            doc["publication_year"]
            for doc in documents.values()
            if doc.get("publication_year") is not None
        ]
        first_year = min(publication_years) if publication_years else None
        years_since_first_report = (
            max(date.today().year - first_year, 0) if first_year is not None else None
        )
        downstream_application_count = sum(
            1
            for validation in context.validations
            if validation["observation_type"] in {"application_demo", "therapeutic_use", "manufacturing_use"}
        )
        contradiction_count = sum(1 for claim in context.claims if claim["polarity"] in {"contradicts", "mixed"})
        retraction_count = sum(1 for doc in documents.values() if doc.get("is_retracted"))

        penalties = self._derive_practicality_penalties(context, independent_count, biological_contexts)
        evidence_strength = _clamp_score(
            min(len(primary_docs), 6) / 6.0 * 0.5
            + min(len(context.claims), 10) / 10.0 * 0.2
            + min(len(context.validations), 8) / 8.0 * 0.3
        )
        replication_score = _clamp_score(
            min(independent_count, 4) / 4.0 * 0.45
            + min(biological_contexts, 4) / 4.0 * 0.35
            + (0.2 if any(role == "independent_validation" for role in citation_roles) else 0.0)
        )
        practicality_score = _clamp_score(
            0.95 - 0.12 * len(penalties) - (0.1 if context.item_type == "multi_component_switch" else 0.0)
        )
        translatability_score = _clamp_score(
            (0.45 if any(v["biological_system_level"] == "mammalian_cell_line" for v in context.validations) else 0.0)
            + (0.25 if any(v["biological_system_level"] == "mouse" for v in context.validations) else 0.0)
            + (0.15 if downstream_application_count > 0 else 0.0)
            + 0.15 * practicality_score
        )
        orphan_tool_flag = independent_count == 0 and len(primary_docs) <= 1

        return {
            "score_version": self.SCORE_VERSION,
            "primary_paper_count": len(primary_docs),
            "independent_primary_paper_count": independent_count,
            "distinct_last_author_clusters": independent_count,
            "distinct_institutions": institution_count,
            "distinct_biological_contexts": biological_contexts,
            "years_since_first_report": years_since_first_report,
            "downstream_application_count": downstream_application_count,
            "orphan_tool_flag": orphan_tool_flag,
            "practicality_penalties": penalties,
            "evidence_strength_score": evidence_strength,
            "replication_score": replication_score,
            "practicality_score": practicality_score,
            "translatability_score": translatability_score,
            "explanation": {
                "primary_document_count": len(primary_docs),
                "claim_count": len(context.claims),
                "validation_count": len(context.validations),
                "independent_count": independent_count,
                "biological_context_count": biological_contexts,
                "penalties": penalties,
                "contradiction_count": contradiction_count,
                "retraction_count": retraction_count,
            },
        }

    @staticmethod
    def _derive_practicality_penalties(
        context: ItemContext,
        independent_count: int,
        biological_contexts: int,
    ) -> List[str]:
        penalties: List[str] = []
        text = context.text_blob
        if any(term in text for term in ("requires exogenous", "exogenous cofactor", "5-deazafmn", "biliverdin", "retinal")):
            penalties.append("Requires extra cofactor or chromophore handling.")
        if context.item_type == "multi_component_switch" or "/" in context.canonical_name:
            penalties.append("Uses more than one coordinated component.")
        if context.primary_input_modality == "light":
            penalties.append("Needs compatible illumination hardware and optical access.")
        if independent_count == 0:
            penalties.append("Independent follow-up evidence is still limited.")
        if biological_contexts <= 1:
            penalties.append("Validation breadth across biological contexts is still narrow.")
        return _dedupe_preserving_order(penalties)

    @staticmethod
    def _update_first_publication_year(cursor: Any, context: ItemContext, replication_summary: Dict[str, Any]) -> None:
        years = [
            claim["source_document"].get("publication_year")
            for claim in context.claims
            if claim["source_document"].get("publication_year") is not None
        ]
        years.extend(
            validation["source_document"].get("publication_year")
            for validation in context.validations
            if validation["source_document"].get("publication_year") is not None
        )
        years.extend(
            citation.get("publication_year")
            for citation in context.citations
            if citation.get("publication_year") is not None
        )
        if not years:
            return
        cursor.execute(
            """
            update toolkit_item
            set first_publication_year = coalesce(first_publication_year, %s)
            where id = %s
            """,
            (min(years), context.item_id),
        )

    @staticmethod
    def _update_item_type(cursor: Any, item_id: Any, item_type: str) -> None:
        cursor.execute(
            """
            update toolkit_item
            set item_type = %s
            where id = %s
            """,
            (item_type, item_id),
        )

    @staticmethod
    def _replace_item_facets(cursor: Any, item_id: Any, facets: List[Dict[str, str]]) -> None:
        cursor.execute("delete from item_facet where item_id = %s", (item_id,))
        for facet in facets:
            cursor.execute(
                """
                insert into item_facet (item_id, facet_name, facet_value, evidence_note)
                values (%s, %s, %s, %s)
                """,
                (
                    item_id,
                    facet["facet_name"],
                    facet["facet_value"],
                    facet.get("evidence_note"),
                ),
            )

    @staticmethod
    def _replace_item_explainers(cursor: Any, item_id: Any, explainers: List[Dict[str, Any]]) -> None:
        cursor.execute("delete from item_explainer where item_id = %s", (item_id,))
        for explainer in explainers:
            cursor.execute(
                """
                insert into item_explainer (
                  item_id, explainer_kind, title, body, evidence_payload, derived_version, updated_at
                )
                values (%s, %s, %s, %s, %s::jsonb, %s, now())
                """,
                (
                    item_id,
                    explainer["explainer_kind"],
                    explainer.get("title"),
                    explainer["body"],
                    json.dumps(explainer.get("evidence_payload", {})),
                    ItemMaterializer.DERIVATION_VERSION,
                ),
            )

    @staticmethod
    def _replace_item_problem_links(cursor: Any, item_id: Any, problems: List[Dict[str, Any]]) -> None:
        cursor.execute("delete from item_problem_link where item_id = %s", (item_id,))
        for problem in problems:
            gap_item_id = None
            gap_slug = problem.get("gap_slug")
            if gap_slug:
                cursor.execute("select id from gap_item where slug = %s", (gap_slug,))
                row = cursor.fetchone()
                if row:
                    gap_item_id = row[0]
            cursor.execute(
                """
                insert into item_problem_link (
                  item_id, gap_item_id, problem_label, why_this_item_helps,
                  source_kind, overall_score, evidence_payload, derived_version, updated_at
                )
                values (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, now())
                """,
                (
                    item_id,
                    gap_item_id,
                    problem["problem_label"],
                    problem["why_this_item_helps"],
                    problem["source_kind"],
                    problem.get("overall_score"),
                    json.dumps(problem.get("evidence_payload", {})),
                    ItemMaterializer.DERIVATION_VERSION,
                ),
            )

    def _replace_item_comparisons(
        self,
        cursor: Any,
        item_ids: Iterable[Any],
        contexts: Dict[Any, ItemContext],
    ) -> None:
        item_ids = list(item_ids)
        if not item_ids:
            return
        cursor.execute("delete from item_comparison where item_id = any(%s)", (item_ids,))
        all_contexts = list(contexts.values())
        for context in all_contexts:
            literature_comparisons = self._build_literature_comparisons(context, all_contexts)
            if literature_comparisons:
                comparisons = literature_comparisons
            else:
                comparisons = sorted(
                    (
                        self._build_comparison(context, candidate)
                        for candidate in all_contexts
                        if candidate.item_id != context.item_id
                    ),
                    key=lambda comparison: comparison["score"],
                    reverse=True,
                )[:3]
            for comparison in comparisons:
                if comparison["score"] <= 0:
                    continue
                cursor.execute(
                    """
                    insert into item_comparison (
                      item_id, related_item_id, relation_type, summary, strengths,
                      weaknesses, overlap_reasons, evidence_payload, derived_version, updated_at
                    )
                    values (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s, now())
                    """,
                    (
                        context.item_id,
                        comparison["related_item_id"],
                        comparison["relation_type"],
                        comparison["summary"],
                        json.dumps(comparison["strengths"]),
                        json.dumps(comparison["weaknesses"]),
                        json.dumps(comparison["overlap_reasons"]),
                        json.dumps(comparison["evidence_payload"]),
                        self.DERIVATION_VERSION,
                    ),
                )

    def _build_literature_comparisons(
        self,
        context: ItemContext,
        all_contexts: Sequence[ItemContext],
    ) -> List[Dict[str, Any]]:
        alternative_statements = self._collect_literature_statements(
            context,
            freeform_key="alternatives",
        )
        if not alternative_statements:
            return []
        extracted_strengths = self._collect_structured_values(context, "strengths")[:3]
        extracted_limitations = self._collect_structured_values(context, "limitations")[:3]
        comparisons: List[Dict[str, Any]] = []
        for candidate in all_contexts:
            if candidate.item_id == context.item_id:
                continue
            matched_statements = [
                statement
                for statement in alternative_statements
                if self._text_mentions_item(statement["text"], candidate)
            ]
            if not matched_statements:
                continue
            summary = "; ".join(
                _dedupe_preserving_order(statement["text"] for statement in matched_statements)
            )
            comparisons.append(
                {
                    "related_item_id": candidate.item_id,
                    "relation_type": "source_stated_alternative",
                    "summary": summary,
                    "strengths": extracted_strengths,
                    "weaknesses": extracted_limitations,
                    "overlap_reasons": ["source-stated alternative in extracted literature"],
                    "evidence_payload": self._build_literature_payload(
                        matched_statements,
                        extra={"match_basis": "name_or_synonym_mention"},
                    ),
                    "score": 100 + len(matched_statements),
                }
            )
        return comparisons

    def _build_comparison(self, context: ItemContext, candidate: ItemContext) -> Dict[str, Any]:
        overlap_reasons = []
        if context.item_type == candidate.item_type:
            overlap_reasons.append("same top-level item type")
        shared_processes = sorted(set(context.target_processes).intersection(candidate.target_processes))
        if shared_processes:
            overlap_reasons.append("shared target processes: " + ", ".join(shared_processes))
        shared_mechanisms = sorted(set(context.mechanisms).intersection(candidate.mechanisms))
        if shared_mechanisms:
            overlap_reasons.append("shared mechanisms: " + ", ".join(shared_mechanisms))
        if (
            context.primary_input_modality
            and context.primary_input_modality == candidate.primary_input_modality
        ):
            overlap_reasons.append(f"same primary input modality: {context.primary_input_modality}")

        score = len(overlap_reasons) + len(shared_processes)
        strengths = self._comparison_strengths(context, candidate)
        weaknesses = self._comparison_strengths(candidate, context)
        summary = (
            f"{context.canonical_name} and {candidate.canonical_name} address a similar problem space"
            + (f" because they share {', '.join(shared_processes)}." if shared_processes else ".")
        )
        return {
            "related_item_id": candidate.item_id,
            "relation_type": "alternative_solution",
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "overlap_reasons": overlap_reasons,
            "evidence_payload": {"shared_processes": shared_processes, "shared_mechanisms": shared_mechanisms},
            "score": score,
        }

    @staticmethod
    def _text_mentions_item(text: str, candidate: ItemContext) -> bool:
        normalized_text = _strip_inline_markup(text).casefold()
        labels = [candidate.canonical_name, *candidate.synonyms]
        for label in labels:
            cleaned_label = _strip_inline_markup(label).strip().casefold()
            if len(cleaned_label) < 4:
                continue
            if "/" in cleaned_label or "-" in cleaned_label:
                if cleaned_label in normalized_text:
                    return True
                continue
            pattern = rf"(?<![a-z0-9]){re.escape(cleaned_label)}(?![a-z0-9])"
            if re.search(pattern, normalized_text):
                return True
        return False

    def _comparison_strengths(self, left: ItemContext, right: ItemContext) -> List[str]:
        strengths: List[str] = []
        left_rep = self._derive_replication_summary(left)
        right_rep = self._derive_replication_summary(right)
        left_text = left.text_blob
        right_text = right.text_blob
        if (left_rep["replication_score"] or 0) > (right_rep["replication_score"] or 0) + 0.1:
            strengths.append("appears more independently replicated")
        if (left_rep["practicality_score"] or 0) > (right_rep["practicality_score"] or 0) + 0.1:
            strengths.append("looks easier to implement in practice")
        if self._derive_cofactor_dependency(right_text) == "requires_exogenous_cofactor" and (
            self._derive_cofactor_dependency(left_text) != "requires_exogenous_cofactor"
        ):
            strengths.append("may avoid an exogenous cofactor requirement")
        if "single-chain" in left_text or "single chain" in left_text:
            if "single-chain" not in right_text and "single chain" not in right_text:
                strengths.append("may reduce component-count burden")
        return _dedupe_preserving_order(strengths)

    @staticmethod
    def _upsert_replication_summary(cursor: Any, item_id: Any, summary: Dict[str, Any]) -> None:
        cursor.execute(
            """
            insert into replication_summary (
              item_id, score_version, primary_paper_count, independent_primary_paper_count,
              distinct_last_author_clusters, distinct_institutions, distinct_biological_contexts,
              years_since_first_report, downstream_application_count, orphan_tool_flag,
              practicality_penalties, evidence_strength_score, replication_score,
              practicality_score, translatability_score, computed_at, explanation
            )
            values (
              %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
              %s::jsonb, %s, %s, %s, %s, now(), %s::jsonb
            )
            on conflict (item_id) do update
            set
              score_version = excluded.score_version,
              primary_paper_count = excluded.primary_paper_count,
              independent_primary_paper_count = excluded.independent_primary_paper_count,
              distinct_last_author_clusters = excluded.distinct_last_author_clusters,
              distinct_institutions = excluded.distinct_institutions,
              distinct_biological_contexts = excluded.distinct_biological_contexts,
              years_since_first_report = excluded.years_since_first_report,
              downstream_application_count = excluded.downstream_application_count,
              orphan_tool_flag = excluded.orphan_tool_flag,
              practicality_penalties = excluded.practicality_penalties,
              evidence_strength_score = excluded.evidence_strength_score,
              replication_score = excluded.replication_score,
              practicality_score = excluded.practicality_score,
              translatability_score = excluded.translatability_score,
              computed_at = excluded.computed_at,
              explanation = excluded.explanation
            """,
            (
                item_id,
                summary["score_version"],
                summary["primary_paper_count"],
                summary["independent_primary_paper_count"],
                summary["distinct_last_author_clusters"],
                summary["distinct_institutions"],
                summary["distinct_biological_contexts"],
                summary["years_since_first_report"],
                summary["downstream_application_count"],
                summary["orphan_tool_flag"],
                json.dumps(summary["practicality_penalties"]),
                summary["evidence_strength_score"],
                summary["replication_score"],
                summary["practicality_score"],
                summary["translatability_score"],
                json.dumps(summary["explanation"]),
            ),
        )
