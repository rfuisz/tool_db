import type { ToolkitItem } from "./types";

export function getAllFamilies(items: ToolkitItem[]): string[] {
  const families = new Set(
    items.map((item) => item.family).filter(Boolean) as string[],
  );
  return Array.from(families).sort();
}

export function getAllMechanisms(items: ToolkitItem[]): string[] {
  const mechanisms = new Set(items.flatMap((item) => item.mechanisms));
  return Array.from(mechanisms).sort();
}

export function getAllTechniques(items: ToolkitItem[]): string[] {
  const techniques = new Set(items.flatMap((item) => item.techniques));
  return Array.from(techniques).sort();
}
