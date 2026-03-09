import "server-only";

import type { ExtractedWorkflowSearchFilters, ItemSearchFilters } from "./api-search";

const DEFAULT_QUERY_MODEL = "gpt-5-nano";
const DEFAULT_QUERY_BASE_URL = "https://api.openai.com/v1";

export interface PromptQueryInterpretation {
  item_filters: ItemSearchFilters;
  workflow_filters: ExtractedWorkflowSearchFilters;
  include_items: boolean;
  include_workflows: boolean;
  ambiguity_notes: string[];
  llm_used: boolean;
}

interface LlmPromptQueryResponse {
  item_filters?: ItemSearchFilters;
  workflow_filters?: ExtractedWorkflowSearchFilters;
  include_items?: boolean;
  include_workflows?: boolean;
  ambiguity_notes?: string[];
}

function getQueryApiKey(): string {
  return (
    process.env.TOOL_DB_QUERY_UPSTREAM_API_KEY ??
    process.env.TOOL_DB_QUERY_LLM_API_KEY ??
    process.env.LLM_API_KEY ??
    process.env.OPENAI_API_KEY ??
    ""
  );
}

function getQueryBaseUrl(): string {
  return (
    process.env.TOOL_DB_QUERY_UPSTREAM_BASE_URL ??
    process.env.TOOL_DB_QUERY_LLM_BASE_URL ??
    process.env.LLM_BASE_URL ??
    process.env.OPENAI_BASE_URL ??
    DEFAULT_QUERY_BASE_URL
  ).replace(/\/+$/, "");
}

function getQueryModel(): string {
  return (
    process.env.TOOL_DB_QUERY_UPSTREAM_MODEL ??
    process.env.TOOL_DB_QUERY_LLM_MODEL ??
    process.env.LLM_MODEL ??
    process.env.OPENAI_MODEL ??
    DEFAULT_QUERY_MODEL
  );
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

function normalizeFilters(
  raw: LlmPromptQueryResponse,
): PromptQueryInterpretation {
  return {
    item_filters: {
      q:
        typeof raw.item_filters?.q === "string"
          ? raw.item_filters.q.trim()
          : undefined,
      type: normalizeStringArray(raw.item_filters?.type),
      mechanism: normalizeStringArray(raw.item_filters?.mechanism),
      technique: normalizeStringArray(raw.item_filters?.technique),
      family: normalizeStringArray(raw.item_filters?.family),
      maturity_stage: normalizeStringArray(raw.item_filters?.maturity_stage),
      status: normalizeStringArray(raw.item_filters?.status),
      has_independent_replication: normalizeBoolean(
        raw.item_filters?.has_independent_replication,
      ),
      has_mouse_in_vivo_validation: normalizeBoolean(
        raw.item_filters?.has_mouse_in_vivo_validation,
      ),
      has_therapeutic_use: normalizeBoolean(
        raw.item_filters?.has_therapeutic_use,
      ),
    },
    workflow_filters: {
      q:
        typeof raw.workflow_filters?.q === "string"
          ? raw.workflow_filters.q.trim()
          : undefined,
      mechanism: normalizeStringArray(raw.workflow_filters?.mechanism),
      technique: normalizeStringArray(raw.workflow_filters?.technique),
    },
    include_items: raw.include_items !== false,
    include_workflows: raw.include_workflows !== false,
    ambiguity_notes: Array.isArray(raw.ambiguity_notes)
      ? raw.ambiguity_notes
          .map((note) => (typeof note === "string" ? note.trim() : ""))
          .filter(Boolean)
      : [],
    llm_used: true,
  };
}

function fallbackInterpretation(prompt: string): PromptQueryInterpretation {
  return {
    item_filters: { q: prompt },
    workflow_filters: { q: prompt },
    include_items: true,
    include_workflows: true,
    ambiguity_notes: [
      "Prompt fallback mode is active because no dedicated query LLM is configured or the upstream parse failed.",
    ],
    llm_used: false,
  };
}

function extractJsonObject(rawContent: string): string {
  const trimmed = rawContent.trim();
  if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
    return trimmed;
  }

  const match = trimmed.match(/\{[\s\S]*\}/);
  if (!match) {
    throw new Error("No JSON object found in LLM response");
  }

  return match[0];
}

export async function interpretPromptQuery(
  prompt: string,
): Promise<PromptQueryInterpretation> {
  const normalizedPrompt = prompt.trim();
  if (!normalizedPrompt) {
    return fallbackInterpretation(prompt);
  }

  const apiKey = getQueryApiKey();
  if (!apiKey) {
    return fallbackInterpretation(normalizedPrompt);
  }

  try {
    const response = await fetch(`${getQueryBaseUrl()}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: getQueryModel(),
        temperature: 0,
        response_format: { type: "json_object" },
        messages: [
          {
            role: "system",
            content:
              "Convert user questions into structured filters for a read-only biotechnology tool database. " +
              "Return JSON with keys item_filters, workflow_filters, include_items, include_workflows, and ambiguity_notes. " +
              "Use only filter keys that exist. " +
              "Valid item filter keys: q, type, mechanism, technique, family, maturity_stage, status, has_independent_replication, has_mouse_in_vivo_validation, has_therapeutic_use. " +
              "Valid workflow filter keys: q, mechanism, technique. " +
              "If a request is broad, keep q populated with the original search terms instead of inventing unsupported filters.",
          },
          {
            role: "user",
            content: normalizedPrompt,
          },
        ],
      }),
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Prompt parser failed with status ${response.status}`);
    }

    const data = (await response.json()) as {
      choices?: Array<{ message?: { content?: string | null } }>;
    };

    const content = data.choices?.[0]?.message?.content;
    if (!content) {
      throw new Error("Prompt parser returned no content");
    }

    const parsed = JSON.parse(
      extractJsonObject(content),
    ) as LlmPromptQueryResponse;
    return normalizeFilters(parsed);
  } catch {
    return fallbackInterpretation(normalizedPrompt);
  }
}
