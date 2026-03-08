# BioControl Toolkit DB

Evidence-first engineering knowledge system for biological control surfaces, engineering methods, assay methods, and DBTL workflows.

## What This Repo Starts With

- Canonical Postgres schema definitions for evidence-first modeling
- Controlled vocabularies and extraction packet contracts
- Cursor-facing repo guidance via `AGENTS.md` and scoped rules
- Seed knowledge artifacts that demonstrate the expected dossier pattern

## Local Database

Use PostgreSQL locally, not SQLite, for the canonical store.

Why:

- the schema already depends on PostgreSQL enums, `jsonb`, `pgcrypto`, and `pgvector`
- the migration and load-plan executors already use `psycopg`
- keeping local and hosted database semantics aligned is more valuable here than a lighter-weight local setup

Quick start:

1. Copy `.env.example` to `.env` and set `DATABASE_URL`.
2. Start Postgres with `docker compose -f docker-compose.local.yml up -d`.
3. Run migrations with `.venv/bin/python -m apps.worker.main run-migrations`.

Recommended local `DATABASE_URL`:

```text
postgresql://tooldb:tooldb@localhost:5432/tooldb
```

## Core Modeling Rule

The primary unit of truth is `claim + context + evidence`.

Human-readable summaries such as "has mouse validation" or "used therapeutically" are derived views built from source-backed observations, not hand-entered booleans.

## Phase 0 Scope

This initialization focuses on:

- schema and taxonomy bootstrap
- extraction contracts
- repo and agent legibility
- seed dossier structure

It does not yet include production ingestion jobs, a live API, or a public web viewer.

## Initial Layout

```text
AGENTS.md
.cursor/rules/
.cursor/agents/
docs/architecture/
docs/adr/
knowledge/items/
knowledge/workflows/
knowledge/taxonomies/
schemas/canonical/
schemas/extraction/
tests/fixtures/
```

## Next Build Steps

1. Turn `schemas/canonical/schema_v1.sql` into versioned migrations.
2. Add real source clients for OpenAlex, Semantic Scholar, ClinicalTrials.gov, and Gap Map.
3. Validate extraction packets against the JSON Schemas during ingestion.
4. Replace seed dossier placeholders with curator-backed evidence packs.

## Subagent Routing

For backend work, use the repo harness rather than treating all tasks as generic coding:

- schema or vocabulary changes: `schema-critic`
- extraction packets, prompts, and source review: `literature-curator`
- candidate matching or merge safety: `entity-resolution-auditor`
- replication or practicality scoring: `replication-auditor`
- workflow timing/cost modeling: `workflow-modeler`
- gap-to-tool scoring: `gap-linker`

## Agent Test Visibility

This repo hides `tests/` from Cursor-style agent search by default using `.cursorignore` so agents do not automatically optimize against the suite.

- Reveal tests intentionally: `python scripts/agent_test_visibility.py show`
- Re-hide tests: `python scripts/agent_test_visibility.py hide`
- Check current state: `python scripts/agent_test_visibility.py status`

This does not change `pytest` behavior, CI behavior, or the filesystem layout for humans.
