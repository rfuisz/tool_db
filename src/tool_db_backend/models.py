from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str


class ItemSummary(BaseModel):
    slug: str
    canonical_name: str
    item_type: str
    status: str
    family: Optional[str] = None
    summary: Optional[str] = None
    first_publication_year: Optional[int] = None
    primary_input_modality: Optional[str] = None
    primary_output_modality: Optional[str] = None


class SourceDocumentRecord(BaseModel):
    id: str
    title: str
    source_type: str
    publication_year: Optional[int] = None
    journal_or_source: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    is_retracted: bool = False


class CanonicalClaimMetric(BaseModel):
    metric_name: str
    operator: Optional[str] = None
    value_num: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    condition_text: Optional[str] = None


class CanonicalClaim(BaseModel):
    id: str
    claim_type: str
    claim_text_normalized: str
    polarity: str
    needs_review: bool = True
    context: Dict[str, Any] = Field(default_factory=dict)
    source_locator: Dict[str, Any] = Field(default_factory=dict)
    metrics: List[CanonicalClaimMetric] = Field(default_factory=list)
    source_document: SourceDocumentRecord


class ValidationMetric(BaseModel):
    metric_name: str
    value_num: Optional[float] = None
    unit: Optional[str] = None
    qualifier: Optional[str] = None
    condition_text: Optional[str] = None


class ValidationObservationRecord(BaseModel):
    id: str
    observation_type: str
    biological_system_level: str
    species: Optional[str] = None
    strain_or_model: Optional[str] = None
    cell_type: Optional[str] = None
    tissue: Optional[str] = None
    delivery_mode: Optional[str] = None
    cargo_or_effector: Optional[str] = None
    construct_name: Optional[str] = None
    assay_description: Optional[str] = None
    success_outcome: str
    independent_lab_cluster_id: Optional[str] = None
    institution_cluster_id: Optional[str] = None
    notes: Optional[str] = None
    source_locator: Dict[str, Any] = Field(default_factory=dict)
    metrics: List[ValidationMetric] = Field(default_factory=list)
    source_document: SourceDocumentRecord


class ValidationRollupRecord(BaseModel):
    has_cell_free_validation: bool = False
    has_bacterial_validation: bool = False
    has_mammalian_cell_validation: bool = False
    has_mouse_in_vivo_validation: bool = False
    has_human_clinical_validation: bool = False
    has_therapeutic_use: bool = False
    has_independent_replication: bool = False


class ReplicationSummaryRecord(BaseModel):
    score_version: str
    primary_paper_count: int = 0
    independent_primary_paper_count: int = 0
    distinct_last_author_clusters: int = 0
    distinct_institutions: int = 0
    distinct_biological_contexts: int = 0
    years_since_first_report: Optional[int] = None
    downstream_application_count: int = 0
    orphan_tool_flag: bool = False
    practicality_penalties: List[str] = Field(default_factory=list)
    evidence_strength_score: Optional[float] = None
    replication_score: Optional[float] = None
    practicality_score: Optional[float] = None
    translatability_score: Optional[float] = None
    explanation: Dict[str, Any] = Field(default_factory=dict)


class ItemBrowse(ItemSummary):
    maturity_stage: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    mechanisms: List[str] = Field(default_factory=list)
    techniques: List[str] = Field(default_factory=list)
    target_processes: List[str] = Field(default_factory=list)
    validation_rollup: Optional[ValidationRollupRecord] = None
    replication_summary: Optional[ReplicationSummaryRecord] = None


class ItemRelationLink(BaseModel):
    slug: str
    canonical_name: str
    item_type: Optional[str] = None
    relation_label: Optional[str] = None


class ItemFacet(BaseModel):
    facet_name: str
    facet_value: str
    evidence_note: Optional[str] = None


class ItemExplainer(BaseModel):
    explainer_kind: str
    title: Optional[str] = None
    body: str
    evidence_payload: Dict[str, Any] = Field(default_factory=dict)


class ItemComparison(BaseModel):
    related_item_slug: str
    related_item_name: str
    relation_type: str
    summary: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    overlap_reasons: List[str] = Field(default_factory=list)
    evidence_payload: Dict[str, Any] = Field(default_factory=dict)


class ItemProblemLink(BaseModel):
    problem_label: str
    why_this_item_helps: str
    source_kind: str
    gap_slug: Optional[str] = None
    gap_title: Optional[str] = None
    overall_score: Optional[float] = None
    evidence_payload: Dict[str, Any] = Field(default_factory=dict)


class ApprovedItemSourceDocument(BaseModel):
    id: str
    title: str
    source_type: str
    publication_year: Optional[int] = None
    journal_or_source: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    is_retracted: bool = False


class ApprovedItemEvidenceSnippet(BaseModel):
    text: str
    source_document: ApprovedItemSourceDocument


class ApprovedItemClaim(BaseModel):
    id: str
    claim_type: str
    claim_text_normalized: str
    polarity: str
    source_locator: Dict[str, Any] = Field(default_factory=dict)
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    source_document: ApprovedItemSourceDocument


class ApprovedItemEvidence(BaseModel):
    matched_first_pass_slugs: List[str] = Field(default_factory=list)
    source_document_count: int = 0
    claim_count: int = 0
    evidence_snippets: List[ApprovedItemEvidenceSnippet] = Field(default_factory=list)
    source_documents: List[ApprovedItemSourceDocument] = Field(default_factory=list)
    claims: List[ApprovedItemClaim] = Field(default_factory=list)


class ItemDetail(ItemSummary):
    maturity_stage: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    mechanisms: List[str] = Field(default_factory=list)
    techniques: List[str] = Field(default_factory=list)
    target_processes: List[str] = Field(default_factory=list)
    parent_items: List[ItemRelationLink] = Field(default_factory=list)
    child_items: List[ItemRelationLink] = Field(default_factory=list)
    external_ids: Dict[str, Any] = Field(default_factory=dict)
    source_status: Dict[str, Any] = Field(default_factory=dict)
    citation_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    workflow_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_workflows: List[Dict[str, Any]] = Field(default_factory=list)
    claims: List[CanonicalClaim] = Field(default_factory=list)
    validation_rollup: Optional[ValidationRollupRecord] = None
    validations: List[ValidationObservationRecord] = Field(default_factory=list)
    replication_summary: Optional[ReplicationSummaryRecord] = None
    item_facets: List[ItemFacet] = Field(default_factory=list)
    explainers: List[ItemExplainer] = Field(default_factory=list)
    comparisons: List[ItemComparison] = Field(default_factory=list)
    problem_links: List[ItemProblemLink] = Field(default_factory=list)
    approval_evidence: Optional[ApprovedItemEvidence] = None
    index_markdown: str
    evidence_markdown: str
    replication_markdown: str
    workflow_fit_markdown: str


class WorkflowSummary(BaseModel):
    slug: str
    name: str
    workflow_family: str
    objective: str
    throughput_class: Optional[str] = None


class WorkflowDetail(WorkflowSummary):
    protocol_family: Optional[str] = None
    engineered_system_family: Optional[str] = None
    why_workflow_works: Optional[str] = None
    priority_logic: Optional[str] = None
    validation_strategy: Optional[str] = None
    recommended_for: List[str] = Field(default_factory=list)
    default_parallelization_assumption: Optional[str] = None
    mechanisms: List[str] = Field(default_factory=list)
    techniques: List[str] = Field(default_factory=list)
    design_goals: List[Dict[str, Any]] = Field(default_factory=list)
    item_roles: List[Dict[str, Any]] = Field(default_factory=list)
    stage_templates: List[Dict[str, Any]] = Field(default_factory=list)
    step_templates: List[Dict[str, Any]] = Field(default_factory=list)
    assumption_notes: List[str] = Field(default_factory=list)
    index_markdown: str


class ExtractedWorkflowSummary(BaseModel):
    workflow_id: str
    workflow_objective: Optional[str] = None
    protocol_family: Optional[str] = None
    engineered_system_family: Optional[str] = None
    target_mechanisms: List[str] = Field(default_factory=list)
    target_techniques: List[str] = Field(default_factory=list)
    why_workflow_works: Optional[str] = None
    workflow_priority_logic: Optional[str] = None
    validation_strategy: Optional[str] = None
    decision_gate_strategy: Optional[str] = None
    evidence_text: Optional[str] = None
    source_document: Dict[str, Any] = Field(default_factory=dict)
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    involved_items: List[Dict[str, Any]] = Field(default_factory=list)


class GapFieldSummary(BaseModel):
    external_gap_field_id: str
    slug: Optional[str] = None
    name: str


class GapResourceSummary(BaseModel):
    external_gap_resource_id: str
    title: str
    url: Optional[str] = None
    summary: Optional[str] = None
    types: List[str] = Field(default_factory=list)


class GapCapabilityDetail(BaseModel):
    external_gap_capability_id: str
    slug: Optional[str] = None
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    resources: List[GapResourceSummary] = Field(default_factory=list)


class GapSummary(BaseModel):
    external_gap_item_id: str
    slug: Optional[str] = None
    title: str
    field: Optional[GapFieldSummary] = None
    capability_count: int = 0


class GapCandidateTool(BaseModel):
    item_slug: str
    canonical_name: str
    item_type: str
    summary: Optional[str] = None
    overall_gap_applicability_score: Optional[float] = None
    mechanistic_match_score: Optional[float] = None
    context_match_score: Optional[float] = None
    throughput_match_score: Optional[float] = None
    time_to_first_test_score: Optional[float] = None
    cost_to_first_test_score: Optional[float] = None
    replication_confidence_modifier: Optional[float] = None
    practicality_modifier: Optional[float] = None
    translatability_modifier: Optional[float] = None
    why_it_might_help: Optional[str] = None
    assumptions: Optional[str] = None
    missing_evidence: Optional[str] = None


class GapDetail(GapSummary):
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    capabilities: List[GapCapabilityDetail] = Field(default_factory=list)
    candidate_tools: List[GapCandidateTool] = Field(default_factory=list)


class VocabularyPayload(BaseModel):
    version: str
    data: Dict[str, Any]


class SourceRegistryEntry(BaseModel):
    source_key: str
    display_name: str
    source_kind: str
    sync_mode: str
    role: str
    status: str
    base_url: str


class FirstPassSourceDocument(BaseModel):
    id: str
    title: str
    source_type: str
    publication_year: Optional[int] = None
    journal_or_source: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None


class FirstPassEvidenceSnippet(BaseModel):
    text: str
    source_document: FirstPassSourceDocument


class FirstPassClaim(BaseModel):
    id: str
    claim_type: str
    claim_text_normalized: str
    polarity: str
    source_locator: Dict[str, Any] = Field(default_factory=dict)
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    source_document: FirstPassSourceDocument


class FirstPassWorkflowObservation(BaseModel):
    local_id: str
    workflow_local_id: Optional[str] = None
    workflow_objective: Optional[str] = None
    protocol_family: Optional[str] = None
    engineered_system_family: Optional[str] = None
    target_property_axes: List[str] = Field(default_factory=list)
    target_mechanisms: List[str] = Field(default_factory=list)
    target_techniques: List[str] = Field(default_factory=list)
    why_workflow_works: Optional[str] = None
    workflow_priority_logic: Optional[str] = None
    validation_strategy: Optional[str] = None
    decision_gate_strategy: Optional[str] = None
    evidence_text: Optional[str] = None
    source_locator: Dict[str, Any] = Field(default_factory=dict)
    source_document: FirstPassSourceDocument


class FirstPassWorkflowStageObservation(BaseModel):
    local_id: str
    workflow_local_id: Optional[str] = None
    stage_name: str
    stage_kind: str
    stage_order: int
    search_modality: Optional[str] = None
    selection_basis: Optional[str] = None
    counterselection_basis: Optional[str] = None
    enriches_for_axes: List[str] = Field(default_factory=list)
    guards_against_axes: List[str] = Field(default_factory=list)
    preserves_downstream_property_axes: List[str] = Field(default_factory=list)
    why_stage_exists: Optional[str] = None
    advance_criteria: Optional[str] = None
    decision_gate_reason: Optional[str] = None
    bottleneck_risk: Optional[str] = None
    higher_fidelity_than_previous: Optional[bool] = None
    source_locator: Dict[str, Any] = Field(default_factory=dict)
    source_document: FirstPassSourceDocument


class FirstPassWorkflowStepObservation(BaseModel):
    local_id: str
    workflow_local_id: Optional[str] = None
    workflow_observation_local_id: Optional[str] = None
    stage_local_id: Optional[str] = None
    stage_name: Optional[str] = None
    step_name: str
    step_order: int
    step_type: Optional[str] = None
    item_local_ids: List[str] = Field(default_factory=list)
    item_role: Optional[str] = None
    purpose: Optional[str] = None
    why_this_step_now: Optional[str] = None
    decision_gate_reason: Optional[str] = None
    advance_criteria: Optional[str] = None
    failure_criteria: Optional[str] = None
    validation_focus: Optional[str] = None
    target_property_axes: List[str] = Field(default_factory=list)
    target_mechanisms: List[str] = Field(default_factory=list)
    target_techniques: List[str] = Field(default_factory=list)
    input_artifact: Optional[str] = None
    output_artifact: Optional[str] = None
    duration_hours: Optional[float] = None
    queue_time_hours: Optional[float] = None
    direct_cost_usd: Optional[float] = None
    success: Optional[bool] = None
    source_locator: Dict[str, Any] = Field(default_factory=dict)
    source_document: FirstPassSourceDocument


class FirstPassExplainer(BaseModel):
    explainer_kind: str
    body: str
    source_document: FirstPassSourceDocument


class FirstPassEntitySummary(BaseModel):
    candidate_type: str
    slug: str
    canonical_name: str
    item_type: Optional[str] = None
    matched_slug: Optional[str] = None
    source_document_count: int
    claim_count: int
    aliases: List[str] = Field(default_factory=list)
    evidence_preview: Optional[str] = None
    evidence_previews: List[str] = Field(default_factory=list)
    claim_previews: List[str] = Field(default_factory=list)


class FirstPassEntityDetail(FirstPassEntitySummary):
    evidence_snippets: List[FirstPassEvidenceSnippet] = Field(default_factory=list)
    source_documents: List[FirstPassSourceDocument] = Field(default_factory=list)
    claims: List[FirstPassClaim] = Field(default_factory=list)
    freeform_explainers: List[FirstPassExplainer] = Field(default_factory=list)
    workflow_observations: List[FirstPassWorkflowObservation] = Field(default_factory=list)
    workflow_stage_observations: List[FirstPassWorkflowStageObservation] = Field(default_factory=list)
    workflow_step_observations: List[FirstPassWorkflowStepObservation] = Field(default_factory=list)


class FirstPassItemSummary(FirstPassEntitySummary):
    pass


class FirstPassItemDetail(FirstPassEntityDetail):
    pass
