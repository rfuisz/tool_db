import type {
  ToolkitItem,
  WorkflowTemplate,
  WorkflowStep,
  ItemCitation,
  CitationRole,
  ItemType,
  ItemStatus,
  MaturityStage,
  Modality,
  WorkflowFamily,
  WorkflowStepType,
} from "./types";

import seedBundle from "./seed-bundle.json";

// ── Seed-bundle shape types ──────────────────────────────────

interface SeedCitationCandidate {
  citation_role: string;
  label: string;
  status: string;
  url?: string;
}

interface SeedStepTemplate {
  step_name: string;
  step_type: string;
  duration_typical_hours: number;
  queue_time_typical_hours?: number;
  hands_on_hours: number;
  direct_cost_usd_typical: number;
  parallelizable: boolean;
  outsourced?: boolean;
}

interface SeedItemStructured {
  id: string;
  slug: string;
  canonical_name: string;
  item_type: string;
  status: string;
  maturity_stage: string;
  family?: string;
  summary?: string;
  primary_input_modality?: string;
  primary_output_modality?: string;
  synonyms?: string[];
  components?: string[];
  mechanisms?: string[];
  techniques?: string[];
  target_processes?: string[];
  citation_candidates?: SeedCitationCandidate[];
  validation_observations_seed?: unknown[];
  workflow_recommendations?: { workflow_slug: string; rationale: string }[];
  source_status?: {
    citation_backfill_required: boolean;
    validation_backfill_required: boolean;
    replication_backfill_required: boolean;
  };
}

interface SeedWorkflowStructured {
  id: string;
  slug: string;
  name: string;
  workflow_family: string;
  objective: string;
  throughput_class?: string;
  recommended_for?: string[];
  step_templates: SeedStepTemplate[];
  assumption_notes?: string[];
}

// ── Transform helpers ────────────────────────────────────────

function mapCitationCandidates(candidates: SeedCitationCandidate[]): ItemCitation[] {
  return candidates
    .filter((c) => c.status !== "needs_curation")
    .map((c, i) => ({
      id: `cit-${i}`,
      source_document_id: `doc-${i}`,
      citation_role: c.citation_role as CitationRole,
      importance_rank: i + 1,
      why_this_matters: c.label,
      document: {
        id: `doc-${i}`,
        source_type: c.citation_role === "database_reference" ? "database_entry" : "primary_paper",
        title: c.label,
        doi: null,
        pmid: null,
        publication_year: null,
        journal_or_source: c.url ?? null,
        is_retracted: false,
      },
    }));
}

function mapStepTemplates(steps: SeedStepTemplate[]): WorkflowStep[] {
  return steps.map((s, i) => ({
    id: `step-${i}`,
    step_name: s.step_name,
    step_type: s.step_type as WorkflowStepType,
    duration_typical_hours: s.duration_typical_hours,
    hands_on_hours: s.hands_on_hours,
    direct_cost_usd_typical: s.direct_cost_usd_typical,
    parallelizable: s.parallelizable,
    failure_probability: null,
    input_artifact: null,
    output_artifact: null,
  }));
}

function mapItem(raw: { slug: string; structured: SeedItemStructured }): ToolkitItem {
  const s = raw.structured;
  return {
    id: s.id,
    slug: s.slug,
    canonical_name: s.canonical_name,
    item_type: s.item_type as ItemType,
    family: s.family ?? null,
    summary: s.summary?.trim() ?? null,
    status: s.status as ItemStatus,
    maturity_stage: (s.maturity_stage ?? "research") as MaturityStage,
    first_publication_year: null,
    primary_input_modality: (s.primary_input_modality as Modality) ?? null,
    primary_output_modality: (s.primary_output_modality as Modality) ?? null,
    mechanisms: s.mechanisms ?? [],
    techniques: s.techniques ?? [],
    target_processes: s.target_processes ?? [],
    synonyms: s.synonyms ?? [],
    validation_rollup: null,
    replication_summary: null,
    citations: mapCitationCandidates(s.citation_candidates ?? []),
    validations: [],
  };
}

function mapWorkflow(raw: { slug: string; structured: SeedWorkflowStructured }): WorkflowTemplate {
  const s = raw.structured;
  return {
    id: s.id,
    slug: s.slug,
    name: s.name,
    workflow_family: s.workflow_family as WorkflowFamily,
    objective: s.objective,
    throughput_class: s.throughput_class ?? null,
    recommended_for: s.recommended_for?.join(", ") ?? null,
    steps: mapStepTemplates(s.step_templates),
  };
}

// ── Exported data ────────────────────────────────────────────

export const ITEMS: ToolkitItem[] = (seedBundle.items as { slug: string; structured: SeedItemStructured }[]).map(mapItem);

export const WORKFLOWS: WorkflowTemplate[] = (seedBundle.workflows as { slug: string; structured: SeedWorkflowStructured }[]).map(mapWorkflow);

// ── Query helpers ────────────────────────────────────────────

export function getItemBySlug(slug: string): ToolkitItem | undefined {
  return ITEMS.find((i) => i.slug === slug);
}

export function getItemsByType(itemType: string): ToolkitItem[] {
  return ITEMS.filter((i) => i.item_type === itemType);
}

export function getItemsByMechanism(mechanism: string): ToolkitItem[] {
  return ITEMS.filter((i) => i.mechanisms.includes(mechanism));
}

export function getItemsByTechnique(technique: string): ToolkitItem[] {
  return ITEMS.filter((i) => i.techniques.includes(technique));
}

export function getItemsByFamily(family: string): ToolkitItem[] {
  return ITEMS.filter((i) => i.family === family);
}

export function getAllFamilies(): string[] {
  const families = new Set(ITEMS.map((i) => i.family).filter(Boolean) as string[]);
  return Array.from(families).sort();
}

export function getAllMechanisms(): string[] {
  const mechanisms = new Set(ITEMS.flatMap((i) => i.mechanisms));
  return Array.from(mechanisms).sort();
}

export function getAllTechniques(): string[] {
  const techniques = new Set(ITEMS.flatMap((i) => i.techniques));
  return Array.from(techniques).sort();
}
