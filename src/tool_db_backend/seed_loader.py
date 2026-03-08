import json
from pathlib import Path
from typing import Any, Dict, Tuple

from tool_db_backend.config import Settings
from tool_db_backend.postgres_loader import LoadPlanExecutionError


class SeedLoader:
    def __init__(self, settings: Settings, connection: Any = None) -> None:
        self.settings = settings
        self._connection = connection

    def load_bundle_file(self, bundle_path: Path) -> Dict[str, int]:
        bundle = json.loads(bundle_path.read_text())
        return self.load_bundle(bundle)

    def load_bundle(self, bundle: Dict[str, Any]) -> Dict[str, int]:
        conn, should_close = self._get_connection()
        inserted_item_count = 0
        inserted_workflow_count = 0
        inserted_step_count = 0

        try:
            with conn.transaction():
                with conn.cursor() as cursor:
                    for item_entry in bundle.get("items", []):
                        inserted_item_count += int(self._load_item(cursor, item_entry))

                    for workflow_entry in bundle.get("workflows", []):
                        workflow_inserted, step_count = self._load_workflow(cursor, workflow_entry)
                        inserted_workflow_count += int(workflow_inserted)
                        inserted_step_count += step_count
        finally:
            if should_close:
                conn.close()

        return {
            "loaded_item_count": len(bundle.get("items", [])),
            "inserted_item_count": inserted_item_count,
            "loaded_workflow_count": len(bundle.get("workflows", [])),
            "inserted_workflow_count": inserted_workflow_count,
            "inserted_workflow_step_count": inserted_step_count,
        }

    def _get_connection(self) -> Tuple[Any, bool]:
        if self._connection is not None:
            return self._connection, False
        if not self.settings.database_url:
            raise LoadPlanExecutionError("DATABASE_URL is required to load seed data.")

        import psycopg

        return psycopg.connect(self.settings.database_url), True

    def _load_item(self, cursor: Any, item_entry: Dict[str, Any]) -> bool:
        structured = item_entry["structured"]
        cursor.execute(
            """
            insert into toolkit_item (
              slug, canonical_name, item_type, family, summary, status, maturity_stage,
              primary_input_modality, primary_output_modality, external_ids
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            on conflict (slug) do nothing
            returning id
            """,
            (
                structured["slug"],
                structured["canonical_name"],
                structured["item_type"],
                structured.get("family"),
                structured.get("summary"),
                structured["status"],
                structured.get("maturity_stage"),
                structured.get("primary_input_modality"),
                structured.get("primary_output_modality"),
                json.dumps(structured.get("external_ids", {})),
            ),
        )
        inserted_row = cursor.fetchone()
        inserted = inserted_row is not None

        cursor.execute("select id from toolkit_item where slug = %s", (structured["slug"],))
        item_id = cursor.fetchone()[0]

        self._insert_distinct_rows(
            cursor,
            "item_synonym",
            "item_id, synonym",
            [(item_id, synonym) for synonym in structured.get("synonyms", [])],
            "item_id = %s and synonym = %s",
        )
        self._insert_distinct_rows(
            cursor,
            "item_mechanism",
            "item_id, mechanism_name",
            [(item_id, mechanism) for mechanism in structured.get("mechanisms", [])],
            "item_id = %s and mechanism_name = %s",
        )
        self._insert_distinct_rows(
            cursor,
            "item_technique",
            "item_id, technique_name",
            [(item_id, technique) for technique in structured.get("techniques", [])],
            "item_id = %s and technique_name = %s",
        )
        self._insert_distinct_rows(
            cursor,
            "item_target_process",
            "item_id, target_process",
            [(item_id, target_process) for target_process in structured.get("target_processes", [])],
            "item_id = %s and target_process = %s",
        )
        return inserted

    def _load_workflow(self, cursor: Any, workflow_entry: Dict[str, Any]) -> Tuple[bool, int]:
        structured = workflow_entry["structured"]
        cursor.execute(
            """
            insert into workflow_template (
              slug, name, workflow_family, objective, throughput_class,
              recommended_for, default_parallelization_assumption, notes
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (slug) do nothing
            returning id
            """,
            (
                structured["slug"],
                structured["name"],
                structured["workflow_family"],
                structured["objective"],
                structured.get("throughput_class"),
                "\n".join(structured.get("recommended_for", [])) or None,
                structured.get("default_parallelization_assumption"),
                None,
            ),
        )
        inserted_row = cursor.fetchone()
        inserted = inserted_row is not None

        cursor.execute("select id from workflow_template where slug = %s", (structured["slug"],))
        workflow_template_id = cursor.fetchone()[0]

        cursor.execute(
            "delete from workflow_assumption where workflow_template_id = %s",
            (workflow_template_id,),
        )
        cursor.execute(
            "delete from workflow_edge where workflow_template_id = %s",
            (workflow_template_id,),
        )
        cursor.execute(
            "delete from workflow_step_template where workflow_template_id = %s",
            (workflow_template_id,),
        )

        step_ids = []
        for step in structured.get("step_templates", []):
            cursor.execute(
                """
                insert into workflow_step_template (
                  workflow_template_id, step_name, step_type, duration_p10_hours,
                  duration_typical_hours, duration_p90_hours, queue_time_typical_hours,
                  hands_on_hours, direct_cost_usd_typical, outsourced, parallelizable,
                  failure_probability, output_artifact, input_artifact, notes
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                returning id
                """,
                (
                    workflow_template_id,
                    step["step_name"],
                    step["step_type"],
                    step.get("duration_p10_hours"),
                    step.get("duration_typical_hours"),
                    step.get("duration_p90_hours"),
                    step.get("queue_time_typical_hours"),
                    step.get("hands_on_hours"),
                    step.get("direct_cost_usd_typical"),
                    step.get("outsourced", False),
                    step.get("parallelizable", False),
                    step.get("failure_probability"),
                    step.get("output_artifact"),
                    step.get("input_artifact"),
                    step.get("notes"),
                ),
            )
            step_ids.append(cursor.fetchone()[0])

        for from_step_id, to_step_id in zip(step_ids, step_ids[1:]):
            cursor.execute(
                """
                insert into workflow_edge (workflow_template_id, from_step_id, to_step_id, edge_type)
                values (%s, %s, %s, %s)
                """,
                (workflow_template_id, from_step_id, to_step_id, "depends_on"),
            )

        for index, note in enumerate(structured.get("assumption_notes", []), start=1):
            cursor.execute(
                """
                insert into workflow_assumption (
                  workflow_template_id, assumption_kind, assumption_name, value_text, rationale
                )
                values (%s, %s, %s, %s, %s)
                """,
                (
                    workflow_template_id,
                    "seed_note",
                    f"assumption_note_{index}",
                    note,
                    "Bootstrapped from knowledge seed bundle.",
                ),
            )

        return inserted, len(step_ids)

    @staticmethod
    def _insert_distinct_rows(
        cursor: Any,
        table_name: str,
        column_sql: str,
        rows: list[tuple[Any, ...]],
        exists_predicate_sql: str,
    ) -> None:
        if not rows:
            return
        placeholders = ", ".join(["%s"] * len(rows[0]))
        for row in rows:
            cursor.execute(
                f"""
                insert into {table_name} ({column_sql})
                select {placeholders}
                where not exists (
                  select 1 from {table_name}
                  where {exists_predicate_sql}
                )
                """,
                row + row,
            )
