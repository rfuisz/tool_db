# Primary Paper Extract v1

Convert one literature source into a `primary_paper_extract_v1` packet.

## Rules

- Extract only source-backed claims.
- Keep claims, contexts, metrics, and validation observations separate.
- Extract workflow-stage observations when the source explicitly describes a multi-stage funnel, such as in silico filtering, library generation, broad screening, selection, counter-screening, secondary characterization, or confirmatory validation.
- Treat workflow stages as source-backed process observations, not as guessed canonical workflow templates.
- Capture why the funnel narrows when the source says so: what each stage enriches for, what it guards against, and what downstream property the authors are trying to preserve.
- Use empty arrays rather than invented content when the source text is insufficient.
- Put any unresolved merge, subject, or context uncertainty into `unresolved_ambiguities`.
- Use only evidence present in the job payload, especially `title`, `abstract_text`, and any explicitly provided metadata.
- Do not infer toolkit items, validation observations, or replication booleans from topic labels alone.
- Do not invent stage counts, gating criteria, or counterselection logic if the source only implies that screening happened.
- Leave `replication_signals` as `{}` unless a field is directly supported by the provided evidence.
- If you set `item_type`, use only canonical-safe values such as `protein_domain`, `multi_component_switch`, `rna_element`, `construct_pattern`, `engineering_method`, `assay_method`, `computation_method`, or `delivery_harness`; otherwise omit `item_type`.
- Set `citation_role_suggestion` only when the source clearly fits an existing canonical citation role such as `foundational`, `best_review`, `independent_validation`, `benchmark`, `protocol`, `therapeutic`, `negative_result`, `structural`, or `database_reference`; otherwise omit it.
- If you emit any `validation_observations`, every observation must include `success_outcome` with one of: `success`, `mixed`, or `failed`.
- Do not create partial validation observations; if the abstract does not support a full schema-valid observation, return `validation_observations: []` instead.

## Output Contract

Validate against `schemas/extraction/primary_paper_extract.v1.schema.json`.

## Harness Notes

- The caller caches JSON extraction responses against the full request payload, so prompt edits intentionally create a new cache key.
- Keep instructions deterministic and source-focused so repeated runs for the same job can reuse the cache safely.

## Minimal Valid Output

- If evidence is thin, return:
  - `entity_candidates: []`
  - `claims: []`
  - `validation_observations: []`
  - `workflow_stage_observations: []`
  - `replication_signals: {}`
  - `unresolved_ambiguities`: one or more ambiguity objects that explain the evidence boundary
- If a toolkit item is explicitly named in the title or abstract, emit an `entity_candidate` using the schema fields from `common.v1.schema.json`.
- If a claim is explicit in the title or abstract, emit a `claim` with `subject_local_ids` pointing at the local IDs of the relevant extracted entities.
- If the source explicitly describes a staged screening or selection funnel, emit one `workflow_stage_observation` per stage in the reported order, using only stage kinds and fields directly supported by the source text.
