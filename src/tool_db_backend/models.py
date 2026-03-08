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
