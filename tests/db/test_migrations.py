from pathlib import Path


def test_latest_migration_matches_canonical_schema() -> None:
    canonical_schema = Path("schemas/canonical/schema_v1.sql").read_text().strip()
    migration_schema = Path("db/migrations/0001_canonical_schema_v1.sql").read_text().strip()

    assert migration_schema == canonical_schema
