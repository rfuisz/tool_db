# Review Extract v1

Convert one review or synthesis source into a `review_extract_v1` packet.

## Rules

- Extract broad, source-backed summaries and candidate toolkit items.
- Do not invent experiment-level validation observations that are not directly stated in the review.
- Extract workflow-stage observations when the review explicitly describes a funnel or workflow ladder, including in silico prefiltering, library build, broad screening, counter-screens, functional characterization, and confirmatory stages.
- Treat these as descriptive workflow evidence, not as permission to guess exact timings, candidate counts, or a canonical workflow mapping.
- Capture the stated reason for narrowing the funnel when available, especially when early stages optimize one property while guarding against later bottlenecks like poor expression, toxicity, manufacturability, or immunogenicity.
- Use `recommended_seed_item_local_ids` only for entities that appear central enough to seed curation.
- If the source lacks enough detail to support extraction, leave arrays empty and explain the evidence boundary in `unresolved_ambiguities`.
- Use only evidence present in the job payload, especially `title`, `abstract_text`, and any explicitly provided metadata.
- Do not turn topic labels or journal metadata into unsupported claims.
- If a toolkit item is named directly in the title or abstract, it is acceptable to emit an `entity_candidate` even when deeper review claims remain sparse.
- Do not emit toolkit-item candidates from concept metadata alone unless the same entity is also supported by the title or abstract text.
- If you set `item_type`, use only canonical-safe values such as `protein_domain`, `multi_component_switch`, `rna_element`, `construct_pattern`, `engineering_method`, `assay_method`, `computation_method`, or `delivery_harness`; otherwise omit `item_type`.
- Set `citation_role_suggestion` only when the source clearly fits an existing canonical citation role such as `foundational`, `best_review`, `independent_validation`, `benchmark`, `protocol`, `therapeutic`, `negative_result`, `structural`, or `database_reference`; otherwise omit it.

## Output Contract

Validate against `schemas/extraction/review_extract.v1.schema.json`.

## Minimal Valid Output

- If evidence is thin, return:
  - `entity_candidates: []`
  - `claims: []`
  - `workflow_stage_observations: []`
  - `recommended_seed_item_local_ids: []`
  - `unresolved_ambiguities`: one or more ambiguity objects that explain the evidence boundary
- If the review title or abstract explicitly names toolkit items, extract those entities conservatively using the field shapes from `common.v1.schema.json`.
- Use `recommended_seed_item_local_ids` only for extracted entities that appear central to the review's stated scope.
- If the review explicitly lays out a staged funnel, emit one `workflow_stage_observation` per described stage in order. Leave omitted stage fields blank rather than inferring them from general domain knowledge.
