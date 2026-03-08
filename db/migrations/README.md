# Migrations

Canonical schema SQL now ships in versioned migration files:

- `0001_canonical_schema_v1.sql`
- `0002_workflow_stage_templates.sql`
- `0003_workflow_stage_assumption_fk.sql`
- `0004_modality_recombination.sql`
- `0005_first_pass_extractions.sql`

## Rule

Keep `schemas/canonical/schema_v1.sql` aligned with the cumulative canonical schema, and add a new append-only migration for any schema delta.

The migration runner records applied files in `schema_migration` and skips previously applied entries. For pre-tracking local databases that already contain the canonical tables, the runner bootstraps `0001_canonical_schema_v1.sql` as applied before running newer migrations.
