export const SCORE_EXPLANATIONS: Record<string, string> = {
  Evidence:
    "Strength of the published evidence base: paper count, citation quality, and breadth of experimental support.",
  Replication:
    "Degree of independent reproduction: how many distinct labs, institutions, and biological contexts have confirmed the finding.",
  Practicality:
    "Ease of real-world use: accounts for known failure modes, setup complexity, cost, and documented pitfalls.",
  Translatability:
    "Path toward therapeutic or deployed use: regulatory precedent, in vivo data, clinical trials, and manufacturing readiness.",
};

export const BIO_SYSTEM_EXPLANATIONS: Record<string, string> = {
  "Cell-free":
    "Validated in cell-free systems (purified protein, in vitro transcription/translation, lysate-based assays).",
  Bacteria:
    "Validated in bacterial hosts such as E. coli, demonstrating function in a prokaryotic context.",
  Mammalian:
    "Validated in mammalian cell lines (e.g. HEK293, HeLa, CHO), showing function in eukaryotic cells.",
  Mouse:
    "Validated in mouse models in vivo, demonstrating function in a living organism.",
  Human:
    "Evidence from human clinical trials or clinical-grade applications.",
  Therapeutic:
    "Used in a therapeutic context: drug development, gene therapy, or clinical intervention.",
  "Indep. Replication":
    "Independently replicated by a lab unaffiliated with the original authors.",
};

export const STEP_TYPE_EXPLANATIONS: Record<string, string> = {
  design: "Computational or manual design of the candidate sequence, construct, or library.",
  dna_acquisition: "Ordering or synthesizing DNA: gene fragments, oligos, or full-length genes from a vendor.",
  assembly: "Molecular cloning or assembly of DNA parts into a functional construct (e.g. Gibson, Golden Gate).",
  transformation: "Introducing DNA into bacterial cells for amplification or screening.",
  colony_screen: "Screening bacterial colonies to identify correct clones after transformation.",
  sequence_verification: "Sanger or NGS sequencing to confirm the construct matches the intended design.",
  transfection: "Introducing DNA/RNA into mammalian or eukaryotic cells for expression.",
  expression: "Growing cells and expressing the construct to produce functional protein.",
  selection_round: "One round of selection or enrichment from a molecular library (e.g. phage display, FACS).",
  assay: "Functional measurement: fluorescence, binding, activity, or phenotypic readout.",
  analysis: "Data analysis and interpretation of experimental results.",
  decision: "Go/no-go decision point based on accumulated data.",
  packaging: "Packaging DNA/RNA into delivery vehicles (e.g. AAV, LNP).",
  delivery: "Delivering the packaged construct to target cells or tissues in vivo.",
};

export const MATURITY_EXPLANATIONS: Record<string, string> = {
  Research: "Early-stage: demonstrated in academic research settings only.",
  Preclinical: "Validated in animal models or advanced in vitro systems with translational intent.",
  Clinical: "In human clinical trials or with clinical-grade manufacturing evidence.",
  Deployed: "Commercially available, FDA-approved, or in routine production use.",
};

export const STATUS_EXPLANATIONS: Record<string, string> = {
  seed: "Initial dossier structure created from known references. Citations, validation data, and scores are placeholders awaiting source-backed curation.",
  normalized: "Data has been ingested and normalized from external sources, but not yet reviewed by a human curator.",
  curated: "Fully reviewed: citations verified, validation observations confirmed, scores computed from evidence.",
  deprecated: "No longer recommended: superseded, retracted, or found to be unreliable.",
};

export const MODALITY_EXPLANATIONS: Record<string, string> = {
  light: "Controlled by light wavelength and intensity (optogenetic).",
  chemical: "Controlled by small molecules, drugs, or chemical inducers.",
  thermal: "Controlled by temperature changes.",
  electrical: "Controlled by electrical stimulation.",
  mechanical: "Controlled by physical force or mechanical stress.",
  magnetic: "Controlled by magnetic fields.",
  sequence: "Takes a DNA/RNA/protein sequence as input.",
  structure: "Takes a 3D molecular structure as input.",
  conformational_change: "Produces a structural/conformational change in a protein or domain.",
  transcription: "Activates or represses gene transcription.",
  translation: "Controls mRNA translation into protein.",
  localization: "Controls subcellular localization (e.g. nuclear, membrane, cytoplasmic).",
  degradation: "Triggers targeted protein or RNA degradation.",
  signaling: "Activates or modulates a cell signaling pathway.",
  editing: "Performs genome or epigenome editing.",
  selection: "Enriches or selects variants from a library.",
  assay_readout: "Provides a measurable experimental readout.",
  analysis: "Produces a computational analysis or prediction.",
};

export const MECHANISM_EXPLANATIONS: Record<string, string> = {
  heterodimerization: "Two different proteins are brought together by a stimulus, enabling recruitment or complex formation.",
  oligomerization: "A protein self-associates into multimers upon stimulation, enabling clustering or activation.",
  conformational_uncaging: "A stimulus triggers a structural change that exposes a previously hidden functional element.",
  membrane_recruitment: "A protein is recruited to a membrane surface (e.g. plasma membrane) by a stimulus.",
  photocleavage: "Light breaks a covalent bond, irreversibly releasing a caged peptide or domain.",
  dna_binding: "A protein binds DNA in a stimulus-dependent manner to regulate gene expression.",
  rna_binding: "A protein or RNA element binds RNA to control translation or stability.",
  degradation: "A stimulus triggers targeted degradation of a protein via the proteasome or other pathways.",
  translation_control: "Post-transcriptional regulation of mRNA translation rate or efficiency.",
};
