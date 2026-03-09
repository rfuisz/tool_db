import { NextResponse } from "next/server";

import { getItems, getExtractedWorkflows } from "@/lib/backend-data";
import {
  searchItems,
  searchExtractedWorkflows,
  type ItemSearchFilters,
  type ExtractedWorkflowSearchFilters,
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

function coerceWorkflowFilters(raw: unknown): Partial<ExtractedWorkflowSearchFilters> {
  if (!raw || typeof raw !== "object") {
    return {};
  }

  const value = raw as Record<string, unknown>;
  return {
    q: typeof value.q === "string" ? value.q.trim() : undefined,
    mechanism: normalizeStringArray(value.mechanism),
    technique: normalizeStringArray(value.technique),
    limit: normalizeNumber(value.limit),
    offset: normalizeNumber(value.offset),
  };
}

function mergeFilters<T extends object>(base: T, override: Partial<T>): T {
  return { ...base, ...override };
}

export async function GET() {
  return NextResponse.json({
    openapi: "3.1.0",
    info: {
      title: "Biocontrol Toolkit Query API",
      version: "1.0.0",
      description:
        "Search the biocontrol toolkit database by structured filters or natural-language prompt. " +
        "Structured queries are free and unauthenticated. " +
        "Prompt queries use an LLM to parse natural language into filters and require an API key.",
    },
    paths: {
      "/api/query": {
        post: {
          summary: "Query toolkit items and extracted workflows",
          description:
            "Two modes: (1) structured — pass item_filters / workflow_filters directly; " +
            "(2) prompt — send a natural-language question that the server parses into filters via LLM. " +
            "Modes can be combined; explicit filters override any LLM-derived filters.",
          security: [
            {
              note: "Required ONLY when the request body contains a `prompt` field. Structured filter queries need no key.",
              ApiKeyAuth: [],
            },
          ],
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: { $ref: "#/components/schemas/QueryRequest" },
              },
            },
          },
          responses: {
            "200": {
              description: "Query results",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/QueryResponse" },
                },
              },
            },
            "400": {
              description: "Invalid JSON body",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      error: { type: "string" },
                    },
                  },
                },
              },
            },
            "401": {
              description:
                "Missing or invalid API key (prompt queries only)",
            },
            "429": {
              description:
                "Rate limit exceeded (prompt queries only). Check Retry-After header.",
            },
          },
        },
      },
    },
    components: {
      securitySchemes: {
        ApiKeyAuth: {
          type: "apiKey",
          in: "header",
          name: "x-api-key",
          description:
            "Required only for prompt-mode queries (requests containing a `prompt` field). " +
            "Also accepted as Authorization: Bearer <key>.",
        },
      },
      schemas: {
        QueryRequest: {
          type: "object",
          description:
            "Send `item_filters` / `workflow_filters` for structured mode, `prompt` for LLM mode, or both.",
          properties: {
            prompt: {
              type: "string",
              description:
                "Natural-language question. The server uses an LLM to convert this into structured filters. Requires API key.",
              example:
                "Which tools have mouse validation and independent replication?",
            },
            item_filters: {
              $ref: "#/components/schemas/ItemFilters",
            },
            workflow_filters: {
              $ref: "#/components/schemas/WorkflowFilters",
            },
            include_items: {
              type: "boolean",
              default: true,
              description: "Set false to omit toolkit items from results.",
            },
            include_workflows: {
              type: "boolean",
              default: true,
              description:
                "Set false to omit extracted workflows from results.",
            },
          },
        },
        ItemFilters: {
          type: "object",
          description:
            "Structured filters for toolkit items. All fields are optional; omitted fields are not filtered.",
          properties: {
            q: {
              type: "string",
              description:
                "Full-text search across name, summary, synonyms, mechanisms, techniques, citations.",
            },
            type: {
              type: "array",
              items: {
                type: "string",
                enum: [
                  "protein_domain",
                  "multi_component_switch",
                  "rna_element",
                  "construct_pattern",
                  "engineering_method",
                  "assay_method",
                  "computation_method",
                  "delivery_harness",
                ],
              },
              description: "Filter by item type. Match is OR across values.",
            },
            mechanism: {
              type: "array",
              items: {
                type: "string",
                enum: [
                  "heterodimerization",
                  "oligomerization",
                  "conformational_uncaging",
                  "membrane_recruitment",
                  "photocleavage",
                  "dna_binding",
                  "rna_binding",
                  "degradation",
                  "translation_control",
                  "mechanotransduction",
                  "sonoporation",
                  "thermal_gating",
                  "magnetic_actuation",
                  "electroconformational_change",
                  "chemical_dimerization",
                  "allosteric_switching",
                  "antigen_recognition",
                  "proteolytic_cleavage",
                  "base_editing",
                  "prime_editing",
                  "transposition",
                  "site_specific_recombination",
                  "rna_interference",
                  "aptamer_binding",
                ],
              },
              description:
                "Filter by biophysical mechanism. Match is OR across values.",
            },
            technique: {
              type: "array",
              items: {
                type: "string",
                enum: [
                  "computational_design",
                  "selection_enrichment",
                  "directed_evolution",
                  "sequence_verification",
                  "functional_assay",
                  "structural_characterization",
                  "high_throughput_screening",
                  "deep_mutational_scanning",
                  "machine_learning_design",
                  "rational_mutagenesis",
                  "domain_shuffling",
                  "codon_optimization",
                  "display_selection",
                  "cell_free_evolution",
                ],
              },
              description:
                "Filter by engineering technique. Match is OR across values.",
            },
            family: {
              type: "array",
              items: { type: "string" },
              description:
                "Filter by tool family name (free-text, e.g. 'LOV', 'CRY2'). OR match.",
            },
            maturity_stage: {
              type: "array",
              items: {
                type: "string",
                enum: ["research", "preclinical", "clinical", "deployed"],
              },
              description: "Filter by maturity stage. OR match.",
            },
            status: {
              type: "array",
              items: {
                type: "string",
                enum: ["seed", "normalized", "curated", "deprecated"],
              },
              description: "Filter by curation status. OR match.",
            },
            has_independent_replication: {
              type: "boolean",
              description:
                "If true, only items validated by an independent lab. If false, only items without.",
            },
            has_mouse_in_vivo_validation: {
              type: "boolean",
              description:
                "If true, only items with mouse in-vivo data. If false, only items without.",
            },
            has_therapeutic_use: {
              type: "boolean",
              description:
                "If true, only items with therapeutic-use evidence. If false, only items without.",
            },
            sort: {
              type: "string",
              enum: [
                "name",
                "evidence",
                "replication",
                "practicality",
                "year",
              ],
              default: "name",
              description: "Sort order for returned items.",
            },
            limit: {
              type: "integer",
              minimum: 1,
              maximum: 500,
              default: 20,
              description: "Page size.",
            },
            offset: {
              type: "integer",
              minimum: 0,
              default: 0,
              description: "Number of items to skip (for pagination).",
            },
          },
        },
        WorkflowFilters: {
          type: "object",
          description:
            "Structured filters for extracted workflows. All fields optional.",
          properties: {
            q: {
              type: "string",
              description:
                "Full-text search across objective, stages, steps, involved items, and source document.",
            },
            mechanism: {
              type: "array",
              items: { type: "string" },
              description:
                "Filter by target mechanism. Same enum as item mechanism filter.",
            },
            technique: {
              type: "array",
              items: { type: "string" },
              description:
                "Filter by target technique. Same enum as item technique filter.",
            },
            limit: {
              type: "integer",
              minimum: 1,
              maximum: 500,
              default: 20,
            },
            offset: {
              type: "integer",
              minimum: 0,
              default: 0,
            },
          },
        },
        QueryResponse: {
          type: "object",
          properties: {
            mode: {
              type: "string",
              enum: ["structured", "prompt"],
              description:
                "'structured' when no prompt was sent; 'prompt' when a natural-language prompt was included.",
            },
            prompt: {
              type: ["string", "null"],
              description: "Echo of the prompt, or null.",
            },
            interpretation: {
              oneOf: [
                { $ref: "#/components/schemas/PromptInterpretation" },
                { type: "null" },
              ],
              description:
                "Present only in prompt mode. Shows how the LLM parsed the question into filters.",
            },
            item_filters: {
              $ref: "#/components/schemas/ItemFilters",
              description: "Effective filters applied (merged prompt + explicit).",
            },
            workflow_filters: {
              $ref: "#/components/schemas/WorkflowFilters",
              description: "Effective workflow filters applied.",
            },
            items: {
              type: "array",
              items: { $ref: "#/components/schemas/ToolkitItem" },
              description: "Matching toolkit items for this page.",
            },
            workflows: {
              type: "array",
              items: {
                $ref: "#/components/schemas/ExtractedWorkflowSummary",
              },
              description: "Matching extracted workflows for this page.",
            },
            total_items: {
              type: "integer",
              description: "Total matching items before pagination.",
            },
            total_workflows: {
              type: "integer",
              description: "Total matching workflows before pagination.",
            },
            item_pagination: {
              type: ["object", "null"],
              properties: {
                limit: { type: "integer" },
                offset: { type: "integer" },
              },
            },
            workflow_pagination: {
              type: ["object", "null"],
              properties: {
                limit: { type: "integer" },
                offset: { type: "integer" },
              },
            },
          },
        },
        PromptInterpretation: {
          type: "object",
          properties: {
            item_filters: { $ref: "#/components/schemas/ItemFilters" },
            workflow_filters: {
              $ref: "#/components/schemas/WorkflowFilters",
            },
            include_items: { type: "boolean" },
            include_workflows: { type: "boolean" },
            ambiguity_notes: {
              type: "array",
              items: { type: "string" },
              description:
                "Notes about ambiguous parts of the prompt or fallback behavior.",
            },
            llm_used: {
              type: "boolean",
              description:
                "True if the LLM successfully parsed the prompt; false if it fell back to raw text search.",
            },
          },
        },
        ToolkitItem: {
          type: "object",
          description:
            "A biocontrol toolkit item with evidence summaries, scores, and citations.",
          properties: {
            id: { type: "string" },
            slug: {
              type: "string",
              description: "URL-safe identifier. Use for detail page links.",
            },
            canonical_name: { type: "string" },
            item_type: {
              type: "string",
              enum: [
                "protein_domain",
                "multi_component_switch",
                "rna_element",
                "construct_pattern",
                "engineering_method",
                "assay_method",
                "computation_method",
                "delivery_harness",
              ],
            },
            family: { type: ["string", "null"] },
            summary: {
              type: ["string", "null"],
              description: "One-paragraph plain-language description.",
            },
            status: {
              type: "string",
              enum: ["seed", "normalized", "curated", "deprecated"],
            },
            maturity_stage: {
              type: "string",
              enum: ["research", "preclinical", "clinical", "deployed"],
            },
            first_publication_year: { type: ["integer", "null"] },
            primary_input_modality: { type: ["string", "null"] },
            primary_output_modality: { type: ["string", "null"] },
            components: {
              type: "array",
              items: { type: "string" },
              description: "Sub-part names for multi-component tools.",
            },
            mechanisms: {
              type: "array",
              items: { type: "string" },
              description: "Biophysical mechanisms this tool uses.",
            },
            techniques: {
              type: "array",
              items: { type: "string" },
              description: "Engineering techniques applied to this tool.",
            },
            target_processes: {
              type: "array",
              items: { type: "string" },
              description:
                "Biological processes this tool targets (e.g. transcription, editing, signaling).",
            },
            synonyms: {
              type: "array",
              items: { type: "string" },
            },
            validation_rollup: {
              type: ["object", "null"],
              description:
                "Boolean summary of validation evidence across biological contexts.",
              properties: {
                has_cell_free_validation: { type: "boolean" },
                has_bacterial_validation: { type: "boolean" },
                has_mammalian_cell_validation: { type: "boolean" },
                has_mouse_in_vivo_validation: { type: "boolean" },
                has_human_clinical_validation: { type: "boolean" },
                has_therapeutic_use: { type: "boolean" },
                has_independent_replication: { type: "boolean" },
              },
            },
            replication_summary: {
              type: ["object", "null"],
              description:
                "Quantitative evidence and replication scores (0-1 scale). Higher is better.",
              properties: {
                score_version: { type: "string" },
                primary_paper_count: { type: "integer" },
                independent_primary_paper_count: { type: "integer" },
                distinct_last_author_clusters: { type: "integer" },
                distinct_institutions: { type: "integer" },
                distinct_biological_contexts: { type: "integer" },
                years_since_first_report: { type: ["integer", "null"] },
                downstream_application_count: { type: "integer" },
                orphan_tool_flag: { type: "boolean" },
                practicality_penalties: {
                  type: "array",
                  items: { type: "string" },
                },
                evidence_strength_score: {
                  type: ["number", "null"],
                  description: "0-1. Breadth and depth of published evidence.",
                },
                replication_score: {
                  type: ["number", "null"],
                  description: "0-1. Independent lab replication evidence.",
                },
                practicality_score: {
                  type: ["number", "null"],
                  description:
                    "0-1. Ease of adoption (delivery burden, cofactors, hardware).",
                },
                translatability_score: {
                  type: ["number", "null"],
                  description:
                    "0-1. Combined score reflecting translational readiness.",
                },
              },
            },
            citations: {
              type: "array",
              description: "Ranked citations with source documents.",
              items: {
                type: "object",
                properties: {
                  id: { type: "string" },
                  citation_role: {
                    type: "string",
                    enum: [
                      "foundational",
                      "best_review",
                      "independent_validation",
                      "benchmark",
                      "protocol",
                      "therapeutic",
                      "negative_result",
                      "structural",
                      "database_reference",
                    ],
                  },
                  importance_rank: { type: "integer" },
                  why_this_matters: { type: "string" },
                  document: {
                    $ref: "#/components/schemas/SourceDocument",
                  },
                },
              },
            },
            validations: {
              type: "array",
              description: "Individual validation observations with context.",
              items: {
                type: "object",
                properties: {
                  id: { type: "string" },
                  observation_type: { type: "string" },
                  biological_system_level: { type: "string" },
                  species: { type: ["string", "null"] },
                  cell_type: { type: ["string", "null"] },
                  delivery_mode: { type: ["string", "null"] },
                  success_outcome: {
                    type: "string",
                    enum: ["success", "mixed", "failed"],
                  },
                  assay_description: { type: ["string", "null"] },
                },
              },
            },
          },
        },
        SourceDocument: {
          type: "object",
          properties: {
            id: { type: "string" },
            source_type: { type: "string" },
            title: { type: "string" },
            doi: { type: ["string", "null"] },
            pmid: { type: ["string", "null"] },
            publication_year: { type: ["integer", "null"] },
            journal_or_source: { type: ["string", "null"] },
            is_retracted: { type: "boolean" },
          },
        },
        ExtractedWorkflowSummary: {
          type: "object",
          description:
            "A literature-extracted experimental workflow with stages, steps, and involved items.",
          properties: {
            workflow_id: { type: "string" },
            workflow_objective: { type: ["string", "null"] },
            protocol_family: { type: ["string", "null"] },
            engineered_system_family: { type: ["string", "null"] },
            target_mechanisms: {
              type: "array",
              items: { type: "string" },
            },
            target_techniques: {
              type: "array",
              items: { type: "string" },
            },
            why_workflow_works: { type: ["string", "null"] },
            evidence_text: { type: ["string", "null"] },
            source_document: {
              $ref: "#/components/schemas/SourceDocument",
            },
            stages: {
              type: "array",
              description: "High-level campaign stages (screening funnels, validation tiers).",
              items: {
                type: "object",
                properties: {
                  stage_name: { type: "string" },
                  stage_kind: { type: "string" },
                  stage_order: { type: "integer" },
                },
              },
            },
            steps: {
              type: "array",
              description: "Bench-level protocol steps.",
              items: {
                type: "object",
                properties: {
                  step_name: { type: "string" },
                  step_order: { type: "integer" },
                  step_type: { type: ["string", "null"] },
                  stage_name: { type: ["string", "null"] },
                  purpose: { type: ["string", "null"] },
                },
              },
            },
            involved_items: {
              type: "array",
              description: "Toolkit items referenced in this workflow.",
              items: {
                type: "object",
                properties: {
                  slug: { type: "string" },
                  canonical_name: { type: "string" },
                  display_name: { type: "string" },
                  item_slug: { type: ["string", "null"] },
                },
              },
            },
          },
        },
      },
    },
  });
}

export async function POST(request: Request) {
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

  let guardHeaders: Record<string, string> | undefined;

  if (prompt) {
    const guardResult = guardQueryRequest(request);
    if (!guardResult.ok) {
      return NextResponse.json(
        { error: guardResult.error },
        { status: guardResult.status ?? 400, headers: guardResult.headers },
      );
    }
    guardHeaders = guardResult.headers;
  }

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
    includeWorkflows ? getExtractedWorkflows() : Promise.resolve([]),
  ]);

  const itemResult = includeItems ? searchItems(items, itemFilters) : null;
  const workflowResult = includeWorkflows
    ? searchExtractedWorkflows(workflows, workflowFilters)
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
    { headers: guardHeaders },
  );
}
