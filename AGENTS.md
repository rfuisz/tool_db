# Repository Operating Rules

## First Principles

- Treat `claim + context + evidence` as the primary unit of truth.
- Keep canonical entities separate from raw extraction output.
- Prefer derived rollups over hand-maintained summary booleans.
- Make every public score explainable and versioned.

## Schema Safety

- Never write LLM extraction output directly into canonical tables.
- Any canonical schema change must update schema docs and migrations together.
- Use controlled vocabularies where the same concept appears across ingestion, storage, and UI layers.
- Keep merge logic conservative; false merges are worse than temporary duplicates.
- Mechanisms describe biophysical processes (photocleavage, heterodimerization); techniques describe engineering methodologies (computational design, selection/enrichment). Do not conflate them.

## Evidence Discipline

- Every item dossier should surface ranked citations.
- Contradictory evidence should be stored, not flattened away.
- Retractions, corrections, and orphan-tool signals must reduce confidence rather than being silently ignored.
- Validation claims are context-dependent; preserve host, assay, delivery, and construct details.

## Workflow Modeling

- Model DBTL timing and cost at the step level.
- Keep sequencing, verification, assay, and delivery choices explicit rather than collapsing them into generic booleans.
- Record the rationale and source for timing and cost assumptions.

## Editing Guidance

- Prefer additive changes over speculative rewrites.
- Keep dossier files stable and legible for both humans and agents.
- When in doubt, leave a `TODO` with the missing evidence boundary instead of inventing facts.

## Backend Subagent Routing

Use these routes before changing `src/tool_db_backend/`, `schemas/`, or extraction-driven dossier flows.

| Task | Primary subagent | Read first | Return before editing |
| --- | --- | --- | --- |
| Canonical schema or vocabulary change | `schema-critic` | `AGENTS.md`, `.cursor/rules/10-schema-safety.mdc`, `.cursor/rules/20-extraction-contracts.mdc` | schema delta, risks, migration/docs checklist |
| Extraction packet, prompt, or normalization boundary | `literature-curator` + `schema-critic` | `.cursor/rules/20-extraction-contracts.mdc` | packet shape, ambiguities, canonical handoff notes |
| Candidate matching, merge safety, or claim-subject resolution | `entity-resolution-auditor` | `AGENTS.md`, `.cursor/rules/10-schema-safety.mdc` | match/new/review recommendation with blockers |
| Replication or practicality scoring | `replication-auditor` | `.cursor/rules/30-citation-and-replication.mdc` | score inputs, penalties, confidence blockers |
| DBTL timing, cost, or workflow rollups | `workflow-modeler` | `AGENTS.md` | step table, assumptions, critical path |
| Gap-to-tool ranking and explainability | `gap-linker` | `.cursor/rules/40-gap-map-linking.mdc` | score breakdown, missing evidence, blockers |

If a task spans multiple rows, run the subagents in that order and pass forward the written output from the previous step.

## Test Visibility

- `tests/` is hidden from Cursor-style agent search by default via `.cursorignore`.
- To reveal the suite intentionally, run `python scripts/agent_test_visibility.py show`.
- To restore the barrier afterward, run `python scripts/agent_test_visibility.py hide`.
- Check the current state with `python scripts/agent_test_visibility.py status`.
