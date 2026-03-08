import { ITEMS, WORKFLOWS } from "./data";
import type { ToolkitItem, WorkflowTemplate } from "./types";

const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 100;

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
  limit?: number;
  offset?: number;
}

export interface WorkflowSearchFilters {
  q?: string;
  workflow_family?: string[];
  limit?: number;
  offset?: number;
}

export interface SearchResult<T> {
  total: number;
  limit: number;
  offset: number;
  results: T[];
}

function normalizeText(value: string | null | undefined): string {
  return (value ?? "").trim().toLowerCase();
}

function tokenizeQuery(query: string | undefined): string[] {
  return normalizeText(query)
    .split(/\s+/)
    .filter(Boolean);
}

function matchesQuery(haystacks: Array<string | null | undefined>, query: string | undefined): boolean {
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

function matchesScalar(value: string | null | undefined, expected: string[] | undefined): boolean {
  if (!expected || expected.length === 0) {
    return true;
  }

  const normalizedValue = normalizeText(value);
  return expected.some((candidate) => normalizeText(candidate) === normalizedValue);
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

function paginate<T>(rows: T[], limit: number | undefined, offset: number | undefined): SearchResult<T> {
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

export function parseBooleanParam(rawValue: string | null): boolean | undefined {
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

export function searchItems(filters: ItemSearchFilters): SearchResult<ToolkitItem> {
  const filtered = ITEMS.filter((item) => {
    if (
      !matchesQuery(
        [
          item.canonical_name,
          item.summary,
          item.family,
          item.item_type,
          item.maturity_stage,
          item.status,
          ...item.mechanisms,
          ...item.techniques,
          ...item.target_processes,
          ...item.synonyms,
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

    if (!matchesAny(item.mechanisms, filters.mechanism)) {
      return false;
    }

    if (!matchesAny(item.techniques, filters.technique)) {
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
      (validation?.has_independent_replication ?? false) !== filters.has_independent_replication
    ) {
      return false;
    }

    if (
      filters.has_mouse_in_vivo_validation !== undefined &&
      (validation?.has_mouse_in_vivo_validation ?? false) !== filters.has_mouse_in_vivo_validation
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

  return paginate(filtered, filters.limit, filters.offset);
}

export function searchWorkflows(filters: WorkflowSearchFilters): SearchResult<WorkflowTemplate> {
  const filtered = WORKFLOWS.filter((workflow) => {
    if (
      !matchesQuery(
        [
          workflow.name,
          workflow.objective,
          workflow.recommended_for,
          workflow.workflow_family,
          workflow.throughput_class,
          workflow.simple_summary,
          ...(workflow.how_to_implement ?? []),
          ...(workflow.used_when ?? []),
          ...(workflow.tradeoffs ?? []),
          ...workflow.steps.map((step) => step.step_name),
        ],
        filters.q,
      )
    ) {
      return false;
    }

    if (!matchesScalar(workflow.workflow_family, filters.workflow_family)) {
      return false;
    }

    return true;
  });

  return paginate(filtered, filters.limit, filters.offset);
}
