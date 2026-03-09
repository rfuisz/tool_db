import type { ToolkitItem } from "./types";
import { buildItemHierarchyAssignments } from "./item-hierarchy";
import { isSupportedTechnique } from "./vocabularies";

export function getAllFamilies(items: ToolkitItem[]): string[] {
  const families = new Set(
    items.map((item) => item.family).filter(Boolean) as string[],
  );
  return Array.from(families).sort();
}

export function getAllMechanisms(items: ToolkitItem[]): string[] {
  const hierarchyAssignments = buildItemHierarchyAssignments(items);
  const mechanisms = new Set(
    items.flatMap(
      (item) => hierarchyAssignments.mechanismsBySlug.get(item.slug) ?? item.mechanisms,
    ),
  );
  return Array.from(mechanisms).sort();
}

export function getAllTechniques(items: ToolkitItem[]): string[] {
  const hierarchyAssignments = buildItemHierarchyAssignments(items);
  const techniques = new Set(
    items
      .flatMap(
        (item) =>
          hierarchyAssignments.techniquesBySlug.get(item.slug) ?? item.techniques,
      )
      .filter(isSupportedTechnique),
  );
  return Array.from(techniques).sort();
}
