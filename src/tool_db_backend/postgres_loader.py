import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from tool_db_backend.config import Settings
from tool_db_backend.review_queue import ReviewQueueWriter


class LoadPlanExecutionError(RuntimeError):
    pass


class PostgresLoadPlanExecutor:
    def __init__(self, settings: Settings, connection: Any = None) -> None:
        self.settings = settings
        self._connection = connection
        self.review_writer = ReviewQueueWriter(settings)

    def build_execution_summary(self, load_plan: Dict[str, Any]) -> Dict[str, Any]:
        review_tasks = self._collect_review_tasks(load_plan)
        toolkit_actions = load_plan.get("actions", {}).get("toolkit_items", [])
        claim_actions = load_plan.get("actions", {}).get("claims", [])
        return {
            "toolkit_item_actions": len(toolkit_actions),
            "claim_actions": len(claim_actions),
            "review_task_count": len(review_tasks),
            "will_apply_database_changes": len(review_tasks) < (len(toolkit_actions) + len(claim_actions)),
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

        try:
            with conn.transaction():
                with conn.cursor() as cursor:
                    source_document_id = self._get_or_create_source_document(
                        cursor,
                        load_plan.get("source_document", {}),
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
                    )
        finally:
            if should_close:
                conn.close()

        return {
            "mode": "applied",
            "summary": summary,
            "source_document_id": source_document_id,
            "inserted_claim_count": len(inserted_claim_ids),
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
                return row[0]

        cursor.execute(
            """
            insert into source_document (
              source_type, title, doi, pmid, openalex_id, semantic_scholar_id, nct_id,
              publication_year, journal_or_source
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            ),
        )
        return cursor.fetchone()[0]

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
    ) -> List[Any]:
        inserted_ids = []
        for action in actions:
            if not action.get("subject_targets"):
                continue
            cursor.execute(
                """
                insert into extracted_claim (
                  source_document_id, claim_type, claim_text_normalized, polarity, needs_review
                )
                values (%s, %s, %s, %s, %s)
                returning id
                """,
                (
                    source_document_id,
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
    def _get_item_id_by_slug(cursor: Any, slug: str) -> Any:
        cursor.execute("select id from toolkit_item where slug = %s", (slug,))
        row = cursor.fetchone()
        if not row:
            raise LoadPlanExecutionError(f"Unknown item slug in load plan execution: {slug}")
        return row[0]

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
        return tasks
