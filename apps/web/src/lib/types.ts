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
export type MaturityStage =
  | "research"
  | "preclinical"
  | "clinical"
  | "deployed";

export type Modality =
  | "light"
  | "chemical"
  | "thermal"
  | "electrical"
  | "mechanical"
  | "magnetic"
  | "sequence"
  | "structure"
  | "conformational_change"
  | "transcription"
  | "translation"
  | "localization"
  | "degradation"
  | "signaling"
  | "recombination"
  | "editing"
  | "selection"
  | "assay_readout"
  | "analysis";

export type BiologicalSystemLevel =
  | "cell_free"
  | "bacteria"
  | "yeast"
  | "mammalian_cell_line"
  | "primary_cells"
  | "organoid"
  | "mouse"
  | "large_animal"
  | "human_clinical";

export type SuccessOutcome = "success" | "mixed" | "failed";
export type ObservationType =
  | "mechanistic_demo"
  | "application_demo"
  | "benchmark"
  | "therapeutic_use"
  | "manufacturing_use"
  | "failed_attempt";

export type CitationRole =
  | "foundational"
  | "best_review"
  | "independent_validation"
  | "benchmark"
  | "protocol"
  | "therapeutic"
  | "negative_result"
  | "structural"
  | "database_reference";

export type WorkflowFamily =
  | "fast_screen"
  | "standard_construct"
  | "library_selection"
  | "in_vivo_pilot"
  | "custom";

export type WorkflowStepType =
  | "design"
  | "dna_acquisition"
  | "assembly"
  | "transformation"
  | "colony_screen"
  | "sequence_verification"
  | "transfection"
  | "expression"
  | "selection_round"
  | "assay"
  | "analysis"
  | "decision"
  | "packaging"
  | "delivery";

export type WorkflowStageKind =
  | "in_silico_filter"
  | "library_design"
  | "library_build"
  | "broad_screen"
  | "selection"
  | "counter_screen"
  | "recovery"
  | "sequencing_readout"
  | "hit_picking"
  | "functional_characterization"
  | "secondary_characterization"
  | "confirmatory_validation"
  | "in_vivo_validation"
  | "decision_gate";

export type WorkflowSearchModality =
  | "in_silico"
  | "display"
  | "pooled_library"
  | "cell_free"
  | "cell_based"
  | "biochemical"
  | "sequencing"
  | "structural"
  | "animal";

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

export interface ItemCitation {
  id: string;
  source_document_id: string;
  citation_role: CitationRole;
  importance_rank: number;
  why_this_matters: string;
  document: SourceDocument;
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

export interface ValidationMetric {
  metric_name: string;
  value_num: number | null;
  unit: string | null;
  qualifier: string | null;
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
  stage_name?: string | null;
  step_type: WorkflowStepType;
  duration_typical_hours: number | null;
  hands_on_hours: number | null;
  direct_cost_usd_typical: number | null;
  parallelizable: boolean;
  failure_probability: number | null;
  input_artifact: string | null;
  output_artifact: string | null;
}

export interface WorkflowStage {
  id: string;
  stage_name: string;
  stage_kind: WorkflowStageKind;
  stage_order: number;
  search_modality: WorkflowSearchModality | null;
  input_candidate_count_typical: number | null;
  output_candidate_count_typical: number | null;
  candidate_unit: string | null;
  selection_basis: string | null;
  counterselection_basis: string | null;
  enriches_for_axes: string[];
  guards_against_axes: string[];
  preserves_downstream_property_axes: string[];
  advance_criteria: string | null;
  bottleneck_risk: string | null;
  higher_fidelity_than_previous: boolean | null;
}

export interface WorkflowReference {
  title: string;
  href: string;
  note: string;
}

export interface WorkflowTemplate {
  id: string;
  slug: string;
  name: string;
  workflow_family: WorkflowFamily;
  objective: string;
  throughput_class: string | null;
  recommended_for: string | null;
  stages?: WorkflowStage[];
  steps: WorkflowStep[];
  simple_summary?: string | null;
  how_to_implement?: string[];
  used_when?: string[];
  tradeoffs?: string[];
  citations?: WorkflowReference[];
}

export interface FirstPassSourceDocument {
  id: string;
  title: string;
  source_type: string;
  publication_year: number | null;
  journal_or_source: string | null;
  doi: string | null;
  pmid: string | null;
}

export interface FirstPassEvidenceSnippet {
  text: string;
  source_document: FirstPassSourceDocument | null;
}

export interface FirstPassClaim {
  id: string;
  claim_type: string;
  claim_text_normalized: string;
  polarity: string;
  source_locator: Record<string, unknown>;
  metrics: Array<Record<string, unknown>>;
  source_document: FirstPassSourceDocument;
}

export interface FirstPassItemSummary {
  slug: string;
  canonical_name: string;
  item_type: string | null;
  matched_slug: string | null;
  source_document_count: number;
  claim_count: number;
  aliases: string[];
  evidence_preview: string | null;
  evidence_previews: string[];
  claim_previews: string[];
}

export interface FirstPassItemDetail extends FirstPassItemSummary {
  evidence_snippets: FirstPassEvidenceSnippet[];
  source_documents: FirstPassSourceDocument[];
  claims: FirstPassClaim[];
}
