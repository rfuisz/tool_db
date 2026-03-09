"""Incremental one-directional sync from a local Postgres to a remote Postgres.

Reads the ``sync_watermark`` on the remote, then for each table (in FK-safe
order) upserts rows whose ``updated_at > watermark`` and deletes rows whose
primary keys no longer exist locally.  Outputs a JSON report to stdout.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence, Tuple

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FK topology: tables ordered so parents come before children.
# Built from the FK graph; verified against the live schema in the plan.
# ---------------------------------------------------------------------------

TABLES_TOPO_ORDER: list[str] = [
    # Tier 0 – no FK parents
    "toolkit_item",
    "source_document",
    "property_definition",
    "gap_field",
    "gap_resource",
    "workflow_template",
    "entity_match_cache",
    # Tier 1
    "extraction_run",
    "source_chunk",
    "gap_capability",
    "gap_item",
    "workflow_stage_template",
    "item_citation",
    "item_comparison",
    "item_component",
    "item_explainer",
    "item_facet",
    "item_mechanism",
    "item_related_item",
    "item_synonym",
    "item_target_process",
    "item_technique",
    "assay_method_profile",
    "computation_method_profile",
    "engineering_method_profile",
    "protein_domain_profile",
    "replication_summary",
    "switch_profile",
    "validation_observation",
    "workflow_mechanism",
    "workflow_technique",
    # Tier 2
    "extracted_packet",
    "workflow_step_template",
    "gap_capability_resource",
    "gap_item_capability",
    "item_gap_link",
    "item_problem_link",
    "validation_metric_value",
    "workflow_design_goal",
    "workflow_item_role",
    # Tier 3
    "extracted_item_candidate",
    "extracted_claim_candidate",
    "workflow_edge",
    "workflow_assumption",
    "workflow_instance_observation",
    # Tier 4
    "extracted_claim",
    "extracted_workflow_observation",
    "extracted_workflow_stage_observation",
    "extracted_workflow_step_observation",
    "extracted_claim_subject_candidate",
    # Tier 5
    "claim_metric",
    "claim_subject_link",
    "item_property_value",
]

TABLE_PKS: dict[str, list[str]] = {
    "assay_method_profile": ["item_id"],
    "claim_metric": ["id"],
    "entity_match_cache": ["id"],
    "claim_subject_link": ["id"],
    "computation_method_profile": ["item_id"],
    "engineering_method_profile": ["item_id"],
    "extracted_claim": ["id"],
    "extracted_claim_candidate": ["id"],
    "extracted_claim_subject_candidate": ["id"],
    "extracted_item_candidate": ["id"],
    "extracted_packet": ["id"],
    "extracted_workflow_observation": ["id"],
    "extracted_workflow_stage_observation": ["id"],
    "extracted_workflow_step_observation": ["id"],
    "extraction_run": ["id"],
    "gap_capability": ["id"],
    "gap_capability_resource": ["gap_capability_id", "gap_resource_id"],
    "gap_field": ["id"],
    "gap_item": ["id"],
    "gap_item_capability": ["gap_item_id", "gap_capability_id"],
    "gap_resource": ["id"],
    "item_citation": ["id"],
    "item_comparison": ["id"],
    "item_component": ["id"],
    "item_explainer": ["id"],
    "item_facet": ["id"],
    "item_gap_link": ["id"],
    "item_mechanism": ["id"],
    "item_problem_link": ["id"],
    "item_property_value": ["id"],
    "item_related_item": ["id"],
    "item_synonym": ["id"],
    "item_target_process": ["id"],
    "item_technique": ["id"],
    "property_definition": ["id"],
    "protein_domain_profile": ["item_id"],
    "replication_summary": ["item_id"],
    "source_chunk": ["id"],
    "source_document": ["id"],
    "switch_profile": ["item_id"],
    "toolkit_item": ["id"],
    "validation_metric_value": ["id"],
    "validation_observation": ["id"],
    "workflow_assumption": ["id"],
    "workflow_design_goal": ["id"],
    "workflow_edge": ["id"],
    "workflow_instance_observation": ["id"],
    "workflow_item_role": ["id"],
    "workflow_mechanism": ["workflow_template_id", "mechanism_name"],
    "workflow_stage_template": ["id"],
    "workflow_step_template": ["id"],
    "workflow_technique": ["workflow_template_id", "technique_name"],
    "workflow_template": ["id"],
}


def _get_columns(conn: Any, table: str) -> list[str]:
    """Return column names for *table* in ordinal order."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s "
            "ORDER BY ordinal_position",
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def _get_jsonb_columns(conn: Any, table: str) -> set[str]:
    """Return the set of column names with data_type 'jsonb'."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s AND data_type='jsonb'",
            (table,),
        )
        return {row[0] for row in cur.fetchall()}


def _adapt_params(row: dict, cols: list[str], jsonb_cols: set[str]) -> dict:
    """Wrap jsonb values with Jsonb() so psycopg can serialize them."""
    params: dict = {}
    for c in cols:
        val = row[c]
        if c in jsonb_cols and val is not None:
            params[c] = Jsonb(val)
        else:
            params[c] = val
    return params


def _read_watermark(remote: Any) -> datetime:
    with remote.cursor() as cur:
        cur.execute(
            "SELECT last_synced_at FROM sync_watermark WHERE id='default'"
        )
        row = cur.fetchone()
        if row is None:
            return datetime(1970, 1, 1, tzinfo=timezone.utc)
        return row[0]


def _write_watermark(remote: Any, ts: datetime) -> None:
    with remote.cursor() as cur:
        cur.execute(
            "INSERT INTO sync_watermark (id, last_synced_at) VALUES ('default', %s) "
            "ON CONFLICT (id) DO UPDATE SET last_synced_at = EXCLUDED.last_synced_at",
            (ts,),
        )


def _upsert_table(
    local: Any,
    remote: Any,
    table: str,
    watermark: datetime,
) -> int:
    """Upsert rows changed since *watermark*. Returns rows upserted."""
    pk_cols = TABLE_PKS[table]
    local_cols = _get_columns(local, table)
    remote_cols = _get_columns(remote, table)
    cols = [c for c in local_cols if c in remote_cols]
    if not cols:
        return 0

    jsonb_cols = _get_jsonb_columns(local, table)

    with local.cursor(row_factory=dict_row) as lcur:
        lcur.execute(
            psycopg.sql.SQL("SELECT {} FROM {} WHERE updated_at > %s").format(
                psycopg.sql.SQL(", ").join(
                    psycopg.sql.Identifier(c) for c in cols
                ),
                psycopg.sql.Identifier(table),
            ),
            (watermark,),
        )
        rows = lcur.fetchall()

    if not rows:
        return 0

    non_pk_cols = [c for c in cols if c not in pk_cols]

    conflict_clause = psycopg.sql.SQL(", ").join(
        psycopg.sql.Identifier(c) for c in pk_cols
    )
    if non_pk_cols:
        update_clause = psycopg.sql.SQL(", ").join(
            psycopg.sql.SQL("{} = EXCLUDED.{}").format(
                psycopg.sql.Identifier(c), psycopg.sql.Identifier(c)
            )
            for c in non_pk_cols
        )
        on_conflict = psycopg.sql.SQL(
            "ON CONFLICT ({}) DO UPDATE SET {}"
        ).format(conflict_clause, update_clause)
    else:
        on_conflict = psycopg.sql.SQL("ON CONFLICT ({}) DO NOTHING").format(
            conflict_clause
        )

    insert_sql = psycopg.sql.SQL("INSERT INTO {} ({}) VALUES ({}) {}").format(
        psycopg.sql.Identifier(table),
        psycopg.sql.SQL(", ").join(psycopg.sql.Identifier(c) for c in cols),
        psycopg.sql.SQL(", ").join(
            psycopg.sql.Placeholder(c) for c in cols
        ),
        on_conflict,
    )

    all_params = [_adapt_params(row, cols, jsonb_cols) for row in rows]
    try:
        with remote.cursor() as rcur:
            rcur.executemany(insert_sql, all_params)
    except psycopg.errors.UniqueViolation:
        raise RuntimeError(
            f"UniqueViolation upserting {table} ({len(all_params)} rows). "
            f"The remote likely has stale rows with conflicting natural keys. "
            f"Run with --full to force a full resync."
        )

    return len(rows)


def _delete_removed_rows(
    local: Any,
    remote: Any,
    table: str,
) -> int:
    """Delete rows from *remote* whose PKs don't exist in *local*."""
    pk_cols = TABLE_PKS[table]

    with remote.cursor() as rcur:
        rcur.execute(
            psycopg.sql.SQL("SELECT {} FROM {}").format(
                psycopg.sql.SQL(", ").join(
                    psycopg.sql.Identifier(c) for c in pk_cols
                ),
                psycopg.sql.Identifier(table),
            )
        )
        remote_pks = [tuple(row) for row in rcur.fetchall()]

    if not remote_pks:
        return 0

    with local.cursor() as lcur:
        lcur.execute(
            psycopg.sql.SQL("SELECT {} FROM {}").format(
                psycopg.sql.SQL(", ").join(
                    psycopg.sql.Identifier(c) for c in pk_cols
                ),
                psycopg.sql.Identifier(table),
            )
        )
        local_pks = {tuple(row) for row in lcur.fetchall()}

    to_delete = [pk for pk in remote_pks if pk not in local_pks]
    if not to_delete:
        return 0

    where_clause = psycopg.sql.SQL(" AND ").join(
        psycopg.sql.SQL("{} = %s").format(psycopg.sql.Identifier(c))
        for c in pk_cols
    )
    delete_sql = psycopg.sql.SQL("DELETE FROM {} WHERE {}").format(
        psycopg.sql.Identifier(table),
        where_clause,
    )

    with remote.cursor() as rcur:
        rcur.executemany(delete_sql, to_delete)

    return len(to_delete)


def run_incremental_sync(
    local_url: str,
    remote_url: str,
) -> Dict[str, Any]:
    """Run an incremental sync and return a JSON-serializable report.

    If the watermark is at epoch (no prior sync), automatically falls back
    to a full sync since upserting all rows individually is too slow.
    """
    start = time.time()

    local = psycopg.connect(local_url, autocommit=False)
    remote = psycopg.connect(remote_url, autocommit=False)

    try:
        watermark = _read_watermark(remote)
        sync_start_ts = datetime.now(timezone.utc)
        logger.info("Sync watermark: %s", watermark.isoformat())

        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        if watermark <= epoch:
            logger.info("Watermark is at epoch; falling back to full sync.")
            local.close()
            remote.close()
            report = run_full_sync(local_url, remote_url)
            report["message"] = "Initial full sync (no prior watermark)."
            return report

        upsert_counts: dict[str, int] = {}
        delete_counts: dict[str, int] = {}

        # Delete rows that no longer exist locally BEFORE upserting.
        # This avoids UniqueViolation when a row was re-created with a new
        # PK but the same natural-key (secondary unique constraint) — the
        # stale remote row must be gone before the new one arrives.
        for table in reversed(TABLES_TOPO_ORDER):
            n = _delete_removed_rows(local, remote, table)
            if n:
                delete_counts[table] = n
                logger.info("Deleted %d rows from %s", n, table)

        for table in TABLES_TOPO_ORDER:
            n = _upsert_table(local, remote, table, watermark)
            if n:
                upsert_counts[table] = n
                logger.info("Upserted %d rows in %s", n, table)

        _write_watermark(remote, sync_start_ts)
        remote.execute("ANALYZE")
        remote.commit()
        local.close()
        remote.close()

        duration = round(time.time() - start, 1)
        total_upserted = sum(upsert_counts.values())
        total_deleted = sum(delete_counts.values())

        return {
            "status": "ok",
            "message": "Incremental sync complete.",
            "watermark_from": watermark.isoformat(),
            "watermark_to": sync_start_ts.isoformat(),
            "total_upserted": total_upserted,
            "total_deleted": total_deleted,
            "upsert_counts": upsert_counts,
            "delete_counts": delete_counts,
            "duration_seconds": duration,
        }
    except Exception:
        remote.rollback()
        local.close()
        remote.close()
        raise


def run_full_sync(local_url: str, remote_url: str) -> Dict[str, Any]:
    """Full truncate-and-restore via pg_dump pipe (fallback)."""
    import subprocess
    import os

    start = time.time()
    pg_bin = ""
    for candidate in ["/opt/homebrew/opt/libpq/bin", "/usr/local/opt/libpq/bin"]:
        if os.path.isdir(candidate):
            pg_bin = candidate
            break

    env = {**os.environ, "PATH": f"{pg_bin}:{os.environ.get('PATH', '')}"}

    remote = psycopg.connect(remote_url, autocommit=True)
    with remote.cursor() as cur:
        cur.execute(
            "DO $$ DECLARE r RECORD; BEGIN "
            "FOR r IN SELECT tablename FROM pg_tables "
            "WHERE schemaname='public' AND tablename <> 'schema_migration' "
            "AND tablename <> 'sync_watermark' "
            "LOOP EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE'; "
            "END LOOP; END $$;"
        )

    proc = subprocess.run(
        f'pg_dump --data-only --no-owner --no-privileges "{local_url}" '
        f'| grep -v transaction_timeout '
        f'| psql "{remote_url}"',
        shell=True,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pg_dump pipe failed: {proc.stderr[:500]}")

    sync_ts = datetime.now(timezone.utc)
    with remote.cursor() as cur:
        cur.execute(
            "INSERT INTO sync_watermark (id, last_synced_at) VALUES ('default', %s) "
            "ON CONFLICT (id) DO UPDATE SET last_synced_at = EXCLUDED.last_synced_at",
            (sync_ts,),
        )
        cur.execute("ANALYZE")
    remote.close()

    with psycopg.connect(remote_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM toolkit_item")
            render_items = cur.fetchone()[0]

    with psycopg.connect(local_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM toolkit_item")
            local_items = cur.fetchone()[0]

    return {
        "status": "ok",
        "message": "Full sync complete.",
        "local_items": local_items,
        "render_items_after": render_items,
        "duration_seconds": round(time.time() - start, 1),
    }


def main() -> None:
    """CLI entry point: python -m tool_db_backend.incremental_sync LOCAL_URL REMOTE_URL [--full]"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if len(sys.argv) < 3:
        print(
            "Usage: python -m tool_db_backend.incremental_sync LOCAL_URL REMOTE_URL [--full]",
            file=sys.stderr,
        )
        sys.exit(1)

    local_url = sys.argv[1]
    remote_url = sys.argv[2]
    full_mode = "--full" in sys.argv

    if full_mode:
        report = run_full_sync(local_url, remote_url)
    else:
        report = run_incremental_sync(local_url, remote_url)

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
