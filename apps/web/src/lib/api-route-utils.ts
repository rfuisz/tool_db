import type {
  ExtractedWorkflowSearchFilters,
  ItemSearchFilters,
  MechanismConceptSearchFilters,
  TechniqueConceptSearchFilters,
} from "./api-search";
import { parseBooleanParam, splitMultiValue } from "./api-search";

function parseOptionalNumber(rawValue: string | null): number | undefined {
  if (!rawValue) {
    return undefined;
  }

  const parsed = Number(rawValue);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function parseMultiValueParams(searchParams: URLSearchParams, key: string): string[] | undefined {
  const values = splitMultiValue(searchParams.getAll(key));
  return values.length > 0 ? values : undefined;
}

export function parseItemSearchFilters(searchParams: URLSearchParams): ItemSearchFilters {
  return {
    q: searchParams.get("q")?.trim() || undefined,
    type: parseMultiValueParams(searchParams, "type"),
    mechanism: parseMultiValueParams(searchParams, "mechanism"),
    technique: parseMultiValueParams(searchParams, "technique"),
    family: parseMultiValueParams(searchParams, "family"),
    maturity_stage: parseMultiValueParams(searchParams, "maturity_stage"),
    status: parseMultiValueParams(searchParams, "status"),
    has_independent_replication: parseBooleanParam(searchParams.get("has_independent_replication")),
    has_mouse_in_vivo_validation: parseBooleanParam(searchParams.get("has_mouse_in_vivo_validation")),
    has_therapeutic_use: parseBooleanParam(searchParams.get("has_therapeutic_use")),
    sort: (searchParams.get("sort") as ItemSearchFilters["sort"] | null) ?? undefined,
    limit: parseOptionalNumber(searchParams.get("limit")),
    offset: parseOptionalNumber(searchParams.get("offset")),
  };
}

export function parseExtractedWorkflowSearchFilters(searchParams: URLSearchParams): ExtractedWorkflowSearchFilters {
  return {
    q: searchParams.get("q")?.trim() || undefined,
    mechanism: parseMultiValueParams(searchParams, "mechanism"),
    technique: parseMultiValueParams(searchParams, "technique"),
    has_stages: parseBooleanParam(searchParams.get("has_stages")),
    has_steps: parseBooleanParam(searchParams.get("has_steps")),
    sort: (searchParams.get("sort") as ExtractedWorkflowSearchFilters["sort"] | null) ?? undefined,
    limit: parseOptionalNumber(searchParams.get("limit")),
    offset: parseOptionalNumber(searchParams.get("offset")),
  };
}

export function parseMechanismConceptSearchFilters(searchParams: URLSearchParams): MechanismConceptSearchFilters {
  return {
    q: searchParams.get("q")?.trim() || undefined,
    sort: (searchParams.get("sort") as MechanismConceptSearchFilters["sort"] | null) ?? undefined,
    limit: parseOptionalNumber(searchParams.get("limit")),
    offset: parseOptionalNumber(searchParams.get("offset")),
  };
}

export function parseTechniqueConceptSearchFilters(searchParams: URLSearchParams): TechniqueConceptSearchFilters {
  return {
    q: searchParams.get("q")?.trim() || undefined,
    sort: (searchParams.get("sort") as TechniqueConceptSearchFilters["sort"] | null) ?? undefined,
    limit: parseOptionalNumber(searchParams.get("limit")),
    offset: parseOptionalNumber(searchParams.get("offset")),
  };
}
