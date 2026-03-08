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
