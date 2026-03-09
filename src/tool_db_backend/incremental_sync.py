"""Incremental one-directional sync from a local Postgres to a remote Postgres.

Reads the ``sync_watermark`` on the remote, then for each table (in FK-safe
order) upserts rows whose ``updated_at > watermark`` and deletes rows whose
primary keys no longer exist locally.  Outputs a JSON report to stdout.

Tables, primary keys, and topological order are discovered from the live
schema at runtime so the sync adapts automatically to migrations.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

EXCLUDED_TABLES: frozenset[str] = frozenset({
    "schema_migration",
    "sync_watermark",
    "spatial_ref_sys",
})

# ---------------------------------------------------------------------------
# Schema introspection helpers
# ---------------------------------------------------------------------------


def _get_public_tables(conn: Any) -> set[str]:
    """Return all base-table names in the public schema."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_type='BASE TABLE'"
        )
        return {row[0] for row in cur.fetchall()}


def _get_all_pks(conn: Any, tables: set[str]) -> dict[str, list[str]]:
    """Return ``{table: [pk_col, ...]}`` for every table in *tables*."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tc.table_name, kcu.column_name "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "  AND tc.table_schema = kcu.table_schema "
            "WHERE tc.table_schema = 'public' "
            "  AND tc.constraint_type = 'PRIMARY KEY' "
            "ORDER BY tc.table_name, kcu.ordinal_position"
        )
        pk_map: dict[str, list[str]] = defaultdict(list)
        for table_name, col_name in cur.fetchall():
            if table_name in tables:
                pk_map[table_name].append(col_name)
    return dict(pk_map)


def _tables_with_column(conn: Any, column: str) -> set[str]:
    """Return table names that have column *column*."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.columns "
            "WHERE table_schema='public' AND column_name=%s",
            (column,),
        )
        return {row[0] for row in cur.fetchall()}


def _build_topo_order(conn: Any, tables: set[str]) -> list[str]:
    """Topologically sort *tables* so FK parents come before children."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tc.table_name, ccu.table_name "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.constraint_column_usage ccu "
            "  ON tc.constraint_name = ccu.constraint_name "
            "  AND tc.constraint_schema = ccu.constraint_schema "
            "WHERE tc.constraint_type = 'FOREIGN KEY' "
            "  AND tc.table_schema = 'public'"
        )
        edges = cur.fetchall()

    children: dict[str, set[str]] = defaultdict(set)
    in_degree: dict[str, int] = {t: 0 for t in tables}

    for child, parent in edges:
        if child in tables and parent in tables and child != parent:
            if child not in children[parent]:
                children[parent].add(child)
                in_degree[child] += 1

    queue = deque(sorted(t for t in tables if in_degree[t] == 0))
    result: list[str] = []
    while queue:
        node = queue.popleft()
        result.append(node)
        for kid in sorted(children.get(node, set())):
            in_degree[kid] -= 1
            if in_degree[kid] == 0:
                queue.append(kid)

    remaining = sorted(tables - set(result))
    if remaining:
        logger.warning(
            "Tables unreachable in topo sort (possible FK cycle): %s",
            remaining,
        )
        result.extend(remaining)

    return result


def _discover_sync_plan(
    local: Any,
    remote: Any,
) -> Tuple[List[str], Dict[str, List[str]]]:
    """Discover syncable tables, their PKs, and topological order.

    Returns ``(topo_ordered_tables, pk_map)`` where only tables present on
    *both* sides and having an ``updated_at`` column are included.
    """
    local_tables = _get_public_tables(local) - EXCLUDED_TABLES
    remote_tables = _get_public_tables(remote) - EXCLUDED_TABLES

    common = local_tables & remote_tables
    local_only = local_tables - remote_tables
    remote_only = remote_tables - local_tables

    if local_only:
        logger.warning("Tables only on local (won't sync): %s", sorted(local_only))
    if remote_only:
        logger.warning("Tables only on remote (untouched): %s", sorted(remote_only))

    local_updated = _tables_with_column(local, "updated_at")
    remote_updated = _tables_with_column(remote, "updated_at")
    syncable = {t for t in common if t in local_updated and t in remote_updated}

    skipped = common - syncable
    if skipped:
        logger.info(
            "Tables without updated_at (skipped for incremental): %s",
            sorted(skipped),
        )

    pk_map = _get_all_pks(local, syncable)

    no_pk = syncable - set(pk_map)
    if no_pk:
        logger.warning("Tables with no PK (skipping): %s", sorted(no_pk))
        syncable -= no_pk

    topo = _build_topo_order(local, syncable)

    logger.info("Sync plan: %d tables", len(topo))
    return topo, pk_map


# ---------------------------------------------------------------------------
# Column / param helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Upsert / delete per table
# ---------------------------------------------------------------------------


def _upsert_table(
    local: Any,
    remote: Any,
    table: str,
    watermark: datetime,
    pk_cols: list[str],
) -> int:
    """Upsert rows changed since *watermark*. Returns rows upserted."""
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
    pk_cols: list[str],
) -> int:
    """Delete rows from *remote* whose PKs don't exist in *local*."""
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


# ---------------------------------------------------------------------------
# Sync entry points
# ---------------------------------------------------------------------------


def run_incremental_sync(
    local_url: str,
    remote_url: str,
) -> Dict[str, Any]:
    """Run an incremental sync and return a JSON-serializable report.

    Tables, PKs, and topological order are discovered from the live schema
    so the sync adapts automatically when migrations add or remove tables.

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

        topo, pk_map = _discover_sync_plan(local, remote)

        upsert_counts: dict[str, int] = {}
        delete_counts: dict[str, int] = {}

        # Phase 1: delete rows that no longer exist locally (reverse topo).
        # Must run BEFORE upserts to avoid UniqueViolation when a row was
        # re-created with a new PK but the same secondary unique key.
        for table in reversed(topo):
            n = _delete_removed_rows(local, remote, table, pk_map[table])
            if n:
                delete_counts[table] = n
                logger.info("Deleted %d rows from %s", n, table)

        # Phase 2: upsert changed rows (forward topo).
        for table in topo:
            n = _upsert_table(local, remote, table, watermark, pk_map[table])
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
            "tables_synced": len(topo),
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
