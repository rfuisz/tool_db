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
  explanation?: Record<string, unknown> | null;
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
  strain_or_model?: string | null;
  cell_type: string | null;
  tissue?: string | null;
  delivery_mode: string | null;
  success_outcome: SuccessOutcome;
  assay_description: string | null;
  construct_name: string | null;
  independent_lab_cluster_id: string | null;
  institution_cluster_id?: string | null;
  notes?: string | null;
  source_locator?: Record<string, unknown>;
  source_document?: SourceDocument | null;
  metrics: ValidationMetric[];
}

export interface ClaimMetric {
  metric_name: string;
  operator: string | null;
  value_num: number | null;
  value_text: string | null;
  unit: string | null;
  condition_text: string | null;
}

export interface ItemClaim {
  id: string;
  claim_type: string;
  claim_text_normalized: string;
  polarity: "supports" | "contradicts" | "mixed" | "neutral";
  needs_review: boolean;
  context: Record<string, unknown>;
  source_locator: Record<string, unknown>;
  source_document: SourceDocument;
  metrics: ClaimMetric[];
}

export interface ApprovedItemSourceDocument {
  id: string;
  title: string;
  source_type: string;
  publication_year: number | null;
  journal_or_source: string | null;
  doi: string | null;
  pmid: string | null;
  is_retracted: boolean;
}

export interface ApprovedItemEvidenceSnippet {
  text: string;
  source_document: ApprovedItemSourceDocument;
}

export interface ApprovedItemClaim {
  id: string;
  claim_type: string;
  claim_text_normalized: string;
  polarity: "supports" | "contradicts" | "mixed" | "neutral";
  source_locator: Record<string, unknown>;
  metrics: Array<Record<string, unknown>>;
  source_document: ApprovedItemSourceDocument;
}

export interface ApprovedItemEvidence {
  matched_first_pass_slugs: string[];
  source_document_count: number;
  claim_count: number;
  evidence_snippets: ApprovedItemEvidenceSnippet[];
  source_documents: ApprovedItemSourceDocument[];
  claims: ApprovedItemClaim[];
}

export interface ItemRelationLink {
  slug: string;
  canonical_name: string;
  item_type: string | null;
  relation_label: string | null;
}

export interface ItemFacet {
  facet_name: string;
  facet_value: string;
  evidence_note?: string | null;
}

export interface ItemExplainer {
  explainer_kind: string;
  title?: string | null;
  body: string;
  evidence_payload?: Record<string, unknown>;
}

export interface ItemComparison {
  related_item_slug: string;
  related_item_name: string;
  relation_type: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  overlap_reasons: string[];
  evidence_payload?: Record<string, unknown>;
}

export interface ItemProblemLink {
  problem_label: string;
  why_this_item_helps: string;
  source_kind: string;
  gap_slug?: string | null;
  gap_title?: string | null;
  overall_score?: number | null;
  evidence_payload?: Record<string, unknown>;
}

export interface WorkflowRecommendation {
  workflow_slug: string;
  workflow_name: string;
  role_name: string;
  stage_name?: string | null;
  step_name?: string | null;
  notes?: string | null;
  objective?: string | null;
}

export interface ExtractedWorkflowStage {
  stage_name: string;
  stage_kind: string;
  stage_order: number;
  search_modality?: string | null;
  input_candidate_count?: number | null;
  output_candidate_count?: number | null;
  selection_basis?: string | null;
  counterselection_basis?: string | null;
  enriches_for_axes: string[];
  guards_against_axes: string[];
  why_stage_exists?: string | null;
  advance_criteria?: string | null;
  bottleneck_risk?: string | null;
}

export interface ExtractedWorkflowStep {
  step_name: string;
  step_order: number;
  step_type?: string | null;
  stage_name?: string | null;
  item_local_ids: string[];
  item_role?: string | null;
  purpose?: string | null;
  why_this_step_now?: string | null;
  advance_criteria?: string | null;
  input_artifact?: string | null;
  output_artifact?: string | null;
  duration_hours?: number | null;
  success?: boolean | null;
}

export interface ExtractedWorkflow {
  workflow_objective?: string | null;
  protocol_family?: string | null;
  engineered_system_family?: string | null;
  target_mechanisms: string[];
  target_techniques: string[];
  why_workflow_works?: string | null;
  workflow_priority_logic?: string | null;
  validation_strategy?: string | null;
  decision_gate_strategy?: string | null;
  evidence_text?: string | null;
  source_document: SourceDocument;
  stages: ExtractedWorkflowStage[];
  steps: ExtractedWorkflowStep[];
}

export interface ExtractedWorkflowInvolvedItem {
  slug: string;
  canonical_name: string;
  display_name: string;
  item_slug: string | null;
}

export interface ExtractedWorkflowSummary extends ExtractedWorkflow {
  workflow_id: string;
  involved_items: ExtractedWorkflowInvolvedItem[];
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
  components?: string[];
  parent_items?: ItemRelationLink[];
  child_items?: ItemRelationLink[];
  mechanisms: string[];
  techniques: string[];
  target_processes: string[];
  synonyms: string[];
  validation_rollup: ValidationRollup | null;
  replication_summary: ReplicationSummary | null;
  citations: ItemCitation[];
  validations: ValidationObservation[];
  claims?: ItemClaim[];
  item_facets?: ItemFacet[];
  explainers?: ItemExplainer[];
  comparisons?: ItemComparison[];
  problem_links?: ItemProblemLink[];
  workflow_recommendations?: WorkflowRecommendation[];
  extracted_workflows?: ExtractedWorkflow[];
  approval_evidence?: ApprovedItemEvidence | null;
  index_markdown?: string | null;
  evidence_markdown?: string | null;
  replication_markdown?: string | null;
  workflow_fit_markdown?: string | null;
}

export interface WorkflowStep {
  id: string;
  step_name: string;
  stage_name?: string | null;
  step_order?: number | null;
  step_type: WorkflowStepType;
  purpose?: string | null;
  why_this_step_now?: string | null;
  decision_gate_reason?: string | null;
  advance_criteria?: string | null;
  failure_criteria?: string | null;
  validation_focus?: string | null;
  target_property_axes?: string[];
  target_mechanisms?: string[];
  target_techniques?: string[];
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
  why_stage_exists?: string | null;
  advance_criteria: string | null;
  decision_gate_reason?: string | null;
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
  protocol_family?: string | null;
  engineered_system_family?: string | null;
  why_workflow_works?: string | null;
  priority_logic?: string | null;
  validation_strategy?: string | null;
  mechanisms?: string[];
  techniques?: string[];
  design_goals?: Array<Record<string, unknown>>;
  item_roles?: Array<Record<string, unknown>>;
  stages?: WorkflowStage[];
  steps: WorkflowStep[];
  simple_summary?: string | null;
  how_to_implement?: string[];
  used_when?: string[];
  tradeoffs?: string[];
  citations?: WorkflowReference[];
}

export interface GapFieldSummary {
  external_gap_field_id: string;
  slug: string | null;
  name: string;
}

export interface GapResourceSummary {
  external_gap_resource_id: string;
  title: string;
  url: string | null;
  summary: string | null;
  types: string[];
}

export interface GapCapabilityDetail {
  external_gap_capability_id: string;
  slug: string | null;
  name: string;
  description: string | null;
  tags: string[];
  resources: GapResourceSummary[];
}

export interface GapSummary {
  external_gap_item_id: string;
  slug: string | null;
  title: string;
  field: GapFieldSummary | null;
  capability_count: number;
}

export interface GapCandidateTool {
  item_slug: string;
  canonical_name: string;
  item_type: ItemType;
  summary: string | null;
  overall_gap_applicability_score: number | null;
  mechanistic_match_score: number | null;
  context_match_score: number | null;
  throughput_match_score: number | null;
  time_to_first_test_score: number | null;
  cost_to_first_test_score: number | null;
  replication_confidence_modifier: number | null;
  practicality_modifier: number | null;
  translatability_modifier: number | null;
  why_it_might_help: string | null;
  assumptions: string | null;
  missing_evidence: string | null;
}

export interface GapDetail extends GapSummary {
  description: string | null;
  tags: string[];
  capabilities: GapCapabilityDetail[];
  candidate_tools: GapCandidateTool[];
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

export interface FirstPassWorkflowObservation {
  local_id: string;
  workflow_local_id: string | null;
  workflow_objective: string | null;
  protocol_family: string | null;
  engineered_system_family: string | null;
  target_property_axes: string[];
  target_mechanisms: string[];
  target_techniques: string[];
  why_workflow_works: string | null;
  workflow_priority_logic: string | null;
  validation_strategy: string | null;
  decision_gate_strategy: string | null;
  evidence_text: string | null;
  source_locator: Record<string, unknown>;
  source_document: FirstPassSourceDocument;
}

export interface FirstPassWorkflowStageObservation {
  local_id: string;
  workflow_local_id: string | null;
  stage_name: string;
  stage_kind: string;
  stage_order: number;
  search_modality: string | null;
  selection_basis: string | null;
  counterselection_basis: string | null;
  enriches_for_axes: string[];
  guards_against_axes: string[];
  preserves_downstream_property_axes: string[];
  why_stage_exists: string | null;
  advance_criteria: string | null;
  decision_gate_reason: string | null;
  bottleneck_risk: string | null;
  higher_fidelity_than_previous: boolean | null;
  source_locator: Record<string, unknown>;
  source_document: FirstPassSourceDocument;
}

export interface FirstPassWorkflowStepObservation {
  local_id: string;
  workflow_local_id: string | null;
  workflow_observation_local_id: string | null;
  stage_local_id: string | null;
  stage_name: string | null;
  step_name: string;
  step_order: number;
  step_type: string | null;
  item_local_ids: string[];
  item_role: string | null;
  purpose: string | null;
  why_this_step_now: string | null;
  decision_gate_reason: string | null;
  advance_criteria: string | null;
  failure_criteria: string | null;
  validation_focus: string | null;
  target_property_axes: string[];
  target_mechanisms: string[];
  target_techniques: string[];
  input_artifact: string | null;
  output_artifact: string | null;
  duration_hours: number | null;
  queue_time_hours: number | null;
  direct_cost_usd: number | null;
  success: boolean | null;
  source_locator: Record<string, unknown>;
  source_document: FirstPassSourceDocument;
}

export interface FirstPassExplainer {
  explainer_kind: string;
  body: string;
  source_document: FirstPassSourceDocument;
}

export interface FirstPassEntitySummary {
  candidate_type: string;
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

export interface FirstPassEntityDetail extends FirstPassEntitySummary {
  evidence_snippets: FirstPassEvidenceSnippet[];
  source_documents: FirstPassSourceDocument[];
  claims: FirstPassClaim[];
  freeform_explainers: FirstPassExplainer[];
  workflow_observations: FirstPassWorkflowObservation[];
  workflow_stage_observations: FirstPassWorkflowStageObservation[];
  workflow_step_observations: FirstPassWorkflowStepObservation[];
}

export type FirstPassItemSummary = FirstPassEntitySummary;

export type FirstPassItemDetail = FirstPassEntityDetail;

export interface ItemBrowseResponse {
  total: number;
  limit: number;
  offset: number;
  items: ToolkitItem[];
}

export interface ItemAggregateTypeBucket {
  value: string;
  count: number;
}

export interface ItemAggregateResponse {
  total_items: number;
  total_families: number;
  avg_evidence_score: number | null;
  by_item_type: ItemAggregateTypeBucket[];
  by_mechanism: ItemAggregateTypeBucket[];
  by_technique: ItemAggregateTypeBucket[];
  by_family: ItemAggregateTypeBucket[];
}
