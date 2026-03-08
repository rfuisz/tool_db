import { NextResponse } from "next/server";

import { getItems, getWorkflows } from "@/lib/backend-data";
import {
  searchItems,
  searchWorkflows,
  type ItemSearchFilters,
  type WorkflowSearchFilters,
} from "@/lib/api-search";
import { interpretPromptQuery } from "@/lib/prompt-query";
import { guardQueryRequest } from "@/lib/query-guard";

export const runtime = "nodejs";

interface QueryRequestBody {
  prompt?: unknown;
  item_filters?: unknown;
  workflow_filters?: unknown;
  include_items?: unknown;
  include_workflows?: unknown;
}

function normalizeStringArray(values: unknown): string[] | undefined {
  if (!Array.isArray(values)) {
    return undefined;
  }

  const normalized = values
    .map((value) => (typeof value === "string" ? value.trim() : ""))
    .filter(Boolean);

  return normalized.length > 0 ? normalized : undefined;
}

function normalizeBoolean(value: unknown): boolean | undefined {
  return typeof value === "boolean" ? value : undefined;
}

function normalizeNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function coerceItemFilters(raw: unknown): Partial<ItemSearchFilters> {
  if (!raw || typeof raw !== "object") {
    return {};
  }

  const value = raw as Record<string, unknown>;
  return {
    q: typeof value.q === "string" ? value.q.trim() : undefined,
    type: normalizeStringArray(value.type),
    mechanism: normalizeStringArray(value.mechanism),
    technique: normalizeStringArray(value.technique),
    family: normalizeStringArray(value.family),
    maturity_stage: normalizeStringArray(value.maturity_stage),
    status: normalizeStringArray(value.status),
    has_independent_replication: normalizeBoolean(
      value.has_independent_replication,
    ),
    has_mouse_in_vivo_validation: normalizeBoolean(
      value.has_mouse_in_vivo_validation,
    ),
    has_therapeutic_use: normalizeBoolean(value.has_therapeutic_use),
    limit: normalizeNumber(value.limit),
    offset: normalizeNumber(value.offset),
  };
}

function coerceWorkflowFilters(raw: unknown): Partial<WorkflowSearchFilters> {
  if (!raw || typeof raw !== "object") {
    return {};
  }

  const value = raw as Record<string, unknown>;
  return {
    q: typeof value.q === "string" ? value.q.trim() : undefined,
    workflow_family: normalizeStringArray(value.workflow_family),
    limit: normalizeNumber(value.limit),
    offset: normalizeNumber(value.offset),
  };
}

function mergeFilters<T extends object>(base: T, override: Partial<T>): T {
  return { ...base, ...override };
}

export async function GET() {
  return NextResponse.json({
    endpoint: "/api/query",
    method: "POST",
    accepts: {
      prompt: "string",
      item_filters: {
        q: "string",
        type: ["string"],
        mechanism: ["string"],
        technique: ["string"],
        family: ["string"],
        maturity_stage: ["string"],
        status: ["string"],
        has_independent_replication: "boolean",
        has_mouse_in_vivo_validation: "boolean",
        has_therapeutic_use: "boolean",
        limit: "number",
        offset: "number",
      },
      workflow_filters: {
        q: "string",
        workflow_family: ["string"],
        limit: "number",
        offset: "number",
      },
      include_items: "boolean",
      include_workflows: "boolean",
    },
    llm_env: {
      upstream_api_key: "TOOL_DB_QUERY_UPSTREAM_API_KEY",
      upstream_base_url: "TOOL_DB_QUERY_UPSTREAM_BASE_URL",
      upstream_model: "TOOL_DB_QUERY_UPSTREAM_MODEL",
      legacy_api_key: "TOOL_DB_QUERY_LLM_API_KEY",
      legacy_base_url: "TOOL_DB_QUERY_LLM_BASE_URL",
      legacy_model: "TOOL_DB_QUERY_LLM_MODEL",
    },
    protection_env: {
      client_api_key: "TOOL_DB_QUERY_CLIENT_API_KEY",
      legacy_shared_api_key: "TOOL_DB_QUERY_API_KEY",
      rate_limit_max_requests: "TOOL_DB_QUERY_RATE_LIMIT_MAX_REQUESTS",
      rate_limit_window_ms: "TOOL_DB_QUERY_RATE_LIMIT_WINDOW_MS",
    },
  });
}

export async function POST(request: Request) {
  const guardResult = guardQueryRequest(request);
  if (!guardResult.ok) {
    return NextResponse.json(
      { error: guardResult.error },
      { status: guardResult.status ?? 400, headers: guardResult.headers },
    );
  }

  let body: QueryRequestBody;

  try {
    body = (await request.json()) as QueryRequestBody;
  } catch {
    return NextResponse.json(
      { error: "Request body must be valid JSON." },
      { status: 400 },
    );
  }

  const prompt = typeof body.prompt === "string" ? body.prompt.trim() : "";
  const promptInterpretation = prompt
    ? await interpretPromptQuery(prompt)
    : null;

  const itemFilters = mergeFilters(
    promptInterpretation?.item_filters ?? {},
    coerceItemFilters(body.item_filters),
  );
  const workflowFilters = mergeFilters(
    promptInterpretation?.workflow_filters ?? {},
    coerceWorkflowFilters(body.workflow_filters),
  );

  const includeItems =
    typeof body.include_items === "boolean"
      ? body.include_items
      : (promptInterpretation?.include_items ?? true);
  const includeWorkflows =
    typeof body.include_workflows === "boolean"
      ? body.include_workflows
      : (promptInterpretation?.include_workflows ?? true);

  const [items, workflows] = await Promise.all([
    includeItems ? getItems() : Promise.resolve([]),
    includeWorkflows ? getWorkflows() : Promise.resolve([]),
  ]);

  const itemResult = includeItems ? searchItems(items, itemFilters) : null;
  const workflowResult = includeWorkflows
    ? searchWorkflows(workflows, workflowFilters)
    : null;

  return NextResponse.json(
    {
      mode: prompt ? "prompt" : "structured",
      prompt: prompt || null,
      interpretation: promptInterpretation
        ? {
            item_filters: promptInterpretation.item_filters,
            workflow_filters: promptInterpretation.workflow_filters,
            include_items: promptInterpretation.include_items,
            include_workflows: promptInterpretation.include_workflows,
            ambiguity_notes: promptInterpretation.ambiguity_notes,
            llm_used: promptInterpretation.llm_used,
          }
        : null,
      item_filters: itemFilters,
      workflow_filters: workflowFilters,
      items: itemResult?.results ?? [],
      workflows: workflowResult?.results ?? [],
      total_items: itemResult?.total ?? 0,
      total_workflows: workflowResult?.total ?? 0,
      item_pagination: itemResult
        ? { limit: itemResult.limit, offset: itemResult.offset }
        : null,
      workflow_pagination: workflowResult
        ? { limit: workflowResult.limit, offset: workflowResult.offset }
        : null,
    },
    { headers: guardResult.headers },
  );
}
