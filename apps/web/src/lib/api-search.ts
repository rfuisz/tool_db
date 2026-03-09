import type { ExtractedWorkflowSummary, ToolkitItem } from "./types";
import {
  buildItemHierarchyAssignments,
  buildMechanismConceptSummaries,
  buildTechniqueConceptSummaries,
  type MechanismConceptSummary,
  type TechniqueConceptSummary,
} from "./item-hierarchy";

const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 500;

type ItemSort =
  | "name"
  | "evidence"
  | "replication"
  | "practicality"
  | "year";

export interface ItemSearchFilters {
  q?: string;
  type?: string[];
  mechanism?: string[];
  technique?: string[];
  family?: string[];
  maturity_stage?: string[];
  status?: string[];
  has_independent_replication?: boolean;
  has_mouse_in_vivo_validation?: boolean;
  has_therapeutic_use?: boolean;
  sort?: ItemSort;
  limit?: number;
  offset?: number;
}

type ExtractedWorkflowSort = "year" | "stages" | "steps" | "objective";

export interface ExtractedWorkflowSearchFilters {
  q?: string;
  mechanism?: string[];
  technique?: string[];
  has_stages?: boolean;
  has_steps?: boolean;
  sort?: ExtractedWorkflowSort;
  limit?: number;
  offset?: number;
}

export interface SearchResult<T> {
  total: number;
  limit: number;
  offset: number;
  results: T[];
}

function sortItems(items: ToolkitItem[], sort: ItemSort | undefined): ToolkitItem[] {
  const sorted = [...items];

  switch (sort) {
    case "evidence":
      sorted.sort(
        (a, b) =>
          (b.replication_summary?.evidence_strength_score ?? 0) -
          (a.replication_summary?.evidence_strength_score ?? 0),
      );
      break;
    case "replication":
      sorted.sort(
        (a, b) =>
          (b.replication_summary?.replication_score ?? 0) -
          (a.replication_summary?.replication_score ?? 0),
      );
      break;
    case "practicality":
      sorted.sort(
        (a, b) =>
          (b.replication_summary?.practicality_score ?? 0) -
          (a.replication_summary?.practicality_score ?? 0),
      );
      break;
    case "year":
      sorted.sort(
        (a, b) =>
          (a.first_publication_year ?? 9999) - (b.first_publication_year ?? 9999),
      );
      break;
    case "name":
    default:
      sorted.sort((a, b) => a.canonical_name.localeCompare(b.canonical_name));
      break;
  }

  return sorted;
}

function normalizeText(value: string | null | undefined): string {
  return (value ?? "").trim().toLowerCase();
}

function tokenizeQuery(query: string | undefined): string[] {
  return normalizeText(query).split(/\s+/).filter(Boolean);
}

function matchesQuery(
  haystacks: Array<string | null | undefined>,
  query: string | undefined,
): boolean {
  const tokens = tokenizeQuery(query);
  if (tokens.length === 0) {
    return true;
  }

  const searchable = haystacks.map((value) => normalizeText(value)).join(" ");
  return tokens.every((token) => searchable.includes(token));
}

function matchesAny(values: string[], expected: string[] | undefined): boolean {
  if (!expected || expected.length === 0) {
    return true;
  }

  const normalizedValues = new Set(values.map((value) => normalizeText(value)));
  return expected.some((value) => normalizedValues.has(normalizeText(value)));
}

function matchesScalar(
  value: string | null | undefined,
  expected: string[] | undefined,
): boolean {
  if (!expected || expected.length === 0) {
    return true;
  }

  const normalizedValue = normalizeText(value);
  return expected.some(
    (candidate) => normalizeText(candidate) === normalizedValue,
  );
}

function normalizeLimit(limit: number | undefined): number {
  if (!Number.isFinite(limit) || !limit || limit < 1) {
    return DEFAULT_LIMIT;
  }
  return Math.min(Math.trunc(limit), MAX_LIMIT);
}

function normalizeOffset(offset: number | undefined): number {
  if (!Number.isFinite(offset) || !offset || offset < 0) {
    return 0;
  }
  return Math.trunc(offset);
}

function paginate<T>(
  rows: T[],
  limit: number | undefined,
  offset: number | undefined,
): SearchResult<T> {
  const normalizedLimit = normalizeLimit(limit);
  const normalizedOffset = normalizeOffset(offset);

  return {
    total: rows.length,
    limit: normalizedLimit,
    offset: normalizedOffset,
    results: rows.slice(normalizedOffset, normalizedOffset + normalizedLimit),
  };
}

export function splitMultiValue(rawValues: string[]): string[] {
  return rawValues
    .flatMap((value) => value.split(","))
    .map((value) => value.trim())
    .filter(Boolean);
}

export function parseBooleanParam(
  rawValue: string | null,
): boolean | undefined {
  if (!rawValue) {
    return undefined;
  }

  const normalized = rawValue.trim().toLowerCase();
  if (normalized === "true" || normalized === "1" || normalized === "yes") {
    return true;
  }
  if (normalized === "false" || normalized === "0" || normalized === "no") {
    return false;
  }

  return undefined;
}

export function searchItems(
  items: ToolkitItem[],
  filters: ItemSearchFilters,
): SearchResult<ToolkitItem> {
  const hierarchyAssignments = buildItemHierarchyAssignments(items);
  const filtered = items.filter((item) => {
    const mechanismAssignments =
      hierarchyAssignments.mechanismsBySlug.get(item.slug) ?? item.mechanisms;
    const techniqueAssignments =
      hierarchyAssignments.techniquesBySlug.get(item.slug) ?? item.techniques;
    if (
      !matchesQuery(
        [
          item.canonical_name,
          item.summary,
          item.family,
          item.item_type,
          item.maturity_stage,
          item.status,
          ...mechanismAssignments,
          ...techniqueAssignments,
          ...item.target_processes,
          ...item.synonyms,
          ...(item.components ?? []),
          ...item.citations.map((citation) => citation.document.title),
        ],
        filters.q,
      )
    ) {
      return false;
    }

    if (!matchesScalar(item.item_type, filters.type)) {
      return false;
    }

    if (!matchesAny(mechanismAssignments, filters.mechanism)) {
      return false;
    }

    if (!matchesAny(techniqueAssignments, filters.technique)) {
      return false;
    }

    if (!matchesScalar(item.family, filters.family)) {
      return false;
    }

    if (!matchesScalar(item.maturity_stage, filters.maturity_stage)) {
      return false;
    }

    if (!matchesScalar(item.status, filters.status)) {
      return false;
    }

    const validation = item.validation_rollup;

    if (
      filters.has_independent_replication !== undefined &&
      (validation?.has_independent_replication ?? false) !==
        filters.has_independent_replication
    ) {
      return false;
    }

    if (
      filters.has_mouse_in_vivo_validation !== undefined &&
      (validation?.has_mouse_in_vivo_validation ?? false) !==
        filters.has_mouse_in_vivo_validation
    ) {
      return false;
    }

    if (
      filters.has_therapeutic_use !== undefined &&
      (validation?.has_therapeutic_use ?? false) !== filters.has_therapeutic_use
    ) {
      return false;
    }

    return true;
  });

  return paginate(sortItems(filtered, filters.sort), filters.limit, filters.offset);
}

function sortExtractedWorkflows(
  workflows: ExtractedWorkflowSummary[],
  sort: ExtractedWorkflowSort | undefined,
): ExtractedWorkflowSummary[] {
  const sorted = [...workflows];
  switch (sort) {
    case "stages":
      sorted.sort((a, b) => b.stages.length - a.stages.length);
      break;
    case "steps":
      sorted.sort((a, b) => b.steps.length - a.steps.length);
      break;
    case "objective":
      sorted.sort((a, b) =>
        (a.workflow_objective ?? "").localeCompare(b.workflow_objective ?? ""),
      );
      break;
    case "year":
    default:
      sorted.sort(
        (a, b) =>
          (b.source_document?.publication_year ?? 0) -
          (a.source_document?.publication_year ?? 0),
      );
      break;
  }
  return sorted;
}

export function searchExtractedWorkflows(
  workflows: ExtractedWorkflowSummary[],
  filters: ExtractedWorkflowSearchFilters,
): SearchResult<ExtractedWorkflowSummary> {
  const filtered = workflows.filter((wf) => {
    if (
      !matchesQuery(
        [
          wf.workflow_objective,
          wf.protocol_family,
          wf.engineered_system_family,
          wf.why_workflow_works,
          wf.evidence_text,
          wf.source_document?.title,
          wf.source_document?.journal_or_source,
          ...wf.target_mechanisms,
          ...wf.target_techniques,
          ...wf.stages.map((s) => s.stage_name),
          ...wf.steps.map((s) => s.step_name),
          ...wf.involved_items.map((i) => i.display_name),
        ],
        filters.q,
      )
    ) {
      return false;
    }

    if (!matchesAny(wf.target_mechanisms, filters.mechanism)) {
      return false;
    }
    if (!matchesAny(wf.target_techniques, filters.technique)) {
      return false;
    }
    if (filters.has_stages === true && wf.stages.length === 0) {
      return false;
    }
    if (filters.has_steps === true && wf.steps.length === 0) {
      return false;
    }
    return true;
  });

  return paginate(
    sortExtractedWorkflows(filtered, filters.sort),
    filters.limit,
    filters.offset,
  );
}

// ---------------------------------------------------------------------------
// Mechanism & Technique concept search
// ---------------------------------------------------------------------------

type MechanismConceptSort = "name" | "items" | "architectures" | "components";
type TechniqueConceptSort = "name" | "items" | "methods";

export interface MechanismConceptSearchFilters {
  q?: string;
  sort?: MechanismConceptSort;
  limit?: number;
  offset?: number;
}

export interface TechniqueConceptSearchFilters {
  q?: string;
  sort?: TechniqueConceptSort;
  limit?: number;
  offset?: number;
}

function sortMechanismConcepts(
  concepts: MechanismConceptSummary[],
  sort: MechanismConceptSort | undefined,
): MechanismConceptSummary[] {
  const sorted = [...concepts];
  switch (sort) {
    case "items":
      sorted.sort((a, b) => b.totalCount - a.totalCount);
      break;
    case "architectures":
      sorted.sort((a, b) => b.architectureCount - a.architectureCount);
      break;
    case "components":
      sorted.sort((a, b) => b.componentCount - a.componentCount);
      break;
    case "name":
    default:
      sorted.sort((a, b) => a.label.localeCompare(b.label));
      break;
  }
  return sorted;
}

function sortTechniqueConcepts(
  concepts: TechniqueConceptSummary[],
  sort: TechniqueConceptSort | undefined,
): TechniqueConceptSummary[] {
  const sorted = [...concepts];
  switch (sort) {
    case "items":
      sorted.sort((a, b) => b.totalCount - a.totalCount);
      break;
    case "methods":
      sorted.sort((a, b) => b.methodCount - a.methodCount);
      break;
    case "name":
    default:
      sorted.sort((a, b) => a.label.localeCompare(b.label));
      break;
  }
  return sorted;
}

export function searchMechanismConcepts(
  items: ToolkitItem[],
  filters: MechanismConceptSearchFilters,
): SearchResult<MechanismConceptSummary> {
  const concepts = buildMechanismConceptSummaries(items);
  const filtered = concepts.filter((c) =>
    matchesQuery(
      [c.label, c.key, c.description, c.summary, ...c.capabilities, ...c.componentNames],
      filters.q,
    ),
  );
  return paginate(
    sortMechanismConcepts(filtered, filters.sort),
    filters.limit,
    filters.offset,
  );
}

export function searchTechniqueConcepts(
  items: ToolkitItem[],
  filters: TechniqueConceptSearchFilters,
): SearchResult<TechniqueConceptSummary> {
  const concepts = buildTechniqueConceptSummaries(items);
  const filtered = concepts.filter((c) =>
    matchesQuery(
      [c.label, c.key, c.description, c.summary, ...c.capabilities],
      filters.q,
    ),
  );
  return paginate(
    sortTechniqueConcepts(filtered, filters.sort),
    filters.limit,
    filters.offset,
  );
}
