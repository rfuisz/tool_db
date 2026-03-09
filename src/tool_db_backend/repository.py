import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from tool_db_backend.config import Settings
from tool_db_backend.gap_linking import GAP_LINK_SCORE_VERSION
from tool_db_backend.models import (
    ApprovedItemClaim,
    ApprovedItemEvidence,
    ApprovedItemEvidenceSnippet,
    ApprovedItemSourceDocument,
    CanonicalClaim,
    CanonicalClaimMetric,
    FirstPassEntityDetail,
    FirstPassEntitySummary,
    FirstPassEvidenceSnippet,
    FirstPassClaim,
    FirstPassItemDetail,
    FirstPassItemSummary,
    FirstPassSourceDocument,
    FirstPassWorkflowStageObservation,
    GapCapabilityDetail,
    GapCandidateTool,
    GapDetail,
    GapFieldSummary,
    GapResourceSummary,
    GapSummary,
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


class KnowledgeRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def list_items(self) -> List[ItemSummary]:
        if self._should_use_database():
            try:
                return self._list_items_from_database()
            except Exception:
                pass
        return self._list_items_from_files()

    def get_item(self, slug: str) -> ItemDetail:
        if self._should_use_database():
            try:
                item = self._get_item_from_database(slug)
                if item is not None:
                    return item
            except Exception:
                pass
        return self._get_item_from_files(slug)

    def list_gaps(self) -> List[GapSummary]:
        if self._should_use_database():
            try:
                return self._list_gaps_from_database()
            except Exception:
                pass
        return []

    def get_gap(self, slug: str) -> GapDetail:
        if self._should_use_database():
            try:
                gap = self._get_gap_from_database(slug)
                if gap is not None:
                    return gap
            except Exception:
                pass
        raise FileNotFoundError(slug)

    def list_workflows(self) -> List[WorkflowSummary]:
        if self._should_use_database():
            try:
                return self._list_workflows_from_database()
            except Exception:
                pass
        return self._list_workflows_from_files()

    def get_workflow(self, slug: str) -> WorkflowDetail:
        if self._should_use_database():
            try:
                workflow = self._get_workflow_from_database(slug)
                if workflow is not None:
                    return workflow
            except Exception:
                pass
        return self._get_workflow_from_files(slug)

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
                        source_document=FirstPassSourceDocument(
                            id=str(snippet_row[1]),
                            title=snippet_row[2],
                            source_type=snippet_row[3],
                            publication_year=snippet_row[4],
                            journal_or_source=snippet_row[5],
                            doi=snippet_row[6],
                            pmid=snippet_row[7],
                        ),
                    )
                    for snippet_row in cursor.fetchall()
                ]

                cursor.execute(
                    """
                    select
                      stage_observation,
                      s.id,
                      s.title,
                      s.source_type::text,
                      s.publication_year,
                      s.journal_or_source,
                      s.doi,
                      s.pmid
                    from extracted_item_candidate e
                    join extracted_packet p on p.packet_fingerprint = e.packet_fingerprint
                    join source_document s on s.id = e.source_document_id
                    cross join lateral jsonb_array_elements(
                      coalesce(p.packet_payload->'workflow_stage_observations', '[]'::jsonb)
                    ) as stage_observation
                    where e.slug = %s
                      and e.candidate_type = %s
                      and coalesce(stage_observation->>'workflow_local_id', '') = e.local_id
                    order by
                      s.publication_year desc nulls last,
                      coalesce((stage_observation->>'stage_order')::int, 2147483647) asc,
                      coalesce(stage_observation->>'stage_name', '') asc
                    """,
                    (slug, candidate_type),
                )
                workflow_stage_observations = [
                    self._map_first_pass_workflow_stage_observation(stage_row)
                    for stage_row in cursor.fetchall()
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
            workflow_stage_observations=workflow_stage_observations,
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
            external_ids=structured.get("external_ids", {}),
            source_status=structured.get("source_status", {}),
            citation_candidates=structured.get("citation_candidates", []),
            workflow_recommendations=structured.get("workflow_recommendations", []),
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
            recommended_for=structured.get("recommended_for", []),
            default_parallelization_assumption=structured.get("default_parallelization_assumption"),
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
                citations = self._fetch_item_citations(cursor, item_id)
                claims = self._fetch_item_claims(cursor, item_id)
                validation_rollup = self._fetch_validation_rollup(cursor, item_id)
                validations = self._fetch_validation_observations(cursor, item_id)
                replication_summary = self._fetch_replication_summary(cursor, item_id)
                item_facets = self._fetch_item_facets(cursor, item_id)
                explainers = self._fetch_item_explainers(cursor, item_id)
                comparisons = self._fetch_item_comparisons(cursor, item_id)
                problem_links = self._fetch_item_problem_links(cursor, item_id)
                approval_evidence = self._fetch_item_approval_evidence(cursor, item_id, row[1])
                markdown = self._get_item_markdown(slug, row[2], row[6])

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
                        "select mechanism_name from item_mechanism where item_id = %s order by mechanism_name asc",
                        item_id,
                    ),
                    techniques=self._fetch_scalar_list(
                        cursor,
                        "select technique_name from item_technique where item_id = %s order by technique_name asc",
                        item_id,
                    ),
                    target_processes=self._fetch_scalar_list(
                        cursor,
                        "select target_process from item_target_process where item_id = %s order by target_process asc",
                        item_id,
                    ),
                    external_ids=row[11] or {},
                    source_status={},
                    citation_candidates=citations,
                    workflow_recommendations=[],
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
                    recommended_for=self._split_multiline_text(row[6]),
                    default_parallelization_assumption=row[7],
                    stage_templates=self._fetch_workflow_stages(cursor, workflow_id),
                    step_templates=self._fetch_workflow_steps(cursor, workflow_id),
                    assumption_notes=self._fetch_workflow_assumptions(cursor, workflow_id),
                    index_markdown=index_markdown,
                )

    def _fetch_item_citations(self, cursor: Any, item_id: Any) -> List[Dict[str, Any]]:
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
        return [
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
              ic.overlap_reasons
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
              advance_criteria,
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
                "advance_criteria": row[12],
                "bottleneck_risk": row[13],
                "higher_fidelity_than_previous": row[14],
            }
            for row in cursor.fetchall()
        ]

    def _fetch_workflow_steps(self, cursor: Any, workflow_id: Any) -> List[Dict[str, Any]]:
        cursor.execute(
            """
            with recursive step_chain as (
              select
                wst.id,
                wst.step_name,
                wst.step_type::text,
                wst.duration_typical_hours,
                wst.hands_on_hours,
                wst.direct_cost_usd_typical,
                wst.parallelizable,
                wst.failure_probability,
                wst.input_artifact,
                wst.output_artifact,
                stage.stage_name,
                1 as sort_order
              from workflow_step_template wst
              left join workflow_stage_template stage on stage.id = wst.workflow_stage_template_id
              where wst.workflow_template_id = %s
                and not exists (
                  select 1
                  from workflow_edge edge
                  where edge.workflow_template_id = wst.workflow_template_id
                    and edge.to_step_id = wst.id
                )
              union all
              select
                next_step.id,
                next_step.step_name,
                next_step.step_type::text,
                next_step.duration_typical_hours,
                next_step.hands_on_hours,
                next_step.direct_cost_usd_typical,
                next_step.parallelizable,
                next_step.failure_probability,
                next_step.input_artifact,
                next_step.output_artifact,
                next_stage.stage_name,
                step_chain.sort_order + 1
              from step_chain
              join workflow_edge edge on edge.from_step_id = step_chain.id
              join workflow_step_template next_step on next_step.id = edge.to_step_id
              left join workflow_stage_template next_stage on next_stage.id = next_step.workflow_stage_template_id
              where edge.workflow_template_id = %s
            )
            select distinct on (id)
              id,
              step_name,
              stage_name,
              step_type,
              duration_typical_hours,
              hands_on_hours,
              direct_cost_usd_typical,
              parallelizable,
              failure_probability,
              input_artifact,
              output_artifact,
              sort_order
            from step_chain
            order by id, sort_order
            """,
            (workflow_id, workflow_id),
        )
        rows = cursor.fetchall()
        if not rows:
            cursor.execute(
                """
                select
                  wst.id,
                  wst.step_name,
                  stage.stage_name,
                  wst.step_type::text,
                  wst.duration_typical_hours,
                  wst.hands_on_hours,
                  wst.direct_cost_usd_typical,
                  wst.parallelizable,
                  wst.failure_probability,
                  wst.input_artifact,
                  wst.output_artifact,
                  coalesce(stage.stage_order, 999999),
                  wst.step_name
                from workflow_step_template wst
                left join workflow_stage_template stage on stage.id = wst.workflow_stage_template_id
                where wst.workflow_template_id = %s
                order by coalesce(stage.stage_order, 999999), wst.step_name
                """,
                (workflow_id,),
            )
            rows = cursor.fetchall()

        rows = sorted(rows, key=lambda row: (row[11], row[1]))
        return [
            {
                "step_name": row[1],
                "stage_name": row[2],
                "step_type": row[3],
                "duration_typical_hours": float(row[4]) if row[4] is not None else None,
                "hands_on_hours": float(row[5]) if row[5] is not None else None,
                "direct_cost_usd_typical": float(row[6]) if row[6] is not None else None,
                "parallelizable": row[7],
                "failure_probability": float(row[8]) if row[8] is not None else None,
                "input_artifact": row[9],
                "output_artifact": row[10],
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
    def _fetch_scalar_list(cursor: Any, query: str, item_id: Any) -> List[str]:
        cursor.execute(query, (item_id,))
        return [row[0] for row in cursor.fetchall()]

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
            advance_criteria=payload.get("advance_criteria"),
            bottleneck_risk=payload.get("bottleneck_risk"),
            higher_fidelity_than_previous=payload.get("higher_fidelity_than_previous"),
            source_locator=payload.get("source_locator") or {},
            source_document=FirstPassSourceDocument(
                id=str(row[1]),
                title=row[2],
                source_type=row[3],
                publication_year=row[4],
                journal_or_source=row[5],
                doi=row[6],
                pmid=row[7],
            ),
        )

    def _get_item_markdown(self, slug: str, canonical_name: str, summary: Optional[str]) -> Dict[str, str]:
        item_dir = self.settings.knowledge_root / "items" / slug
        if item_dir.exists():
            return {
                "index_markdown": self._read_text(item_dir / "index.md"),
                "evidence_markdown": self._read_text(item_dir / "evidence.md"),
                "replication_markdown": self._read_text(item_dir / "replication.md"),
                "workflow_fit_markdown": self._read_text(item_dir / "workflow-fit.md"),
            }

        summary_text = summary or "Postgres-backed canonical item record."
        return {
            "index_markdown": f"# {canonical_name}\n\n{summary_text}\n",
            "evidence_markdown": f"# {canonical_name} Evidence\n\nEvidence is currently being served from the hosted Postgres canonical store.\n",
            "replication_markdown": f"# {canonical_name} Replication\n\nReplication details are currently being served from the hosted Postgres canonical store.\n",
            "workflow_fit_markdown": f"# {canonical_name} Workflow Fit\n\nWorkflow fit notes are not yet available for this Postgres-backed record.\n",
        }

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
