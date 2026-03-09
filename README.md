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
4. Populate the local database with checked-in literature and Gap Map packets using `.venv/bin/python -m apps.worker.main populate-local-db`.
5. Recompute canonical item explainers, comparisons, facets, and scores with `.venv/bin/python -m apps.worker.main materialize-item-details` when you change derivation logic without reingesting.

Worker commands now emit progress logs by default for long-running passes such as `materialize-item-details`. Set `LOG_LEVEL=DEBUG` if you want more verbose worker-side tracing.

Recommended local `DATABASE_URL`:

```text
postgresql://tooldb:tooldb@localhost:5432/tooldb
```

## Hosted Render Sync

The repo now includes a root `render.yaml` blueprint that provisions:

- a managed Render Postgres database
- a private Python API/data service
- the Next.js web app

The hosted sync model is git-driven. On each Render deploy, the API service runs:

```bash
python -m apps.worker.main populate-local-db
```

That reruns migrations, reloads the checked-in seed bundle, ingests the checked-in extraction artifacts into hosted Postgres, and rematerializes canonical item detail outputs before traffic shifts.

Practical implication:

- if the change exists in tracked repo artifacts and you push it, Render will pick it up
- if the change exists only in your local Postgres, Render cannot see it until you export or check in the corresponding repo state

For one-off curator syncs from localhost, the local web app now exposes a top-nav `Sync Render DB` control. It runs a preflight against the hosted Render Postgres target, then overwrites that hosted database from your local `DATABASE_URL` after confirmation.

## Core Modeling Rule

The primary unit of truth is `claim + context + evidence`.

Human-readable summaries such as "has mouse validation" or "used therapeutically" are derived views built from source-backed observations, not hand-entered booleans.

## Hierarchy Browsing

The web hierarchy is intentionally built as two branches beneath workflows:

- mechanism `->` architecture `->` component
- technique `->` method

When the browse UI builds those branches, low-level items are rolled upward conservatively from explicit tags first, then from architecture/component context when needed. Top-level mechanism and technique sections also synthesize short coverage summaries so a concept like `conformational_uncaging` can explain both what it means and which current toolkit items support it.

Those synthesized concepts are also available as dedicated app routes under `/mechanisms`, `/mechanisms/[slug]`, `/techniques`, and `/techniques/[slug]`.

Paper ingestion now treats workflows as a two-layer model:

- `paper-observed workflow` captures what a source actually did, why it ordered tests the way it did, and which mechanisms/techniques/properties it was optimizing for
- `canonical workflow template` captures the reusable archetype promoted from multiple sources or curated evidence

First-pass workflow extraction can now preserve workflow-level logic, stage observations, and ordered step observations instead of flattening everything into stage-only notes.

## Current Scope

This initialization focuses on:

- schema and taxonomy bootstrap
- extraction contracts
- repo and agent legibility
- seed dossier structure

It does not yet include production ingestion jobs, a live API, or a public web viewer, but it now includes a conservative local ingestion path for checked-in literature extractions and client-source packet artifacts.

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

1. Improve the review-to-promotion path for new literature item candidates that do not safely resolve to existing canonicals.
2. Add fuller typed staging and downstream canonical mapping for trial and OptoBase source artifacts.
3. Expand source-backed validation and replication coverage from checked-in packets to larger curated batches.
4. Replace remaining seed dossier placeholders with curator-backed evidence packs.

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
