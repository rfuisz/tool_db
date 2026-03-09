# Review Extract v1

Convert one review or synthesis source into a `review_extract_v1` packet.

## Rules

- Extract broad, source-backed summaries and candidate toolkit items.
- Do not invent experiment-level validation observations that are not directly stated in the review.
- Extract workflow-stage observations when the review explicitly describes a funnel or workflow ladder, including in silico prefiltering, library build, broad screening, counter-screens, functional characterization, and confirmatory stages.
- Treat these as descriptive workflow evidence, not as permission to guess exact timings, candidate counts, or a canonical workflow mapping.
- If the review explicitly names a workflow archetype or campaign as a distinct entity, emit a `workflow_template` candidate and use its local ID as `workflow_local_id` on the relevant stage observations.
- Capture the stated reason for narrowing the funnel when available, especially when early stages optimize one property while guarding against later bottlenecks like poor expression, toxicity, manufacturability, or immunogenicity.
- Use `recommended_seed_item_local_ids` only for entities that appear central enough to seed curation.
- If the source lacks enough detail to support extraction, leave arrays empty and explain the evidence boundary in `unresolved_ambiguities`.
- Use only evidence present in the job payload, especially `title`, `abstract_text`, and any explicitly provided metadata.
- Preserve the provided `source_document` metadata exactly when it is already present in the job payload, including IDs, `abstract_text`, license flags, and raw payload references.
- Do not turn topic labels or journal metadata into unsupported claims.
- If a toolkit item is named directly in the title or abstract, it is acceptable to emit an `entity_candidate` even when deeper review claims remain sparse.
- Emit `toolkit_item` candidates only for discrete tools, tool components, engineered constructs, delivery harnesses, or named methods/assays that could plausibly become collection records.
- Do not emit plain genes, endogenous proteins, receptors, enzymes, pathways, compounds, cell types, tissues, species, or diseases as `toolkit_item` candidates unless the review clearly treats them as the tool itself or as a named engineered construct/pattern.
- If a broad class or topic is useful context but is not a collection-worthy item, emit it as `candidate_type: "concept_label"` instead of `toolkit_item`.
- Do not emit toolkit-item candidates from concept metadata alone unless the same entity is also supported by the title or abstract text.
- If you set `item_type`, use only canonical-safe values such as `protein_domain`, `multi_component_switch`, `rna_element`, `construct_pattern`, `engineering_method`, `assay_method`, `computation_method`, or `delivery_harness`; otherwise omit `item_type`.
- When choosing `item_type`, prefer the thing itself over the fact that it was engineered:
  - use method types for named practices, protocols, algorithms, or assays
  - use `multi_component_switch` or `construct_pattern` for named engineered systems, circuits, modules, or constructs
  - use `delivery_harness` for named delivery strategies or vehicles such as AAV, LNP, viral vectors, or electroporation-based deployment packages
- Do not label a named engineered system as `engineering_method` just because the review discusses engineering it.
- For every emitted `toolkit_item`, explicitly ask yourself:
  - how is this useful?
  - what problem does it solve?
  - what are the main implementation constraints or prerequisites?
  - what strengths or weaknesses relative to nearby alternatives are directly stated in the review?
- If the title or abstract supports those answers, store them on the entity candidate using `useful_for`, `problem_solved`, `strengths`, `limitations`, `implementation_constraints`, and `facet_hints`.
- Keep those fields short, source-backed, and empty rather than speculative when the evidence is thin.
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
- Metadata-only packets are valid extraction outputs, but they remain review-only until there is source-backed entity, claim, or workflow evidence.
- If the review title or abstract explicitly names toolkit items, extract those entities conservatively using the field shapes from `common.v1.schema.json`.
- Use `recommended_seed_item_local_ids` only for extracted entities that appear central to the review's stated scope.
- Do not use `recommended_seed_item_local_ids` for broad classes, topic labels, or generic biological categories that are unlikely to survive canonicalization.
- If the review explicitly lays out a staged funnel, emit one `workflow_stage_observation` per described stage in order. Leave omitted stage fields blank rather than inferring them from general domain knowledge.
