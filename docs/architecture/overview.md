# Architecture Overview

## Source Of Truth

PostgreSQL is the canonical store for normalized entities, evidence records, validation observations, workflow templates, and scored links.

Use `JSONB` for raw payload shadows and long-tail structured fields that do not yet justify new columns. Use `pgvector` later for claim and chunk retrieval once ingestion is live.

## Data Flow

1. Acquire source payloads and raw text from external systems.
2. Store untouched payloads in object storage or an equivalent raw cache.
3. Extract typed intermediate packets that validate against `schemas/extraction/`.
4. Normalize units, IDs, synonyms, vocab values, and citation roles deterministically.
5. Merge conservatively into canonical tables.
6. Materialize summaries for dossiers, rankings, replication rollups, and workflow fit.

## Service Split

- `api`: read/write and curation endpoints
- `worker`: ingestion, extraction, normalization, scoring, and sync jobs
- `web`: public and curator-facing viewer

## Design Guardrails

- Avoid black-box scoring.
- Keep evidence provenance inspectable.
- Do not encode context-sensitive biology as flat booleans.
- Treat gap linking as a computed layer between a problem catalog and a tool catalog.
