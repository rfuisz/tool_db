import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from tool_db_backend.config import Settings
from tool_db_backend.review_queue import ReviewQueueWriter


class LoadPlanExecutionError(RuntimeError):
    pass


def _strip_nul_bytes(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, list):
        return [_strip_nul_bytes(item) for item in value]
    if isinstance(value, dict):
        return {key: _strip_nul_bytes(item) for key, item in value.items()}
    return value


class PostgresLoadPlanExecutor:
    def __init__(self, settings: Settings, connection: Any = None) -> None:
        self.settings = settings
        self._connection = connection
        self.review_writer = ReviewQueueWriter(settings)

    def build_execution_summary(self, load_plan: Dict[str, Any]) -> Dict[str, Any]:
        review_tasks = self._collect_review_tasks(load_plan)
        toolkit_actions = load_plan.get("actions", {}).get("toolkit_items", [])
        claim_actions = load_plan.get("actions", {}).get("claims", [])
        validation_actions = load_plan.get("actions", {}).get("validation_observations", [])
        replication_actions = load_plan.get("actions", {}).get("replication", [])
        workflow_actions = load_plan.get("actions", {}).get("workflows", [])
        gap_item_actions = load_plan.get("actions", {}).get("gap_items", [])
        return {
            "toolkit_item_actions": len(toolkit_actions),
            "claim_actions": len(claim_actions),
            "validation_actions": len(validation_actions),
            "replication_actions": len(replication_actions),
            "workflow_actions": len(workflow_actions),
            "gap_item_actions": len(gap_item_actions),
            "review_task_count": len(review_tasks),
            "will_apply_database_changes": len(review_tasks)
            < (
                len(toolkit_actions)
                + len(claim_actions)
                + len(validation_actions)
                + len(replication_actions)
                + len(workflow_actions)
                + len(gap_item_actions)
            ),
        }

    def load_plan_from_file(self, load_plan_path: Path) -> Dict[str, Any]:
        return json.loads(load_plan_path.read_text())

    def execute_load_plan_file(
        self,
        load_plan_path: Path,
        apply: bool = False,
        review_output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        load_plan = self.load_plan_from_file(load_plan_path)
        return self.execute_load_plan(load_plan, apply=apply, review_output_path=review_output_path)

    def execute_load_plan(
        self,
        load_plan: Dict[str, Any],
        apply: bool = False,
        review_output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        load_plan = _strip_nul_bytes(load_plan)
        summary = self.build_execution_summary(load_plan)
        review_tasks = self._collect_review_tasks(load_plan)
        review_queue_path = None
        if review_tasks:
            review_queue_path = self.review_writer.write_tasks(
                source_document=load_plan.get("source_document", {}),
                tasks=review_tasks,
                output_path=review_output_path,
            )

        if not apply:
            return {
                "mode": "dry_run",
                "summary": summary,
                "review_queue_path": str(review_queue_path) if review_queue_path else None,
            }

        conn, should_close = self._get_connection()
        slug_to_item_id: Dict[str, Any] = {}
        inserted_claim_ids: List[Any] = []
        inserted_validation_count = 0
        attached_replication_citation_count = 0
        upserted_workflow_stage_count = 0
        upserted_gap_item_count = 0

        try:
            with conn.transaction():
                with conn.cursor() as cursor:
                    source_document_id = self._get_or_create_source_document(
                        cursor,
                        load_plan.get("source_document", {}),
                    )
                    extraction_run_id = self._maybe_insert_extraction_run(
                        cursor,
                        source_document_id=source_document_id,
                        packet_kind=load_plan.get("packet_kind"),
                        schema_version=load_plan.get("schema_version"),
                    )
                    self._execute_toolkit_item_actions(
                        cursor,
                        load_plan.get("actions", {}).get("toolkit_items", []),
                        slug_to_item_id,
                        source_document_id,
                    )
                    inserted_claim_ids = self._execute_claim_actions(
                        cursor,
                        load_plan.get("actions", {}).get("claims", []),
                        slug_to_item_id,
                        source_document_id,
                        extraction_run_id,
                    )
                    inserted_validation_count = self._execute_validation_actions(
                        cursor,
                        load_plan.get("actions", {}).get("validation_observations", []),
                        slug_to_item_id,
                        source_document_id,
                    )
                    attached_replication_citation_count = self._execute_replication_actions(
                        cursor,
                        load_plan.get("actions", {}).get("replication", []),
                        slug_to_item_id,
                        source_document_id,
                    )
                    upserted_workflow_stage_count = self._execute_workflow_actions(
                        cursor,
                        load_plan.get("actions", {}).get("workflows", []),
                        source_document_id,
                    )
                    upserted_gap_item_count = self._execute_gap_item_actions(
                        cursor,
                        load_plan.get("actions", {}).get("gap_items", []),
                        source_document_id,
                        load_plan.get("packet_kind"),
                        load_plan.get("schema_version"),
                    )
        finally:
            if should_close:
                conn.close()

        return {
            "mode": "applied",
            "summary": summary,
            "source_document_id": str(source_document_id),
            "inserted_claim_count": len(inserted_claim_ids),
            "inserted_validation_count": inserted_validation_count,
            "attached_replication_citation_count": attached_replication_citation_count,
            "upserted_workflow_stage_count": upserted_workflow_stage_count,
            "upserted_gap_item_count": upserted_gap_item_count,
            "review_queue_path": str(review_queue_path) if review_queue_path else None,
        }

    def _get_connection(self) -> Any:
        if self._connection is not None:
            return self._connection, False
        if not self.settings.database_url:
            raise LoadPlanExecutionError("DATABASE_URL is required to apply a load plan.")

        import psycopg

        return psycopg.connect(self.settings.database_url), True

    def _get_or_create_source_document(self, cursor: Any, source_document: Dict[str, Any]) -> Any:
        query_specs = [
            ("doi", "select id from source_document where doi = %s"),
            ("openalex_id", "select id from source_document where openalex_id = %s"),
            ("semantic_scholar_id", "select id from source_document where semantic_scholar_id = %s"),
            ("nct_id", "select id from source_document where nct_id = %s"),
            (
                "title",
                "select id from source_document where title = %s and publication_year is not distinct from %s and source_type = %s",
            ),
        ]
        for key, query in query_specs:
            value = source_document.get(key)
            if not value:
                continue
            if key == "title":
                cursor.execute(
                    query,
                    (
                        value,
                        source_document.get("publication_year"),
                        source_document.get("source_type"),
                    ),
                )
            else:
                cursor.execute(query, (value,))
            row = cursor.fetchone()
            if row:
                self._update_source_document(cursor, row[0], source_document)
                return row[0]

        cursor.execute(
            """
            insert into source_document (
              source_type, title, doi, pmid, openalex_id, semantic_scholar_id, nct_id,
              publication_year, journal_or_source, abstract_text, fulltext_license_status,
              is_retracted, retraction_metadata, raw_payload_ref
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            returning id
            """,
            (
                source_document.get("source_type"),
                source_document.get("title"),
                source_document.get("doi"),
                source_document.get("pmid"),
                source_document.get("openalex_id"),
                source_document.get("semantic_scholar_id"),
                source_document.get("nct_id"),
                source_document.get("publication_year"),
                source_document.get("journal_or_source"),
                source_document.get("abstract_text"),
                source_document.get("fulltext_license_status"),
                source_document.get("is_retracted", False),
                json.dumps(source_document.get("retraction_metadata", {})),
                source_document.get("raw_payload_ref"),
            ),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _update_source_document(cursor: Any, source_document_id: Any, source_document: Dict[str, Any]) -> None:
        cursor.execute(
            """
            update source_document
            set
              source_type = coalesce(%s, source_type),
              title = coalesce(%s, title),
              doi = coalesce(%s, doi),
              pmid = coalesce(%s, pmid),
              openalex_id = coalesce(%s, openalex_id),
              semantic_scholar_id = coalesce(%s, semantic_scholar_id),
              nct_id = coalesce(%s, nct_id),
              publication_year = coalesce(%s, publication_year),
              journal_or_source = coalesce(%s, journal_or_source),
              abstract_text = coalesce(%s, abstract_text),
              fulltext_license_status = coalesce(%s, fulltext_license_status),
              is_retracted = coalesce(%s, is_retracted),
              retraction_metadata = case
                when coalesce(%s::jsonb, '{}'::jsonb) = '{}'::jsonb then retraction_metadata
                else coalesce(retraction_metadata, '{}'::jsonb) || %s::jsonb
              end,
              raw_payload_ref = coalesce(%s, raw_payload_ref)
            where id = %s
            """,
            (
                source_document.get("source_type"),
                source_document.get("title"),
                source_document.get("doi"),
                source_document.get("pmid"),
                source_document.get("openalex_id"),
                source_document.get("semantic_scholar_id"),
                source_document.get("nct_id"),
                source_document.get("publication_year"),
                source_document.get("journal_or_source"),
                source_document.get("abstract_text"),
                source_document.get("fulltext_license_status"),
                source_document.get("is_retracted"),
                json.dumps(source_document.get("retraction_metadata", {})),
                json.dumps(source_document.get("retraction_metadata", {})),
                source_document.get("raw_payload_ref"),
                source_document_id,
            ),
        )

    def _execute_toolkit_item_actions(
        self,
        cursor: Any,
        actions: List[Dict[str, Any]],
        slug_to_item_id: Dict[str, Any],
        source_document_id: Any,
    ) -> None:
        for action in actions:
            kind = action["action"]
            if kind in {"manual_resolution_required", "manual_candidate_review_required"}:
                continue
            if kind == "create_normalized_item":
                target_slug = action["proposed_slug"]
                slug_to_item_id[target_slug] = self._create_or_get_normalized_item(
                    cursor,
                    slug=target_slug,
                    canonical_name=action["canonical_name"],
                    item_type=action["item_type"],
                    summary=action.get("summary"),
                    external_ids=action.get("external_ids", {}),
                    primary_input_modality=action.get("primary_input_modality"),
                    primary_output_modality=action.get("primary_output_modality"),
                )
                self._upsert_synonyms(
                    cursor,
                    slug_to_item_id[target_slug],
                    action.get("aliases", []),
                    source_document_id,
                )
                self._upsert_item_mechanisms(
                    cursor,
                    slug_to_item_id[target_slug],
                    action.get("mechanisms", []),
                )
                self._upsert_item_techniques(
                    cursor,
                    slug_to_item_id[target_slug],
                    action.get("techniques", []),
                )
                self._upsert_item_target_processes(
                    cursor,
                    slug_to_item_id[target_slug],
                    action.get("target_processes", []),
                )
                continue
            if kind == "attach_evidence_to_existing_item":
                target_slug = action["target_slug"]
                slug_to_item_id[target_slug] = self._get_item_id_by_slug(cursor, target_slug)
                self._upsert_synonyms(
                    cursor,
                    slug_to_item_id[target_slug],
                    action.get("aliases", []),
                    source_document_id,
                )
                continue

    def _execute_claim_actions(
        self,
        cursor: Any,
        actions: List[Dict[str, Any]],
        slug_to_item_id: Dict[str, Any],
        source_document_id: Any,
        extraction_run_id: Optional[Any],
    ) -> List[Any]:
        inserted_ids = []
        for action in actions:
            if not action.get("subject_targets"):
                continue
            cursor.execute(
                """
                insert into extracted_claim (
                  source_document_id, extraction_run_id, claim_type, claim_text_normalized, polarity, needs_review
                )
                values (%s, %s, %s, %s, %s, %s)
                returning id
                """,
                (
                    source_document_id,
                    extraction_run_id,
                    action["claim_type"],
                    action["claim_text_normalized"],
                    action["polarity"],
                    True,
                ),
            )
            claim_id = cursor.fetchone()[0]
            inserted_ids.append(claim_id)

            for metric in action.get("metrics", []):
                cursor.execute(
                    """
                    insert into claim_metric (
                      claim_id, metric_name, operator, value_num, value_text, unit, condition_text
                    )
                    values (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        claim_id,
                        metric.get("metric_name"),
                        metric.get("operator"),
                        metric.get("value_num"),
                        metric.get("value_text"),
                        metric.get("unit"),
                        metric.get("condition_text"),
                    ),
                )

            for subject_target in action["subject_targets"]:
                target_slug = subject_target.get("target_slug") or subject_target.get("proposed_slug")
                if target_slug not in slug_to_item_id:
                    slug_to_item_id[target_slug] = self._get_item_id_by_slug(cursor, target_slug)
                item_id = slug_to_item_id[target_slug]
                cursor.execute(
                    """
                    insert into claim_subject_link (claim_id, item_id, subject_role)
                    values (%s, %s, %s)
                    """,
                    (claim_id, item_id, "subject"),
                )
                if action.get("citation_role_suggestion"):
                    cursor.execute(
                        """
                        insert into item_citation (
                          item_id, source_document_id, citation_role, importance_rank, why_this_matters
                        )
                        values (%s, %s, %s, %s, %s)
                        on conflict (item_id, source_document_id, citation_role) do nothing
                        """,
                        (
                            item_id,
                            source_document_id,
                            action["citation_role_suggestion"],
                            999,
                            f"Seeded from load plan for claim {action['claim_local_id']}.",
                        ),
                    )

        return inserted_ids

    def _execute_validation_actions(
        self,
        cursor: Any,
        actions: List[Dict[str, Any]],
        slug_to_item_id: Dict[str, Any],
        source_document_id: Any,
    ) -> int:
        inserted_count = 0
        for action in actions:
            if not action.get("subject_targets"):
                continue
            notes = self._build_validation_notes(action)
            for subject_target in action["subject_targets"]:
                target_slug = subject_target.get("target_slug") or subject_target.get("proposed_slug")
                if target_slug not in slug_to_item_id:
                    slug_to_item_id[target_slug] = self._get_item_id_by_slug(cursor, target_slug)
                item_id = slug_to_item_id[target_slug]
                cursor.execute(
                    """
                    insert into validation_observation (
                      item_id, source_document_id, construct_name, observation_type,
                      biological_system_level, species, strain_or_model, cell_type, tissue,
                      subcellular_target, delivery_mode, cargo_or_effector, success_outcome,
                      assay_description, independent_lab_cluster_id, institution_cluster_id, notes
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    returning id
                    """,
                    (
                        item_id,
                        source_document_id,
                        action.get("construct_name"),
                        action.get("observation_type"),
                        action.get("biological_system_level"),
                        action.get("species"),
                        action.get("strain_or_model"),
                        action.get("cell_type"),
                        action.get("tissue"),
                        action.get("subcellular_target"),
                        action.get("delivery_mode"),
                        action.get("cargo_or_effector"),
                        action.get("success_outcome"),
                        action.get("assay_description"),
                        action.get("independent_lab_cluster_id"),
                        action.get("institution_cluster_id"),
                        notes,
                    ),
                )
                validation_observation_id = cursor.fetchone()[0]
                inserted_count += 1
                for metric in action.get("metrics", []):
                    cursor.execute(
                        """
                        insert into validation_metric_value (
                          validation_observation_id, metric_name, value_num, unit, qualifier, condition_text
                        )
                        values (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            validation_observation_id,
                            metric.get("metric_name"),
                            metric.get("value_num"),
                            metric.get("unit"),
                            metric.get("operator") or metric.get("value_text"),
                            metric.get("condition_text"),
                        ),
                    )
        return inserted_count

    def _execute_replication_actions(
        self,
        cursor: Any,
        actions: List[Dict[str, Any]],
        slug_to_item_id: Dict[str, Any],
        source_document_id: Any,
    ) -> int:
        attached_count = 0
        for action in actions:
            if action.get("action") != "attach_replication_signal_citation":
                continue
            target_slug = action.get("target_slug")
            if not target_slug:
                continue
            if target_slug not in slug_to_item_id:
                slug_to_item_id[target_slug] = self._get_item_id_by_slug(cursor, target_slug)
            item_id = slug_to_item_id[target_slug]
            for citation_role in action.get("citation_roles", []):
                cursor.execute(
                    """
                    insert into item_citation (
                      item_id, source_document_id, citation_role, importance_rank, why_this_matters
                    )
                    values (%s, %s, %s, %s, %s)
                    on conflict (item_id, source_document_id, citation_role) do nothing
                    """,
                    (
                        item_id,
                        source_document_id,
                        citation_role,
                        100,
                        self._build_replication_why_this_matters(action, citation_role),
                    ),
                )
                attached_count += max(cursor.rowcount, 0)
        return attached_count

    def _execute_workflow_actions(
        self,
        cursor: Any,
        actions: List[Dict[str, Any]],
        source_document_id: Any,
    ) -> int:
        upserted_stage_count = 0
        for action in actions:
            if action["action"] != "upsert_workflow_stages_for_existing_workflow":
                continue
            workflow_template_id = self._get_workflow_template_id_by_slug(cursor, action["target_slug"])
            for stage in action.get("stages", []):
                workflow_stage_template_id = self._upsert_workflow_stage_template(
                    cursor,
                    workflow_template_id=workflow_template_id,
                    stage=stage,
                )
                self._upsert_workflow_stage_assumption(
                    cursor,
                    workflow_template_id=workflow_template_id,
                    workflow_stage_template_id=workflow_stage_template_id,
                    source_document_id=source_document_id,
                    stage=stage,
                )
                upserted_stage_count += 1
        return upserted_stage_count

    def _execute_gap_item_actions(
        self,
        cursor: Any,
        actions: List[Dict[str, Any]],
        source_document_id: Any,
        packet_kind: Optional[str],
        schema_version: Optional[str],
    ) -> int:
        if not actions:
            return 0

        extraction_run_id = self._insert_extraction_run(
            cursor,
            source_document_id=source_document_id,
            packet_kind=packet_kind or "database_entry_extract_v1",
            schema_version=schema_version or "v1",
        )
        upserted_count = 0

        for action in actions:
            database_fields = action.get("database_fields", {})
            gap_field_id = self._upsert_gap_field(cursor, database_fields.get("field"))
            payload = {
                "database_name": action.get("database_name"),
                "entry_url": action.get("entry_url"),
                "external_ids": action.get("external_ids", {}),
                "evidence_text": action.get("evidence_text"),
                "database_fields": database_fields,
                "claims": action.get("claims", []),
                "unresolved_ambiguities": action.get("unresolved_ambiguities", []),
                "source_document_id": str(source_document_id),
                "extraction_run_id": str(extraction_run_id),
            }
            cursor.execute(
                """
                insert into gap_item (external_gap_item_id, gap_field_id, slug, title, payload)
                values (%s, %s, %s, %s, %s::jsonb)
                on conflict (external_gap_item_id) do update
                set
                  gap_field_id = coalesce(excluded.gap_field_id, gap_item.gap_field_id),
                  slug = coalesce(excluded.slug, gap_item.slug),
                  title = excluded.title,
                  payload = excluded.payload
                returning id
                """,
                (
                    action["external_gap_item_id"],
                    gap_field_id,
                    action.get("external_ids", {}).get("gap_map_slug"),
                    action["canonical_name"],
                    json.dumps(payload),
                ),
            )
            gap_item_id = cursor.fetchone()[0]
            capability_ids = self._upsert_gap_capabilities(
                cursor,
                database_fields.get("capabilities", []),
            )
            self._replace_gap_item_capabilities(cursor, gap_item_id, capability_ids)
            self._upsert_gap_resources(cursor, database_fields.get("resources", []))
            self._replace_gap_capability_resources(
                cursor,
                database_fields.get("capabilities", []),
            )
            upserted_count += 1

        return upserted_count

    @staticmethod
    def _upsert_synonyms(cursor: Any, item_id: Any, aliases: List[str], source_document_id: Any) -> None:
        for alias in aliases:
            cursor.execute(
                """
                insert into item_synonym (item_id, synonym, source_document_id)
                values (%s, %s, %s)
                on conflict (item_id, synonym) do nothing
                """,
                (item_id, alias, source_document_id),
            )

    @staticmethod
    def _create_or_get_normalized_item(
        cursor: Any,
        *,
        slug: str,
        canonical_name: str,
        item_type: str,
        summary: Optional[str],
        external_ids: Dict[str, Any],
        primary_input_modality: Optional[str],
        primary_output_modality: Optional[str],
    ) -> Any:
        cursor.execute(
            """
            insert into toolkit_item (
              slug, canonical_name, item_type, summary, status, external_ids,
              primary_input_modality, primary_output_modality
            )
            values (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            on conflict (slug) do update
            set
              summary = coalesce(toolkit_item.summary, excluded.summary),
              external_ids = toolkit_item.external_ids || excluded.external_ids,
              primary_input_modality = coalesce(
                toolkit_item.primary_input_modality,
                excluded.primary_input_modality
              ),
              primary_output_modality = coalesce(
                toolkit_item.primary_output_modality,
                excluded.primary_output_modality
              )
            returning id
            """,
            (
                slug,
                canonical_name,
                item_type,
                summary,
                "normalized",
                json.dumps(external_ids or {}),
                primary_input_modality,
                primary_output_modality,
            ),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _upsert_item_mechanisms(cursor: Any, item_id: Any, mechanisms: List[str]) -> None:
        for mechanism in mechanisms:
            cursor.execute(
                """
                insert into item_mechanism (item_id, mechanism_name)
                select %s, %s
                where not exists (
                  select 1
                  from item_mechanism
                  where item_id = %s and mechanism_name = %s
                )
                """,
                (item_id, mechanism, item_id, mechanism),
            )

    @staticmethod
    def _upsert_item_techniques(cursor: Any, item_id: Any, techniques: List[str]) -> None:
        for technique in techniques:
            cursor.execute(
                """
                insert into item_technique (item_id, technique_name)
                select %s, %s
                where not exists (
                  select 1
                  from item_technique
                  where item_id = %s and technique_name = %s
                )
                """,
                (item_id, technique, item_id, technique),
            )

    @staticmethod
    def _upsert_item_target_processes(cursor: Any, item_id: Any, target_processes: List[str]) -> None:
        for target_process in target_processes:
            cursor.execute(
                """
                insert into item_target_process (item_id, target_process)
                select %s, %s
                where not exists (
                  select 1
                  from item_target_process
                  where item_id = %s and target_process = %s
                )
                """,
                (item_id, target_process, item_id, target_process),
            )

    @staticmethod
    def _get_item_id_by_slug(cursor: Any, slug: str) -> Any:
        cursor.execute("select id from toolkit_item where slug = %s", (slug,))
        row = cursor.fetchone()
        if not row:
            raise LoadPlanExecutionError(f"Unknown item slug in load plan execution: {slug}")
        return row[0]

    @staticmethod
    def _get_workflow_template_id_by_slug(cursor: Any, slug: str) -> Any:
        cursor.execute("select id from workflow_template where slug = %s", (slug,))
        row = cursor.fetchone()
        if not row:
            raise LoadPlanExecutionError(f"Unknown workflow slug in load plan execution: {slug}")
        return row[0]

    @staticmethod
    def _upsert_workflow_stage_template(cursor: Any, workflow_template_id: Any, stage: Dict[str, Any]) -> Any:
        cursor.execute(
            """
            insert into workflow_stage_template (
              workflow_template_id, stage_name, stage_kind, stage_order, search_modality,
              input_candidate_count_typical, output_candidate_count_typical, candidate_unit,
              selection_basis, counterselection_basis, enriches_for_axes, guards_against_axes,
              preserves_downstream_property_axes, advance_criteria, bottleneck_risk,
              higher_fidelity_than_previous, notes
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (workflow_template_id, stage_order) do update
            set
              stage_name = excluded.stage_name,
              stage_kind = excluded.stage_kind,
              search_modality = excluded.search_modality,
              input_candidate_count_typical = excluded.input_candidate_count_typical,
              output_candidate_count_typical = excluded.output_candidate_count_typical,
              candidate_unit = excluded.candidate_unit,
              selection_basis = excluded.selection_basis,
              counterselection_basis = excluded.counterselection_basis,
              enriches_for_axes = excluded.enriches_for_axes,
              guards_against_axes = excluded.guards_against_axes,
              preserves_downstream_property_axes = excluded.preserves_downstream_property_axes,
              advance_criteria = excluded.advance_criteria,
              bottleneck_risk = excluded.bottleneck_risk,
              higher_fidelity_than_previous = excluded.higher_fidelity_than_previous,
              notes = excluded.notes
            returning id
            """,
            (
                workflow_template_id,
                stage.get("stage_name"),
                stage.get("stage_kind"),
                stage.get("stage_order"),
                stage.get("search_modality"),
                stage.get("input_candidate_count"),
                stage.get("output_candidate_count"),
                stage.get("candidate_unit"),
                stage.get("selection_basis"),
                stage.get("counterselection_basis"),
                stage.get("enriches_for_axes", []),
                stage.get("guards_against_axes", []),
                stage.get("preserves_downstream_property_axes", []),
                stage.get("advance_criteria"),
                stage.get("bottleneck_risk"),
                stage.get("higher_fidelity_than_previous"),
                PostgresLoadPlanExecutor._format_workflow_stage_notes(stage),
            ),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _upsert_workflow_stage_assumption(
        cursor: Any,
        *,
        workflow_template_id: Any,
        workflow_stage_template_id: Any,
        source_document_id: Any,
        stage: Dict[str, Any],
    ) -> None:
        cursor.execute(
            """
            delete from workflow_assumption
            where workflow_stage_template_id = %s
              and source_document_id = %s
              and assumption_kind = %s
            """,
            (workflow_stage_template_id, source_document_id, "source_backed_stage_observation"),
        )
        cursor.execute(
            """
            insert into workflow_assumption (
              workflow_template_id, workflow_stage_template_id, assumption_kind, assumption_name,
              value_text, rationale, source_document_id
            )
            values (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                workflow_template_id,
                workflow_stage_template_id,
                "source_backed_stage_observation",
                stage.get("stage_name"),
                stage.get("selection_basis") or stage.get("advance_criteria"),
                PostgresLoadPlanExecutor._format_workflow_stage_rationale(stage),
                source_document_id,
            ),
        )

    @staticmethod
    def _format_workflow_stage_notes(stage: Dict[str, Any]) -> Optional[str]:
        parts = []
        if stage.get("selection_basis"):
            parts.append(f"Selection basis: {stage['selection_basis']}")
        if stage.get("counterselection_basis"):
            parts.append(f"Counterselection: {stage['counterselection_basis']}")
        if stage.get("advance_criteria"):
            parts.append(f"Advance criteria: {stage['advance_criteria']}")
        if stage.get("bottleneck_risk"):
            parts.append(f"Bottleneck risk: {stage['bottleneck_risk']}")
        locator = stage.get("source_locator") or {}
        if locator.get("section_label"):
            parts.append(f"Source section: {locator['section_label']}")
        if locator.get("page_or_locator"):
            parts.append(f"Source locator: {locator['page_or_locator']}")
        return " | ".join(parts) if parts else None

    @staticmethod
    def _format_workflow_stage_rationale(stage: Dict[str, Any]) -> str:
        parts = []
        if stage.get("enriches_for_axes"):
            parts.append("Enriches for: " + ", ".join(stage["enriches_for_axes"]))
        if stage.get("guards_against_axes"):
            parts.append("Guards against: " + ", ".join(stage["guards_against_axes"]))
        if stage.get("preserves_downstream_property_axes"):
            parts.append(
                "Preserves downstream properties: "
                + ", ".join(stage["preserves_downstream_property_axes"])
            )
        if stage.get("higher_fidelity_than_previous") is True:
            parts.append("Marked as higher fidelity than the previous stage.")
        locator = stage.get("source_locator") or {}
        if locator.get("quoted_text"):
            parts.append(f"Quoted text: {locator['quoted_text']}")
        return " ".join(parts) or "Source-backed workflow stage observation."

    @staticmethod
    def _insert_extraction_run(
        cursor: Any,
        *,
        source_document_id: Any,
        packet_kind: str,
        schema_version: str,
    ) -> Any:
        cursor.execute(
            """
            insert into extraction_run (
              source_document_id, packet_kind, schema_version, status
            )
            values (%s, %s, %s, %s)
            returning id
            """,
            (source_document_id, packet_kind, schema_version, "completed"),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _maybe_insert_extraction_run(
        cursor: Any,
        *,
        source_document_id: Any,
        packet_kind: Optional[str],
        schema_version: Optional[str],
    ) -> Optional[Any]:
        if not packet_kind or not schema_version:
            return None
        try:
            return PostgresLoadPlanExecutor._insert_extraction_run(
                cursor,
                source_document_id=source_document_id,
                packet_kind=packet_kind,
                schema_version=schema_version,
            )
        except AssertionError:
            return None

    @staticmethod
    def _upsert_gap_field(cursor: Any, field_payload: Optional[Dict[str, Any]]) -> Optional[Any]:
        if not field_payload or not field_payload.get("id"):
            return None
        cursor.execute(
            """
            insert into gap_field (external_gap_field_id, slug, name, payload)
            values (%s, %s, %s, %s::jsonb)
            on conflict (external_gap_field_id) do update
            set
              slug = coalesce(excluded.slug, gap_field.slug),
              name = excluded.name,
              payload = excluded.payload
            returning id
            """,
            (
                str(field_payload["id"]),
                field_payload.get("slug"),
                field_payload.get("name") or str(field_payload["id"]),
                json.dumps(field_payload),
            ),
        )
        return cursor.fetchone()[0]

    @staticmethod
    def _upsert_gap_capabilities(cursor: Any, capability_payloads: List[Dict[str, Any]]) -> List[Any]:
        capability_ids: List[Any] = []
        for capability_payload in capability_payloads:
            capability_id = capability_payload.get("id")
            if not capability_id:
                continue
            cursor.execute(
                """
                insert into gap_capability (external_gap_capability_id, slug, name, payload)
                values (%s, %s, %s, %s::jsonb)
                on conflict (external_gap_capability_id) do update
                set
                  slug = coalesce(excluded.slug, gap_capability.slug),
                  name = excluded.name,
                  payload = excluded.payload
                returning id
                """,
                (
                    str(capability_id),
                    capability_payload.get("slug"),
                    capability_payload.get("name") or str(capability_id),
                    json.dumps(capability_payload),
                ),
            )
            capability_ids.append(cursor.fetchone()[0])
        return capability_ids

    @staticmethod
    def _upsert_gap_resources(cursor: Any, resource_payloads: List[Dict[str, Any]]) -> None:
        for resource_payload in resource_payloads:
            resource_id = resource_payload.get("id")
            if not resource_id:
                continue
            cursor.execute(
                """
                insert into gap_resource (external_gap_resource_id, title, payload)
                values (%s, %s, %s::jsonb)
                on conflict (external_gap_resource_id) do update
                set
                  title = excluded.title,
                  payload = excluded.payload
                """,
                (
                    str(resource_id),
                    resource_payload.get("title") or str(resource_id),
                    json.dumps(resource_payload),
                ),
            )

    @staticmethod
    def _replace_gap_item_capabilities(cursor: Any, gap_item_id: Any, capability_ids: List[Any]) -> None:
        cursor.execute("delete from gap_item_capability where gap_item_id = %s", (gap_item_id,))
        for capability_id in capability_ids:
            cursor.execute(
                """
                insert into gap_item_capability (gap_item_id, gap_capability_id)
                values (%s, %s)
                on conflict do nothing
                """,
                (gap_item_id, capability_id),
            )

    @staticmethod
    def _replace_gap_capability_resources(cursor: Any, capability_payloads: List[Dict[str, Any]]) -> None:
        for capability_payload in capability_payloads:
            capability_external_id = capability_payload.get("id")
            if not capability_external_id:
                continue
            cursor.execute(
                "select id from gap_capability where external_gap_capability_id = %s",
                (str(capability_external_id),),
            )
            capability_row = cursor.fetchone()
            if not capability_row:
                continue
            gap_capability_id = capability_row[0]
            cursor.execute(
                "delete from gap_capability_resource where gap_capability_id = %s",
                (gap_capability_id,),
            )
            for resource_external_id in capability_payload.get("resources", []):
                cursor.execute(
                    "select id from gap_resource where external_gap_resource_id = %s",
                    (str(resource_external_id),),
                )
                resource_row = cursor.fetchone()
                if not resource_row:
                    continue
                cursor.execute(
                    """
                    insert into gap_capability_resource (gap_capability_id, gap_resource_id)
                    values (%s, %s)
                    on conflict do nothing
                    """,
                    (gap_capability_id, resource_row[0]),
                )

    @staticmethod
    def _collect_review_tasks(load_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        tasks: List[Dict[str, Any]] = []
        for action in load_plan.get("actions", {}).get("toolkit_items", []):
            if action["action"] == "manual_resolution_required":
                tasks.append(
                    {
                        "task_type": "item_resolution_review",
                        "local_id": action["local_id"],
                        "candidate_matches": action.get("candidate_matches", []),
                    }
                )
            elif action["action"] == "manual_candidate_review_required":
                tasks.append(
                    {
                        "task_type": "new_item_candidate_review",
                        "local_id": action["local_id"],
                        "proposed_slug": action.get("proposed_slug"),
                        "canonical_name": action.get("canonical_name"),
                        "item_type": action.get("item_type"),
                        "aliases": action.get("aliases", []),
                    }
                )
        for action in load_plan.get("actions", {}).get("claims", []):
            if not action.get("subject_targets"):
                tasks.append(
                    {
                        "task_type": "claim_subject_review",
                        "claim_local_id": action["claim_local_id"],
                        "reason": "No resolvable subject targets available.",
                        "unresolved_subject_candidates": action.get("unresolved_subject_candidates", []),
                    }
                )
        for action in load_plan.get("actions", {}).get("validation_observations", []):
            if not action.get("subject_targets"):
                tasks.append(
                    {
                        "task_type": "validation_subject_review",
                        "observation_local_id": action.get("observation_local_id"),
                        "reason": "No resolvable subject targets available for validation observation.",
                        "unresolved_subject_candidates": action.get("unresolved_subject_candidates", []),
                    }
                )
        for action in load_plan.get("actions", {}).get("replication", []):
            if not action.get("target_slug"):
                tasks.append(
                    {
                        "task_type": "replication_signal_review",
                        "local_id": action.get("local_id"),
                        "reason": "Replication signals could not be attached to a resolved canonical item.",
                        "replication_signals": action.get("replication_signals", {}),
                    }
                )
        for action in load_plan.get("actions", {}).get("workflows", []):
            if action["action"] == "manual_workflow_candidate_review_required":
                tasks.append(
                    {
                        "task_type": "new_workflow_candidate_review",
                        "local_id": action["local_id"],
                        "proposed_slug": action.get("proposed_slug"),
                        "canonical_name": action.get("canonical_name"),
                        "stages": action.get("stages", []),
                    }
                )
            elif action["action"] == "manual_workflow_resolution_required":
                tasks.append(
                    {
                        "task_type": "workflow_resolution_review",
                        "local_id": action["local_id"],
                        "candidate_matches": action.get("candidate_matches", []),
                        "stages": action.get("stages", []),
                    }
                )
            elif action["action"] == "manual_workflow_stage_review_required":
                tasks.append(
                    {
                        "task_type": "workflow_stage_review",
                        "reason": action.get("reason"),
                        "stages": action.get("stages", []),
                    }
                )
        return tasks

    @staticmethod
    def _build_validation_notes(action: Dict[str, Any]) -> Optional[str]:
        parts: List[str] = []
        if action.get("notes"):
            parts.append(str(action["notes"]).strip())
        if action.get("derived_from_claim_local_id"):
            parts.append(f"Derived from claim {action['derived_from_claim_local_id']}.")
        locator = action.get("source_locator") or {}
        if locator.get("section_label"):
            parts.append(f"Section: {locator['section_label']}.")
        if locator.get("quoted_text"):
            parts.append(f"Quoted text: {locator['quoted_text']}")
        joined = " ".join(part for part in parts if part)
        return joined or None

    @staticmethod
    def _build_replication_why_this_matters(action: Dict[str, Any], citation_role: str) -> str:
        signals = action.get("replication_signals", {})
        penalties = signals.get("practicality_penalties", [])
        if citation_role == "foundational":
            base = "Marked as a foundational paper by extraction-time replication signals."
        elif citation_role == "independent_validation":
            base = "Marked as an independent follow-up by extraction-time replication signals."
        else:
            base = "Marked as a negative or mixed follow-up by extraction-time replication signals."
        if penalties:
            return base + " Practicality notes: " + "; ".join(penalties)
        return base
