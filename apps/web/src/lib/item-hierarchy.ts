import {
  MECHANISM_DESCRIPTIONS,
  TECHNIQUE_DESCRIPTIONS,
} from "./explanations";
import type { ItemType, ToolkitItem } from "./types";
import {
  MECHANISM_LABELS,
  TECHNIQUE_LABELS,
  isSupportedTechnique,
} from "./vocabularies";

export type TaxonomyAxis = "mechanism" | "technique";
export type MechanismLayerId = "architecture" | "component";

export type ItemTypeTaxonomyPosition = {
  axis: TaxonomyAxis;
  axisTitle: string;
  layerTitle: string;
  title: string;
  description: string;
};

export type MechanismHierarchySection = {
  id: "mechanism" | MechanismLayerId;
  title: string;
  description: string;
  itemTypes?: ItemType[];
};

export type TechniqueHierarchySection = {
  id: "technique" | "method";
  title: string;
  description: string;
  itemTypes?: ItemType[];
};

export type MechanismConceptSummary = {
  key: string;
  label: string;
  description: string;
  summary: string;
  totalCount: number;
  architectureCount: number;
  componentCount: number;
  capabilities: string[];
  architectureItems: ToolkitItem[];
  componentItems: ToolkitItem[];
  componentNames: string[];
};

export type TechniqueConceptSummary = {
  key: string;
  label: string;
  description: string;
  summary: string;
  totalCount: number;
  methodCount: number;
  capabilities: string[];
  methodItems: ToolkitItem[];
};

export const MECHANISM_HIERARCHY_SECTIONS: MechanismHierarchySection[] = [
  {
    id: "mechanism",
    title: "Mechanisms",
    description:
      "Top-level concepts: biophysical action modes such as heterodimerization, photocleavage, or RNA binding.",
  },
  {
    id: "architecture",
    title: "Architectures",
    description:
      "Arrangements that realize or deploy mechanisms, including switches, construct patterns, and delivery strategies.",
    itemTypes: ["multi_component_switch", "construct_pattern", "delivery_harness"],
  },
  {
    id: "component",
    title: "Components",
    description:
      "Low-level parts and sequence-defined elements used inside architectures, including protein domains and RNA elements.",
    itemTypes: ["protein_domain", "rna_element"],
  },
];

export const TECHNIQUE_HIERARCHY_SECTIONS: TechniqueHierarchySection[] = [
  {
    id: "technique",
    title: "Approaches",
    description:
      "High-level engineering practices such as computational design, directed evolution, sequence verification, and functional assay.",
  },
  {
    id: "method",
    title: "Methods",
    description:
      "Concrete methods used to design, build, verify, or characterize engineered systems.",
    itemTypes: [
      "engineering_method",
      "computation_method",
      "assay_method",
    ],
  },
];

const ITEM_TYPE_ORDER: Record<ItemType, number> = {
  protein_domain: 0,
  rna_element: 1,
  multi_component_switch: 2,
  construct_pattern: 3,
  delivery_harness: 4,
  engineering_method: 5,
  computation_method: 6,
  assay_method: 7,
};

const ITEM_TYPE_TAXONOMY: Record<ItemType, ItemTypeTaxonomyPosition> = {
  protein_domain: {
    axis: "mechanism",
    axisTitle: "Mechanism Branch",
    layerTitle: "Component",
    title: "Component",
    description:
      "A low-level protein part used inside a larger architecture that realizes a mechanism.",
  },
  rna_element: {
    axis: "mechanism",
    axisTitle: "Mechanism Branch",
    layerTitle: "Component",
    title: "Component",
    description:
      "A low-level RNA part used inside a larger architecture that realizes a mechanism.",
  },
  multi_component_switch: {
    axis: "mechanism",
    axisTitle: "Mechanism Branch",
    layerTitle: "Architecture",
    title: "Architecture",
    description:
      "A composed arrangement of multiple parts that instantiates one or more mechanisms.",
  },
  construct_pattern: {
    axis: "mechanism",
    axisTitle: "Mechanism Branch",
    layerTitle: "Architecture",
    title: "Architecture",
    description:
      "A reusable architecture pattern for arranging parts into an engineered system.",
  },
  delivery_harness: {
    axis: "mechanism",
    axisTitle: "Mechanism Branch",
    layerTitle: "Architecture",
    title: "Architecture",
    description:
      "A delivery strategy grouped with the mechanism branch because it determines how a system is instantiated and deployed in context.",
  },
  engineering_method: {
    axis: "technique",
    axisTitle: "Technique Branch",
    layerTitle: "Method",
    title: "Method",
    description:
      "A concrete method used to build, optimize, or evolve an engineered system.",
  },
  computation_method: {
    axis: "technique",
    axisTitle: "Technique Branch",
    layerTitle: "Method",
    title: "Method",
    description:
      "A concrete computational method used to design, rank, or analyze an engineered system.",
  },
  assay_method: {
    axis: "technique",
    axisTitle: "Technique Branch",
    layerTitle: "Method",
    title: "Method",
    description:
      "A concrete measurement method used to characterize an engineered system.",
  },
};

export const ARCHITECTURE_ITEM_TYPES: ItemType[] = [
  "multi_component_switch",
  "construct_pattern",
  "delivery_harness",
];

export const COMPONENT_ITEM_TYPES: ItemType[] = ["protein_domain", "rna_element"];

export const METHOD_ITEM_TYPES: ItemType[] = [
  "engineering_method",
  "computation_method",
  "assay_method",
];

const MECHANISM_SIGNAL_MAP: Record<string, string[]> = {
  heterodimerization: ["heterodimer", "dimer", "binding partner", "bind sspb"],
  oligomerization: ["oligomer", "multimer", "cluster"],
  conformational_uncaging: [
    "conformational",
    "allosteric",
    "undock",
    "sterically blocked",
    "uncag",
  ],
  membrane_recruitment: [
    "membrane recruitment",
    "membrane-localized",
    "subcellular localization",
  ],
  photocleavage: ["photocleavage", "cleav"],
  dna_binding: ["dna binding", "bind dna"],
  rna_binding: ["rna binding", "bind rna", "riboswitch", "aptamer"],
  degradation: ["degradation", "degrade", "proteolysis"],
  translation_control: ["translation", "translational"],
};

const TECHNIQUE_SIGNAL_MAP: Record<string, string[]> = {
  computational_design: [
    "computational design",
    "protein design",
    "in silico",
    "algorithm",
    "model",
  ],
  selection_enrichment: [
    "selection",
    "enrichment",
    "phage display",
    "screen",
  ],
  directed_evolution: ["directed evolution", "evolution"],
  sequence_verification: ["sequence verification", "sequencing", "sanger"],
  functional_assay: ["assay", "screen", "readout", "measurement"],
  structural_characterization: [
    "crystal structure",
    "structural",
    "x-ray",
    "cryo-em",
    "nmr",
  ],
};

export function getItemTaxonomyPosition(
  itemType: ItemType,
): ItemTypeTaxonomyPosition {
  return ITEM_TYPE_TAXONOMY[itemType];
}

export function getOrderedItemTypes(itemTypes: ItemType[]): ItemType[] {
  return [...itemTypes].sort(
    (left, right) => ITEM_TYPE_ORDER[left] - ITEM_TYPE_ORDER[right],
  );
}

export function getItemTypeCount(items: ToolkitItem[], itemType: ItemType): number {
  return items.filter((item) => item.item_type === itemType).length;
}

function getItemText(item: ToolkitItem): string {
  return [
    item.canonical_name,
    item.summary ?? "",
    ...item.synonyms,
    ...(item.components ?? []),
    ...item.mechanisms,
    ...item.techniques,
    ...item.target_processes,
  ]
    .join(" ")
    .toLowerCase();
}

function formatFallbackLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function joinNaturalLanguage(values: string[]): string {
  if (values.length === 0) {
    return "";
  }
  if (values.length === 1) {
    return values[0];
  }
  if (values.length === 2) {
    return `${values[0]} and ${values[1]}`;
  }
  return `${values.slice(0, -1).join(", ")}, and ${values[values.length - 1]}`;
}

function buildItemLookup(items: ToolkitItem[]): Map<string, ToolkitItem> {
  const lookup = new Map<string, ToolkitItem>();
  for (const item of items) {
    lookup.set(item.slug.toLowerCase(), item);
    lookup.set(item.canonical_name.toLowerCase(), item);
    for (const synonym of item.synonyms) {
      lookup.set(synonym.toLowerCase(), item);
    }
  }
  return lookup;
}

function buildComponentParentMap(items: ToolkitItem[]): Map<string, ToolkitItem[]> {
  const lookup = buildItemLookup(items);
  const parentsByComponentSlug = new Map<string, ToolkitItem[]>();

  for (const item of items) {
    if (!ARCHITECTURE_ITEM_TYPES.includes(item.item_type)) {
      continue;
    }
    for (const componentName of item.components ?? []) {
      const component = lookup.get(componentName.toLowerCase());
      if (!component) {
        continue;
      }
      const existing = parentsByComponentSlug.get(component.slug) ?? [];
      if (!existing.some((candidate) => candidate.slug === item.slug)) {
        existing.push(item);
      }
      parentsByComponentSlug.set(component.slug, existing);
    }
  }

  return parentsByComponentSlug;
}

function collectSignalMatches(
  text: string,
  signalMap: Record<string, string[]>,
): string[] {
  return Object.entries(signalMap)
    .filter(([, signals]) => signals.some((signal) => text.includes(signal)))
    .map(([label]) => label);
}

function getMechanismAssignments(
  item: ToolkitItem,
  parentsByComponentSlug: Map<string, ToolkitItem[]>,
): string[] {
  const assignments = new Set(item.mechanisms);
  const text = getItemText(item);

  for (const match of collectSignalMatches(text, MECHANISM_SIGNAL_MAP)) {
    assignments.add(match);
  }

  for (const parent of parentsByComponentSlug.get(item.slug) ?? []) {
    for (const mechanism of parent.mechanisms) {
      assignments.add(mechanism);
    }
  }

  return [...assignments].sort();
}

function getTechniqueAssignments(item: ToolkitItem): string[] {
  const assignments = new Set(
    item.techniques.filter((technique) => isSupportedTechnique(technique)),
  );
  const text = getItemText(item);

  for (const match of collectSignalMatches(text, TECHNIQUE_SIGNAL_MAP)) {
    assignments.add(match);
  }

  if (item.item_type === "computation_method") {
    assignments.add("computational_design");
  }
  if (item.item_type === "assay_method") {
    assignments.add("functional_assay");
  }

  return [...assignments]
    .filter((technique) => isSupportedTechnique(technique))
    .sort();
}

function collectCapabilityLabels(items: ToolkitItem[]): string[] {
  const counts = new Map<string, number>();
  for (const item of items) {
    for (const targetProcess of item.target_processes) {
      counts.set(targetProcess, (counts.get(targetProcess) ?? 0) + 1);
    }
  }

  return [...counts.entries()]
    .sort((left, right) => {
      if (right[1] !== left[1]) {
        return right[1] - left[1];
      }
      return left[0].localeCompare(right[0]);
    })
    .slice(0, 3)
    .map(([value]) => formatFallbackLabel(value));
}

function getSortedItems(items: ToolkitItem[]): ToolkitItem[] {
  return [...items].sort((left, right) =>
    left.canonical_name.localeCompare(right.canonical_name),
  );
}

function buildMechanismSummary(
  description: string,
  architectureItems: ToolkitItem[],
  componentItems: ToolkitItem[],
  capabilities: string[],
  componentNames: string[],
): string {
  const parts = [description];

  if (architectureItems.length > 0 || componentItems.length > 0) {
    parts.push(
      `Current coverage includes ${architectureItems.length} architecture${
        architectureItems.length === 1 ? "" : "s"
      } and ${componentItems.length} component${
        componentItems.length === 1 ? "" : "s"
      }.`,
    );
  }

  if (capabilities.length > 0) {
    parts.push(
      `Across those tools, the main enabled capabilities are ${joinNaturalLanguage(capabilities)}.`,
    );
  }

  if (componentNames.length > 0) {
    parts.push(
      `Representative components include ${joinNaturalLanguage(componentNames.slice(0, 3))}.`,
    );
  }

  return parts.join(" ");
}

function buildTechniqueSummary(
  description: string,
  methodItems: ToolkitItem[],
  capabilities: string[],
): string {
  const parts = [description];

  if (methodItems.length > 0) {
    parts.push(
      `Current coverage includes ${methodItems.length} concrete method${
        methodItems.length === 1 ? "" : "s"
      }.`,
    );
  }

  if (capabilities.length > 0) {
    parts.push(
      `These methods are most often used to support ${joinNaturalLanguage(capabilities)} work.`,
    );
  }

  return parts.join(" ");
}

export function buildMechanismConceptSummaries(
  items: ToolkitItem[],
): MechanismConceptSummary[] {
  const parentsByComponentSlug = buildComponentParentMap(items);
  const grouped = new Map<
    string,
    { architectureItems: ToolkitItem[]; componentItems: ToolkitItem[]; componentNames: Set<string> }
  >();

  for (const item of items) {
    if (getItemTaxonomyPosition(item.item_type).axis !== "mechanism") {
      continue;
    }

    const mechanisms = getMechanismAssignments(item, parentsByComponentSlug);
    for (const mechanism of mechanisms) {
      const bucket = grouped.get(mechanism) ?? {
        architectureItems: [],
        componentItems: [],
        componentNames: new Set<string>(),
      };
      if (ARCHITECTURE_ITEM_TYPES.includes(item.item_type)) {
        if (!bucket.architectureItems.some((candidate) => candidate.slug === item.slug)) {
          bucket.architectureItems.push(item);
        }
        for (const componentName of item.components ?? []) {
          bucket.componentNames.add(componentName);
        }
      }
      if (COMPONENT_ITEM_TYPES.includes(item.item_type)) {
        if (!bucket.componentItems.some((candidate) => candidate.slug === item.slug)) {
          bucket.componentItems.push(item);
        }
        bucket.componentNames.add(item.canonical_name);
      }
      grouped.set(mechanism, bucket);
    }
  }

  return [...grouped.entries()]
    .map(([mechanism, bucket]) => {
      const architectureItems = getSortedItems(bucket.architectureItems);
      const componentItems = getSortedItems(bucket.componentItems);
      const allItems = [...architectureItems, ...componentItems];
      const capabilities = collectCapabilityLabels(allItems);
      const description =
        MECHANISM_DESCRIPTIONS[mechanism] ??
        "A mechanism-level grouping derived from the current toolkit evidence.";
      return {
        key: mechanism,
        label: MECHANISM_LABELS[mechanism] ?? formatFallbackLabel(mechanism),
        description,
        summary: buildMechanismSummary(
          description,
          architectureItems,
          componentItems,
          capabilities,
          [...bucket.componentNames].sort(),
        ),
        totalCount: allItems.length,
        architectureCount: architectureItems.length,
        componentCount: componentItems.length,
        capabilities,
        architectureItems,
        componentItems,
        componentNames: [...bucket.componentNames].sort(),
      };
    })
    .sort((left, right) => left.label.localeCompare(right.label));
}

export function buildTechniqueConceptSummaries(
  items: ToolkitItem[],
): TechniqueConceptSummary[] {
  const grouped = new Map<string, ToolkitItem[]>();

  for (const item of items) {
    if (!METHOD_ITEM_TYPES.includes(item.item_type)) {
      continue;
    }
    for (const technique of getTechniqueAssignments(item)) {
      const bucket = grouped.get(technique) ?? [];
      if (!bucket.some((candidate) => candidate.slug === item.slug)) {
        bucket.push(item);
      }
      grouped.set(technique, bucket);
    }
  }

  return [...grouped.entries()]
    .map(([technique, methodItems]) => {
      const sortedMethodItems = getSortedItems(methodItems);
      const capabilities = collectCapabilityLabels(sortedMethodItems);
      const description =
        TECHNIQUE_DESCRIPTIONS[technique] ??
        "A technique-level grouping derived from the current toolkit evidence.";
      return {
        key: technique,
        label: TECHNIQUE_LABELS[technique] ?? formatFallbackLabel(technique),
        description,
        summary: buildTechniqueSummary(description, sortedMethodItems, capabilities),
        totalCount: sortedMethodItems.length,
        methodCount: sortedMethodItems.length,
        capabilities,
        methodItems: sortedMethodItems,
      };
    })
    .sort((left, right) => left.label.localeCompare(right.label));
}

export function buildItemHierarchyAssignments(items: ToolkitItem[]): {
  mechanismsBySlug: Map<string, string[]>;
  techniquesBySlug: Map<string, string[]>;
} {
  const parentsByComponentSlug = buildComponentParentMap(items);
  return {
    mechanismsBySlug: new Map(
      items.map((item) => [item.slug, getMechanismAssignments(item, parentsByComponentSlug)]),
    ),
    techniquesBySlug: new Map(
      items.map((item) => [item.slug, getTechniqueAssignments(item)]),
    ),
  };
}

export function getMechanismConceptSummary(
  items: ToolkitItem[],
  slug: string,
): MechanismConceptSummary | undefined {
  return buildMechanismConceptSummaries(items).find((concept) => concept.key === slug);
}

export function getTechniqueConceptSummary(
  items: ToolkitItem[],
  slug: string,
): TechniqueConceptSummary | undefined {
  return buildTechniqueConceptSummaries(items).find((concept) => concept.key === slug);
}
