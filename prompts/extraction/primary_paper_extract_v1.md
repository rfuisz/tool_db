# Primary Paper Extract v1

Convert one literature source into a `primary_paper_extract_v1` packet.

## Rules

- Extract only source-backed claims.
- Keep claims, contexts, metrics, and validation observations separate.
- Extract `workflow_observations` when the source describes an end-to-end engineering campaign, not just isolated assays. Capture the paper-level objective, target properties/mechanisms, priority logic, and why the workflow is expected to work.
- Extract workflow-stage observations when the source explicitly describes a multi-stage funnel, such as in silico filtering, library generation, broad screening, selection, counter-screening, secondary characterization, or confirmatory validation.
- Extract `workflow_step_observations` when the source gives enough detail to recover ordered protocol logic within that funnel, especially when one test is done before another for a stated reason.
- Treat workflow stages as source-backed process observations, not as guessed canonical workflow templates.
- If the source explicitly names a workflow, campaign, or archetypal funnel as a distinct thing, emit a `workflow_template` entity candidate and point related stage observations at it using `workflow_local_id`.
- Capture why the funnel narrows when the source says so: what each stage enriches for, what it guards against, and what downstream property the authors are trying to preserve.
- For workflow observations and steps, capture why earlier tests are lower-cost, higher-throughput, lower-fidelity, or risk-reducing when the paper says so.
- Use `target_mechanisms` for biophysical aims and `target_techniques` for engineering/search methodology. Do not conflate them.
- Use `item_local_ids` on workflow steps only when a named extracted toolkit item is actually part of that step as the thing being engineered, screened, validated, or used as the assay/method.
- Use empty arrays rather than invented content when the source text is insufficient.
- Put any unresolved merge, subject, or context uncertainty into `unresolved_ambiguities`.
- Use only evidence present in the job payload, especially `title`, `abstract_text`, and any explicitly provided metadata.
- Preserve the provided `source_document` metadata exactly when it is already present in the job payload, including IDs, `abstract_text`, license flags, and raw payload references.
- Do not infer toolkit items, validation observations, or replication booleans from topic labels alone.
- Emit `toolkit_item` candidates only for discrete tools, tool components, engineered constructs, delivery harnesses, or named methods/assays that could plausibly deserve a collection record.
- Do not emit plain genes, endogenous proteins, receptors, enzymes, pathways, compounds, cell types, tissues, species, or diseases as `toolkit_item` candidates unless the source clearly presents them as the tool itself or as a named engineered construct/pattern.
- If a broad class or topic still matters for interpretation but is not a collection-worthy item, emit it as `candidate_type: "concept_label"` instead of `toolkit_item`.
- Do not invent stage counts, gating criteria, or counterselection logic if the source only implies that screening happened.
- Leave `replication_signals` as `{}` unless a field is directly supported by the provided evidence.
- If you set `item_type`, use only canonical-safe values such as `protein_domain`, `multi_component_switch`, `rna_element`, `construct_pattern`, `engineering_method`, `assay_method`, `computation_method`, or `delivery_harness`; otherwise omit `item_type`.
- When choosing `item_type`, prefer the thing itself over the fact that it was engineered:
  - use `engineering_method`, `assay_method`, or `computation_method` for named practices, protocols, algorithms, or measurement methods
  - use `multi_component_switch` or `construct_pattern` for named engineered systems, circuits, modules, or constructs
  - use `delivery_harness` for named delivery strategies or vehicles such as AAV, LNP, viral vectors, or electroporation-based deployment packages
- Do not label a named engineered system as `engineering_method` just because the paper describes how it was built.
- For every emitted `toolkit_item`, explicitly ask yourself:
  - how is this useful?
  - what problem does it solve?
  - what are the main implementation constraints or prerequisites?
  - what makes it stronger or weaker than nearby alternatives mentioned in the same source?
- Also ask these first-pass curator questions for every emitted `toolkit_item`:
  - what is the tool actually doing?
  - what resources, cofactors, hardware, delivery components, assays, or other prerequisites are required to execute it?
  - what problem does it solve, and what important problem does it *not* solve or where does it break down?
  - what alternatives, substitutes, or contrasted approaches does the source mention?
- If those answers are directly supported by the source, store the terse structured signals on the entity candidate using `useful_for`, `problem_solved`, `strengths`, `limitations`, `implementation_constraints`, and `facet_hints`.
- Also store richer source-backed prose in `freeform_explainers`:
  - `what_it_does`
  - `resources_required`
  - `problem_it_solves`
  - `problem_it_does_not_solve`
  - `alternatives`
- Each `freeform_explainers` field should be 1-3 compact sentences, grounded in the title/abstract/full-text evidence actually provided to the model, and left blank or omitted when unsupported.
- Keep those fields source-backed and terse; use empty arrays when the abstract does not support them.
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
  - `workflow_observations: []`
  - `workflow_stage_observations: []`
  - `workflow_step_observations: []`
  - `replication_signals: {}`
  - `unresolved_ambiguities`: one or more ambiguity objects that explain the evidence boundary
- Metadata-only packets are valid extraction outputs, but they remain review-only until there is source-backed entity, claim, validation, or workflow evidence.
- If a toolkit item is explicitly named in the title or abstract, emit an `entity_candidate` using the schema fields from `common.v1.schema.json`.
- Prefer fewer, higher-precision `toolkit_item` candidates over broad biological nouns that are unlikely to survive canonicalization.
- If a claim is explicit in the title or abstract, emit a `claim` with `subject_local_ids` pointing at the local IDs of the relevant extracted entities.
- If the source explicitly describes a paper-scale engineering campaign, emit one `workflow_observation` for that campaign.
- If the source explicitly describes a staged screening or selection funnel, emit one `workflow_stage_observation` per stage in the reported order, using only stage kinds and fields directly supported by the source text.
- If the source describes ordered workflow steps with meaningful sequencing logic, emit one `workflow_step_observation` per step in the reported order and capture why each step happens when it does.
