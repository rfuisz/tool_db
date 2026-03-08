import type { ItemType, BiologicalSystemLevel, CitationRole, MaturityStage, WorkflowFamily, Modality } from "./types";

export const ITEM_TYPE_LABELS: Record<ItemType, string> = {
  protein_domain: "Protein Domain",
  multi_component_switch: "Multi-Component Switch",
  rna_element: "RNA Element",
  construct_pattern: "Construct Pattern",
  engineering_method: "Engineering Method",
  assay_method: "Assay Method",
  computation_method: "Computation Method",
  delivery_harness: "Delivery Harness",
};

export const ITEM_TYPE_COLORS: Record<ItemType, string> = {
  protein_domain:          "bg-blue-50 text-blue-800",
  multi_component_switch:  "bg-violet-50 text-violet-800",
  rna_element:             "bg-emerald-50 text-emerald-800",
  construct_pattern:       "bg-amber-50 text-amber-800",
  engineering_method:      "bg-rose-50 text-rose-800",
  assay_method:            "bg-cyan-50 text-cyan-800",
  computation_method:      "bg-orange-50 text-orange-800",
  delivery_harness:        "bg-teal-50 text-teal-800",
};

export const BIO_SYSTEM_LABELS: Record<BiologicalSystemLevel, string> = {
  cell_free: "Cell-free",
  bacteria: "Bacteria",
  yeast: "Yeast",
  mammalian_cell_line: "Mammalian Cell Line",
  primary_cells: "Primary Cells",
  organoid: "Organoid",
  mouse: "Mouse",
  large_animal: "Large Animal",
  human_clinical: "Human Clinical",
};

export const BIO_SYSTEM_ORDER: BiologicalSystemLevel[] = [
  "cell_free",
  "bacteria",
  "yeast",
  "mammalian_cell_line",
  "primary_cells",
  "organoid",
  "mouse",
  "large_animal",
  "human_clinical",
];

export const CITATION_ROLE_LABELS: Record<CitationRole, string> = {
  foundational: "Foundational",
  best_review: "Best Review",
  independent_validation: "Independent Validation",
  benchmark: "Benchmark",
  protocol: "Protocol",
  therapeutic: "Therapeutic",
  negative_result: "Negative Result",
  structural: "Structural",
  database_reference: "Database Reference",
};

export const MATURITY_LABELS: Record<MaturityStage, string> = {
  research: "Research",
  preclinical: "Preclinical",
  clinical: "Clinical",
  deployed: "Deployed",
};

export const MATURITY_COLORS: Record<MaturityStage, string> = {
  research:    "bg-surface-alt text-ink-secondary",
  preclinical: "bg-brand-light text-brand",
  clinical:    "bg-indigo-50 text-indigo-800",
  deployed:    "bg-valid-light text-valid",
};

export const WORKFLOW_FAMILY_LABELS: Record<WorkflowFamily, string> = {
  fast_screen: "Fast Screen",
  standard_construct: "Standard Construct",
  library_selection: "Library Selection",
  in_vivo_pilot: "In Vivo Pilot",
  custom: "Custom",
};

export const MODALITY_LABELS: Record<Modality, string> = {
  light: "Light",
  chemical: "Chemical",
  thermal: "Thermal",
  electrical: "Electrical",
  mechanical: "Mechanical",
  magnetic: "Magnetic",
  sequence: "Sequence",
  structure: "Structure",
  conformational_change: "Conformational Change",
  transcription: "Transcription",
  translation: "Translation",
  localization: "Localization",
  degradation: "Degradation",
  signaling: "Signaling",
  editing: "Editing",
  selection: "Selection",
  assay_readout: "Assay Readout",
  analysis: "Analysis",
};

export const MECHANISM_FAMILIES = [
  "heterodimerization",
  "oligomerization",
  "conformational_uncaging",
  "membrane_recruitment",
  "photocleavage",
  "dna_binding",
  "rna_binding",
  "degradation",
  "translation_control",
] as const;

export const MECHANISM_LABELS: Record<string, string> = {
  heterodimerization: "Heterodimerization",
  oligomerization: "Oligomerization",
  conformational_uncaging: "Conformational Uncaging",
  membrane_recruitment: "Membrane Recruitment",
  photocleavage: "Photocleavage",
  dna_binding: "DNA Binding",
  rna_binding: "RNA Binding",
  degradation: "Degradation",
  translation_control: "Translation Control",
};

export const TECHNIQUE_FAMILIES = [
  "computational_design",
  "selection_enrichment",
  "directed_evolution",
  "sequence_verification",
  "functional_assay",
  "structural_characterization",
  "delivery_optimization",
] as const;

export const TECHNIQUE_LABELS: Record<string, string> = {
  computational_design: "Computational Design",
  selection_enrichment: "Selection / Enrichment",
  directed_evolution: "Directed Evolution",
  sequence_verification: "Sequence Verification",
  functional_assay: "Functional Assay",
  structural_characterization: "Structural Characterization",
  delivery_optimization: "Delivery Optimization",
};
