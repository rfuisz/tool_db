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
    primary_input_modality: Optional[str] = None
    primary_output_modality: Optional[str] = None


class ItemDetail(ItemSummary):
    maturity_stage: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    mechanisms: List[str] = Field(default_factory=list)
    techniques: List[str] = Field(default_factory=list)
    target_processes: List[str] = Field(default_factory=list)
    external_ids: Dict[str, Any] = Field(default_factory=dict)
    source_status: Dict[str, Any] = Field(default_factory=dict)
    citation_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    workflow_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
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
    recommended_for: List[str] = Field(default_factory=list)
    default_parallelization_assumption: Optional[str] = None
    stage_templates: List[Dict[str, Any]] = Field(default_factory=list)
    step_templates: List[Dict[str, Any]] = Field(default_factory=list)
    assumption_notes: List[str] = Field(default_factory=list)
    index_markdown: str


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


class FirstPassItemSummary(BaseModel):
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


class FirstPassItemDetail(FirstPassItemSummary):
    evidence_snippets: List[FirstPassEvidenceSnippet] = Field(default_factory=list)
    source_documents: List[FirstPassSourceDocument] = Field(default_factory=list)
    claims: List[FirstPassClaim] = Field(default_factory=list)
