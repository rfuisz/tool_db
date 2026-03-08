from pathlib import Path
from typing import Any, List, Optional, Tuple

from tool_db_backend.config import Settings
from tool_db_backend.postgres_loader import LoadPlanExecutionError


class MigrationRunner:
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
                    for path in self.list_migration_paths():
                        cursor.execute(path.read_text())
                        applied.append(path.name)
        finally:
            if should_close:
                conn.close()
        return applied

    def _get_connection(self) -> Tuple[Any, bool]:
        if self._connection is not None:
            return self._connection, False
        if not self.settings.database_url:
            raise LoadPlanExecutionError("DATABASE_URL is required to apply migrations.")

        import psycopg

        return psycopg.connect(self.settings.database_url), True
