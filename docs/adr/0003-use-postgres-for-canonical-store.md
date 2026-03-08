# ADR 0003: Use PostgreSQL for the Canonical Store

## Status

Accepted

## Context

The canonical schema already depends on PostgreSQL-specific capabilities:

- enum types for controlled state and modality fields
- `jsonb` for structured long-tail payloads
- `pgcrypto` for UUID generation
- `pgvector` for future claim and chunk retrieval

The current loader and migration code also assume a PostgreSQL connection via `psycopg`.

Adding a parallel SQLite canonical path would create a second persistence model with different typing, migration behavior, and feature limits. That would make local development drift away from production exactly where evidence, provenance, and conservative merges matter most.

## Decision

Use PostgreSQL as the single canonical database for both local development and hosted environments.

For local development:

- run PostgreSQL in Docker using `docker-compose.local.yml`
- point `DATABASE_URL` at that local instance
- run the repo migrations against the same schema used in hosted environments

SQLite may still be used later for narrow local caches or one-off tooling, but not as the canonical application database.

## Consequences

- local development matches production semantics more closely
- migrations, loaders, and future scoring jobs only need one canonical backend
- hosted deployment can use a managed PostgreSQL provider without changing schema assumptions
- development machines need Docker or another PostgreSQL runtime available
