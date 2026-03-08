import type { ToolkitItem, WorkflowTemplate } from "./types";

import {
  ITEMS as EXPANDED_ITEMS,
  WORKFLOWS as EXPANDED_WORKFLOWS,
} from "./mock-data-expanded";

// ── Exported data ────────────────────────────────────────────

export const ITEMS: ToolkitItem[] = EXPANDED_ITEMS;

export const WORKFLOWS: WorkflowTemplate[] = EXPANDED_WORKFLOWS;

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
  const families = new Set(
    ITEMS.map((i) => i.family).filter(Boolean) as string[],
  );
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
