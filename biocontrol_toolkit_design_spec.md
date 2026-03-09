# BioControl Toolkit Database - Software Design Spec

## 1. Project Intent

Build an evidence-first, engineering-oriented database for biological control surfaces and the methods used to create, validate, and operationalize them.

The system should let a user answer questions like:

- Which protein domains or molecular assemblies can control transcription, translation, localization, degradation, signaling, editing, or selection?
- Which of these tools are actually practical rather than merely clever on paper?
- Which have been replicated independently, in which contexts, and with what caveats?
- How fast and expensive is the design-build-test loop for trying one?
- Which tools are plausibly useful for closing specific scientific or technological gaps from the Gap Map?

This should **not** be modeled as a single table of proteins.
It should be modeled as a set of intersecting knowledge layers.

---

## 2. Core Design Principles

1. **Evidence-first, not summary-first**  
   Every important field should be traceable to one or more source-backed claims.

2. **Claims before rollups**  
   Do not store only booleans like `used_in_humans = true`. Store the underlying validation observations and derive rollups.

3. **Canonical entities separated from extracted text**  
   Raw LLM extraction should never write directly into canonical tables.

4. **Flexible schema with typed core + extensible property system**  
   Common fields should be normalized. Long-tail biology should live in an extensible property layer.

5. **Replicability and usefulness are first-class dimensions**  
   The database should discount one-off tools and “looks amazing, never reused” artifacts.

6. **Human + agent navigability**  
   Markdown dossiers, stable schemas, ADRs, and Cursor-oriented repo rules should make the project easy for humans and coding agents to navigate.

---

## 3. Taxonomy Philosophy

The toolkit should not be presented as one flat list of item groups.

It is better modeled as **two related hierarchies** that meet inside workflows.

### 3.1 Mechanism branch

This hierarchy describes **the thing being engineered**:

- `mechanism` — the top conceptual layer; biophysical modes of action such as heterodimerization, photocleavage, DNA binding, RNA binding, degradation, translation control
- `architecture` — composed arrangements that realize one or more mechanisms
- `component` — low-level parts or sequence-defined elements used inside an architecture

Examples:

- mechanism: heterodimerization
- architecture: multi-component switch
- component: `AsLOV2`
- component: riboswitch / aptamer / other RNA element

Important implication:

- protein domains and RNA elements are low in the mechanism branch
- multi-component switches are above them
- mechanisms are above architectures
- when rendering or deriving hierarchy views, low-level components should roll up either directly to a tagged mechanism or to an architecture that itself rolls up to a mechanism
- mechanism sections should summarize current toolkit coverage, including available architectures, available components, and the main capabilities those tools enable

Delivery strategies likely belong on this side as well, as deployment architectures rather than techniques.

### 3.2 Technique branch

This hierarchy describes **methods of use** rather than the thing being engineered:

- `technique` — high-level engineering practices or approaches
- `method` — concrete methods, assays, and computational tools

Examples:

- technique: computational design
- technique: sequence verification
- method: `ProteinMPNN`
- method: amplicon NGS

Important implication:

- assay methods are not the same kind of thing as architectures
- computational methods are not the same kind of thing as mechanisms
- delivery strategy should usually sit with the mechanism branch as an architecture of deployment, not under techniques
- within the technique branch, the top level should stay abstract and practice-oriented, with concrete methods below it
- when rendering or deriving hierarchy views, low-level methods should always roll up to one or more technique categories, using conservative inference only when explicit technique tags are missing
- technique sections should summarize the currently available methods and the kinds of work they support

### 3.3 Workflow as the joining layer

Workflows sit above both hierarchies.

A workflow uses one or more **techniques** to obtain, build, optimize, verify, deliver, or evaluate an engineered **composition**.

In plain language:

- mechanism says how the composition works
- architecture says how the composition is arranged
- components are the concrete parts used to instantiate that architecture
- techniques say how the composition is designed, screened, measured, or deployed
- workflows describe how those choices are combined into a DBTL campaign

---

## 4. The Five Data Models

### A. Toolkit Item Model

This is the catalog of things in the engineering toolkit.

Top-level entity: `toolkit_item`

Subtypes:

- `protein_domain`
- `multi_component_switch`
- `rna_element`
- `construct_pattern`
- `engineering_method`
- `assay_method`
- `computation_method`
- `delivery_harness` (later phase)

These subtypes are **not all siblings in the same conceptual hierarchy**.

Recommended mapping:

- mechanism branch / `component`
  - `protein_domain`
  - `rna_element`
- mechanism branch / `architecture`
  - `multi_component_switch`
  - `construct_pattern`
  - `delivery_harness`
- technique branch / `method`
  - `engineering_method`
  - `assay_method`
  - `computation_method`

Examples:

- AsLOV2
- CRY2/CIB1
- EL222
- PhoCl
- ribosome display
- mRNA display
- PACE/PANCE
- amplicon NGS
- whole plasmid long-read sequencing
- RFdiffusion
- ProteinMPNN

### B. Evidence / Claim Model

This is the provenance layer.

Top-level entities:

- `source_document`
- `source_chunk`
- `extraction_run`
- `extracted_claim`
- `claim_subject_link`
- `claim_metric`
- `item_citation`

This layer records:

- what was said
- by which source
- where in the source it came from
- whether it supports or contradicts a claim
- what quantitative metrics were reported

### C. Validation / Context Model

This records whether a tool actually worked, where, and how.

Top-level entity: `validation_observation`

Important dimensions:

- biological system: cell-free, bacteria, yeast, mammalian cell line, primary cells, organoids, mouse, large animal, human clinical
- assay type: proof-of-mechanism, benchmark, therapeutic, manufacturing, diagnostic, delivery
- species / strain / cell type / tissue / organ
- delivery mode
- target process controlled
- success / mixed / failed
- quantitative performance metrics

### D. Replicability / Practicality Model

This is the “don’t get fooled by shiny nonsense” layer.

Top-level entity: `replication_summary`

It should summarize:

- number of independent confirmations
- same-lab vs cross-lab reuse
- number of distinct institutions
- number of distinct validation contexts
- downstream reuse over time
- contradictory or null follow-up evidence
- corrections / retractions / expressions of concern
- practical penalties such as toxicity, leakage, low dynamic range, poor delivery compatibility, special cofactor dependence, large payload size

### E. Workflow / DBTL Model

This captures the design-build-test loop as a compositional workflow.

Top-level entities:

- `workflow_template`
- `workflow_stage_template`
- `workflow_step_template`
- `workflow_edge`
- `workflow_assumption`
- `workflow_instance_observation`

This model lets you represent both:

- a full loop (`design -> order DNA -> assemble -> verify -> assay -> analyze -> iterate`)
- and the nested subcomponents (`sequencing`, `cell-free assay`, `amplicon NGS`, `clone picking`, etc.)
- and the funnel shape above those steps (`large search space -> broad screen -> higher-fidelity characterization -> confirmatory gate`)

---

## 5. Recommended Canonical Schema

### 5.1 `toolkit_item`

Core table for all cataloged entities.

Fields:

- `id` UUID
- `slug` text unique
- `canonical_name` text
- `item_type` enum
- `family` text
- `summary` text
- `status` enum (`seed`, `normalized`, `curated`, `deprecated`)
- `maturity_stage` enum (`research`, `preclinical`, `clinical`, `deployed`)
- `first_publication_year` int
- `primary_input_modality` enum
- `primary_output_modality` enum
- `external_ids` jsonb
- `created_at`, `updated_at`

### 5.2 Type-specific profile tables

#### `protein_domain_profile`

- `item_id`
- `source_organism`
- `domain_family`
- `monomeric_or_oligomeric`
- `requires_exogenous_cofactor`
- `cofactor_name`
- `spectral_min_nm`
- `spectral_max_nm`
- `reversible`
- `genetic_payload_bp_estimate`
- `notes`

#### `switch_profile`

- `item_id`
- `partner_requirement`
- `component_count`
- `switching_mode`
- `default_state`
- `recovery_mode`
- `dark_state_behavior`

#### `engineering_method_profile`

- `item_id`
- `method_family`
- `display_or_selection_mode`
- `library_type`
- `genotype_phenotype_linkage`
- `typical_rounds`
- `readout_mode`
- `throughput_class`

#### `computation_method_profile`

- `item_id`
- `method_family`
- `input_artifact_type`
- `output_artifact_type`
- `gpu_required`
- `inference_scale`
- `design_stage`
- `deterministic_or_stochastic`

#### `assay_method_profile`

- `item_id`
- `assay_family`
- `resolution_type`
- `throughput_class`
- `sample_type`
- `outsourceable`

### 5.3 Extensible property system

#### `property_definition`

- `id`
- `name`
- `applies_to_item_type`
- `value_type` (`bool`, `int`, `float`, `text`, `enum`, `json`)
- `unit`
- `controlled_vocabulary`
- `description`

#### `item_property_value`

- `item_id`
- `property_id`
- `value_bool`
- `value_int`
- `value_float`
- `value_text`
- `value_json`
- `source_claim_id`
- `confidence`

This is the main flex point that will let the system grow without weekly schema surgery.

### 5.4 Relationship tables

- `item_synonym`
- `item_component`
- `item_mechanism` — biophysical mechanisms of molecular tools (photocleavage, heterodimerization, etc.)
- `item_technique` — engineering methodology categories (computational design, selection/enrichment, etc.)
- `item_target_process`
- `item_related_item`
- `item_problem_link`

`item_component` is important because many useful constructs are composite rather than single domains.

Taxonomy interpretation:

- `item_mechanism` attaches an item to the **top mechanism layer**
- `item_component` helps express how lower-level components instantiate an architecture
- `item_technique` attaches an item to the **methods-of-use hierarchy**
- workflows then connect technique choices to mechanism-branch choices

---

## 6. Evidence and Citation Schema

### 5.1 `source_document`

Fields:

- `id`
- `source_type` (`review`, `primary_paper`, `trial_record`, `database_entry`, `protocol`, `benchmark`, `preprint`)
- `title`
- `doi`
- `pmid`
- `openalex_id`
- `semantic_scholar_id`
- `nct_id`
- `publication_year`
- `journal_or_source`
- `abstract_text`
- `fulltext_license_status`
- `is_retracted`
- `retraction_metadata`
- `raw_payload_ref`

### 5.2 `source_chunk`

- `id`
- `source_document_id`
- `chunk_index`
- `text`
- `section_label`
- `page_or_locator`
- `embedding`

### 5.3 `extracted_claim`

- `id`
- `source_document_id`
- `source_chunk_id`
- `claim_type`
- `claim_text_normalized`
- `polarity` (`supports`, `contradicts`, `mixed`, `neutral`)
- `confidence_model`
- `confidence_curator`
- `needs_review`

### 5.4 `claim_metric`

- `claim_id`
- `metric_name`
- `operator`
- `value_num`
- `value_text`
- `unit`
- `condition_text`

### 5.5 `item_citation`

- `item_id`
- `source_document_id`
- `citation_role` (`foundational`, `best_review`, `independent_validation`, `benchmark`, `protocol`, `therapeutic`, `negative_result`, `structural`, `database_reference`)
- `importance_rank`
- `why_this_matters`

This table gives you the ranked citation list every item page should show.

---

## 7. Validation Schema

### 6.1 `validation_observation`

Fields:

- `id`
- `item_id`
- `source_document_id`
- `construct_name`
- `observation_type` (`mechanistic_demo`, `application_demo`, `benchmark`, `therapeutic_use`, `manufacturing_use`, `failed_attempt`)
- `biological_system_level`
- `species`
- `strain_or_model`
- `cell_type`
- `tissue`
- `subcellular_target`
- `delivery_mode`
- `cargo_or_effector`
- `success_outcome`
- `assay_description`
- `independent_lab_cluster_id`
- `institution_cluster_id`
- `notes`

### 6.2 `validation_metric_value`

- `validation_observation_id`
- `metric_name`
- `value_num`
- `unit`
- `qualifier`
- `condition_text`

Suggested common metrics:

- fold induction
- repression efficiency
- dark-state leak
- on-kinetics
- off-kinetics
- EC50 / Kd / affinity
- viability / toxicity
- editing efficiency
- localization precision
- signal-to-noise
- tissue penetration compatibility

### 6.3 Derived rollups

Materialized views or cached summaries:

- `has_cell_free_validation`
- `has_bacterial_validation`
- `has_mammalian_cell_validation`
- `has_mouse_in_vivo_validation`
- `has_human_clinical_validation`
- `has_therapeutic_use`
- `has_independent_replication`

Do **not** treat these as primary data. They are computed outputs from observations.

---

## 8. Replicability and Practicality Model

Create a computed table `replication_summary` with the following inputs:

- primary-paper count
- independent-primary-paper count
- distinct last-author clusters
- distinct institutions
- distinct biological contexts
- years since first report
- downstream application count
- review-to-primary ratio
- same-lab fraction
- contradiction count
- retraction / correction count
- orphan flag (no independent reuse after a threshold)
- implementation count from external databases when available

Suggested scores:

### `evidence_strength_score`

How much primary evidence exists?

### `replication_score`

Has the tool been independently reproduced and reused?

### `practicality_score`

How usable is it in real workflows?
Penalize:

- severe dark leak
- low dynamic range
- toxicity
- large genetic footprint
- requirement for unusual cofactors
- poor tissue penetration
- fragile delivery compatibility
- repeated reports of being hard to implement

### `translatability_score`

How close is it to serious preclinical or clinical use?

### `orphan_tool_flag`

Turn this on when a tool looked promising but never propagated meaningfully beyond its originating group.

A useful early rule:

- if there is one founding paper, no independent primary follow-up after 3-5 years, and high review mention but low experimental reuse, discount it heavily.

---

## 9. Workflow / DBTL Schema

### 8.1 `workflow_template`

Represents a named loop, such as:

- fast cell-free screen
- standard plasmid build + mammalian assay
- library evolution + amplicon sequencing
- mouse pilot validation

Fields:

- `id`
- `name`
- `workflow_family`
- `objective`
- `throughput_class`
- `recommended_for`
- `default_parallelization_assumption`

### 8.2 `workflow_stage_template`

Represents one funnel stage within a workflow, such as:

- in silico pre-filtering before library build
- broad display-based enrichment
- counter-screen against a failure mode
- secondary functional characterization in a more realistic host
- final confirmatory validation

Fields:

- `id`
- `workflow_template_id`
- `stage_name`
- `stage_kind`
- `stage_order`
- `search_modality`
- `input_candidate_count_typical`
- `output_candidate_count_typical`
- `candidate_unit`
- `selection_basis`
- `counterselection_basis`
- `enriches_for_axes`
- `guards_against_axes`
- `preserves_downstream_property_axes`
- `advance_criteria`
- `bottleneck_risk`
- `higher_fidelity_than_previous`

This is the layer that represents the descending funnel explicitly, so the DB can capture not only what steps are run, but why the candidate set narrows and what later-stage failure modes the early filters are trying to avoid.

### 8.3 `workflow_step_template`

Fields:

- `id`
- `workflow_template_id`
- `workflow_stage_template_id`
- `step_name`
- `step_type` (`design`, `dna_acquisition`, `assembly`, `transformation`, `colony_screen`, `sequence_verification`, `transfection`, `expression`, `selection_round`, `assay`, `analysis`, `decision`)
- `duration_p10_hours`
- `duration_typical_hours`
- `duration_p90_hours`
- `queue_time_typical_hours`
- `hands_on_hours`
- `direct_cost_usd_typical`
- `outsourced`
- `parallelizable`
- `failure_probability`
- `output_artifact`
- `input_artifact`

Steps stay useful for critical-path, timing, and cost estimation. Stages stay useful for modeling attrition, proxy alignment, and fidelity escalation across a campaign.

### 8.4 `workflow_edge`

Connects steps and allows critical-path calculation.

### 8.5 `workflow_assumption`

Store the source and rationale for any timing, pricing, attrition, or funnel-design assumption.

### 8.6 `workflow_instance_observation`

Record real-world timings from your own lab or collaborators. This is what will make the system more accurate over time.

---

## 10. Concrete Workflow Archetypes to Seed

### A. Fast no-cloning screen

Use when testing a known sequence or a small design set.

Typical components:

1. design candidate
2. order gene fragment
3. cell-free expression / biochemical assay
4. analyze

Recommended when:

- you need a fast yes/no answer
- host toxicity is a concern
- you want same-day assay after DNA arrival

### B. Standard construct engineering loop

1. design
2. order fragment or clonal gene
3. assemble / clone
4. sequence verify
5. transfect / transform
6. assay
7. analyze and iterate

### C. Library selection loop

1. design library
2. build library
3. ribosome display / mRNA display / other selection
4. recover enriched sequences
5. amplicon NGS or other sequence readout
6. pick winners
7. rebuild / rescreen

### D. In vivo pilot loop

1. select candidate with strong prior validation
2. build and fully verify construct
3. package / deliver
4. animal or tissue validation
5. quantify efficacy and tolerability

This loop should be modeled as a separate family because vector prep, delivery, and scheduling dominate total time.

---

## 11. When to Use Which Sequencing Mode

Store sequencing as a first-class assay/method item, and also as workflow steps.

### Sanger

Best for:

- single clone verification
- targeted locus confirmation
- low-throughput spot checks

### Amplicon NGS

Best for:

- pooled edits
- library diversity
- clone pool composition
- enrichment analysis after display/selection rounds
- allele distributions

### Whole-plasmid long-read

Best for:

- complex plasmids
- repetitive constructs
- full backbone verification
- structural rearrangement detection
- avoiding primer blind spots

Do not encode “sequencing needed” as a single boolean. Encode it as a workflow choice driven by throughput, ambiguity, construct complexity, and failure cost.

---

## 12. Gap Map Integration Model

Sync the Gap Map JSON into local cache tables:

- `gap_field`
- `gap_item`
- `gap_capability`
- `gap_resource`

Then create `item_gap_link` with score breakdown:

- `mechanistic_match_score`
- `context_match_score`
- `throughput_match_score`
- `time_to_first_test_score`
- `cost_to_first_test_score`
- `replication_confidence_modifier`
- `practicality_modifier`
- `translatability_modifier`
- `overall_gap_applicability_score`

Important:

- Gap Map is the problem catalog.
- Your database is the tool catalog.
- The connection between them should be computed on your side and explainable.

Every `item_gap_link` should include:

- why the item might help
- what assumptions that depends on
- what missing evidence blocks confidence

---

## 13. Ingestion Pipeline

### Stage 1: Source acquisition

Seed from:

- review articles
- OptoBase-like databases
- Europe PMC search + identifiers
- PubMed Central full text where allowed / available
- OpenAlex works and citation graph
- Semantic Scholar recommendations / citation graph
- ClinicalTrials records
- Gap Map data

### Stage 2: Raw source store

Store untouched API payloads and retrieved text chunks in object storage.

Use a multi-source literature stack rather than forcing one provider to do everything:

- `Europe PMC` for biomedical literature discovery, DOI/PMID/PMCID alignment, and open-access metadata
- `PMC` for evidence-bearing full text and section-level extraction where available
- `OpenAlex` for breadth, institution metadata, references, and cited-by graph structure
- `Semantic Scholar` for related-paper expansion and additional citation graph signals
- `OptoBase` plus curated reviews for high-signal seeding

### Stage 3: LLM extraction to typed JSON

Do not extract straight into canonical tables.

Use schema-specific extraction packets such as:

- `review_extract_v1.json`
- `primary_paper_extract_v1.json`
- `trial_extract_v1.json`
- `database_entry_extract_v1.json`

Each packet should contain:

- entity candidates
- claims
- metrics
- contexts
- citation-role suggestions
- unresolved ambiguities

### Stage 4: Deterministic normalization

- resolve IDs
- normalize synonyms
- normalize units
- map to controlled vocabularies
- deduplicate near-duplicate entities
- flag conflicts

### Stage 5: Entity resolution / merge

Keep merge rules conservative. False merges will poison the graph.

### Stage 6: Curation queue

Anything low-confidence, high-impact, or contradictory should enter human review.

### Stage 7: Materialized summaries

Generate:

- item cards
- citation rankings
- replication summaries
- workflow rollups
- gap applicability links

---

## 14. Recommended Technical Architecture

### Storage

- **PostgreSQL** as source of truth
- **JSONB** for raw payload shadows and long-tail structured data
- **pgvector** for semantic search over claims and sources
- **Object store** for raw API payloads, cached PDFs where allowed, extraction packets, and exports

### Services

- **FastAPI** backend for ingestion, curation, and public read APIs
- **Worker service** for extraction, normalization, citation graph refresh, and scoring jobs
- **Next.js** public viewer for the website

### Search

Start with:

- PostgreSQL full text + pgvector

Only add OpenSearch later if traffic or scale forces it.

### Jobs / orchestration

- Background queue for ingestion and scoring
- Periodic sync jobs for OpenAlex, Semantic Scholar, ClinicalTrials, Gap Map
- Deterministic versioned scoring pipelines

### Why not start with a graph database?

Because most of the difficult work is evidence provenance, normalization, and rollup logic. Postgres handles this well. If graph-style traversals become dominant later, add a graph projection or graph replica.

---

## 15. Public Viewer Design

The viewer should explain the collection as **two branches plus workflows**, not as one flat set of browse buckets.

### 15.1 First-order navigation model

1. **Mechanism branch**
   Start at the top conceptual layer and move downward:
   `mechanism -> architecture -> component`

2. **Technique branch**
   Browse methods of use separately:
   high-level technique / approach -> concrete method

3. **Workflow layer**
   Show workflows as the place where technique choices are applied to obtain, screen, verify, characterize, deliver, or operationalize a target composition.

### 15.2 Concrete browse modes

1. **Explore by mechanism**
   Heterodimerization, oligomerization, conformational uncaging, membrane recruitment, photocleavage, DNA binding, RNA binding, degradation, translation control, etc.

2. **Explore by architecture**
   Multi-component switches, construct patterns, split systems, recruitment systems, uncaging systems, cleavage systems, etc.

3. **Explore by component**
   Protein domains, RNA elements, and eventually more sequence-defined or part-level items.

4. **Explore by technique**
   Computational design, selection / enrichment, directed evolution, sequence verification, functional assay, structural characterization, etc.

5. **Explore by method class**
   Engineering methods, computational methods, assay methods.

6. **Explore by family**
   LOV, BLUF, cryptochromes, phytochromes, fluorescent proteins, chemogenetic receptors, RNA element families, display platforms, etc.

7. **Explore by validation context**
   cell-free, bacteria, mammalian, in vivo mouse, human, therapeutic

8. **Explore by workflow speed / cost**
   fastest-to-first-test, cheapest-to-screen, hardest-to-debug, best for libraries

9. **Explore by Gap Map problem**
   show candidate tools ranked by applicability and confidence

### 15.3 Item-page framing

Each item page should show:

- summary
- where the item sits in the taxonomy:
  - mechanism branch / architecture / component, or
  - technique branch / method
- linked mechanisms
- linked techniques
- component structure where relevant
- validation matrix
- replication / practicality meter
- workflow fit
- ranked citations
- limitations and failure modes
- related tools / alternates

---

## 16. Repo Layout for Humans and Agents

Recommended monorepo layout:

```text
AGENTS.md
.cursor/
  rules/
  agents/
  skills/
apps/
  web/
  api/
  worker/
db/
  migrations/
  seeds/
schemas/
  extraction/
  canonical/
knowledge/
  items/
  workflows/
  taxonomies/
  gaps/
docs/
  architecture/
  ontology/
  adr/
  operations/
prompts/
  extraction/
  curation/
  scoring/
tests/
  fixtures/
  golden/
scripts/
```

### Agent-friendly Markdown pattern

Every major concept gets its own directory with stable files:

```text
knowledge/items/aslov2/
  index.md
  evidence.md
  replication.md
  workflow-fit.md
  structured.yaml
```

Suggested `index.md` frontmatter:

```yaml
id: item_aslov2
canonical_name: AsLOV2
item_type: protein_domain
status: curated
primary_input_modality: light
primary_output_modality: conformational_change
families:
  - LOV
synonyms:
  - Avena sativa LOV2
last_reviewed: 2026-03-08
```

Stable markdown sections:

- Summary
- Mechanism (for molecular tools) and/or Technique (for engineering methods)
- Inputs
- Outputs
- Components
- Validation contexts
- Replication notes
- Practical limitations
- Ranked citations
- Open questions

This makes the repo legible to both humans and agents.

---

## 17. Cursor Harness Engineering

Create:

### `AGENTS.md`

Repository-wide operating rules:

- evidence-first
- no direct writes from LLM extraction to canonical DB
- every item page must include ranked citations
- every schema change needs docs + migration
- score functions must be versioned and explainable

### `.cursor/rules/`

Small scoped rules rather than one giant omnibus file.

Suggested rules:

- `00-repo-map.mdc`
- `10-schema-safety.mdc`
- `20-extraction-contracts.mdc`
- `30-citation-and-replication.mdc`
- `40-gap-map-linking.mdc`

### `.cursorignore`

Use `.cursorignore` as a soft barrier for evaluation assets that should not be
indexed by default during agent-led development.

Recommended default:

- hide `tests/` from Cursor-style agent search so agents do not passively train
  to the suite
- provide an explicit reveal step such as
  `python scripts/agent_test_visibility.py show`
- provide a matching restore step such as
  `python scripts/agent_test_visibility.py hide`
- keep runtime behavior unchanged for humans and CI

### `.cursor/agents/`

Specialized subagents such as:

- `literature-curator.md`
- `schema-critic.md`
- `replication-auditor.md`
- `workflow-modeler.md`
- `gap-linker.md`

### `.cursor/skills/`

Reusable workflows such as:

- ingest paper metadata
- extract toolkit item from review
- recompute replication score
- generate item dossier
- generate migration + docs + tests together

---

## 18. Scoring and Transparency Requirements

Every score shown publicly should expose its breakdown.

For example, an item rank for a given problem should show:

- mechanism fit: 0.81
- validation-context fit: 0.74
- replication modifier: +0.12
- practicality penalty: -0.18
- translational maturity modifier: +0.04
- final score: 0.53

No black-box leaderboard nonsense.

---

## 19. First Build Plan

### Phase 0 - Ontology and schema

- define taxonomies
- build canonical schema
- build extraction schemas
- write AGENTS.md and Cursor rules

### Phase 1 - Seed catalog

- ingest OptoBase-like optogenetic data
- seed review articles
- load OpenAlex / Semantic Scholar metadata links
- render first item pages

### Phase 2 - Evidence and replication

- claim extraction
- citation ranking
- replication summaries
- contradiction / retraction handling

### Phase 3 - Workflow model

- define core DBTL templates
- attach sequencing, synthesis, and assay choices
- estimate timing / cost rollups

### Phase 4 - Gap Map integration

- sync gaps / capabilities / resources
- compute and display applicability links

### Phase 5 - Curation and scaling

- curator workflows
- bulk ingestion
- score tuning from real-world usage

---

## 20. Most Important Non-Obvious Design Choice

The most important choice is this:

**Make “claim + context + evidence” the primary unit of truth, and make “tool summary pages” a computed view.**

That one decision will keep the project extensible, auditable, and scientifically useful.

If you instead start with a flat table of tools and a few booleans, you will get a brittle catalog that cannot represent contradiction, context dependence, or practical failure. In biology, that is how databases turn into decorative fossils.
