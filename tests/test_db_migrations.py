from tool_db_backend.config import get_settings
from tool_db_backend.db_migrations import MigrationRunner


class _FakeTransaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _MigrationCursor:
    def __init__(self, statements):
        self.statements = statements

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement):
        self.statements.append(statement)


class _MigrationConnection:
    def __init__(self):
        self.statements = []

    def transaction(self):
        return _FakeTransaction()

    def cursor(self):
        return _MigrationCursor(self.statements)


def test_migration_runner_executes_all_sql_files() -> None:
    connection = _MigrationConnection()
    runner = MigrationRunner(get_settings(), connection=connection)

    applied = runner.apply_all()

    assert "0001_canonical_schema_v1.sql" in applied
    assert any("create table toolkit_item" in statement for statement in connection.statements)
