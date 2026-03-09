# Repository Operating Rules

## First Principles

- Treat `claim + context + evidence` as the primary unit of truth.
- Keep canonical entities separate from raw extraction output.
- Prefer derived rollups over hand-maintained summary booleans.
- Make every public score explainable and versioned.

## Database Safety

- NEVER run `populate-local-db`, `run-migrations`, `execute-load-plan --apply`, `load-seed-bundle`, `rematerialize-stale`, `materialize-item-details`, `materialize-gap-links`, `synthesize-item-profiles`, or any other DB-mutating worker command without explicit user confirmation.
- The developer's local Postgres database contains curated data that is expensive to rebuild. Accidentally running a populate or migration command can overwrite or corrupt it.
- Read-only commands (`staleness-report`, `validate-packet`, `export-seeds`, `normalize-packet`, `build-load-plan`) are safe to run without confirmation.
- When diagnosing deployment issues, inspect code, config, logs, and remote endpoints — do not replay the pipeline locally as a shortcut.

## Schema Safety

- Never write LLM extraction output directly into canonical tables.
- Any canonical schema change must update schema docs and migrations together.
- Use controlled vocabularies where the same concept appears across ingestion, storage, and UI layers.
- Keep merge logic conservative; false merges are worse than temporary duplicates.
- Mechanisms describe biophysical processes (photocleavage, heterodimerization); techniques describe engineering methodologies (computational design, selection/enrichment). Do not conflate them.

## Evidence Discipline

- Every item dossier should surface ranked citations.
- Source-backed explainer prose about usefulness, constraints, and alternatives should keep document provenance when promoted beyond first-pass review.
- Contradictory evidence should be stored, not flattened away.
- Retractions, corrections, and orphan-tool signals must reduce confidence rather than being silently ignored.
- Validation claims are context-dependent; preserve host, assay, delivery, and construct details.

## Workflow Modeling

- Model DBTL timing and cost at the step level.
- Keep sequencing, verification, assay, and delivery choices explicit rather than collapsing them into generic booleans.
- Record the rationale and source for timing and cost assumptions.

## Concurrency and I/O

- Always parallelize I/O-bound calls. Never loop serially over network fetches when they can be fanned out with `ThreadPoolExecutor`.
- OpenAI API calls can handle very high parallelism; use `llm_max_concurrency` (default 64) as the worker pool size for LLM and web-research calls.
- OpenAlex has a low request-per-minute limit. Gate live API calls through `openalex_max_concurrency` (default 3) using a `threading.Semaphore`, but let cached reads bypass the semaphore so reruns stay fast.
- Other literature providers (Europe PMC, PMC BioC, Semantic Scholar, OptoBase) can use the full `llm_max_concurrency` pool width.
- Raw upstream payloads are cached in `data/raw/`; the harvester and artifact builder check for a cached payload before making any API call, so repeated corpus runs are mostly local file reads.

## Pipeline Versioning and Staleness

- Extraction and materialization outputs are version-stamped. Current versions live in `src/tool_db_backend/pipeline_versions.py`.
- Bump `EXTRACTION_VERSION` when prompts, extraction schemas, or first-pass loader normalization logic changes.
- Bump `MATERIALIZATION_VERSION` when `ItemMaterializer` derivation logic, scoring formulas, or explainer templates change.
- Rows with a version below the current constant are stale and eligible for re-processing.
- Use `python apps/worker/main.py staleness-report` to see how many items need re-extraction or re-materialization.
- Use `python apps/worker/main.py rematerialize-stale` to re-derive content for stale items.
- Entity resolution results are cached in `entity_match_cache`. The cache auto-invalidates when the item count changes; call `EntityResolver.invalidate_match_cache()` after bulk item additions or name changes.
- When adding a new extraction field or prompt version, update `EXTRACTION_VERSION` and the migration backfill pattern so existing rows get correctly classified as legacy.

## Editing Guidance

- Prefer additive changes over speculative rewrites.
- Keep dossier files stable and legible for both humans and agents.
- Keep Markdown harness files current when behavior changes. If you update agent workflows, extraction behavior, schemas, or pipeline contracts, also update the relevant `.md` sources such as `.cursor/agents/*.md`, `prompts/**/*.md`, `README.md`, and design/spec docs in the same change.
- When in doubt, leave a `TODO` with the missing evidence boundary instead of inventing facts.

## Backend Subagent Routing

Use these routes before changing `src/tool_db_backend/`, `schemas/`, or extraction-driven dossier flows.

| Task                                                          | Primary subagent                       | Read first                                                                                     | Return before editing                              |
| ------------------------------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Canonical schema or vocabulary change                         | `schema-critic`                        | `AGENTS.md`, `.cursor/rules/10-schema-safety.mdc`, `.cursor/rules/20-extraction-contracts.mdc` | schema delta, risks, migration/docs checklist      |
| Extraction packet, prompt, or normalization boundary          | `literature-curator` + `schema-critic` | `.cursor/rules/20-extraction-contracts.mdc`                                                    | packet shape, ambiguities, canonical handoff notes |
| Candidate matching, merge safety, or claim-subject resolution | `entity-resolution-auditor`            | `AGENTS.md`, `.cursor/rules/10-schema-safety.mdc`                                              | match/new/review recommendation with blockers      |
| Replication or practicality scoring                           | `replication-auditor`                  | `.cursor/rules/30-citation-and-replication.mdc`                                                | score inputs, penalties, confidence blockers       |
| DBTL timing, cost, or workflow rollups                        | `workflow-modeler`                     | `AGENTS.md`                                                                                    | step table, assumptions, critical path             |
| Gap-to-tool ranking and explainability                        | `gap-linker`                           | `.cursor/rules/40-gap-map-linking.mdc`                                                         | score breakdown, missing evidence, blockers        |

If a task spans multiple rows, run the subagents in that order and pass forward the written output from the previous step.

## Test Visibility

- `tests/` is hidden from Cursor-style agent search by default via `.cursorignore`.
- To reveal the suite intentionally, run `python scripts/agent_test_visibility.py show`.
- To restore the barrier afterward, run `python scripts/agent_test_visibility.py hide`.
- Check the current state with `python scripts/agent_test_visibility.py status`.
