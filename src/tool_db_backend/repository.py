import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from tool_db_backend.config import Settings
from tool_db_backend.models import (
    FirstPassEvidenceSnippet,
    FirstPassClaim,
    FirstPassItemDetail,
    FirstPassItemSummary,
    FirstPassSourceDocument,
    ItemDetail,
    ItemSummary,
    SourceRegistryEntry,
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

    def list_first_pass_items(self, limit: int = 500) -> List[FirstPassItemSummary]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    with alias_rows as (
                      select
                        e.slug,
                        alias
                      from extracted_item_candidate e
                      cross join lateral unnest(e.aliases) as alias
                      where e.candidate_type = 'toolkit_item'
                    )
                    select
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
                              and e2.candidate_type = 'toolkit_item'
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
                    left join alias_rows on alias_rows.slug = e.slug
                    where e.candidate_type = 'toolkit_item'
                    group by e.slug
                    order by source_document_count desc, claim_count desc, canonical_name asc
                    limit %s
                    """,
                    (limit,),
                )
                return [
                    FirstPassItemSummary(
                        slug=row[0],
                        canonical_name=row[1],
                        item_type=row[2],
                        matched_slug=row[3],
                        source_document_count=row[4],
                        claim_count=row[5],
                        aliases=list(row[6] or []),
                        evidence_preview=(row[7][0] if row[7] else None),
                        evidence_previews=list(row[7] or []),
                        claim_previews=list(row[8] or []),
                    )
                    for row in cursor.fetchall()
                ]

    def get_first_pass_item(self, slug: str) -> FirstPassItemDetail:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    with alias_rows as (
                      select alias
                      from extracted_item_candidate e
                      cross join lateral unnest(e.aliases) as alias
                      where e.slug = %s and e.candidate_type = 'toolkit_item'
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
                    where e.slug = %s and e.candidate_type = 'toolkit_item'
                    group by e.slug
                    """,
                    (slug, slug),
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
                    where e.slug = %s and e.candidate_type = 'toolkit_item'
                    order by s.publication_year desc nulls last, s.title asc
                    """,
                    (slug,),
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
                    order by s.publication_year desc nulls last, c.claim_type asc, c.claim_text_normalized asc
                    """,
                    (slug,),
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
                      and e.candidate_type = 'toolkit_item'
                      and e.evidence_text is not null
                      and e.evidence_text <> ''
                    order by s.publication_year desc nulls last, s.title asc, e.evidence_text asc
                    limit 20
                    """,
                    (slug,),
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

        return FirstPassItemDetail(
            slug=row[0],
            canonical_name=row[1],
            item_type=row[2],
            matched_slug=row[3],
            source_document_count=row[4],
            claim_count=row[5],
            aliases=list(row[6] or []),
            evidence_preview=evidence_snippets[0].text if evidence_snippets else None,
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
            primary_input_modality=structured.get("primary_input_modality"),
            primary_output_modality=structured.get("primary_output_modality"),
            maturity_stage=structured.get("maturity_stage"),
            synonyms=structured.get("synonyms", []),
            mechanisms=structured.get("mechanisms", []),
            techniques=structured.get("techniques", []),
            target_processes=structured.get("target_processes", []),
            external_ids=structured.get("external_ids", {}),
            source_status=structured.get("source_status", {}),
            citation_candidates=structured.get("citation_candidates", []),
            workflow_recommendations=structured.get("workflow_recommendations", []),
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
                        primary_input_modality=row[6],
                        primary_output_modality=row[7],
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
                markdown = self._get_item_markdown(slug, row[2], row[6])

                return ItemDetail(
                    slug=row[1],
                    canonical_name=row[2],
                    item_type=row[3],
                    status=row[4],
                    family=row[5],
                    summary=row[6],
                    primary_input_modality=row[7],
                    primary_output_modality=row[8],
                    maturity_stage=row[9],
                    synonyms=self._fetch_scalar_list(
                        cursor,
                        "select synonym from item_synonym where item_id = %s order by synonym asc",
                        item_id,
                    ),
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
                    external_ids=row[10] or {},
                    source_status={},
                    citation_candidates=citations,
                    workflow_recommendations=[],
                    index_markdown=markdown["index_markdown"],
                    evidence_markdown=markdown["evidence_markdown"],
                    replication_markdown=markdown["replication_markdown"],
                    workflow_fit_markdown=markdown["workflow_fit_markdown"],
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
              sd.title,
              case
                when sd.is_retracted then 'retracted'
                else 'curated'
              end as status,
              sd.journal_or_source,
              sd.doi
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
                "label": row[1],
                "status": row[2],
                "url": row[3],
                "doi": row[4],
            }
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
    def _fetch_scalar_list(cursor: Any, query: str, item_id: Any) -> List[str]:
        cursor.execute(query, (item_id,))
        return [row[0] for row in cursor.fetchall()]

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
