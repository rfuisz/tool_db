# Generate Expanded Mock Dataset for BioControl Toolkit DB

## Goal

Produce a single TypeScript file (`apps/web/src/lib/mock-data-expanded.ts`) that exports an `ITEMS` array (≥ 40 items) and a `WORKFLOWS` array (≥ 7 workflows). This dataset will stress-test the web viewer's filters, sort, detail pages, validation matrix, citation list, score breakdown, and workflow timeline components.

---

## Output Format

The file must be valid TypeScript and must satisfy the types below verbatim (do **not** change the types — copy them exactly).

```typescript
// ── Type definitions (copy exactly) ──────────────────────────────────

export type ItemType =
  | "protein_domain"
  | "multi_component_switch"
  | "rna_element"
  | "construct_pattern"
  | "engineering_method"
  | "assay_method"
  | "computation_method"
  | "delivery_harness";

export type ItemStatus = "seed" | "normalized" | "curated" | "deprecated";
export type MaturityStage = "research" | "preclinical" | "clinical" | "deployed";

export type Modality =
  | "light" | "chemical" | "thermal" | "electrical" | "mechanical"
  | "magnetic" | "sequence" | "structure" | "conformational_change"
  | "transcription" | "translation" | "localization" | "degradation"
  | "signaling" | "editing" | "selection" | "assay_readout" | "analysis";

export type BiologicalSystemLevel =
  | "cell_free" | "bacteria" | "yeast" | "mammalian_cell_line"
  | "primary_cells" | "organoid" | "mouse" | "large_animal" | "human_clinical";

export type SuccessOutcome = "success" | "mixed" | "failed";

export type ObservationType =
  | "mechanistic_demo" | "application_demo" | "benchmark"
  | "therapeutic_use" | "manufacturing_use" | "failed_attempt";

export type CitationRole =
  | "foundational" | "best_review" | "independent_validation"
  | "benchmark" | "protocol" | "therapeutic" | "negative_result"
  | "structural" | "database_reference";

export type WorkflowFamily =
  | "fast_screen" | "standard_construct" | "library_selection"
  | "in_vivo_pilot" | "custom";

export type WorkflowStepType =
  | "design" | "dna_acquisition" | "assembly" | "transformation"
  | "colony_screen" | "sequence_verification" | "transfection"
  | "expression" | "selection_round" | "assay" | "analysis"
  | "decision" | "packaging" | "delivery";

export interface ValidationMetric {
  metric_name: string;
  value_num: number | null;
  unit: string | null;
  qualifier: string | null;
}

export interface ValidationObservation {
  id: string;
  item_id: string;
  observation_type: ObservationType;
  biological_system_level: BiologicalSystemLevel;
  species: string | null;
  cell_type: string | null;
  delivery_mode: string | null;
  success_outcome: SuccessOutcome;
  assay_description: string | null;
  construct_name: string | null;
  independent_lab_cluster_id: string | null;
  metrics: ValidationMetric[];
}

export interface SourceDocument {
  id: string;
  source_type: string;
  title: string;
  doi: string | null;
  pmid: string | null;
  publication_year: number | null;
  journal_or_source: string | null;
  is_retracted: boolean;
}

export interface ItemCitation {
  id: string;
  source_document_id: string;
  citation_role: CitationRole;
  importance_rank: number;
  why_this_matters: string;
  document: SourceDocument;
}

export interface ValidationRollup {
  has_cell_free_validation: boolean;
  has_bacterial_validation: boolean;
  has_mammalian_cell_validation: boolean;
  has_mouse_in_vivo_validation: boolean;
  has_human_clinical_validation: boolean;
  has_therapeutic_use: boolean;
  has_independent_replication: boolean;
}

export interface ReplicationSummary {
  score_version: string;
  primary_paper_count: number;
  independent_primary_paper_count: number;
  distinct_last_author_clusters: number;
  distinct_institutions: number;
  distinct_biological_contexts: number;
  years_since_first_report: number | null;
  downstream_application_count: number;
  orphan_tool_flag: boolean;
  practicality_penalties: string[];
  evidence_strength_score: number | null;
  replication_score: number | null;
  practicality_score: number | null;
  translatability_score: number | null;
}

export interface ToolkitItem {
  id: string;
  slug: string;
  canonical_name: string;
  item_type: ItemType;
  family: string | null;
  summary: string | null;
  status: ItemStatus;
  maturity_stage: MaturityStage;
  first_publication_year: number | null;
  primary_input_modality: Modality | null;
  primary_output_modality: Modality | null;
  mechanisms: string[];
  techniques: string[];
  target_processes: string[];
  synonyms: string[];
  validation_rollup: ValidationRollup | null;
  replication_summary: ReplicationSummary | null;
  citations: ItemCitation[];
  validations: ValidationObservation[];
}

export interface WorkflowStep {
  id: string;
  step_name: string;
  step_type: WorkflowStepType;
  duration_typical_hours: number | null;
  hands_on_hours: number | null;
  direct_cost_usd_typical: number | null;
  parallelizable: boolean;
  failure_probability: number | null;
  input_artifact: string | null;
  output_artifact: string | null;
}

export interface WorkflowTemplate {
  id: string;
  slug: string;
  name: string;
  workflow_family: WorkflowFamily;
  objective: string;
  throughput_class: string | null;
  recommended_for: string | null;
  steps: WorkflowStep[];
}
```

---

## Controlled Vocabularies (values you must draw from)

### mechanism_families
`heterodimerization`, `oligomerization`, `conformational_uncaging`, `membrane_recruitment`, `photocleavage`, `dna_binding`, `rna_binding`, `degradation`, `translation_control`

### technique_families
`computational_design`, `selection_enrichment`, `directed_evolution`, `sequence_verification`, `functional_assay`, `structural_characterization`, `delivery_optimization`

### target_processes
`transcription`, `translation`, `localization`, `degradation`, `signaling`, `editing`, `selection`, `manufacturing`, `diagnostic`

### common_metric_names
`fold_induction`, `repression_efficiency`, `dark_state_leak`, `on_kinetics_minutes`, `off_kinetics_minutes`, `affinity_kd`, `viability_percent`, `toxicity_signal`, `editing_efficiency_percent`, `localization_precision`, `signal_to_noise`, `tissue_penetration_compatibility`

### throughput_class (for workflows)
`single`, `low`, `medium`, `high`, `library_scale`

---

## Coverage Requirements

### Item type distribution (≥ 40 items total)

| item_type               | min count | notes                                              |
|-------------------------|-----------|----------------------------------------------------|
| protein_domain          | 8         | mix of LOV, phytochrome, fluorescent protein, BLUF families |
| multi_component_switch  | 5         | at least one 3-component system                    |
| rna_element             | 3         | riboswitches, aptazymes, toehold switches           |
| construct_pattern       | 2         | e.g., split-intein reconstitution, degron fusions   |
| engineering_method      | 6         | display, PACE, FACS-based, computational screening  |
| assay_method            | 5         | sequencing, flow cytometry, microscopy, ELISA, SPR  |
| computation_method      | 5         | RFdiffusion, AlphaFold, ESM, ProteinMPNN, Rosetta   |
| delivery_harness        | 3         | AAV, LNP, electroporation                           |

### Status distribution
- At least 2 items with `status: "seed"` (sparse data — minimal citations/validations)
- At least 2 with `status: "normalized"` (some data filled in)
- Majority `status: "curated"` (rich data)
- At least 1 with `status: "deprecated"` (with a note in `practicality_penalties`)

### Maturity stages
- At least 3 items at each of: `research`, `preclinical`, `clinical`, `deployed`

### Mechanism + technique coverage
- Every `mechanism_families` value must appear on at least 1 item
- Every `technique_families` value must appear on at least 1 item
- At least 2 items should use **both** a mechanism and a technique (e.g., a protein domain whose engineering also used directed_evolution)

### Modality coverage
- Use at least 10 distinct modality values across inputs and outputs
- Include at least 1 item with `chemical` input, 1 with `thermal` input, 1 with `magnetic` or `electrical` input

### Validation observation coverage
- Total validation observations across all items: **≥ 100**
- Every `biological_system_level` value must appear in at least 2 observations
- Every `observation_type` must appear at least twice
- Every `success_outcome` must appear (include at least 5 `"failed"` and 5 `"mixed"` outcomes)
- Use at least 8 distinct `common_metric_names` across all metrics
- At least 10 observations should have 2+ metrics each
- At least 5 observations should have `species` set to non-human, non-E. coli organisms (zebrafish, C. elegans, S. cerevisiae, Drosophila, rat, etc.)

### Citation coverage
- Total citations across all items: **≥ 80**
- Every `citation_role` must appear at least twice
- At least 3 citations must have `is_retracted: true` on their document
- Use realistic-looking DOIs (`10.XXXX/...`) and PMIDs (7-8 digit numbers) — they can be fictional but must be plausible format
- At least 4 items should have ≥ 4 citations each
- At least 5 items should have 0 citations (seed/normalized items)

### Replication summary stress cases
- At least 2 items with `orphan_tool_flag: true`
- At least 3 items with `evidence_strength_score` below 0.4
- At least 3 items with empty `practicality_penalties` arrays
- At least 2 items with 3+ entries in `practicality_penalties`
- Score ranges: ensure the full 0.1–0.99 range is spanned for each score dimension
- At least 1 item with `replication_summary: null` (seed item)
- At least 1 item with `validation_rollup: null` (seed item)

### Edge cases & adversarial patterns
- 1 item with a very long `summary` (300+ words)
- 1 item with `summary: null`
- 1 item with `first_publication_year: null`
- 1 item with `family: null`
- 2 items sharing the same `family` but different `item_type` values
- 1 item whose `canonical_name` contains special characters (e.g., Greek letters like "Gβγ-GRIP" or slashes like "CRY2/CIB1/SPA1")
- 1 item with 5+ synonyms
- 2 items that share a synonym (testing deduplication edge case)
- 1 validation observation with an empty `metrics` array
- 1 validation observation where `delivery_mode`, `species`, `cell_type`, `assay_description`, and `construct_name` are all null

### Workflow coverage (≥ 7 templates)
- At least 1 template per `workflow_family` value (fast_screen, standard_construct, library_selection, in_vivo_pilot, custom)
- Step count range: at least 1 workflow with 3 steps, at least 1 with 8+ steps
- At least 1 step per `workflow_step_type` value across all templates
- Include at least 1 workflow where multiple steps have `parallelizable: true`
- Include at least 1 workflow where a step has `failure_probability ≥ 0.30`
- Cost range: at least 1 workflow totaling < $100 and 1 totaling > $5,000

---

## ID Conventions

- Item IDs: UUID format `a1000000-0000-0000-0000-0000000000XX` (increment XX from 11 onward; items 01–10 are taken)
- Citation IDs: `c` + 3-digit number starting at `c100`
- Source document IDs: `d` + 3-digit number starting at `d100`
- Validation observation IDs: `v` + 3-digit number starting at `v100`
- Workflow IDs: `w` + 3-digit number starting at `w010`
- Workflow step IDs: `ws` + 3-digit number starting at `ws100`

---

## Scientific Realism Guidelines

Items should be **real or plausible** tools from optogenetics, synthetic biology, protein engineering, gene editing, and related fields. Good candidates to include:

**Protein domains / switches:** iLID/SspB, BphP1/PpsR2 (near-IR), Dronpa, pdDronpa, LOVpep, VVD, PhyB/PIF, UVR8/COP1, ABI/PYL (chemical: ABA-inducible), FKBP/FRB (rapamycin-inducible), Magnets (nMag/pMag), phiLOV, miniSOG, TULIPs

**RNA elements:** theophylline aptazyme, toehold switches, riboswitch-gated expression

**Construct patterns:** split-intein reconstitution, N/C-split Cre recombinase

**Engineering methods:** phage display, yeast surface display, CelluSpot, FACS-Seq

**Assay methods:** flow cytometry, plate reader kinetics, SPR/BLI, cryo-EM, AlphaScreen

**Computation methods:** AlphaFold2, ESMFold, Rosetta, Chai-1

**Delivery harnesses:** AAV serotypes, lipid nanoparticles (LNP), electroporation

Use realistic organism names, cell types (HEK293T, HeLa, CHO, Jurkat, U2OS, NIH3T3, primary cortical neurons, iPSC-derived cardiomyocytes), and delivery modes (transient transfection, lentiviral transduction, AAV injection, LNP IV, electroporation, microinjection).

---

## Internal Consistency Rules

1. `validation_rollup` booleans must be **derivable** from the `validations` array:
   - `has_cell_free_validation` = true iff any validation has `biological_system_level === "cell_free"` and `success_outcome !== "failed"`
   - `has_bacterial_validation` = true iff any validation has `biological_system_level === "bacteria"` and `success_outcome !== "failed"`
   - `has_mammalian_cell_validation` = true iff any validation has `biological_system_level === "mammalian_cell_line"` and `success_outcome !== "failed"`
   - `has_mouse_in_vivo_validation` = true iff any validation has `biological_system_level === "mouse"` and `success_outcome !== "failed"`
   - `has_human_clinical_validation` = true iff any validation has `biological_system_level === "human_clinical"` and `success_outcome !== "failed"`
   - `has_therapeutic_use` = true iff any validation has `observation_type === "therapeutic_use"` and `success_outcome !== "failed"`
   - `has_independent_replication` = true iff there are ≥ 2 distinct `independent_lab_cluster_id` values (ignoring nulls) with `success_outcome !== "failed"`
2. `replication_summary.independent_primary_paper_count ≤ primary_paper_count`
3. `replication_summary.distinct_institutions ≤ distinct_last_author_clusters * 2` (roughly plausible)
4. Items with `status: "seed"` should have few or no citations/validations
5. Items with `status: "deprecated"` should have a `practicality_penalties` entry explaining why
6. Each citation's `importance_rank` should be unique within that item's citations array (1, 2, 3, ...)
7. `years_since_first_report` should be consistent with `first_publication_year` (current year minus publication year)
8. `score_version` is always `"v1"`
9. All slugs must be unique; use lowercase-kebab-case

---

## File Structure

```typescript
import type {
  ToolkitItem,
  WorkflowTemplate,
} from "./types";

export const ITEMS: ToolkitItem[] = [
  // ... 40+ items
];

export const WORKFLOWS: WorkflowTemplate[] = [
  // ... 7+ workflows
];
```

Do **not** include the type definitions in the output file — they are imported from `"./types"`.

Do **not** include helper functions — only the two exported arrays.

---

## Delivery checklist (self-verify before returning)

- [ ] File parses as valid TypeScript with zero errors
- [ ] ≥ 40 items, ≥ 7 workflows
- [ ] Every enum value from controlled vocabularies used at least once
- [ ] validation_rollup booleans consistent with validations array
- [ ] ≥ 100 total validation observations
- [ ] ≥ 80 total citations
- [ ] ≥ 3 retracted documents
- [ ] ≥ 2 orphan-tool items
- [ ] All ID sequences start above the reserved ranges
- [ ] No duplicate slugs or IDs
- [ ] Edge cases from "adversarial patterns" section all present
