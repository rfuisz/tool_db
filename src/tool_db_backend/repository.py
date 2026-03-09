import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from tool_db_backend.config import Settings

logger = logging.getLogger(__name__)
from tool_db_backend.gap_linking import GAP_LINK_SCORE_VERSION
from dataclasses import dataclass, field

from tool_db_backend.models import (
    ApprovedItemClaim,
    ApprovedItemEvidence,
    ApprovedItemEvidenceSnippet,
    ApprovedItemSourceDocument,
    CanonicalClaim,
    CanonicalClaimMetric,
    ExtractedWorkflowSummary,
    FirstPassExplainer,
    FirstPassEntityDetail,
    FirstPassEntitySummary,
    FirstPassEvidenceSnippet,
    FirstPassClaim,
    FirstPassItemDetail,
    FirstPassItemSummary,
    FirstPassSourceDocument,
    FirstPassWorkflowObservation,
    FirstPassWorkflowStageObservation,
    FirstPassWorkflowStepObservation,
    GapCapabilityDetail,
    GapCandidateTool,
    GapDetail,
    GapFieldSummary,
    GapResourceSummary,
    GapSummary,
    ItemAggregateResponse,
    ItemAggregateTypeBucket,
    ItemBrowse,
    ItemBrowseResponse,
    ItemDetail,
    ItemComparison,
    ItemExplainer,
    ItemFacet,
    ItemProblemLink,
    ItemSummary,
    ReplicationSummaryRecord,
    SourceRegistryEntry,
    SourceDocumentRecord,
    ValidationMetric,
    ValidationObservationRecord,
    ValidationRollupRecord,
    VocabularyPayload,
    WorkflowDetail,
    WorkflowSummary,
)


@dataclass
class ItemBrowseFilters:
    q: Optional[str] = None
    item_types: List[str] = field(default_factory=list)
    mechanisms: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    families: List[str] = field(default_factory=list)
    maturity_stages: List[str] = field(default_factory=list)
    statuses: List[str] = field(default_factory=list)
    has_independent_replication: Optional[bool] = None
    has_mouse_in_vivo_validation: Optional[bool] = None
    has_therapeutic_use: Optional[bool] = None
    sort: str = "name"
    limit: int = 20
    offset: int = 0


def _dedupe_preserving_order(values: List[str]) -> List[str]:
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


class KnowledgeRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_item_browse(self) -> List[ItemBrowse]:
        if self._should_use_database():
            try:
                return self._list_item_browse_from_database()
            except Exception:
                logger.exception("Database item-browse listing failed, falling back to files")
        return [self._item_browse_from_detail(self._get_item_from_files(summary.slug)) for summary in self.list_items()]

    def list_item_browse_filtered(self, filters: ItemBrowseFilters) -> ItemBrowseResponse:
        if self._should_use_database():
            return self._list_item_browse_filtered_from_database(filters)
        all_items = self.list_item_browse()
        total = len(all_items)
        start = min(filters.offset, total)
        end = min(start + filters.limit, total)
        return ItemBrowseResponse(total=total, limit=filters.limit, offset=filters.offset, items=all_items[start:end])

    def get_item_aggregates(self) -> ItemAggregateResponse:
        if self._should_use_database():
            return self._get_item_aggregates_from_database()
        all_items = self.list_item_browse()
        return self._compute_aggregates_from_items(all_items)

    def list_items(self) -> List[ItemSummary]:
        if self._should_use_database():
            try:
                return self._list_items_from_database()
            except Exception:
                logger.exception("Database item listing failed, falling back to files")
        return self._list_items_from_files()

    def get_item(self, slug: str) -> ItemDetail:
        if self._should_use_database():
            try:
                item = self._get_item_from_database(slug)
                if item is not None:
                    return item
            except Exception:
                logger.exception("Database item detail failed for slug=%s, falling back to files", slug)
        return self._get_item_from_files(slug)

    def list_gaps(self) -> List[GapSummary]:
        if self._should_use_database():
            try:
                return self._list_gaps_from_database()
            except Exception:
                logger.exception("Database gap listing failed")
        return []

    def get_gap(self, slug: str) -> GapDetail:
        if self._should_use_database():
            try:
                gap = self._get_gap_from_database(slug)
                if gap is not None:
                    return gap
            except Exception:
                logger.exception("Database gap detail failed for slug=%s", slug)
        raise FileNotFoundError(slug)

    def list_workflows(self) -> List[WorkflowSummary]:
        if self._should_use_database():
            try:
                return self._list_workflows_from_database()
            except Exception:
                logger.exception("Database workflow listing failed, falling back to files")
        return self._list_workflows_from_files()

    def get_workflow(self, slug: str) -> WorkflowDetail:
        if self._should_use_database():
            try:
                workflow = self._get_workflow_from_database(slug)
                if workflow is not None:
                    return workflow
            except Exception:
                logger.exception("Database workflow detail failed for slug=%s, falling back to files", slug)
        return self._get_workflow_from_files(slug)

    def list_extracted_workflows(self) -> List[ExtractedWorkflowSummary]:
        if not self._should_use_database():
            return []
        return self._list_extracted_workflows_from_database()

    def get_vocabularies(self) -> VocabularyPayload:
        vocab_path = self.settings.schema_root / "canonical" / "controlled_vocabularies.v1.json"
        data = json.loads(vocab_path.read_text())
        version = data.get("version", "unknown")
        return VocabularyPayload(version=version, data=data)

    def get_source_registry(self) -> List[SourceRegistryEntry]:
        registry_path = self.settings.repo_root / "db" / "seeds" / "source_registry.v1.json"
        data = json.loads(registry_path.read_text())
        return [SourceRegistryEntry(**entry) for entry in data]

    def list_first_pass_entities(self, limit: int = 5000) -> List[FirstPassEntitySummary]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    with alias_rows as (
                      select
                        e.candidate_type,
                        e.slug,
                        alias
                      from extracted_item_candidate e
                      cross join lateral unnest(e.aliases) as alias
                    )
                    select
                      e.candidate_type,
                      e.slug,
                      min(e.canonical_name) as canonical_name,
                      min(e.item_type) filter (where e.item_type is not null and e.item_type <> '') as item_type,
                      min(e.matched_slug) filter (where e.matched_slug is not null and e.matched_slug <> '') as matched_slug,
                      count(distinct e.source_document_id) as source_document_count,
                      count(distinct l.extracted_claim_candidate_id) as claim_count,
                      coalesce(array_agg(distinct alias_rows.alias) filter (where alias_rows.alias is not null and alias_rows.alias <> ''), '{}'::text[]) as aliases,
                      coalesce(
                        array(
                          select evidence_preview_text
                          from (
                            select distinct
                              e2.evidence_text as evidence_preview_text,
                              s2.publication_year,
                              s2.title
                            from extracted_item_candidate e2
                            join source_document s2 on s2.id = e2.source_document_id
                            where e2.slug = e.slug
                              and e2.candidate_type = e.candidate_type
                              and e2.evidence_text is not null
                              and e2.evidence_text <> ''
                          ) evidence_preview_rows
                          order by publication_year desc nulls last, title asc, evidence_preview_text asc
                          limit 3
                        ),
                        '{}'::text[]
                      ) as evidence_previews,
                      coalesce(
                        array(
                          select claim_preview_text
                          from (
                            select distinct
                              coalesce(
                                nullif(c2.source_locator->>'quoted_text', ''),
                                c2.claim_text_normalized
                              ) as claim_preview_text,
                              s2.publication_year,
                              c2.claim_type,
                              c2.claim_text_normalized
                            from extracted_claim_candidate c2
                            join extracted_claim_subject_candidate l2 on l2.extracted_claim_candidate_id = c2.id
                            join extracted_item_candidate e2 on e2.id = l2.extracted_item_candidate_id
                            join source_document s2 on s2.id = c2.source_document_id
                            where e2.slug = e.slug
                              and e2.candidate_type = e.candidate_type
                              and coalesce(
                                nullif(c2.source_locator->>'quoted_text', ''),
                                c2.claim_text_normalized
                              ) <> ''
                          ) claim_preview_rows
                          order by publication_year desc nulls last, claim_type asc, claim_text_normalized asc
                          limit 3
                        ),
                        '{}'::text[]
                      ) as claim_previews
                    from extracted_item_candidate e
                    left join extracted_claim_subject_candidate l on l.extracted_item_candidate_id = e.id
                    left join alias_rows on alias_rows.slug = e.slug and alias_rows.candidate_type = e.candidate_type
                    where (
                      e.candidate_type <> 'toolkit_item'
                      or (
                        e.matched_item_id is null
                        and not exists (
                          select 1
                          from toolkit_item ti
                          where ti.slug = e.slug
                        )
                      )
                    )
                      and (
                        e.candidate_type <> 'workflow_template'
                        or not exists (
                          select 1
                          from workflow_template wt
                          where wt.slug = e.slug
                        )
                      )
                    group by e.candidate_type, e.slug
                    order by source_document_count desc, claim_count desc, canonical_name asc, e.slug asc
                    limit %s
                    """,
                    (limit,),
                )
                return [
                    FirstPassEntitySummary(
                        candidate_type=row[0],
                        slug=row[1],
                        canonical_name=row[2],
                        item_type=row[3],
                        matched_slug=row[4],
                        source_document_count=row[5],
                        claim_count=row[6],
                        aliases=list(row[7] or []),
                        evidence_preview=(row[8][0] if row[8] else None),
                        evidence_previews=list(row[8] or []),
                        claim_previews=list(row[9] or []),
                    )
                    for row in cursor.fetchall()
                ]

    def list_first_pass_items(self, limit: int = 5000) -> List[FirstPassItemSummary]:
        return [
            FirstPassItemSummary(**summary.model_dump())
            for summary in self.list_first_pass_entities(limit=limit)
            if summary.candidate_type == "toolkit_item"
        ]

    def get_first_pass_entity(self, candidate_type: str, slug: str) -> FirstPassEntityDetail:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    with alias_rows as (
                      select alias
                      from extracted_item_candidate e
                      cross join lateral unnest(e.aliases) as alias
                      where e.slug = %s and e.candidate_type = %s
                    )
                    select
                      e.slug,
                      min(e.canonical_name) as canonical_name,
                      min(e.item_type) filter (where e.item_type is not null and e.item_type <> '') as item_type,
                      min(e.matched_slug) filter (where e.matched_slug is not null and e.matched_slug <> '') as matched_slug,
                      count(distinct e.source_document_id) as source_document_count,
                      count(distinct l.extracted_claim_candidate_id) as claim_count,
                      coalesce(array_agg(distinct alias_rows.alias) filter (where alias_rows.alias is not null and alias_rows.alias <> ''), '{}'::text[]) as aliases
                    from extracted_item_candidate e
                    left join extracted_claim_subject_candidate l on l.extracted_item_candidate_id = e.id
                    left join alias_rows on true
                    where e.slug = %s and e.candidate_type = %s
                      and (
                        e.candidate_type <> 'toolkit_item'
                        or (
                          e.matched_item_id is null
                          and not exists (
                            select 1
                            from toolkit_item ti
                            where ti.slug = e.slug
                          )
                        )
                      )
                      and (
                        e.candidate_type <> 'workflow_template'
                        or not exists (
                          select 1
                          from workflow_template wt
                          where wt.slug = e.slug
                        )
                      )
                    group by e.slug
                    """,
                    (slug, candidate_type, slug, candidate_type),
                )
                row = cursor.fetchone()
                if row is None:
                    raise FileNotFoundError(slug)

                cursor.execute(
                    """
                    select distinct
                      s.id,
                      s.title,
                      s.source_type::text,
                      s.publication_year,
                      s.journal_or_source,
                      s.doi,
                      s.pmid
                    from extracted_item_candidate e
                    join source_document s on s.id = e.source_document_id
                    where e.slug = %s and e.candidate_type = %s
                      and (
                        e.candidate_type <> 'toolkit_item'
                        or (
                          e.matched_item_id is null
                          and not exists (
                            select 1
                            from toolkit_item ti
                            where ti.slug = e.slug
                          )
                        )
                      )
                      and (
                        e.candidate_type <> 'workflow_template'
                        or not exists (
                          select 1
                          from workflow_template wt
                          where wt.slug = e.slug
                        )
                      )
                    order by s.publication_year desc nulls last, s.title asc
                    """,
                    (slug, candidate_type),
                )
                source_documents = [
                    FirstPassSourceDocument(
                        id=str(doc_row[0]),
                        title=doc_row[1],
                        source_type=doc_row[2],
                        publication_year=doc_row[3],
                        journal_or_source=doc_row[4],
                        doi=doc_row[5],
                        pmid=doc_row[6],
                    )
                    for doc_row in cursor.fetchall()
                ]

                cursor.execute(
                    """
                    select distinct
                      c.id,
                      c.claim_type,
                      c.claim_text_normalized,
                      c.polarity,
                      c.source_locator,
                      c.metrics,
                      s.id,
                      s.title,
                      s.source_type::text,
                      s.publication_year,
                      s.journal_or_source,
                      s.doi,
                      s.pmid
                    from extracted_claim_candidate c
                    join extracted_claim_subject_candidate l on l.extracted_claim_candidate_id = c.id
                    join extracted_item_candidate e on e.id = l.extracted_item_candidate_id
                    join source_document s on s.id = c.source_document_id
                    where e.slug = %s
                      and e.candidate_type = %s
                      and (
                        e.candidate_type <> 'toolkit_item'
                        or (
                          e.matched_item_id is null
                          and not exists (
                            select 1
                            from toolkit_item ti
                            where ti.slug = e.slug
                          )
                        )
                      )
                      and (
                        e.candidate_type <> 'workflow_template'
                        or not exists (
                          select 1
                          from workflow_template wt
                          where wt.slug = e.slug
                        )
                      )
                    order by s.publication_year desc nulls last, c.claim_type asc, c.claim_text_normalized asc
                    """,
                    (slug, candidate_type),
                )
                claims = [
                    FirstPassClaim(
                        id=str(claim_row[0]),
                        claim_type=claim_row[1],
                        claim_text_normalized=claim_row[2],
                        polarity=claim_row[3],
                        source_locator=claim_row[4] or {},
                        metrics=claim_row[5] or [],
                        source_document=FirstPassSourceDocument(
                            id=str(claim_row[6]),
                            title=claim_row[7],
                            source_type=claim_row[8],
                            publication_year=claim_row[9],
                            journal_or_source=claim_row[10],
                            doi=claim_row[11],
                            pmid=claim_row[12],
                        ),
                    )
                    for claim_row in cursor.fetchall()
                ]

                cursor.execute(
                    """
                    select distinct
                      e.evidence_text,
                      s.id,
                      s.title,
                      s.source_type::text,
                      s.publication_year,
                      s.journal_or_source,
                      s.doi,
                      s.pmid
                    from extracted_item_candidate e
                    join source_document s on s.id = e.source_document_id
                    where e.slug = %s
                      and e.candidate_type = %s
                      and (
                        e.candidate_type <> 'toolkit_item'
                        or (
                          e.matched_item_id is null
                          and not exists (
                            select 1
                            from toolkit_item ti
                            where ti.slug = e.slug
                          )
                        )
                      )
                      and (
                        e.candidate_type <> 'workflow_template'
                        or not exists (
                          select 1
                          from workflow_template wt
                          where wt.slug = e.slug
                        )
                      )
                      and e.evidence_text is not null
                      and e.evidence_text <> ''
                    order by s.publication_year desc nulls last, s.title asc, e.evidence_text asc
                    limit 20
                    """,
                    (slug, candidate_type),
                )
                evidence_snippets = [
                    FirstPassEvidenceSnippet(
                        text=snippet_row[0],
                        source_document=self._map_first_pass_source_document(snippet_row, 1),
                    )
                    for snippet_row in cursor.fetchall()
                ]

                cursor.execute(
                    """
                    select
                      e.raw_payload,
                      s.id,
                      s.title,
                      s.source_type::text,
                      s.publication_year,
                      s.journal_or_source,
                      s.doi,
                      s.pmid
                    from extracted_item_candidate e
                    join source_document s on s.id = e.source_document_id
                    where e.slug = %s
                      and e.candidate_type = %s
                      and (
                        e.candidate_type <> 'toolkit_item'
                        or (
                          e.matched_item_id is null
                          and not exists (
                            select 1
                            from toolkit_item ti
                            where ti.slug = e.slug
                          )
                        )
                      )
                      and (
                        e.candidate_type <> 'workflow_template'
                        or not exists (
                          select 1
                          from workflow_template wt
                          where wt.slug = e.slug
                        )
                      )
                    order by s.publication_year desc nulls last, s.title asc
                    """,
                    (slug, candidate_type),
                )
                freeform_explainers = [
                    explainer
                    for explainers_for_row in (
                        self._extract_first_pass_explainers(explainer_row)
                        for explainer_row in cursor.fetchall()
                    )
                    for explainer in explainers_for_row
                ]

                cursor.execute(
                    """
                    select
                      o.raw_payload,
                      s.id,
                      s.title,
                      s.source_type::text,
                      s.publication_year,
                      s.journal_or_source,
                      s.doi,
                      s.pmid
                    from extracted_item_candidate e
                    join extracted_workflow_observation o on (
                      o.workflow_candidate_id = e.id
                      or (o.packet_fingerprint = e.packet_fingerprint and coalesce(o.workflow_local_id, '') = e.local_id)
                    )
                    join source_document s on s.id = o.source_document_id
                    where e.slug = %s and e.candidate_type = %s
                    order by s.publication_year desc nulls last, coalesce(o.local_id, '') asc
                    """,
                    (slug, candidate_type),
                )
                workflow_observations = [
                    self._map_first_pass_workflow_observation(workflow_row)
                    for workflow_row in cursor.fetchall()
                ]

                cursor.execute(
                    """
                    select
                      stage.raw_payload,
                      s.id,
                      s.title,
                      s.source_type::text,
                      s.publication_year,
                      s.journal_or_source,
                      s.doi,
                      s.pmid
                    from extracted_item_candidate e
                    join extracted_workflow_stage_observation stage on (
                      stage.workflow_candidate_id = e.id
                      or (stage.packet_fingerprint = e.packet_fingerprint and coalesce(stage.workflow_local_id, '') = e.local_id)
                    )
                    join source_document s on s.id = stage.source_document_id
                    where e.slug = %s and e.candidate_type = %s
                    order by
                      s.publication_year desc nulls last,
                      stage.stage_order asc,
                      stage.stage_name asc
                    """,
                    (slug, candidate_type),
                )
                workflow_stage_observations = [
                    self._map_first_pass_workflow_stage_observation(stage_row)
                    for stage_row in cursor.fetchall()
                ]

                cursor.execute(
                    """
                    select
                      step.raw_payload,
                      s.id,
                      s.title,
                      s.source_type::text,
                      s.publication_year,
                      s.journal_or_source,
                      s.doi,
                      s.pmid
                    from extracted_item_candidate e
                    join extracted_workflow_step_observation step on (
                      step.workflow_candidate_id = e.id
                      or (step.packet_fingerprint = e.packet_fingerprint and coalesce(step.workflow_local_id, '') = e.local_id)
                    )
                    join source_document s on s.id = step.source_document_id
                    where e.slug = %s and e.candidate_type = %s
                    order by
                      s.publication_year desc nulls last,
                      step.step_order asc,
                      step.step_name asc
                    """,
                    (slug, candidate_type),
                )
                workflow_step_observations = [
                    self._map_first_pass_workflow_step_observation(step_row)
                    for step_row in cursor.fetchall()
                ]

        return FirstPassEntityDetail(
            candidate_type=candidate_type,
            slug=row[0],
            canonical_name=row[1],
            item_type=row[2],
            matched_slug=row[3],
            source_document_count=row[4],
            claim_count=row[5],
            aliases=list(row[6] or []),
            evidence_preview=evidence_snippets[0].text if evidence_snippets else None,
            evidence_previews=[snippet.text for snippet in evidence_snippets[:3]],
            claim_previews=[
                claim.source_locator.get("quoted_text") or claim.claim_text_normalized
                for claim in claims[:3]
            ],
            evidence_snippets=evidence_snippets,
            source_documents=source_documents,
            claims=claims,
            freeform_explainers=freeform_explainers,
            workflow_observations=workflow_observations,
            workflow_stage_observations=workflow_stage_observations,
            workflow_step_observations=workflow_step_observations,
        )

    def get_first_pass_item(self, slug: str) -> FirstPassItemDetail:
        detail = self.get_first_pass_entity("toolkit_item", slug)
        return FirstPassItemDetail(**detail.model_dump())

    @staticmethod
    def _fetch_item_approval_evidence(
        cursor: Any, item_id: Any, item_slug: str
    ) -> Optional[ApprovedItemEvidence]:
        where_clause = """
            where e.candidate_type = 'toolkit_item'
              and (
                e.matched_item_id = %s
                or e.matched_slug = %s
                or e.slug = %s
              )
        """
        params = (item_id, item_slug, item_slug)

        cursor.execute(
            f"""
            select
              coalesce(array_agg(distinct e.slug) filter (where e.slug is not null and e.slug <> ''), '{{}}'::text[]) as matched_first_pass_slugs,
              count(distinct e.source_document_id) as source_document_count,
              count(distinct c.id) as claim_count
            from extracted_item_candidate e
            left join extracted_claim_subject_candidate l on l.extracted_item_candidate_id = e.id
            left join extracted_claim_candidate c on c.id = l.extracted_claim_candidate_id
            {where_clause}
            """,
            params,
        )
        summary_row = cursor.fetchone()
        if summary_row is None:
            return None

        matched_first_pass_slugs = list(summary_row[0] or [])
        source_document_count = int(summary_row[1] or 0)
        claim_count = int(summary_row[2] or 0)
        if not matched_first_pass_slugs and source_document_count == 0 and claim_count == 0:
            return None

        cursor.execute(
            f"""
            select distinct
              s.id,
              s.title,
              s.source_type::text,
              s.publication_year,
              s.journal_or_source,
              s.doi,
              s.pmid
            from extracted_item_candidate e
            join source_document s on s.id = e.source_document_id
            {where_clause}
            order by s.publication_year desc nulls last, s.title asc
            """,
            params,
        )
        source_documents = [
            ApprovedItemSourceDocument(
                id=str(row[0]),
                title=row[1],
                source_type=row[2],
                publication_year=row[3],
                journal_or_source=row[4],
                doi=row[5],
                pmid=row[6],
            )
            for row in cursor.fetchall()
        ]

        cursor.execute(
            f"""
            select distinct
              e.evidence_text,
              s.id,
              s.title,
              s.source_type::text,
              s.publication_year,
              s.journal_or_source,
              s.doi,
              s.pmid
            from extracted_item_candidate e
            join source_document s on s.id = e.source_document_id
            {where_clause}
              and e.evidence_text is not null
              and e.evidence_text <> ''
            order by s.publication_year desc nulls last, s.title asc, e.evidence_text asc
            limit 12
            """,
            params,
        )
        evidence_snippets = [
            ApprovedItemEvidenceSnippet(
                text=row[0],
                source_document=ApprovedItemSourceDocument(
                    id=str(row[1]),
                    title=row[2],
                    source_type=row[3],
                    publication_year=row[4],
                    journal_or_source=row[5],
                    doi=row[6],
                    pmid=row[7],
                ),
            )
            for row in cursor.fetchall()
        ]

        cursor.execute(
            f"""
            select distinct
              c.id,
              c.claim_type,
              c.claim_text_normalized,
              c.polarity,
              c.source_locator,
              c.metrics,
              s.id,
              s.title,
              s.source_type::text,
              s.publication_year,
              s.journal_or_source,
              s.doi,
              s.pmid
            from extracted_claim_candidate c
            join extracted_claim_subject_candidate l on l.extracted_claim_candidate_id = c.id
            join extracted_item_candidate e on e.id = l.extracted_item_candidate_id
            join source_document s on s.id = c.source_document_id
            {where_clause}
            order by s.publication_year desc nulls last, c.claim_type asc, c.claim_text_normalized asc
            limit 20
            """,
            params,
        )
        claims = [
            ApprovedItemClaim(
                id=str(row[0]),
                claim_type=row[1],
                claim_text_normalized=row[2],
                polarity=row[3],
                source_locator=row[4] or {},
                metrics=row[5] or [],
                source_document=ApprovedItemSourceDocument(
                    id=str(row[6]),
                    title=row[7],
                    source_type=row[8],
                    publication_year=row[9],
                    journal_or_source=row[10],
                    doi=row[11],
                    pmid=row[12],
                ),
            )
            for row in cursor.fetchall()
        ]

        return ApprovedItemEvidence(
            matched_first_pass_slugs=matched_first_pass_slugs,
            source_document_count=source_document_count,
            claim_count=claim_count,
            evidence_snippets=evidence_snippets,
            source_documents=source_documents,
            claims=claims,
        )

    def _list_items_from_files(self) -> List[ItemSummary]:
        items = []
        items_root = self.settings.knowledge_root / "items"
        for structured_path in sorted(items_root.glob("*/structured.yaml")):
            data = self._read_yaml(structured_path)
            items.append(
                ItemSummary(
                    slug=data["slug"],
                    canonical_name=data["canonical_name"],
                    item_type=data["item_type"],
                    status=data["status"],
                    family=data.get("family"),
                    summary=data.get("summary"),
                    first_publication_year=data.get("first_publication_year"),
                    primary_input_modality=data.get("primary_input_modality"),
                    primary_output_modality=data.get("primary_output_modality"),
                )
            )
        return items

    def _get_item_from_files(self, slug: str) -> ItemDetail:
        item_dir = self.settings.knowledge_root / "items" / slug
        structured = self._read_yaml(item_dir / "structured.yaml")
        return ItemDetail(
            slug=structured["slug"],
            canonical_name=structured["canonical_name"],
            item_type=structured["item_type"],
            status=structured["status"],
            family=structured.get("family"),
            summary=structured.get("summary"),
            first_publication_year=structured.get("first_publication_year"),
            primary_input_modality=structured.get("primary_input_modality"),
            primary_output_modality=structured.get("primary_output_modality"),
            maturity_stage=structured.get("maturity_stage"),
            synonyms=structured.get("synonyms", []),
            components=structured.get("components", []),
            mechanisms=structured.get("mechanisms", []),
            techniques=structured.get("techniques", []),
            target_processes=structured.get("target_processes", []),
            parent_items=[],
            child_items=[],
            external_ids=structured.get("external_ids", {}),
            source_status=structured.get("source_status", {}),
            citation_candidates=structured.get("citation_candidates", []),
            workflow_recommendations=structured.get("workflow_recommendations", []),
            extracted_workflows=[],
            claims=[],
            validation_rollup=None,
            validations=[],
            replication_summary=None,
            item_facets=[],
            explainers=[],
            comparisons=[],
            problem_links=[],
            approval_evidence=None,
            index_markdown=self._read_text(item_dir / "index.md"),
            evidence_markdown=self._read_text(item_dir / "evidence.md"),
            replication_markdown=self._read_text(item_dir / "replication.md"),
            workflow_fit_markdown=self._read_text(item_dir / "workflow-fit.md"),
        )

    def _list_workflows_from_files(self) -> List[WorkflowSummary]:
        workflows = []
        workflow_root = self.settings.knowledge_root / "workflows"
        for structured_path in sorted(workflow_root.glob("*/structured.yaml")):
            data = self._read_yaml(structured_path)
            workflows.append(
                WorkflowSummary(
                    slug=data["slug"],
                    name=data["name"],
                    workflow_family=data["workflow_family"],
                    objective=data["objective"],
                    throughput_class=data.get("throughput_class"),
                )
            )
        return workflows

    def _get_workflow_from_files(self, slug: str) -> WorkflowDetail:
        workflow_dir = self.settings.knowledge_root / "workflows" / slug
        structured = self._read_yaml(workflow_dir / "structured.yaml")
        return WorkflowDetail(
            slug=structured["slug"],
            name=structured["name"],
            workflow_family=structured["workflow_family"],
            objective=structured["objective"],
            throughput_class=structured.get("throughput_class"),
            protocol_family=structured.get("protocol_family"),
            engineered_system_family=structured.get("engineered_system_family"),
            why_workflow_works=structured.get("why_workflow_works"),
            priority_logic=structured.get("priority_logic"),
            validation_strategy=structured.get("validation_strategy"),
            recommended_for=structured.get("recommended_for", []),
            default_parallelization_assumption=structured.get("default_parallelization_assumption"),
            mechanisms=structured.get("mechanisms", []),
            techniques=structured.get("techniques", []),
            design_goals=structured.get("design_goals", []),
            item_roles=structured.get("item_roles", []),
            stage_templates=structured.get("stage_templates", []),
            step_templates=structured.get("step_templates", []),
            assumption_notes=structured.get("assumption_notes", []),
            index_markdown=self._read_text(workflow_dir / "index.md"),
        )

    def _list_items_from_database(self) -> List[ItemSummary]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      slug,
                      canonical_name,
                      item_type::text,
                      status::text,
                      family,
                      summary,
                      first_publication_year,
                      primary_input_modality::text,
                      primary_output_modality::text
                    from toolkit_item
                    order by canonical_name asc, slug asc
                    """
                )
                return [
                    ItemSummary(
                        slug=row[0],
                        canonical_name=row[1],
                        item_type=row[2],
                        status=row[3],
                        family=row[4],
                        summary=row[5],
                        first_publication_year=row[6],
                        primary_input_modality=row[7],
                        primary_output_modality=row[8],
                    )
                    for row in cursor.fetchall()
                ]

    def _list_item_browse_from_database(self) -> List[ItemBrowse]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      id,
                      slug,
                      canonical_name,
                      item_type::text,
                      status::text,
                      family,
                      summary,
                      first_publication_year,
                      primary_input_modality::text,
                      primary_output_modality::text,
                      maturity_stage::text
                    from toolkit_item
                    order by canonical_name asc, slug asc
                    """
                )
                rows = cursor.fetchall()

                browse_by_id: Dict[Any, Dict[str, Any]] = {}
                ordered_item_ids: List[Any] = []
                for row in rows:
                    item_id = row[0]
                    ordered_item_ids.append(item_id)
                    browse_by_id[item_id] = {
                        "slug": row[1],
                        "canonical_name": row[2],
                        "item_type": row[3],
                        "status": row[4],
                        "family": row[5],
                        "summary": row[6],
                        "first_publication_year": row[7],
                        "primary_input_modality": row[8],
                        "primary_output_modality": row[9],
                        "maturity_stage": row[10],
                        "synonyms": [],
                        "components": [],
                        "mechanisms": [],
                        "techniques": [],
                        "target_processes": [],
                        "validation_rollup": None,
                        "replication_summary": None,
                    }

                if not ordered_item_ids:
                    return []

                for item_id, value in self._fetch_grouped_scalar_lists(
                    cursor,
                    """
                    select item_id, synonym
                    from item_synonym
                    order by synonym asc
                    """,
                ).items():
                    if item_id in browse_by_id:
                        browse_by_id[item_id]["synonyms"] = value

                for item_id, value in self._fetch_grouped_scalar_lists(
                    cursor,
                    """
                    select parent_item_id, component.canonical_name
                    from item_component ic
                    join toolkit_item component on component.id = ic.component_item_id
                    order by component.canonical_name asc
                    """,
                ).items():
                    if item_id in browse_by_id:
                        browse_by_id[item_id]["components"] = value

                for item_id, value in self._fetch_grouped_scalar_lists(
                    cursor,
                    """
                    select item_id, mechanism_name
                    from item_mechanism
                    order by mechanism_name asc
                    """,
                ).items():
                    if item_id in browse_by_id:
                        browse_by_id[item_id]["mechanisms"] = value

                for item_id, value in self._fetch_grouped_scalar_lists(
                    cursor,
                    """
                    select item_id, technique_name
                    from item_technique
                    order by technique_name asc
                    """,
                ).items():
                    if item_id in browse_by_id:
                        browse_by_id[item_id]["techniques"] = value

                for item_id, value in self._fetch_grouped_scalar_lists(
                    cursor,
                    """
                    select item_id, target_process
                    from item_target_process
                    order by target_process asc
                    """,
                ).items():
                    if item_id in browse_by_id:
                        browse_by_id[item_id]["target_processes"] = value

                cursor.execute(
                    """
                    select
                      item_id,
                      has_cell_free_validation,
                      has_bacterial_validation,
                      has_mammalian_cell_validation,
                      has_mouse_in_vivo_validation,
                      has_human_clinical_validation,
                      has_therapeutic_use,
                      has_independent_replication
                    from item_validation_rollup_v1
                    """
                )
                for row in cursor.fetchall():
                    item_id = row[0]
                    if item_id not in browse_by_id:
                        continue
                    browse_by_id[item_id]["validation_rollup"] = ValidationRollupRecord(
                        has_cell_free_validation=bool(row[1]),
                        has_bacterial_validation=bool(row[2]),
                        has_mammalian_cell_validation=bool(row[3]),
                        has_mouse_in_vivo_validation=bool(row[4]),
                        has_human_clinical_validation=bool(row[5]),
                        has_therapeutic_use=bool(row[6]),
                        has_independent_replication=bool(row[7]),
                    )

                cursor.execute(
                    """
                    select
                      item_id,
                      score_version,
                      primary_paper_count,
                      independent_primary_paper_count,
                      distinct_last_author_clusters,
                      distinct_institutions,
                      distinct_biological_contexts,
                      years_since_first_report,
                      downstream_application_count,
                      orphan_tool_flag,
                      practicality_penalties,
                      evidence_strength_score,
                      replication_score,
                      practicality_score,
                      translatability_score,
                      explanation
                    from replication_summary
                    """
                )
                for row in cursor.fetchall():
                    item_id = row[0]
                    if item_id not in browse_by_id:
                        continue
                    browse_by_id[item_id]["replication_summary"] = ReplicationSummaryRecord(
                        score_version=row[1],
                        primary_paper_count=row[2],
                        independent_primary_paper_count=row[3],
                        distinct_last_author_clusters=row[4],
                        distinct_institutions=row[5],
                        distinct_biological_contexts=row[6],
                        years_since_first_report=row[7],
                        downstream_application_count=row[8],
                        orphan_tool_flag=bool(row[9]),
                        practicality_penalties=list(row[10] or []),
                        evidence_strength_score=float(row[11]) if row[11] is not None else None,
                        replication_score=float(row[12]) if row[12] is not None else None,
                        practicality_score=float(row[13]) if row[13] is not None else None,
                        translatability_score=float(row[14]) if row[14] is not None else None,
                        explanation=row[15] or {},
                    )

                return [ItemBrowse(**browse_by_id[item_id]) for item_id in ordered_item_ids]

    def _list_item_browse_filtered_from_database(self, filters: ItemBrowseFilters) -> ItemBrowseResponse:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                where_clauses: List[str] = []
                params: List[Any] = []

                if filters.q:
                    where_clauses.append("""(
                        ti.canonical_name ILIKE %s
                        OR ti.summary ILIKE %s
                        OR ti.family ILIKE %s
                        OR EXISTS (SELECT 1 FROM item_synonym s WHERE s.item_id = ti.id AND s.synonym ILIKE %s)
                        OR EXISTS (SELECT 1 FROM item_mechanism m WHERE m.item_id = ti.id AND m.mechanism_name ILIKE %s)
                        OR EXISTS (SELECT 1 FROM item_technique t WHERE t.item_id = ti.id AND t.technique_name ILIKE %s)
                        OR EXISTS (SELECT 1 FROM item_target_process tp WHERE tp.item_id = ti.id AND tp.target_process ILIKE %s)
                    )""")
                    pattern = f"%{filters.q}%"
                    params.extend([pattern] * 7)

                if filters.item_types:
                    where_clauses.append(f"ti.item_type::text = ANY(%s)")
                    params.append(filters.item_types)

                if filters.mechanisms:
                    where_clauses.append(
                        "EXISTS (SELECT 1 FROM item_mechanism m WHERE m.item_id = ti.id AND LOWER(REPLACE(m.mechanism_name, ' ', '_')) = ANY(%s))"
                    )
                    params.append([v.lower().replace(" ", "_") for v in filters.mechanisms])

                if filters.techniques:
                    where_clauses.append(
                        "EXISTS (SELECT 1 FROM item_technique t WHERE t.item_id = ti.id AND LOWER(REPLACE(t.technique_name, ' ', '_')) = ANY(%s))"
                    )
                    params.append([v.lower().replace(" ", "_") for v in filters.techniques])

                if filters.families:
                    where_clauses.append("LOWER(ti.family) = ANY(%s)")
                    params.append([v.lower() for v in filters.families])

                if filters.maturity_stages:
                    where_clauses.append("ti.maturity_stage::text = ANY(%s)")
                    params.append(filters.maturity_stages)

                if filters.statuses:
                    where_clauses.append("ti.status::text = ANY(%s)")
                    params.append(filters.statuses)

                if filters.has_independent_replication is not None:
                    where_clauses.append(
                        "EXISTS (SELECT 1 FROM item_validation_rollup_v1 vr WHERE vr.item_id = ti.id AND vr.has_independent_replication = %s)"
                    )
                    params.append(filters.has_independent_replication)

                if filters.has_mouse_in_vivo_validation is not None:
                    where_clauses.append(
                        "EXISTS (SELECT 1 FROM item_validation_rollup_v1 vr WHERE vr.item_id = ti.id AND vr.has_mouse_in_vivo_validation = %s)"
                    )
                    params.append(filters.has_mouse_in_vivo_validation)

                if filters.has_therapeutic_use is not None:
                    where_clauses.append(
                        "EXISTS (SELECT 1 FROM item_validation_rollup_v1 vr WHERE vr.item_id = ti.id AND vr.has_therapeutic_use = %s)"
                    )
                    params.append(filters.has_therapeutic_use)

                where_sql = (" AND ".join(where_clauses)) if where_clauses else "TRUE"

                sort_map = {
                    "name": "ti.canonical_name ASC, ti.slug ASC",
                    "year": "COALESCE(ti.first_publication_year, 9999) ASC, ti.canonical_name ASC",
                    "score": "COALESCE(rs.evidence_strength_score, 0) + COALESCE(rs.replication_score, 0) + COALESCE(rs.practicality_score, 0) DESC, ti.canonical_name ASC",
                    "evidence": "COALESCE(rs.evidence_strength_score, 0) DESC, ti.canonical_name ASC",
                    "replication": "COALESCE(rs.replication_score, 0) DESC, ti.canonical_name ASC",
                    "practicality": "COALESCE(rs.practicality_score, 0) DESC, ti.canonical_name ASC",
                }
                order_sql = sort_map.get(filters.sort, sort_map["name"])
                needs_rs_join = filters.sort in ("score", "evidence", "replication", "practicality")

                rs_join = "LEFT JOIN replication_summary rs ON rs.item_id = ti.id" if needs_rs_join else ""

                cursor.execute(
                    f"SELECT COUNT(*) FROM toolkit_item ti {rs_join} WHERE {where_sql}",
                    params,
                )
                total = cursor.fetchone()[0]

                limit = max(1, min(filters.limit, 500))
                offset = max(0, filters.offset)

                cursor.execute(
                    f"""
                    SELECT ti.id, ti.slug, ti.canonical_name, ti.item_type::text, ti.status::text,
                           ti.family, ti.summary, ti.first_publication_year,
                           ti.primary_input_modality::text, ti.primary_output_modality::text,
                           ti.maturity_stage::text
                    FROM toolkit_item ti
                    {rs_join}
                    WHERE {where_sql}
                    ORDER BY {order_sql}
                    LIMIT %s OFFSET %s
                    """,
                    params + [limit, offset],
                )
                rows = cursor.fetchall()

                if not rows:
                    return ItemBrowseResponse(total=total, limit=limit, offset=offset, items=[])

                browse_by_id: Dict[Any, Dict[str, Any]] = {}
                ordered_item_ids: List[Any] = []
                for row in rows:
                    item_id = row[0]
                    ordered_item_ids.append(item_id)
                    browse_by_id[item_id] = {
                        "slug": row[1], "canonical_name": row[2], "item_type": row[3],
                        "status": row[4], "family": row[5], "summary": row[6],
                        "first_publication_year": row[7], "primary_input_modality": row[8],
                        "primary_output_modality": row[9], "maturity_stage": row[10],
                        "synonyms": [], "components": [], "mechanisms": [],
                        "techniques": [], "target_processes": [],
                        "validation_rollup": None, "replication_summary": None,
                    }

                id_tuple = tuple(ordered_item_ids)
                self._hydrate_browse_relations(cursor, browse_by_id, id_tuple)

                items = [ItemBrowse(**browse_by_id[item_id]) for item_id in ordered_item_ids]
                return ItemBrowseResponse(total=total, limit=limit, offset=offset, items=items)

    def _hydrate_browse_relations(
        self, cursor: Any, browse_by_id: Dict[Any, Dict[str, Any]], item_ids: tuple
    ) -> None:
        if not item_ids:
            return

        placeholders = ",".join(["%s"] * len(item_ids))

        for table, col, key in [
            ("item_synonym", "synonym", "synonyms"),
            ("item_mechanism", "mechanism_name", "mechanisms"),
            ("item_technique", "technique_name", "techniques"),
            ("item_target_process", "target_process", "target_processes"),
        ]:
            cursor.execute(
                f"SELECT item_id, {col} FROM {table} WHERE item_id IN ({placeholders}) ORDER BY {col} ASC",
                item_ids,
            )
            for item_id, value in cursor.fetchall():
                if item_id in browse_by_id:
                    browse_by_id[item_id][key].append(value)

        cursor.execute(
            f"""
            SELECT ic.parent_item_id, component.canonical_name
            FROM item_component ic
            JOIN toolkit_item component ON component.id = ic.component_item_id
            WHERE ic.parent_item_id IN ({placeholders})
            ORDER BY component.canonical_name ASC
            """,
            item_ids,
        )
        for item_id, value in cursor.fetchall():
            if item_id in browse_by_id:
                browse_by_id[item_id]["components"].append(value)

        cursor.execute(
            f"""
            SELECT item_id, has_cell_free_validation, has_bacterial_validation,
                   has_mammalian_cell_validation, has_mouse_in_vivo_validation,
                   has_human_clinical_validation, has_therapeutic_use, has_independent_replication
            FROM item_validation_rollup_v1
            WHERE item_id IN ({placeholders})
            """,
            item_ids,
        )
        for row in cursor.fetchall():
            if row[0] in browse_by_id:
                browse_by_id[row[0]]["validation_rollup"] = ValidationRollupRecord(
                    has_cell_free_validation=bool(row[1]),
                    has_bacterial_validation=bool(row[2]),
                    has_mammalian_cell_validation=bool(row[3]),
                    has_mouse_in_vivo_validation=bool(row[4]),
                    has_human_clinical_validation=bool(row[5]),
                    has_therapeutic_use=bool(row[6]),
                    has_independent_replication=bool(row[7]),
                )

        cursor.execute(
            f"""
            SELECT item_id, score_version, primary_paper_count, independent_primary_paper_count,
                   distinct_last_author_clusters, distinct_institutions, distinct_biological_contexts,
                   years_since_first_report, downstream_application_count, orphan_tool_flag,
                   practicality_penalties, evidence_strength_score, replication_score,
                   practicality_score, translatability_score, explanation
            FROM replication_summary
            WHERE item_id IN ({placeholders})
            """,
            item_ids,
        )
        for row in cursor.fetchall():
            if row[0] in browse_by_id:
                browse_by_id[row[0]]["replication_summary"] = ReplicationSummaryRecord(
                    score_version=row[1], primary_paper_count=row[2],
                    independent_primary_paper_count=row[3], distinct_last_author_clusters=row[4],
                    distinct_institutions=row[5], distinct_biological_contexts=row[6],
                    years_since_first_report=row[7], downstream_application_count=row[8],
                    orphan_tool_flag=bool(row[9]), practicality_penalties=list(row[10] or []),
                    evidence_strength_score=float(row[11]) if row[11] is not None else None,
                    replication_score=float(row[12]) if row[12] is not None else None,
                    practicality_score=float(row[13]) if row[13] is not None else None,
                    translatability_score=float(row[14]) if row[14] is not None else None,
                    explanation=row[15] or {},
                )

    _MECHANISM_FAMILIES = [
        "heterodimerization", "oligomerization", "conformational_uncaging",
        "membrane_recruitment", "photocleavage", "dna_binding", "rna_binding",
        "degradation", "translation_control",
    ]
    _TECHNIQUE_FAMILIES = [
        "computational_design", "selection_enrichment", "directed_evolution",
        "sequence_verification", "functional_assay", "structural_characterization",
    ]

    def _get_item_aggregates_from_database(self) -> ItemAggregateResponse:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM toolkit_item")
                total_items = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT family) FROM toolkit_item WHERE family IS NOT NULL AND family != ''")
                total_families = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT AVG(evidence_strength_score) FROM replication_summary "
                    "WHERE evidence_strength_score IS NOT NULL "
                    "AND item_id NOT IN (SELECT item_id FROM replication_summary WHERE orphan_tool_flag = TRUE)"
                )
                avg_row = cursor.fetchone()
                avg_evidence = round(float(avg_row[0]), 2) if avg_row and avg_row[0] is not None else None

                cursor.execute("SELECT item_type::text, COUNT(*) FROM toolkit_item GROUP BY item_type ORDER BY COUNT(*) DESC")
                by_type = [ItemAggregateTypeBucket(value=r[0], count=r[1]) for r in cursor.fetchall()]

                cursor.execute(
                    "SELECT REPLACE(mechanism_name, ' ', '_') AS norm, COUNT(DISTINCT item_id) "
                    "FROM item_mechanism "
                    "WHERE REPLACE(mechanism_name, ' ', '_') = ANY(%s) "
                    "GROUP BY norm ORDER BY COUNT(DISTINCT item_id) DESC",
                    (self._MECHANISM_FAMILIES,),
                )
                by_mechanism = [ItemAggregateTypeBucket(value=r[0], count=r[1]) for r in cursor.fetchall()]

                cursor.execute(
                    "SELECT REPLACE(technique_name, ' ', '_') AS norm, COUNT(DISTINCT item_id) "
                    "FROM item_technique "
                    "WHERE REPLACE(technique_name, ' ', '_') = ANY(%s) "
                    "GROUP BY norm ORDER BY COUNT(DISTINCT item_id) DESC",
                    (self._TECHNIQUE_FAMILIES,),
                )
                by_technique = [ItemAggregateTypeBucket(value=r[0], count=r[1]) for r in cursor.fetchall()]

                cursor.execute("SELECT family, COUNT(*) FROM toolkit_item WHERE family IS NOT NULL AND family != '' GROUP BY family HAVING COUNT(*) >= 3 ORDER BY COUNT(*) DESC")
                by_family = [ItemAggregateTypeBucket(value=r[0], count=r[1]) for r in cursor.fetchall()]

                return ItemAggregateResponse(
                    total_items=total_items,
                    total_families=total_families,
                    avg_evidence_score=avg_evidence,
                    by_item_type=by_type,
                    by_mechanism=by_mechanism,
                    by_technique=by_technique,
                    by_family=by_family,
                )

    @classmethod
    def _compute_aggregates_from_items(cls, items: List[ItemBrowse]) -> ItemAggregateResponse:
        from collections import Counter
        type_counts: Counter[str] = Counter()
        mech_counts: Counter[str] = Counter()
        tech_counts: Counter[str] = Counter()
        family_counts: Counter[str] = Counter()
        evidence_scores: List[float] = []
        mech_set = set(cls._MECHANISM_FAMILIES)
        tech_set = set(cls._TECHNIQUE_FAMILIES)
        for item in items:
            type_counts[item.item_type] += 1
            for m in item.mechanisms:
                norm = m.replace(" ", "_")
                if norm in mech_set:
                    mech_counts[norm] += 1
            for t in item.techniques:
                norm = t.replace(" ", "_")
                if norm in tech_set:
                    tech_counts[norm] += 1
            if item.family:
                family_counts[item.family] += 1
            rs = item.replication_summary
            if rs and rs.evidence_strength_score is not None and not rs.orphan_tool_flag:
                evidence_scores.append(rs.evidence_strength_score)

        return ItemAggregateResponse(
            total_items=len(items),
            total_families=len(family_counts),
            avg_evidence_score=round(sum(evidence_scores) / len(evidence_scores), 2) if evidence_scores else None,
            by_item_type=[ItemAggregateTypeBucket(value=k, count=v) for k, v in type_counts.most_common()],
            by_mechanism=[ItemAggregateTypeBucket(value=k, count=v) for k, v in mech_counts.most_common()],
            by_technique=[ItemAggregateTypeBucket(value=k, count=v) for k, v in tech_counts.most_common()],
            by_family=[ItemAggregateTypeBucket(value=k, count=v) for k, v in family_counts.most_common() if v >= 3],
        )

    def _get_item_from_database(self, slug: str) -> Optional[ItemDetail]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      id,
                      slug,
                      canonical_name,
                      item_type::text,
                      status::text,
                      family,
                      summary,
                      first_publication_year,
                      primary_input_modality::text,
                      primary_output_modality::text,
                      maturity_stage::text,
                      external_ids
                    from toolkit_item
                    where slug = %s
                    """,
                    (slug,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None

                item_id = row[0]
                claims = self._fetch_item_claims(cursor, item_id)
                validation_rollup = self._fetch_validation_rollup(cursor, item_id)
                validations = self._fetch_validation_observations(cursor, item_id)
                citations = self._fetch_item_citations(cursor, item_id, claims=claims, validations=validations)
                replication_summary = self._fetch_replication_summary(cursor, item_id)
                item_facets = self._fetch_item_facets(cursor, item_id)
                explainers = self._fetch_item_explainers(cursor, item_id)
                comparisons = self._fetch_item_comparisons(cursor, item_id)
                problem_links = self._fetch_item_problem_links(cursor, item_id)
                workflow_recommendations = self._fetch_item_workflow_recommendations(cursor, item_id)
                extracted_workflows = self._fetch_extracted_workflows(cursor, item_id, row[1])
                approval_evidence = self._fetch_item_approval_evidence(cursor, item_id, row[1])
                markdown = self._get_item_markdown(
                    slug, row[2], row[6],
                    workflow_recommendations=workflow_recommendations,
                    extracted_workflows=extracted_workflows,
                )

                return ItemDetail(
                    slug=row[1],
                    canonical_name=row[2],
                    item_type=row[3],
                    status=row[4],
                    family=row[5],
                    summary=row[6],
                    first_publication_year=row[7],
                    primary_input_modality=row[8],
                    primary_output_modality=row[9],
                    maturity_stage=row[10],
                    synonyms=self._fetch_scalar_list(
                        cursor,
                        "select synonym from item_synonym where item_id = %s order by synonym asc",
                        item_id,
                    ),
                    components=self._fetch_item_components(cursor, item_id),
                    mechanisms=self._fetch_scalar_list(
                        cursor,
                        "select distinct mechanism_name from item_mechanism where item_id = %s order by mechanism_name asc",
                        item_id,
                    ),
                    techniques=self._fetch_scalar_list(
                        cursor,
                        "select distinct technique_name from item_technique where item_id = %s order by technique_name asc",
                        item_id,
                    ),
                    target_processes=self._fetch_scalar_list(
                        cursor,
                        "select target_process from item_target_process where item_id = %s order by target_process asc",
                        item_id,
                    ),
                    parent_items=self._fetch_parent_item_links(cursor, item_id),
                    child_items=self._fetch_child_item_links(cursor, item_id),
                    external_ids=row[11] or {},
                    source_status={},
                    citation_candidates=citations,
                    workflow_recommendations=workflow_recommendations,
                    extracted_workflows=extracted_workflows,
                    claims=claims,
                    validation_rollup=validation_rollup,
                    validations=validations,
                    replication_summary=replication_summary,
                    item_facets=item_facets,
                    explainers=explainers,
                    comparisons=comparisons,
                    problem_links=problem_links,
                    approval_evidence=approval_evidence,
                    index_markdown=markdown["index_markdown"],
                    evidence_markdown=markdown["evidence_markdown"],
                    replication_markdown=markdown["replication_markdown"],
                    workflow_fit_markdown=markdown["workflow_fit_markdown"],
                )

    def _list_gaps_from_database(self) -> List[GapSummary]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      gi.external_gap_item_id,
                      coalesce(gi.slug, gi.payload->'external_ids'->>'gap_map_slug') as slug,
                      gi.title,
                      gf.external_gap_field_id,
                      gf.slug,
                      gf.name,
                      count(gic.gap_capability_id) as capability_count
                    from gap_item gi
                    left join gap_field gf on gf.id = gi.gap_field_id
                    left join gap_item_capability gic on gic.gap_item_id = gi.id
                    group by gi.id, gf.id
                    order by gi.title asc
                    """
                )
                return [
                    GapSummary(
                        external_gap_item_id=row[0],
                        slug=row[1],
                        title=row[2],
                        field=(
                            GapFieldSummary(
                                external_gap_field_id=row[3],
                                slug=row[4],
                                name=row[5],
                            )
                            if row[3]
                            else None
                        ),
                        capability_count=row[6],
                    )
                    for row in cursor.fetchall()
                ]

    def _get_gap_from_database(self, slug: str) -> Optional[GapDetail]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      gi.id,
                      gi.external_gap_item_id,
                      coalesce(gi.slug, gi.payload->'external_ids'->>'gap_map_slug') as slug,
                      gi.title,
                      gi.payload,
                      gf.external_gap_field_id,
                      gf.slug,
                      gf.name
                    from gap_item gi
                    left join gap_field gf on gf.id = gi.gap_field_id
                    where coalesce(gi.slug, gi.payload->'external_ids'->>'gap_map_slug') = %s
                       or gi.external_gap_item_id = %s
                    """,
                    (slug, slug),
                )
                row = cursor.fetchone()
                if row is None:
                    return None

                gap_item_id = row[0]
                payload = row[4] or {}
                database_fields = payload.get("database_fields", {})

                cursor.execute(
                    """
                    select
                      gc.external_gap_capability_id,
                      gc.slug,
                      gc.name,
                      gc.payload
                    from gap_item_capability gic
                    join gap_capability gc on gc.id = gic.gap_capability_id
                    where gic.gap_item_id = %s
                    order by gc.name asc
                    """,
                    (gap_item_id,),
                )
                capability_rows = cursor.fetchall()

                capabilities: List[GapCapabilityDetail] = []
                for capability_row in capability_rows:
                    capability_payload = capability_row[3] or {}
                    cursor.execute(
                        """
                        select
                          gr.external_gap_resource_id,
                          gr.title,
                          gr.payload
                        from gap_capability_resource gcr
                        join gap_resource gr on gr.id = gcr.gap_resource_id
                        join gap_capability gc on gc.id = gcr.gap_capability_id
                        where gc.external_gap_capability_id = %s
                        order by gr.title asc
                        """,
                        (capability_row[0],),
                    )
                    resources = [
                        GapResourceSummary(
                            external_gap_resource_id=resource_row[0],
                            title=resource_row[1],
                            url=(resource_row[2] or {}).get("url"),
                            summary=(resource_row[2] or {}).get("summary"),
                            types=(resource_row[2] or {}).get("types") or [],
                        )
                        for resource_row in cursor.fetchall()
                    ]
                    capabilities.append(
                        GapCapabilityDetail(
                            external_gap_capability_id=capability_row[0],
                            slug=capability_row[1],
                            name=capability_row[2],
                            description=capability_payload.get("description"),
                            tags=capability_payload.get("tags") or [],
                            resources=resources,
                        )
                    )

                candidate_tools = self._fetch_gap_candidate_tools(cursor, gap_item_id)

                return GapDetail(
                    external_gap_item_id=row[1],
                    slug=row[2],
                    title=row[3],
                    field=(
                        GapFieldSummary(
                            external_gap_field_id=row[5],
                            slug=row[6],
                            name=row[7],
                        )
                        if row[5]
                        else None
                    ),
                    capability_count=len(capabilities),
                    description=database_fields.get("description")
                    or payload.get("evidence_text")
                    or (
                        payload.get("claims", [{}])[0].get("claim_text_normalized")
                        if payload.get("claims")
                        else None
                    ),
                    tags=database_fields.get("tags") or [],
                    capabilities=capabilities,
                    candidate_tools=candidate_tools,
                )

    def _list_workflows_from_database(self) -> List[WorkflowSummary]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      slug,
                      name,
                      workflow_family::text,
                      objective,
                      throughput_class::text
                    from workflow_template
                    order by name asc, slug asc
                    """
                )
                return [
                    WorkflowSummary(
                        slug=row[0],
                        name=row[1],
                        workflow_family=row[2],
                        objective=row[3],
                        throughput_class=row[4],
                    )
                    for row in cursor.fetchall()
                ]

    def _get_workflow_from_database(self, slug: str) -> Optional[WorkflowDetail]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    select
                      id,
                      slug,
                      name,
                      workflow_family::text,
                      objective,
                      throughput_class::text,
                      protocol_family,
                      engineered_system_family,
                      why_workflow_works,
                      priority_logic,
                      validation_strategy,
                      recommended_for,
                      default_parallelization_assumption
                    from workflow_template
                    where slug = %s
                    """,
                    (slug,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None

                workflow_id = row[0]
                index_markdown = self._get_workflow_index_markdown(slug, row[2], row[4])
                return WorkflowDetail(
                    slug=row[1],
                    name=row[2],
                    workflow_family=row[3],
                    objective=row[4],
                    throughput_class=row[5],
                    protocol_family=row[6],
                    engineered_system_family=row[7],
                    why_workflow_works=row[8],
                    priority_logic=row[9],
                    validation_strategy=row[10],
                    recommended_for=self._split_multiline_text(row[11]),
                    default_parallelization_assumption=row[12],
                    mechanisms=self._fetch_workflow_mechanisms(cursor, workflow_id),
                    techniques=self._fetch_workflow_techniques(cursor, workflow_id),
                    design_goals=self._fetch_workflow_design_goals(cursor, workflow_id),
                    item_roles=self._fetch_workflow_item_roles(cursor, workflow_id),
                    stage_templates=self._fetch_workflow_stages(cursor, workflow_id),
                    step_templates=self._fetch_workflow_steps(cursor, workflow_id),
                    assumption_notes=self._fetch_workflow_assumptions(cursor, workflow_id),
                    index_markdown=index_markdown,
                )

    def _list_extracted_workflows_from_database(self) -> List[ExtractedWorkflowSummary]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    select
                      ewo.id, ewo.packet_fingerprint, ewo.local_id,
                      ewo.workflow_local_id, ewo.workflow_objective,
                      ewo.protocol_family, ewo.engineered_system_family,
                      ewo.target_mechanisms, ewo.target_techniques,
                      ewo.why_workflow_works, ewo.workflow_priority_logic,
                      ewo.validation_strategy, ewo.decision_gate_strategy,
                      ewo.evidence_text,
                      sd.id, sd.title, sd.source_type::text,
                      sd.publication_year, sd.journal_or_source, sd.doi, sd.pmid
                    from extracted_workflow_observation ewo
                    join source_document sd on sd.id = ewo.source_document_id
                    order by sd.publication_year desc nulls last, sd.title asc
                """)
                workflow_rows = cursor.fetchall()
                results: List[ExtractedWorkflowSummary] = []
                for row in workflow_rows:
                    wf_id = str(row[0])
                    packet_fp = row[1]
                    workflow_local_id = row[3]

                    cursor.execute(
                        """
                        select stage_name, stage_kind, stage_order, search_modality,
                          input_candidate_count, output_candidate_count,
                          selection_basis, counterselection_basis,
                          enriches_for_axes, guards_against_axes,
                          why_stage_exists, advance_criteria, bottleneck_risk
                        from extracted_workflow_stage_observation
                        where packet_fingerprint = %s
                          and (workflow_local_id is not distinct from %s)
                        order by stage_order asc
                        """,
                        (packet_fp, workflow_local_id),
                    )
                    stages = [
                        {
                            "stage_name": s[0],
                            "stage_kind": s[1],
                            "stage_order": s[2],
                            "search_modality": s[3],
                            "input_candidate_count": s[4],
                            "output_candidate_count": s[5],
                            "selection_basis": s[6],
                            "counterselection_basis": s[7],
                            "enriches_for_axes": list(s[8] or []),
                            "guards_against_axes": list(s[9] or []),
                            "why_stage_exists": s[10],
                            "advance_criteria": s[11],
                            "bottleneck_risk": s[12],
                        }
                        for s in cursor.fetchall()
                    ]

                    obs_local_id = row[2]
                    cursor.execute(
                        """
                        select step_name, step_order, step_type, stage_name,
                          item_local_ids, item_role, purpose, why_this_step_now,
                          advance_criteria, input_artifact, output_artifact,
                          duration_hours, success
                        from extracted_workflow_step_observation
                        where packet_fingerprint = %s
                          and (
                            workflow_observation_local_id = %s
                            or (workflow_local_id is not distinct from %s
                                and workflow_observation_local_id is null)
                          )
                        order by step_order asc
                        """,
                        (packet_fp, obs_local_id, workflow_local_id),
                    )
                    steps = [
                        {
                            "step_name": st[0],
                            "step_order": st[1],
                            "step_type": st[2],
                            "stage_name": st[3],
                            "item_local_ids": list(st[4] or []),
                            "item_role": st[5],
                            "purpose": st[6],
                            "why_this_step_now": st[7],
                            "advance_criteria": st[8],
                            "input_artifact": st[9],
                            "output_artifact": st[10],
                            "duration_hours": st[11],
                            "success": st[12],
                        }
                        for st in cursor.fetchall()
                    ]

                    cursor.execute(
                        """
                        select eic.slug, eic.canonical_name,
                          coalesce(ti.canonical_name, eic.canonical_name) as display_name,
                          ti.slug as item_slug
                        from extracted_item_candidate eic
                        left join toolkit_item ti on ti.id = eic.matched_item_id
                        where eic.packet_fingerprint = %s
                          and eic.candidate_type = 'toolkit_item'
                        order by eic.canonical_name asc
                        """,
                        (packet_fp,),
                    )
                    involved_items = [
                        {
                            "slug": it[0],
                            "canonical_name": it[1],
                            "display_name": it[2],
                            "item_slug": it[3],
                        }
                        for it in cursor.fetchall()
                    ]

                    results.append(
                        ExtractedWorkflowSummary(
                            workflow_id=wf_id,
                            workflow_objective=row[4],
                            protocol_family=row[5],
                            engineered_system_family=row[6],
                            target_mechanisms=list(row[7] or []),
                            target_techniques=list(row[8] or []),
                            why_workflow_works=row[9],
                            workflow_priority_logic=row[10],
                            validation_strategy=row[11],
                            decision_gate_strategy=row[12],
                            evidence_text=row[13],
                            source_document={
                                "id": str(row[14]),
                                "title": row[15],
                                "source_type": row[16],
                                "publication_year": row[17],
                                "journal_or_source": row[18],
                                "doi": row[19],
                                "pmid": row[20],
                            },
                            stages=stages,
                            steps=steps,
                            involved_items=involved_items,
                        )
                    )
                return results

    def _fetch_item_citations(
        self,
        cursor: Any,
        item_id: Any,
        *,
        claims: Optional[List[CanonicalClaim]] = None,
        validations: Optional[List[ValidationObservationRecord]] = None,
    ) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              ic.citation_role::text,
              ic.importance_rank,
              ic.why_this_matters,
              sd.id,
              sd.title,
              case
                when sd.is_retracted then 'retracted'
                else 'curated'
              end as status,
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
        citations = [
            {
                "citation_role": row[0],
                "importance_rank": row[1],
                "why_this_matters": row[2],
                "source_document_id": str(row[3]),
                "label": row[4],
                "status": row[5],
                "source_type": row[6],
                "publication_year": row[7],
                "url": row[8],
                "doi": row[9],
                "pmid": row[10],
                "is_retracted": row[11],
            }
            for row in cursor.fetchall()
        ]
        if citations:
            return self._dedupe_item_citations(citations)
        return self._derive_item_citations_from_evidence(claims or [], validations or [])

    @staticmethod
    def _citation_identity_key(citation: Dict[str, Any]) -> str:
        doi = str(citation.get("doi") or "").strip().casefold()
        if doi:
            return f"doi:{doi}"
        pmid = str(citation.get("pmid") or "").strip().casefold()
        if pmid:
            return f"pmid:{pmid}"
        label = str(citation.get("label") or "").strip().casefold()
        publication_year = citation.get("publication_year")
        source_type = str(citation.get("source_type") or "").strip().casefold()
        return f"title:{label}|year:{publication_year}|type:{source_type}"

    @classmethod
    def _dedupe_item_citations(cls, citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        role_priority = {
            "structural": 0,
            "benchmark": 1,
            "independent_validation": 2,
            "negative_result": 3,
            "therapeutic": 4,
            "protocol": 5,
            "best_review": 6,
            "foundational": 7,
            "database_reference": 8,
        }
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for citation in citations:
            grouped.setdefault(cls._citation_identity_key(citation), []).append(citation)

        deduped: List[Dict[str, Any]] = []
        for group in grouped.values():
            best = min(
                group,
                key=lambda citation: (
                    citation.get("importance_rank") if citation.get("importance_rank") is not None else 10_000,
                    role_priority.get(str(citation.get("citation_role") or ""), 99),
                    str(citation.get("source_document_id") or ""),
                ),
            ).copy()
            rationale_parts = _dedupe_preserving_order(
                str(citation.get("why_this_matters") or "").strip() for citation in group
            )
            if rationale_parts:
                best["why_this_matters"] = " ".join(rationale_parts)
            deduped.append(best)

        deduped.sort(
            key=lambda citation: (
                citation.get("importance_rank") if citation.get("importance_rank") is not None else 10_000,
                str(citation.get("label") or ""),
            )
        )
        for index, citation in enumerate(deduped, start=1):
            citation["importance_rank"] = index
        return deduped

    @staticmethod
    def _derive_item_citations_from_evidence(
        claims: List[CanonicalClaim],
        validations: List[ValidationObservationRecord],
    ) -> List[Dict[str, Any]]:
        source_rows: Dict[str, Dict[str, Any]] = {}
        for claim in claims:
            source_id = claim.source_document.id
            row = source_rows.setdefault(
                source_id,
                {
                    "document": claim.source_document,
                    "claim_count": 0,
                    "validation_count": 0,
                    "claim_types": set(),
                    "example_texts": [],
                },
            )
            row["claim_count"] += 1
            row["claim_types"].add(claim.claim_type)
            quoted_text = str(claim.source_locator.get("quoted_text") or "").strip()
            if quoted_text:
                row["example_texts"].append(quoted_text)
            elif claim.claim_text_normalized:
                row["example_texts"].append(claim.claim_text_normalized)
        for validation in validations:
            source_id = validation.source_document.id
            row = source_rows.setdefault(
                source_id,
                {
                    "document": validation.source_document,
                    "claim_count": 0,
                    "validation_count": 0,
                    "claim_types": set(),
                    "example_texts": [],
                },
            )
            row["validation_count"] += 1
            if validation.notes:
                row["example_texts"].append(validation.notes)

        def sort_key(row: Dict[str, Any]) -> tuple:
            doc = row["document"]
            return (
                -row["validation_count"],
                -row["claim_count"],
                -(doc.publication_year or 0),
                doc.title,
            )

        sorted_rows = sorted(source_rows.values(), key=sort_key)
        citations: List[Dict[str, Any]] = []
        primary_primary_seen = False
        for index, row in enumerate(sorted_rows, start=1):
            document = row["document"]
            claim_types = row["claim_types"]
            if document.source_type == "review":
                citation_role = "best_review"
            elif document.source_type == "benchmark":
                citation_role = "benchmark"
            elif "structure_determination" in claim_types or "structural_characterization" in claim_types:
                citation_role = "structural"
            elif row["validation_count"] > 0 and primary_primary_seen:
                citation_role = "independent_validation"
            else:
                citation_role = "foundational"
            if document.source_type in {"primary_paper", "preprint", "trial_record"}:
                primary_primary_seen = True
            example_text = str((row["example_texts"] or [""])[0]).strip()
            why_this_matters = (
                f"Derived from {row['claim_count']} linked claims"
                + (
                    f" and {row['validation_count']} validation observations"
                    if row["validation_count"] > 0
                    else ""
                )
                + (f". Example evidence: {example_text}" if example_text else ".")
            )
            citations.append(
                {
                    "citation_role": citation_role,
                    "importance_rank": index,
                    "why_this_matters": why_this_matters,
                    "source_document_id": document.id,
                    "label": document.title,
                    "status": "retracted" if document.is_retracted else "derived_from_claims",
                    "source_type": document.source_type,
                    "publication_year": document.publication_year,
                    "url": document.journal_or_source,
                    "doi": document.doi,
                    "pmid": document.pmid,
                    "is_retracted": document.is_retracted,
                }
            )
        return citations

    def _fetch_item_claims(self, cursor: Any, item_id: Any) -> List[CanonicalClaim]:
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
        claims: List[CanonicalClaim] = []
        for row in cursor.fetchall():
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
                CanonicalClaimMetric(
                    metric_name=metric_row[0],
                    operator=metric_row[1],
                    value_num=metric_row[2],
                    value_text=metric_row[3],
                    unit=metric_row[4],
                    condition_text=metric_row[5],
                )
                for metric_row in cursor.fetchall()
            ]
            claims.append(
                CanonicalClaim(
                    id=str(claim_id),
                    claim_type=row[1],
                    claim_text_normalized=row[2],
                    polarity=row[3],
                    needs_review=row[4],
                    context=row[5] or {},
                    source_locator=row[6] or {},
                    source_document=SourceDocumentRecord(
                        id=str(row[7]),
                        title=row[8],
                        source_type=row[9],
                        publication_year=row[10],
                        journal_or_source=row[11],
                        doi=row[12],
                        pmid=row[13],
                        is_retracted=row[14],
                    ),
                    metrics=metrics,
                )
            )
        return claims

    def _fetch_validation_rollup(self, cursor: Any, item_id: Any) -> Optional[ValidationRollupRecord]:
        cursor.execute(
            """
            select
              has_cell_free_validation,
              has_bacterial_validation,
              has_mammalian_cell_validation,
              has_mouse_in_vivo_validation,
              has_human_clinical_validation,
              has_therapeutic_use,
              has_independent_replication
            from item_validation_rollup_v1
            where item_id = %s
            """,
            (item_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return ValidationRollupRecord(
            has_cell_free_validation=bool(row[0]),
            has_bacterial_validation=bool(row[1]),
            has_mammalian_cell_validation=bool(row[2]),
            has_mouse_in_vivo_validation=bool(row[3]),
            has_human_clinical_validation=bool(row[4]),
            has_therapeutic_use=bool(row[5]),
            has_independent_replication=bool(row[6]),
        )

    def _fetch_validation_observations(self, cursor: Any, item_id: Any) -> List[ValidationObservationRecord]:
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
        observations: List[ValidationObservationRecord] = []
        for row in cursor.fetchall():
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
                ValidationMetric(
                    metric_name=metric_row[0],
                    value_num=metric_row[1],
                    unit=metric_row[2],
                    qualifier=metric_row[3],
                    condition_text=metric_row[4],
                )
                for metric_row in cursor.fetchall()
            ]
            observations.append(
                ValidationObservationRecord(
                    id=str(validation_id),
                    observation_type=row[1],
                    biological_system_level=row[2],
                    species=row[3],
                    strain_or_model=row[4],
                    cell_type=row[5],
                    tissue=row[6],
                    delivery_mode=row[7],
                    cargo_or_effector=row[8],
                    construct_name=row[9],
                    assay_description=row[10],
                    success_outcome=row[11],
                    independent_lab_cluster_id=row[12],
                    institution_cluster_id=row[13],
                    notes=row[14],
                    source_locator=row[15] or {},
                    source_document=SourceDocumentRecord(
                        id=str(row[16]),
                        title=row[17],
                        source_type=row[18],
                        publication_year=row[19],
                        journal_or_source=row[20],
                        doi=row[21],
                        pmid=row[22],
                        is_retracted=row[23],
                    ),
                    metrics=metrics,
                )
            )
        return observations

    def _fetch_replication_summary(self, cursor: Any, item_id: Any) -> Optional[ReplicationSummaryRecord]:
        cursor.execute(
            """
            select
              score_version,
              primary_paper_count,
              independent_primary_paper_count,
              distinct_last_author_clusters,
              distinct_institutions,
              distinct_biological_contexts,
              years_since_first_report,
              downstream_application_count,
              orphan_tool_flag,
              practicality_penalties,
              evidence_strength_score,
              replication_score,
              practicality_score,
              translatability_score,
              explanation
            from replication_summary
            where item_id = %s
            """,
            (item_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return ReplicationSummaryRecord(
            score_version=row[0],
            primary_paper_count=row[1],
            independent_primary_paper_count=row[2],
            distinct_last_author_clusters=row[3],
            distinct_institutions=row[4],
            distinct_biological_contexts=row[5],
            years_since_first_report=row[6],
            downstream_application_count=row[7],
            orphan_tool_flag=bool(row[8]),
            practicality_penalties=list(row[9] or []),
            evidence_strength_score=float(row[10]) if row[10] is not None else None,
            replication_score=float(row[11]) if row[11] is not None else None,
            practicality_score=float(row[12]) if row[12] is not None else None,
            translatability_score=float(row[13]) if row[13] is not None else None,
            explanation=row[14] or {},
        )

    def _fetch_item_facets(self, cursor: Any, item_id: Any) -> List[ItemFacet]:
        cursor.execute(
            """
            select facet_name, facet_value, evidence_note
            from item_facet
            where item_id = %s
            order by facet_name asc, facet_value asc
            """,
            (item_id,),
        )
        return [
            ItemFacet(facet_name=row[0], facet_value=row[1], evidence_note=row[2])
            for row in cursor.fetchall()
        ]

    def _fetch_item_explainers(self, cursor: Any, item_id: Any) -> List[ItemExplainer]:
        cursor.execute(
            """
            select explainer_kind, title, body, evidence_payload
            from item_explainer
            where item_id = %s
            order by explainer_kind asc
            """,
            (item_id,),
        )
        return [
            ItemExplainer(
                explainer_kind=row[0],
                title=row[1],
                body=row[2],
                evidence_payload=row[3] or {},
            )
            for row in cursor.fetchall()
        ]

    def _fetch_item_comparisons(self, cursor: Any, item_id: Any) -> List[ItemComparison]:
        cursor.execute(
            """
            select
              ti.slug,
              ti.canonical_name,
              ic.relation_type,
              ic.summary,
              ic.strengths,
              ic.weaknesses,
              ic.overlap_reasons,
              ic.evidence_payload
            from item_comparison ic
            join toolkit_item ti on ti.id = ic.related_item_id
            where ic.item_id = %s
            order by ti.canonical_name asc
            """,
            (item_id,),
        )
        return [
            ItemComparison(
                related_item_slug=row[0],
                related_item_name=row[1],
                relation_type=row[2],
                summary=row[3],
                strengths=list(row[4] or []),
                weaknesses=list(row[5] or []),
                overlap_reasons=list(row[6] or []),
                evidence_payload=row[7] or {},
            )
            for row in cursor.fetchall()
        ]

    def _fetch_item_problem_links(self, cursor: Any, item_id: Any) -> List[ItemProblemLink]:
        cursor.execute(
            """
            select
              ipl.problem_label,
              ipl.why_this_item_helps,
              ipl.source_kind,
              gi.slug,
              gi.title,
              ipl.overall_score,
              ipl.evidence_payload
            from item_problem_link ipl
            left join gap_item gi on gi.id = ipl.gap_item_id
            where ipl.item_id = %s
            order by coalesce(ipl.overall_score, 0) desc, ipl.problem_label asc
            """,
            (item_id,),
        )
        return [
            ItemProblemLink(
                problem_label=row[0],
                why_this_item_helps=row[1],
                source_kind=row[2],
                gap_slug=row[3],
                gap_title=row[4],
                overall_score=float(row[5]) if row[5] is not None else None,
                evidence_payload=row[6] or {},
            )
            for row in cursor.fetchall()
        ]

    def _fetch_workflow_stages(self, cursor: Any, workflow_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              stage_name,
              stage_kind::text,
              stage_order,
              search_modality::text,
              input_candidate_count_typical,
              output_candidate_count_typical,
              candidate_unit,
              selection_basis,
              counterselection_basis,
              enriches_for_axes,
              guards_against_axes,
              preserves_downstream_property_axes,
              why_stage_exists,
              advance_criteria,
              decision_gate_reason,
              bottleneck_risk,
              higher_fidelity_than_previous
            from workflow_stage_template
            where workflow_template_id = %s
            order by stage_order asc
            """,
            (workflow_id,),
        )
        return [
            {
                "stage_name": row[0],
                "stage_kind": row[1],
                "stage_order": row[2],
                "search_modality": row[3],
                "input_candidate_count_typical": row[4],
                "output_candidate_count_typical": row[5],
                "candidate_unit": row[6],
                "selection_basis": row[7],
                "counterselection_basis": row[8],
                "enriches_for_axes": row[9] or [],
                "guards_against_axes": row[10] or [],
                "preserves_downstream_property_axes": row[11] or [],
                "why_stage_exists": row[12],
                "advance_criteria": row[13],
                "decision_gate_reason": row[14],
                "bottleneck_risk": row[15],
                "higher_fidelity_than_previous": row[16],
            }
            for row in cursor.fetchall()
        ]

    def _fetch_workflow_steps(self, cursor: Any, workflow_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              wst.id,
              wst.step_name,
              stage.stage_name,
              wst.step_order,
              wst.step_type::text,
              wst.purpose,
              wst.why_this_step_now,
              wst.decision_gate_reason,
              wst.advance_criteria,
              wst.failure_criteria,
              wst.validation_focus,
              wst.target_property_axes,
              wst.target_mechanisms,
              wst.target_techniques,
              wst.duration_typical_hours,
              wst.hands_on_hours,
              wst.direct_cost_usd_typical,
              wst.parallelizable,
              wst.failure_probability,
              wst.input_artifact,
              wst.output_artifact
            from workflow_step_template wst
            left join workflow_stage_template stage on stage.id = wst.workflow_stage_template_id
            where wst.workflow_template_id = %s
            order by
              coalesce(wst.step_order, 999999),
              coalesce(stage.stage_order, 999999),
              wst.step_name
            """,
            (workflow_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "step_name": row[1],
                "stage_name": row[2],
                "step_order": row[3],
                "step_type": row[4],
                "purpose": row[5],
                "why_this_step_now": row[6],
                "decision_gate_reason": row[7],
                "advance_criteria": row[8],
                "failure_criteria": row[9],
                "validation_focus": row[10],
                "target_property_axes": row[11] or [],
                "target_mechanisms": row[12] or [],
                "target_techniques": row[13] or [],
                "duration_typical_hours": float(row[14]) if row[14] is not None else None,
                "hands_on_hours": float(row[15]) if row[15] is not None else None,
                "direct_cost_usd_typical": float(row[16]) if row[16] is not None else None,
                "parallelizable": row[17],
                "failure_probability": float(row[18]) if row[18] is not None else None,
                "input_artifact": row[19],
                "output_artifact": row[20],
            }
            for row in rows
        ]

    def _fetch_workflow_assumptions(self, cursor: Any, workflow_id: Any) -> List[str]:
        cursor.execute(
            """
            select value_text
            from workflow_assumption
            where workflow_template_id = %s
              and value_text is not null
            order by assumption_name asc
            """,
            (workflow_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def _fetch_workflow_mechanisms(cursor: Any, workflow_id: Any) -> List[str]:
        cursor.execute(
            """
            select mechanism_name
            from workflow_mechanism
            where workflow_template_id = %s
            order by mechanism_name asc
            """,
            (workflow_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def _fetch_workflow_techniques(cursor: Any, workflow_id: Any) -> List[str]:
        cursor.execute(
            """
            select technique_name
            from workflow_technique
            where workflow_template_id = %s
            order by technique_name asc
            """,
            (workflow_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def _fetch_workflow_design_goals(cursor: Any, workflow_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select goal_name, goal_kind, rationale
            from workflow_design_goal
            where workflow_template_id = %s
            order by goal_kind asc, goal_name asc
            """,
            (workflow_id,),
        )
        return [
            {
                "goal_name": row[0],
                "goal_kind": row[1],
                "rationale": row[2],
            }
            for row in cursor.fetchall()
        ]

    @staticmethod
    def _fetch_workflow_item_roles(cursor: Any, workflow_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              ti.slug,
              ti.canonical_name,
              wir.role_name,
              stage.stage_name,
              step.step_name,
              wir.notes
            from workflow_item_role wir
            join toolkit_item ti on ti.id = wir.item_id
            left join workflow_stage_template stage on stage.id = wir.workflow_stage_template_id
            left join workflow_step_template step on step.id = wir.workflow_step_template_id
            where wir.workflow_template_id = %s
            order by wir.role_name asc, ti.canonical_name asc
            """,
            (workflow_id,),
        )
        return [
            {
                "item_slug": row[0],
                "item_name": row[1],
                "role_name": row[2],
                "stage_name": row[3],
                "step_name": row[4],
                "notes": row[5],
            }
            for row in cursor.fetchall()
        ]

    @staticmethod
    def _fetch_item_workflow_recommendations(cursor: Any, item_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            select
              wt.slug,
              wt.name,
              wir.role_name,
              stage.stage_name,
              step.step_name,
              wir.notes,
              wt.objective
            from workflow_item_role wir
            join workflow_template wt on wt.id = wir.workflow_template_id
            left join workflow_stage_template stage on stage.id = wir.workflow_stage_template_id
            left join workflow_step_template step on step.id = wir.workflow_step_template_id
            where wir.item_id = %s
            order by wt.name asc, wir.role_name asc, coalesce(step.step_name, '') asc
            """,
            (item_id,),
        )
        return [
            {
                "workflow_slug": row[0],
                "workflow_name": row[1],
                "role_name": row[2],
                "stage_name": row[3],
                "step_name": row[4],
                "notes": row[5],
                "objective": row[6],
            }
            for row in cursor.fetchall()
        ]

    @staticmethod
    def _fetch_extracted_workflows(cursor: Any, item_id: Any, item_slug: str) -> List[Dict[str, Any]]:
        """Fetch real workflow observations from papers that mention this item."""
        cursor.execute(
            """
            select distinct ewo.id, ewo.packet_fingerprint, ewo.local_id,
              ewo.workflow_local_id, ewo.workflow_objective,
              ewo.protocol_family, ewo.engineered_system_family,
              ewo.target_mechanisms, ewo.target_techniques,
              ewo.why_workflow_works, ewo.workflow_priority_logic,
              ewo.validation_strategy, ewo.decision_gate_strategy,
              ewo.evidence_text,
              sd.id, sd.title, sd.source_type::text,
              sd.publication_year, sd.journal_or_source, sd.doi, sd.pmid
            from extracted_workflow_observation ewo
            join source_document sd on sd.id = ewo.source_document_id
            where ewo.packet_fingerprint in (
              select packet_fingerprint
              from extracted_item_candidate
              where matched_item_id = %s
                or matched_slug = %s
                or (slug = %s and matched_item_id is null
                    and coalesce(matched_slug, '') = '')
            )
            order by sd.publication_year desc nulls last
            """,
            (item_id, item_slug, item_slug),
        )
        workflows = []
        for row in cursor.fetchall():
            packet_fp = row[1]
            obs_local_id = row[2]
            workflow_local_id = row[3]

            cursor.execute(
                """
                select stage_name, stage_kind, stage_order, search_modality,
                  input_candidate_count, output_candidate_count,
                  selection_basis, counterselection_basis,
                  enriches_for_axes, guards_against_axes,
                  why_stage_exists, advance_criteria, bottleneck_risk
                from extracted_workflow_stage_observation
                where packet_fingerprint = %s
                  and (workflow_local_id is not distinct from %s)
                order by stage_order asc
                """,
                (packet_fp, workflow_local_id),
            )
            stages = [
                {
                    "stage_name": s[0],
                    "stage_kind": s[1],
                    "stage_order": s[2],
                    "search_modality": s[3],
                    "input_candidate_count": s[4],
                    "output_candidate_count": s[5],
                    "selection_basis": s[6],
                    "counterselection_basis": s[7],
                    "enriches_for_axes": list(s[8] or []),
                    "guards_against_axes": list(s[9] or []),
                    "why_stage_exists": s[10],
                    "advance_criteria": s[11],
                    "bottleneck_risk": s[12],
                }
                for s in cursor.fetchall()
            ]

            cursor.execute(
                """
                select step_name, step_order, step_type, stage_name,
                  item_local_ids, item_role, purpose, why_this_step_now,
                  advance_criteria, input_artifact, output_artifact,
                  duration_hours, success
                from extracted_workflow_step_observation
                where packet_fingerprint = %s
                  and (
                    workflow_observation_local_id = %s
                    or (workflow_local_id is not distinct from %s
                        and workflow_observation_local_id is null)
                  )
                order by step_order asc
                """,
                (packet_fp, obs_local_id, workflow_local_id),
            )
            steps = [
                {
                    "step_name": st[0],
                    "step_order": st[1],
                    "step_type": st[2],
                    "stage_name": st[3],
                    "item_local_ids": list(st[4] or []),
                    "item_role": st[5],
                    "purpose": st[6],
                    "why_this_step_now": st[7],
                    "advance_criteria": st[8],
                    "input_artifact": st[9],
                    "output_artifact": st[10],
                    "duration_hours": st[11],
                    "success": st[12],
                }
                for st in cursor.fetchall()
            ]

            workflows.append(
                {
                    "workflow_objective": row[4],
                    "protocol_family": row[5],
                    "engineered_system_family": row[6],
                    "target_mechanisms": list(row[7] or []),
                    "target_techniques": list(row[8] or []),
                    "why_workflow_works": row[9],
                    "workflow_priority_logic": row[10],
                    "validation_strategy": row[11],
                    "decision_gate_strategy": row[12],
                    "evidence_text": row[13],
                    "source_document": {
                        "id": str(row[14]),
                        "title": row[15],
                        "source_type": row[16],
                        "publication_year": row[17],
                        "journal_or_source": row[18],
                        "doi": row[19],
                        "pmid": row[20],
                    },
                    "stages": stages,
                    "steps": steps,
                }
            )
        return workflows

    @staticmethod
    def _fetch_item_components(cursor: Any, item_id: Any) -> List[str]:
        cursor.execute(
            """
            select distinct component.canonical_name
            from item_component ic
            join toolkit_item component on component.id = ic.component_item_id
            where ic.parent_item_id = %s
            order by component.canonical_name asc
            """,
            (item_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def _fetch_child_item_links(cursor: Any, item_id: Any) -> list:
        from tool_db_backend.models import ItemRelationLink

        cursor.execute(
            """
            select distinct component.slug, component.canonical_name, component.item_type
            from item_component ic
            join toolkit_item component on component.id = ic.component_item_id
            where ic.parent_item_id = %s
            order by component.canonical_name asc
            """,
            (item_id,),
        )
        return [
            ItemRelationLink(slug=row[0], canonical_name=row[1], item_type=row[2], relation_label="component")
            for row in cursor.fetchall()
        ]

    @staticmethod
    def _fetch_parent_item_links(cursor: Any, item_id: Any) -> list:
        from tool_db_backend.models import ItemRelationLink

        cursor.execute(
            """
            select distinct parent.slug, parent.canonical_name, parent.item_type
            from item_component ic
            join toolkit_item parent on parent.id = ic.parent_item_id
            where ic.component_item_id = %s
            order by parent.canonical_name asc
            """,
            (item_id,),
        )
        return [
            ItemRelationLink(slug=row[0], canonical_name=row[1], item_type=row[2], relation_label="assembly")
            for row in cursor.fetchall()
        ]

    @staticmethod
    def _fetch_grouped_scalar_lists(cursor: Any, query: str) -> Dict[Any, List[str]]:
        cursor.execute(query)
        grouped: Dict[Any, List[str]] = {}
        for item_id, value in cursor.fetchall():
            if item_id not in grouped:
                grouped[item_id] = []
            grouped[item_id].append(value)
        return grouped

    @staticmethod
    def _fetch_scalar_list(cursor: Any, query: str, item_id: Any) -> List[str]:
        cursor.execute(query, (item_id,))
        return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def _item_browse_from_detail(detail: ItemDetail) -> ItemBrowse:
        return ItemBrowse(
            slug=detail.slug,
            canonical_name=detail.canonical_name,
            item_type=detail.item_type,
            status=detail.status,
            family=detail.family,
            summary=detail.summary,
            first_publication_year=detail.first_publication_year,
            primary_input_modality=detail.primary_input_modality,
            primary_output_modality=detail.primary_output_modality,
            maturity_stage=detail.maturity_stage,
            synonyms=detail.synonyms,
            components=detail.components,
            mechanisms=detail.mechanisms,
            techniques=detail.techniques,
            target_processes=detail.target_processes,
            validation_rollup=detail.validation_rollup,
            replication_summary=detail.replication_summary,
        )

    @staticmethod
    def _fetch_gap_candidate_tools(cursor: Any, gap_item_id: Any) -> List[GapCandidateTool]:
        cursor.execute(
            """
            select
              ti.slug,
              ti.canonical_name,
              ti.item_type::text,
              ti.summary,
              igl.overall_gap_applicability_score,
              igl.mechanistic_match_score,
              igl.context_match_score,
              igl.throughput_match_score,
              igl.time_to_first_test_score,
              igl.cost_to_first_test_score,
              igl.replication_confidence_modifier,
              igl.practicality_modifier,
              igl.translatability_modifier,
              igl.why_it_might_help,
              igl.assumptions,
              igl.missing_evidence
            from item_gap_link igl
            join toolkit_item ti on ti.id = igl.item_id
            where igl.gap_item_id = %s
              and igl.score_version = %s
            order by igl.overall_gap_applicability_score desc nulls last, ti.canonical_name asc
            """,
            (gap_item_id, GAP_LINK_SCORE_VERSION),
        )
        return [
            GapCandidateTool(
                item_slug=row[0],
                canonical_name=row[1],
                item_type=row[2],
                summary=row[3],
                overall_gap_applicability_score=float(row[4]) if row[4] is not None else None,
                mechanistic_match_score=float(row[5]) if row[5] is not None else None,
                context_match_score=float(row[6]) if row[6] is not None else None,
                throughput_match_score=float(row[7]) if row[7] is not None else None,
                time_to_first_test_score=float(row[8]) if row[8] is not None else None,
                cost_to_first_test_score=float(row[9]) if row[9] is not None else None,
                replication_confidence_modifier=float(row[10]) if row[10] is not None else None,
                practicality_modifier=float(row[11]) if row[11] is not None else None,
                translatability_modifier=float(row[12]) if row[12] is not None else None,
                why_it_might_help=row[13],
                assumptions=row[14],
                missing_evidence=row[15],
            )
            for row in cursor.fetchall()
        ]

    @staticmethod
    def _map_first_pass_source_document(row: Any, offset: int = 0) -> FirstPassSourceDocument:
        return FirstPassSourceDocument(
            id=str(row[offset]),
            title=row[offset + 1],
            source_type=row[offset + 2],
            publication_year=row[offset + 3],
            journal_or_source=row[offset + 4],
            doi=row[offset + 5],
            pmid=row[offset + 6],
        )

    @classmethod
    def _extract_first_pass_explainers(cls, row: Any) -> List[FirstPassExplainer]:
        payload = row[0] or {}
        if not isinstance(payload, dict):
            return []
        explainers = payload.get("freeform_explainers") or {}
        if not isinstance(explainers, dict):
            return []
        source_document = cls._map_first_pass_source_document(row, 1)
        ordered_keys = (
            "what_it_does",
            "resources_required",
            "problem_it_solves",
            "problem_it_does_not_solve",
            "alternatives",
        )
        results: List[FirstPassExplainer] = []
        for key in ordered_keys:
            value = explainers.get(key)
            if value is None:
                continue
            body = str(value).strip()
            if not body:
                continue
            results.append(
                FirstPassExplainer(
                    explainer_kind=key,
                    body=body,
                    source_document=source_document,
                )
            )
        return results

    @staticmethod
    def _map_first_pass_workflow_observation(row: Any) -> FirstPassWorkflowObservation:
        payload = row[0] or {}
        return FirstPassWorkflowObservation(
            local_id=str(payload.get("local_id", "")),
            workflow_local_id=payload.get("workflow_local_id"),
            workflow_objective=payload.get("workflow_objective"),
            protocol_family=payload.get("protocol_family"),
            engineered_system_family=payload.get("engineered_system_family"),
            target_property_axes=list(payload.get("target_property_axes") or []),
            target_mechanisms=list(payload.get("target_mechanisms") or []),
            target_techniques=list(payload.get("target_techniques") or []),
            why_workflow_works=payload.get("why_workflow_works"),
            workflow_priority_logic=payload.get("workflow_priority_logic"),
            validation_strategy=payload.get("validation_strategy"),
            decision_gate_strategy=payload.get("decision_gate_strategy"),
            evidence_text=payload.get("evidence_text"),
            source_locator=payload.get("source_locator") or {},
            source_document=KnowledgeRepository._map_first_pass_source_document(row, 1),
        )

    @staticmethod
    def _map_first_pass_workflow_stage_observation(row: Any) -> FirstPassWorkflowStageObservation:
        payload = row[0] or {}
        return FirstPassWorkflowStageObservation(
            local_id=str(payload.get("local_id", "")),
            workflow_local_id=payload.get("workflow_local_id"),
            stage_name=str(payload.get("stage_name", "")),
            stage_kind=str(payload.get("stage_kind", "")),
            stage_order=int(payload.get("stage_order", 0) or 0),
            search_modality=payload.get("search_modality"),
            selection_basis=payload.get("selection_basis"),
            counterselection_basis=payload.get("counterselection_basis"),
            enriches_for_axes=list(payload.get("enriches_for_axes") or []),
            guards_against_axes=list(payload.get("guards_against_axes") or []),
            preserves_downstream_property_axes=list(
                payload.get("preserves_downstream_property_axes") or []
            ),
            why_stage_exists=payload.get("why_stage_exists"),
            advance_criteria=payload.get("advance_criteria"),
            decision_gate_reason=payload.get("decision_gate_reason"),
            bottleneck_risk=payload.get("bottleneck_risk"),
            higher_fidelity_than_previous=payload.get("higher_fidelity_than_previous"),
            source_locator=payload.get("source_locator") or {},
            source_document=KnowledgeRepository._map_first_pass_source_document(row, 1),
        )

    @staticmethod
    def _map_first_pass_workflow_step_observation(row: Any) -> FirstPassWorkflowStepObservation:
        payload = row[0] or {}
        return FirstPassWorkflowStepObservation(
            local_id=str(payload.get("local_id", "")),
            workflow_local_id=payload.get("workflow_local_id"),
            workflow_observation_local_id=payload.get("workflow_observation_local_id"),
            stage_local_id=payload.get("stage_local_id"),
            stage_name=payload.get("stage_name"),
            step_name=str(payload.get("step_name", "")),
            step_order=int(payload.get("step_order", 0) or 0),
            step_type=payload.get("step_type"),
            item_local_ids=list(payload.get("item_local_ids") or []),
            item_role=payload.get("item_role"),
            purpose=payload.get("purpose"),
            why_this_step_now=payload.get("why_this_step_now"),
            decision_gate_reason=payload.get("decision_gate_reason"),
            advance_criteria=payload.get("advance_criteria"),
            failure_criteria=payload.get("failure_criteria"),
            validation_focus=payload.get("validation_focus"),
            target_property_axes=list(payload.get("target_property_axes") or []),
            target_mechanisms=list(payload.get("target_mechanisms") or []),
            target_techniques=list(payload.get("target_techniques") or []),
            input_artifact=payload.get("input_artifact"),
            output_artifact=payload.get("output_artifact"),
            duration_hours=float(payload["duration_hours"]) if payload.get("duration_hours") is not None else None,
            queue_time_hours=float(payload["queue_time_hours"]) if payload.get("queue_time_hours") is not None else None,
            direct_cost_usd=float(payload["direct_cost_usd"]) if payload.get("direct_cost_usd") is not None else None,
            success=payload.get("success"),
            source_locator=payload.get("source_locator") or {},
            source_document=KnowledgeRepository._map_first_pass_source_document(row, 1),
        )

    def _get_item_markdown(
        self,
        slug: str,
        canonical_name: str,
        summary: Optional[str],
        workflow_recommendations: Optional[List[Dict[str, Any]]] = None,
        extracted_workflows: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, str]:
        item_dir = self.settings.knowledge_root / "items" / slug
        if item_dir.exists():
            return {
                "index_markdown": self._read_text(item_dir / "index.md"),
                "evidence_markdown": self._read_text(item_dir / "evidence.md"),
                "replication_markdown": self._read_text(item_dir / "replication.md"),
                "workflow_fit_markdown": self._read_text(item_dir / "workflow-fit.md"),
            }

        summary_text = summary or "Postgres-backed canonical item record."
        workflow_body = self._build_workflow_fit_markdown(
            canonical_name, workflow_recommendations or [], extracted_workflows or [],
        )
        return {
            "index_markdown": f"# {canonical_name}\n\n{summary_text}\n",
            "evidence_markdown": f"# {canonical_name} Evidence\n\nEvidence is currently being served from the hosted Postgres canonical store.\n",
            "replication_markdown": f"# {canonical_name} Replication\n\nReplication details are currently being served from the hosted Postgres canonical store.\n",
            "workflow_fit_markdown": workflow_body,
        }

    @staticmethod
    def _build_workflow_fit_markdown(
        canonical_name: str,
        workflow_recommendations: List[Dict[str, Any]],
        extracted_workflows: List[Dict[str, Any]],
    ) -> str:
        parts: List[str] = [f"# {canonical_name} Workflows"]

        if extracted_workflows:
            for wf in extracted_workflows:
                doc = wf.get("source_document") or {}
                title = doc.get("title") or "Untitled source"
                year = doc.get("publication_year")
                header = f"{title} ({year})" if year else title
                parts.append(f"\n## {header}")

                objective = wf.get("workflow_objective")
                if objective:
                    parts.append(f"\n**Objective:** {objective}")

                why = wf.get("why_workflow_works")
                if why:
                    parts.append(f"\n**Why it works:** {why}")

                mechs = wf.get("target_mechanisms") or []
                techs = wf.get("target_techniques") or []
                if mechs:
                    parts.append(f"\n**Target mechanisms:** {', '.join(mechs)}")
                if techs:
                    parts.append(f"\n**Techniques:** {', '.join(techs)}")

                stages = wf.get("stages") or []
                if stages:
                    parts.append("\n### Stages")
                    for stage in stages:
                        name = stage.get("stage_name", "Stage")
                        kind = stage.get("stage_kind", "")
                        why_exists = stage.get("why_stage_exists") or ""
                        line = f"- **{name}** ({kind})"
                        if why_exists:
                            line += f": {why_exists}"
                        parts.append(line)

                steps = wf.get("steps") or []
                if steps:
                    parts.append("\n### Steps")
                    for step in steps:
                        name = step.get("step_name", "Step")
                        purpose = step.get("purpose") or ""
                        role = step.get("item_role") or ""
                        line = f"- **{name}**"
                        if purpose:
                            line += f": {purpose}"
                        if role:
                            line += f" (role: {role})"
                        parts.append(line)

        elif workflow_recommendations:
            parts.append("\n## Likely Fit")
            for rec in workflow_recommendations:
                notes = rec.get("notes") or rec.get("objective") or rec.get("role_name", "")
                parts.append(f"- `{rec.get('workflow_slug', '')}`: {notes}")
        else:
            parts.append("\nNo workflow evidence has been extracted from literature for this record yet.")

        return "\n".join(parts) + "\n"

    def _get_workflow_index_markdown(self, slug: str, name: str, objective: str) -> str:
        workflow_dir = self.settings.knowledge_root / "workflows" / slug
        if workflow_dir.exists():
            return self._read_text(workflow_dir / "index.md")
        return f"# {name}\n\n{objective}\n"

    @staticmethod
    def _split_multiline_text(value: Optional[str]) -> List[str]:
        if not value:
            return []
        return [line.strip() for line in value.splitlines() if line.strip()]

    def _should_use_database(self) -> bool:
        return bool(self.settings.database_url)

    def _connect(self) -> Any:
        import psycopg

        return psycopg.connect(self.settings.database_url)

    @staticmethod
    def _read_text(path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(path)
        return path.read_text()

    @staticmethod
    def _read_yaml(path: Path) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(path)
        parsed = yaml.safe_load(path.read_text())
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected mapping in {path}")
        return parsed
