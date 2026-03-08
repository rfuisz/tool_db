from pathlib import Path
from typing import Any, List, Optional, Tuple

from tool_db_backend.config import Settings
from tool_db_backend.postgres_loader import LoadPlanExecutionError


class MigrationRunner:
    TRACKING_TABLE = "schema_migration"
    BASELINE_MIGRATION = "0001_canonical_schema_v1.sql"
    BASELINE_SENTINEL_TABLE = "public.toolkit_item"

    def __init__(self, settings: Settings, connection: Any = None) -> None:
        self.settings = settings
        self._connection = connection

    def list_migration_paths(self) -> List[Path]:
        return sorted((self.settings.repo_root / "db" / "migrations").glob("*.sql"))

    def apply_all(self) -> List[str]:
        conn, should_close = self._get_connection()
        applied = []
        try:
            with conn.transaction():
                with conn.cursor() as cursor:
                    self._ensure_tracking_table(cursor)
                    self._bootstrap_baseline_if_needed(cursor)
                    already_applied = self._applied_migration_names(cursor)
                    for path in self.list_migration_paths():
                        if path.name in already_applied:
                            continue
                        cursor.execute(path.read_text())
                        cursor.execute(
                            f"insert into {self.TRACKING_TABLE} (name) values (%s)",
                            (path.name,),
                        )
                        applied.append(path.name)
        finally:
            if should_close:
                conn.close()
        return applied

    def _ensure_tracking_table(self, cursor: Any) -> None:
        cursor.execute(
            f"""
            create table if not exists {self.TRACKING_TABLE} (
              name text primary key,
              applied_at timestamptz not null default now()
            )
            """
        )

    def _bootstrap_baseline_if_needed(self, cursor: Any) -> None:
        cursor.execute(f"select count(*) from {self.TRACKING_TABLE}")
        tracked_count = cursor.fetchone()[0]
        if tracked_count:
            return

        cursor.execute("select to_regclass(%s)", (self.BASELINE_SENTINEL_TABLE,))
        sentinel_exists = cursor.fetchone()[0] is not None
        if not sentinel_exists:
            return

        cursor.execute(
            f"insert into {self.TRACKING_TABLE} (name) values (%s) on conflict (name) do nothing",
            (self.BASELINE_MIGRATION,),
        )

    def _applied_migration_names(self, cursor: Any) -> set[str]:
        cursor.execute(f"select name from {self.TRACKING_TABLE}")
        return {row[0] for row in cursor.fetchall()}

    def _get_connection(self) -> Tuple[Any, bool]:
        if self._connection is not None:
            return self._connection, False
        if not self.settings.database_url:
            raise LoadPlanExecutionError("DATABASE_URL is required to apply migrations.")

        import psycopg

        return psycopg.connect(self.settings.database_url), True
