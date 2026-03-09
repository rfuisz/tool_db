import "server-only";

import seedBundle from "./seed-bundle.json";
import { WORKFLOW_EXPLAINERS } from "./workflow-explainers";
import type {
  ApprovedItemEvidence,
  FirstPassEntityDetail,
  FirstPassExplainer,
  FirstPassEntitySummary,
  FirstPassItemDetail,
  FirstPassEvidenceSnippet,
  FirstPassSourceDocument,
  FirstPassItemSummary,
  CitationRole,
  ClaimMetric,
  GapDetail,
  GapSummary,
  ItemClaim,
  ItemComparison,
  ItemCitation,
  ItemExplainer,
  ItemFacet,
  ItemProblemLink,
  ItemStatus,
  MaturityStage,
  Modality,
  SourceDocument,
  ToolkitItem,
  ValidationObservation,
  ValidationRollup,
  WorkflowFamily,
  WorkflowRecommendation,
  WorkflowSearchModality,
  WorkflowStage,
  WorkflowStageKind,
  WorkflowStep,
  WorkflowStepType,
  WorkflowTemplate,
} from "./types";

type BackendItemSummary = {
  slug: string;
  canonical_name: string;
  item_type: ToolkitItem["item_type"];
  status: ItemStatus;
  family?: string | null;
  summary?: string | null;
  first_publication_year?: number | null;
  primary_input_modality?: string | null;
  primary_output_modality?: string | null;
};

type CitationCandidate = {
  citation_role?: CitationRole;
  importance_rank?: number;
  why_this_matters?: string;
  source_document_id?: string;
  label?: string;
  status?: string;
  source_type?: string;
  publication_year?: number | null;
  url?: string;
  doi?: string;
  pmid?: string | null;
  is_retracted?: boolean;
};

type BackendClaimMetric = ClaimMetric;

type BackendItemClaim = {
  id: string;
  claim_type: string;
  claim_text_normalized: string;
  polarity: ItemClaim["polarity"];
  needs_review: boolean;
  context?: Record<string, unknown>;
  source_locator?: Record<string, unknown>;
  metrics?: BackendClaimMetric[];
  source_document: SourceDocument;
};

type BackendItemFacet = ItemFacet;
type BackendItemExplainer = ItemExplainer;
type BackendItemComparison = ItemComparison;
type BackendItemProblemLink = ItemProblemLink;
type BackendWorkflowRecommendation = WorkflowRecommendation;
type BackendValidationObservation = Omit<
  ValidationObservation,
  "item_id" | "metrics"
> & {
  item_id?: string;
  metrics?: ValidationObservation["metrics"];
  source_locator?: Record<string, unknown>;
  source_document?: SourceDocument | null;
};

type BackendReplicationSummary = ToolkitItem["replication_summary"];
type BackendValidationRollup = ValidationRollup;

type BackendItemBrowse = BackendItemSummary & {
  maturity_stage?: MaturityStage | null;
  synonyms?: string[];
  components?: string[];
  mechanisms?: string[];
  techniques?: string[];
  target_processes?: string[];
  validation_rollup?: BackendValidationRollup | null;
  replication_summary?: BackendReplicationSummary | null;
};

type BackendItemDetail = BackendItemSummary & {
  maturity_stage?: MaturityStage | null;
  synonyms?: string[];
  components?: string[];
  mechanisms?: string[];
  techniques?: string[];
  target_processes?: string[];
  external_ids?: Record<string, unknown>;
  source_status?: Record<string, unknown>;
  citation_candidates?: CitationCandidate[];
  workflow_recommendations?: BackendWorkflowRecommendation[];
  claims?: BackendItemClaim[];
  validation_rollup?: BackendValidationRollup | null;
  validations?: BackendValidationObservation[];
  replication_summary?: BackendReplicationSummary | null;
  item_facets?: BackendItemFacet[];
  explainers?: BackendItemExplainer[];
  comparisons?: BackendItemComparison[];
  problem_links?: BackendItemProblemLink[];
  approval_evidence?: ApprovedItemEvidence | null;
  index_markdown: string;
  evidence_markdown: string;
  replication_markdown: string;
  workflow_fit_markdown: string;
};

type BackendWorkflowSummary = {
  slug: string;
  name: string;
  workflow_family: WorkflowFamily;
  objective: string;
  throughput_class?: string | null;
};

type BackendWorkflowStepTemplate = {
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
  duration_typical_hours?: number | null;
  hands_on_hours?: number | null;
  direct_cost_usd_typical?: number | null;
  parallelizable?: boolean | null;
  failure_probability?: number | null;
  input_artifact?: string | null;
  output_artifact?: string | null;
};

type BackendWorkflowStageTemplate = {
  stage_name: string;
  stage_kind: WorkflowStageKind;
  stage_order: number;
  search_modality?: WorkflowSearchModality | null;
  input_candidate_count_typical?: number | null;
  output_candidate_count_typical?: number | null;
  candidate_unit?: string | null;
  selection_basis?: string | null;
  counterselection_basis?: string | null;
  enriches_for_axes?: string[];
  guards_against_axes?: string[];
  preserves_downstream_property_axes?: string[];
  why_stage_exists?: string | null;
  advance_criteria?: string | null;
  decision_gate_reason?: string | null;
  bottleneck_risk?: string | null;
  higher_fidelity_than_previous?: boolean | null;
};

type BackendWorkflowDetail = BackendWorkflowSummary & {
  protocol_family?: string | null;
  engineered_system_family?: string | null;
  why_workflow_works?: string | null;
  priority_logic?: string | null;
  validation_strategy?: string | null;
  recommended_for?: string[];
  default_parallelization_assumption?: string | null;
  mechanisms?: string[];
  techniques?: string[];
  design_goals?: Array<Record<string, unknown>>;
  item_roles?: Array<Record<string, unknown>>;
  stage_templates?: BackendWorkflowStageTemplate[];
  step_templates?: BackendWorkflowStepTemplate[];
  assumption_notes?: string[];
  index_markdown: string;
};

type BackendGapSummary = GapSummary;
type BackendGapDetail = GapDetail;

type SeedBundleItem = {
  slug: string;
  structured: Record<string, unknown>;
};

type SeedBundleWorkflow = {
  slug: string;
  structured: Record<string, unknown>;
};

type RawFirstPassEvidenceSnippet =
  | string
  | {
      text?: string | null;
      source_document?: FirstPassSourceDocument | null;
    };

type RawFirstPassExplainer = Partial<FirstPassExplainer> & {
  explainer_kind?: string;
  body?: string | null;
  source_document?: FirstPassSourceDocument | null;
};

type RawFirstPassEntityDetail = Omit<FirstPassEntityDetail, "evidence_snippets"> & {
  evidence_snippets?: RawFirstPassEvidenceSnippet[];
  freeform_explainers?: RawFirstPassExplainer[];
};

type RawFirstPassEntitySummary = Partial<
  Omit<
    FirstPassEntitySummary,
    "candidate_type" | "slug" | "canonical_name" | "source_document_count" | "claim_count"
  >
> & {
  candidate_type: string;
  slug: string;
  canonical_name: string;
  source_document_count: number;
  claim_count: number;
};

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const REVALIDATE_SECONDS = 30;
const ALLOW_SEED_FALLBACK = process.env.TOOL_DB_ALLOW_SEED_FALLBACK === "true";

class BackendNotFoundError extends Error {
  constructor(path: string) {
    super(`Backend returned 404 for ${path}`);
    this.name = "BackendNotFoundError";
  }
}

type FetchBackendJsonOptions = {
  cacheMode?: "revalidate" | "no-store";
};

export function getApiBaseUrl(): string {
  const internalHost = process.env.TOOL_DB_API_HOST?.trim();
  if (internalHost) {
    const internalPort = process.env.TOOL_DB_API_PORT?.trim() || "8000";
    const internalProtocol = process.env.TOOL_DB_API_PROTOCOL?.trim() || "http";
    return `${internalProtocol}://${internalHost}:${internalPort}`.replace(
      /\/$/,
      "",
    );
  }

  return (
    process.env.TOOL_DB_API_BASE_URL ||
    process.env.NEXT_PUBLIC_TOOL_DB_API_BASE_URL ||
    DEFAULT_API_BASE_URL
  ).replace(/\/$/, "");
}

async function fetchBackendJson<T>(
  path: string,
  options: FetchBackendJsonOptions = {},
): Promise<T> {
  const cacheMode = options.cacheMode ?? "revalidate";
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...(cacheMode === "no-store"
      ? { cache: "no-store" as const }
      : { next: { revalidate: REVALIDATE_SECONDS } }),
  });

  if (response.status === 404) {
    throw new BackendNotFoundError(path);
  }
  if (!response.ok) {
    throw new Error(`Backend request failed for ${path}: ${response.status}`);
  }

  return (await response.json()) as T;
}

function backendUnavailableError(
  resourceName: string,
  error: unknown,
): Error {
  const detail =
    error instanceof Error ? error.message : typeof error === "string" ? error : "unknown backend error";
  return new Error(
    `Backend data unavailable for ${resourceName} from ${getApiBaseUrl()}. ` +
      `The frontend no longer silently falls back to the bundled seed dataset unless TOOL_DB_ALLOW_SEED_FALLBACK=true. ` +
      `Make sure the local API is running and serving current routes. Original error: ${detail}`,
  );
}

function coerceModality(value: string | null | undefined): Modality | null {
  if (!value) {
    return null;
  }
  return value as Modality;
}

function normalizeItemType(
  rawType: ToolkitItem["item_type"],
  canonicalName: string,
  summary: string | null | undefined,
  synonyms: string[] | undefined,
): ToolkitItem["item_type"] {
  if (rawType !== "engineering_method") {
    return rawType;
  }

  const text = [canonicalName, summary ?? "", ...(synonyms ?? [])]
    .join(" ")
    .toLowerCase();

  const architectureHint =
    /\b(system|circuit|construct|platform|module)\b/.test(text) &&
    !/\b(method|methods|assay|protocol|workflow|algorithm|framework|analysis|optimization)\b/.test(
      text,
    );

  if (!architectureHint) {
    return rawType;
  }

  if (/\b(switch|split|dimerization|dimerisation|recruitment|inducible)\b/.test(text)) {
    return "multi_component_switch";
  }

  return "construct_pattern";
}

function buildCitationDocument(
  itemSlug: string,
  citation: CitationCandidate,
  index: number,
): SourceDocument {
  return {
    id: citation.source_document_id ?? `${itemSlug}-citation-doc-${index + 1}`,
    source_type:
      citation.source_type ??
      (citation.citation_role === "database_reference"
        ? "database_entry"
        : "primary_paper"),
    title: citation.label ?? `Citation ${index + 1}`,
    doi: citation.doi ?? null,
    pmid: citation.pmid ?? null,
    publication_year: citation.publication_year ?? null,
    journal_or_source: citation.url ?? null,
    is_retracted: citation.is_retracted ?? false,
  };
}

function mapCitationCandidates(
  itemSlug: string,
  citations: CitationCandidate[] | undefined,
): ItemCitation[] {
  return (citations ?? []).map((citation, index) => ({
    id: `${itemSlug}-citation-${index + 1}`,
    source_document_id:
      citation.source_document_id ?? `${itemSlug}-citation-doc-${index + 1}`,
    citation_role: citation.citation_role ?? "foundational",
    importance_rank: citation.importance_rank ?? index + 1,
    why_this_matters:
      citation.why_this_matters ??
      (citation.status === "needs_curation"
        ? "Citation placeholder kept to show the next curator target for this dossier."
        : "Citation promoted into the dossier from the current backend curation layer."),
    document: buildCitationDocument(itemSlug, citation, index),
  }));
}

function mapValidationObservation(
  itemId: string,
  observation: BackendValidationObservation,
): ValidationObservation {
  return {
    ...observation,
    item_id: observation.item_id ?? itemId,
    metrics: observation.metrics ?? [],
    source_locator: observation.source_locator ?? {},
    source_document: observation.source_document ?? null,
  };
}

function mapItemClaim(claim: BackendItemClaim): ItemClaim {
  return {
    ...claim,
    context: claim.context ?? {},
    source_locator: claim.source_locator ?? {},
    metrics: claim.metrics ?? [],
  };
}

function mapBackendItem(detail: BackendItemDetail): ToolkitItem {
  const itemId = `item_${detail.slug.replace(/-/g, "_")}`;
  const validations = (detail.validations ?? []).map((observation) =>
    mapValidationObservation(itemId, observation),
  );
  const synonyms = detail.synonyms ?? [];
  return {
    id: itemId,
    slug: detail.slug,
    canonical_name: detail.canonical_name,
    item_type: normalizeItemType(
      detail.item_type,
      detail.canonical_name,
      detail.summary,
      synonyms,
    ),
    family: detail.family ?? null,
    summary: detail.summary ?? null,
    status: detail.status,
    maturity_stage: detail.maturity_stage ?? "research",
    first_publication_year: detail.first_publication_year ?? null,
    primary_input_modality: coerceModality(detail.primary_input_modality),
    primary_output_modality: coerceModality(detail.primary_output_modality),
    components: detail.components ?? [],
    mechanisms: detail.mechanisms ?? [],
    techniques: detail.techniques ?? [],
    target_processes: detail.target_processes ?? [],
    synonyms,
    validation_rollup: detail.validation_rollup ?? null,
    replication_summary: detail.replication_summary ?? null,
    citations: mapCitationCandidates(detail.slug, detail.citation_candidates),
    validations,
    claims: (detail.claims ?? []).map(mapItemClaim),
    item_facets: detail.item_facets ?? [],
    explainers: detail.explainers ?? [],
    comparisons: detail.comparisons ?? [],
    problem_links: detail.problem_links ?? [],
    workflow_recommendations: detail.workflow_recommendations ?? [],
    approval_evidence: detail.approval_evidence ?? null,
    index_markdown: detail.index_markdown,
    evidence_markdown: detail.evidence_markdown,
    replication_markdown: detail.replication_markdown,
    workflow_fit_markdown: detail.workflow_fit_markdown,
  };
}

function mapBackendBrowseItem(detail: BackendItemBrowse): ToolkitItem {
  const itemId = `item_${detail.slug.replace(/-/g, "_")}`;
  const synonyms = detail.synonyms ?? [];
  return {
    id: itemId,
    slug: detail.slug,
    canonical_name: detail.canonical_name,
    item_type: normalizeItemType(
      detail.item_type,
      detail.canonical_name,
      detail.summary,
      synonyms,
    ),
    family: detail.family ?? null,
    summary: detail.summary ?? null,
    status: detail.status,
    maturity_stage: detail.maturity_stage ?? "research",
    first_publication_year: detail.first_publication_year ?? null,
    primary_input_modality: coerceModality(detail.primary_input_modality),
    primary_output_modality: coerceModality(detail.primary_output_modality),
    components: detail.components ?? [],
    mechanisms: detail.mechanisms ?? [],
    techniques: detail.techniques ?? [],
    target_processes: detail.target_processes ?? [],
    synonyms,
    validation_rollup: detail.validation_rollup ?? null,
    replication_summary: detail.replication_summary ?? null,
    citations: [],
    validations: [],
    claims: [],
    item_facets: [],
    explainers: [],
    comparisons: [],
    problem_links: [],
    workflow_recommendations: [],
    approval_evidence: null,
    index_markdown: null,
    evidence_markdown: null,
    replication_markdown: null,
    workflow_fit_markdown: null,
  };
}

function mapSeedItem(item: SeedBundleItem): ToolkitItem {
  const structured = item.structured;
  const synonyms = (structured.synonyms as string[] | undefined) ?? [];
  const canonicalName = String(structured.canonical_name ?? item.slug);
  const summary = (structured.summary as string | null | undefined) ?? null;
  return {
    id: String(structured.id ?? `item_${item.slug.replace(/-/g, "_")}`),
    slug: String(structured.slug ?? item.slug),
    canonical_name: canonicalName,
    item_type: normalizeItemType(
      structured.item_type as ToolkitItem["item_type"],
      canonicalName,
      summary,
      synonyms,
    ),
    family: (structured.family as string | null | undefined) ?? null,
    summary,
    status: structured.status as ItemStatus,
    maturity_stage:
      (structured.maturity_stage as MaturityStage | undefined) ?? "research",
    first_publication_year: null,
    primary_input_modality: coerceModality(
      (structured.primary_input_modality as string | null | undefined) ?? null,
    ),
    primary_output_modality: coerceModality(
      (structured.primary_output_modality as string | null | undefined) ?? null,
    ),
    components: (structured.components as string[] | undefined) ?? [],
    mechanisms: (structured.mechanisms as string[] | undefined) ?? [],
    techniques: (structured.techniques as string[] | undefined) ?? [],
    target_processes:
      (structured.target_processes as string[] | undefined) ?? [],
    synonyms,
    validation_rollup: null,
    replication_summary: null,
    citations: mapCitationCandidates(
      item.slug,
      (structured.citation_candidates as CitationCandidate[] | undefined) ?? [],
    ),
    validations: [],
    claims: [],
    item_facets: [],
    explainers: [],
    comparisons: [],
    problem_links: [],
    workflow_recommendations:
      (structured.workflow_recommendations as ToolkitItem["workflow_recommendations"]) ??
      [],
    approval_evidence: null,
    index_markdown:
      (structured.index_markdown as string | null | undefined) ?? null,
    evidence_markdown:
      (structured.evidence_markdown as string | null | undefined) ?? null,
    replication_markdown:
      (structured.replication_markdown as string | null | undefined) ?? null,
    workflow_fit_markdown:
      (structured.workflow_fit_markdown as string | null | undefined) ?? null,
  };
}

function mapWorkflowStep(
  slug: string,
  step: BackendWorkflowStepTemplate,
  index: number,
): WorkflowStep {
  return {
    id: `${slug}-step-${index + 1}`,
    step_name: step.step_name,
    stage_name: step.stage_name ?? null,
    step_order: step.step_order ?? null,
    step_type: step.step_type,
    purpose: step.purpose ?? null,
    why_this_step_now: step.why_this_step_now ?? null,
    decision_gate_reason: step.decision_gate_reason ?? null,
    advance_criteria: step.advance_criteria ?? null,
    failure_criteria: step.failure_criteria ?? null,
    validation_focus: step.validation_focus ?? null,
    target_property_axes: step.target_property_axes ?? [],
    target_mechanisms: step.target_mechanisms ?? [],
    target_techniques: step.target_techniques ?? [],
    duration_typical_hours: step.duration_typical_hours ?? null,
    hands_on_hours: step.hands_on_hours ?? null,
    direct_cost_usd_typical: step.direct_cost_usd_typical ?? null,
    parallelizable: step.parallelizable ?? false,
    failure_probability: step.failure_probability ?? null,
    input_artifact: step.input_artifact ?? null,
    output_artifact: step.output_artifact ?? null,
  };
}

function mapWorkflowStage(
  slug: string,
  stage: BackendWorkflowStageTemplate,
  index: number,
): WorkflowStage {
  return {
    id: `${slug}-stage-${index + 1}`,
    stage_name: stage.stage_name,
    stage_kind: stage.stage_kind,
    stage_order: stage.stage_order,
    search_modality: stage.search_modality ?? null,
    input_candidate_count_typical: stage.input_candidate_count_typical ?? null,
    output_candidate_count_typical:
      stage.output_candidate_count_typical ?? null,
    candidate_unit: stage.candidate_unit ?? null,
    selection_basis: stage.selection_basis ?? null,
    counterselection_basis: stage.counterselection_basis ?? null,
    enriches_for_axes: stage.enriches_for_axes ?? [],
    guards_against_axes: stage.guards_against_axes ?? [],
    preserves_downstream_property_axes:
      stage.preserves_downstream_property_axes ?? [],
    why_stage_exists: stage.why_stage_exists ?? null,
    advance_criteria: stage.advance_criteria ?? null,
    decision_gate_reason: stage.decision_gate_reason ?? null,
    bottleneck_risk: stage.bottleneck_risk ?? null,
    higher_fidelity_than_previous: stage.higher_fidelity_than_previous ?? null,
  };
}

function mapBackendWorkflow(detail: BackendWorkflowDetail): WorkflowTemplate {
  const explainer = WORKFLOW_EXPLAINERS[detail.slug] ?? {};
  return {
    id: `workflow_${detail.slug.replace(/-/g, "_")}`,
    slug: detail.slug,
    name: detail.name,
    workflow_family: detail.workflow_family,
    objective: detail.objective,
    throughput_class: detail.throughput_class ?? null,
    recommended_for: detail.recommended_for?.join(", ") ?? null,
    protocol_family: detail.protocol_family ?? null,
    engineered_system_family: detail.engineered_system_family ?? null,
    why_workflow_works: detail.why_workflow_works ?? null,
    priority_logic: detail.priority_logic ?? null,
    validation_strategy: detail.validation_strategy ?? null,
    mechanisms: detail.mechanisms ?? [],
    techniques: detail.techniques ?? [],
    design_goals: detail.design_goals ?? [],
    item_roles: detail.item_roles ?? [],
    stages: (detail.stage_templates ?? [])
      .map((stage, index) => mapWorkflowStage(detail.slug, stage, index))
      .sort((a, b) => a.stage_order - b.stage_order),
    steps: (detail.step_templates ?? []).map((step, index) =>
      mapWorkflowStep(detail.slug, step, index),
    ),
    ...explainer,
  };
}

function mapSeedWorkflow(entry: SeedBundleWorkflow): WorkflowTemplate {
  const structured = entry.structured;
  const explainer = WORKFLOW_EXPLAINERS[entry.slug] ?? {};
  const stages = (
    (structured.stage_templates as
      | BackendWorkflowStageTemplate[]
      | undefined) ?? []
  )
    .map((stage, index) => mapWorkflowStage(entry.slug, stage, index))
    .sort((a, b) => a.stage_order - b.stage_order);
  const steps = (
    (structured.step_templates as BackendWorkflowDetail["step_templates"]) ?? []
  ).map((step, index) => mapWorkflowStep(entry.slug, step, index));
  return {
    id: String(structured.id ?? `workflow_${entry.slug.replace(/-/g, "_")}`),
    slug: String(structured.slug ?? entry.slug),
    name: String(structured.name ?? entry.slug),
    workflow_family: structured.workflow_family as WorkflowFamily,
    objective: String(structured.objective ?? ""),
    throughput_class:
      (structured.throughput_class as string | null | undefined) ?? null,
    recommended_for: Array.isArray(structured.recommended_for)
      ? (structured.recommended_for as string[]).join(", ")
      : null,
    protocol_family:
      (structured.protocol_family as string | null | undefined) ?? null,
    engineered_system_family:
      (structured.engineered_system_family as string | null | undefined) ?? null,
    why_workflow_works:
      (structured.why_workflow_works as string | null | undefined) ?? null,
    priority_logic:
      (structured.priority_logic as string | null | undefined) ?? null,
    validation_strategy:
      (structured.validation_strategy as string | null | undefined) ?? null,
    mechanisms: (structured.mechanisms as string[] | undefined) ?? [],
    techniques: (structured.techniques as string[] | undefined) ?? [],
    design_goals:
      (structured.design_goals as Array<Record<string, unknown>> | undefined) ??
      [],
    item_roles:
      (structured.item_roles as Array<Record<string, unknown>> | undefined) ?? [],
    stages,
    steps,
    ...explainer,
  };
}

function getSeedItems(): ToolkitItem[] {
  return (seedBundle.items as SeedBundleItem[]).map(mapSeedItem);
}

function getSeedWorkflows(): WorkflowTemplate[] {
  return (seedBundle.workflows as SeedBundleWorkflow[]).map(mapSeedWorkflow);
}

function normalizeFirstPassEvidenceSnippet(
  snippet: RawFirstPassEvidenceSnippet,
): FirstPassEvidenceSnippet {
  if (typeof snippet === "string") {
    return {
      text: snippet,
      source_document: null,
    };
  }

  return {
    text: snippet.text ?? "",
    source_document: snippet.source_document ?? null,
  };
}

function normalizeFirstPassExplainer(
  explainer: RawFirstPassExplainer,
): FirstPassExplainer | null {
  if (!explainer.explainer_kind || !explainer.body || !explainer.source_document) {
    return null;
  }
  const body = explainer.body.trim();
  if (!body) {
    return null;
  }
  return {
    explainer_kind: explainer.explainer_kind,
    body,
    source_document: explainer.source_document,
  };
}

function normalizeFirstPassEntityDetail(
  detail: RawFirstPassEntityDetail,
): FirstPassEntityDetail {
  return {
    ...detail,
    candidate_type: detail.candidate_type,
    aliases: detail.aliases ?? [],
    evidence_snippets: (detail.evidence_snippets ?? []).map(
      normalizeFirstPassEvidenceSnippet,
    ),
    source_documents: detail.source_documents ?? [],
    claims: detail.claims ?? [],
    freeform_explainers: (detail.freeform_explainers ?? [])
      .map(normalizeFirstPassExplainer)
      .filter((explainer): explainer is FirstPassExplainer => explainer !== null),
    workflow_observations: detail.workflow_observations ?? [],
    workflow_stage_observations: detail.workflow_stage_observations ?? [],
    workflow_step_observations: detail.workflow_step_observations ?? [],
  };
}

function normalizeFirstPassEntitySummary(
  summary: RawFirstPassEntitySummary,
): FirstPassEntitySummary {
  const evidencePreviews = summary.evidence_previews ?? [];

  return {
    candidate_type: summary.candidate_type,
    slug: summary.slug,
    canonical_name: summary.canonical_name,
    item_type: summary.item_type ?? null,
    matched_slug: summary.matched_slug ?? null,
    source_document_count: summary.source_document_count,
    claim_count: summary.claim_count,
    aliases: summary.aliases ?? [],
    evidence_preview: summary.evidence_preview ?? null,
    evidence_previews:
      evidencePreviews.length > 0
        ? evidencePreviews
        : summary.evidence_preview
          ? [summary.evidence_preview]
          : [],
    claim_previews: summary.claim_previews ?? [],
  };
}

function normalizeGapDetail(detail: BackendGapDetail): GapDetail {
  return {
    ...detail,
    tags: detail.tags ?? [],
    capabilities: detail.capabilities ?? [],
    candidate_tools: detail.candidate_tools ?? [],
  };
}

export async function getItems(): Promise<ToolkitItem[]> {
  try {
    const browseItems =
      await fetchBackendJson<BackendItemBrowse[]>("/api/v1/items-browse");
    return browseItems.map(mapBackendBrowseItem);
  } catch (error) {
    if (ALLOW_SEED_FALLBACK) {
    return getSeedItems();
    }
    throw backendUnavailableError("canonical item browse", error);
  }
}

export async function getItemBySlug(
  slug: string,
): Promise<ToolkitItem | undefined> {
  try {
    const detail = await fetchBackendJson<BackendItemDetail>(
      `/api/v1/items/${slug}`,
    );
    return mapBackendItem(detail);
  } catch (error) {
    if (error instanceof BackendNotFoundError) {
      return undefined;
    }
    if (ALLOW_SEED_FALLBACK) {
      return getSeedItems().find((item) => item.slug === slug);
    }
    throw backendUnavailableError(`canonical item detail for ${slug}`, error);
  }
}

export async function getWorkflows(): Promise<WorkflowTemplate[]> {
  try {
    const summaries =
      await fetchBackendJson<BackendWorkflowSummary[]>("/api/v1/workflows");
    const details = await Promise.all(
      summaries.map((summary) =>
        fetchBackendJson<BackendWorkflowDetail>(
          `/api/v1/workflows/${summary.slug}`,
        ),
      ),
    );
    return details.map(mapBackendWorkflow);
  } catch (error) {
    if (ALLOW_SEED_FALLBACK) {
      return getSeedWorkflows();
    }
    throw backendUnavailableError("workflow listing", error);
  }
}

export async function getGaps(): Promise<GapDetail[]> {
  try {
    const summaries = await fetchBackendJson<BackendGapSummary[]>("/api/v1/gaps");
    const details = await Promise.all(
      summaries
        .filter((summary) => summary.slug)
        .map((summary) =>
          fetchBackendJson<BackendGapDetail>(`/api/v1/gaps/${summary.slug}`),
        ),
    );
    return details.map(normalizeGapDetail);
  } catch (error) {
    throw backendUnavailableError("gap listing", error);
  }
}

export async function getFirstPassEntities(): Promise<FirstPassEntitySummary[]> {
  try {
    const summaries = await fetchBackendJson<RawFirstPassEntitySummary[]>(
      "/api/v1/first-pass-entities",
      { cacheMode: "no-store" },
    );
    return summaries.map(normalizeFirstPassEntitySummary);
  } catch (error) {
    throw backendUnavailableError("first-pass entity listing", error);
  }
}

export async function getFirstPassEntityByKey(
  candidateType: string,
  slug: string,
): Promise<FirstPassEntityDetail | undefined> {
  try {
    const detail = await fetchBackendJson<RawFirstPassEntityDetail>(
      `/api/v1/first-pass-entities/${candidateType}/${slug}`,
      { cacheMode: "no-store" },
    );
    return normalizeFirstPassEntityDetail(detail);
  } catch (error) {
    if (error instanceof BackendNotFoundError) {
      return undefined;
    }
    throw backendUnavailableError(
      `first-pass entity detail for ${candidateType}/${slug}`,
      error,
    );
  }
}

export async function getFirstPassItems(): Promise<FirstPassItemSummary[]> {
  const entities = await getFirstPassEntities();
  return entities.filter(
    (entity): entity is FirstPassItemSummary =>
      entity.candidate_type === "toolkit_item",
  );
}

export async function getFirstPassItemBySlug(
  slug: string,
): Promise<FirstPassItemDetail | undefined> {
  const detail = await getFirstPassEntityByKey("toolkit_item", slug);
  return detail as FirstPassItemDetail | undefined;
}
