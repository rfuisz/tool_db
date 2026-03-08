// AUTO-GENERATED from schemas/canonical/controlled_vocabularies.v2.json
// Do not edit by hand — run: npm run generate:explanations

export const ITEM_TYPE_DESCRIPTIONS: Record<string, string> = {
  "protein_domain": "A single protein domain or engineered variant used as a modular building block in synthetic biology constructs.",
  "multi_component_switch": "A system requiring two or more interacting molecular components to achieve stimulus-responsive behavior.",
  "rna_element": "An RNA-based regulatory element such as a riboswitch, aptamer, or ribozyme used to control gene expression.",
  "construct_pattern": "A reusable genetic architecture or design pattern for assembling functional circuits from parts.",
  "engineering_method": "A laboratory method for creating, modifying, or optimizing biological parts (e.g. directed evolution, computational design).",
  "assay_method": "A measurement technique for characterizing the performance of engineered biological parts.",
  "computation_method": "A computational tool or algorithm for predicting, designing, or analyzing biological constructs.",
  "delivery_harness": "A vehicle or strategy for delivering engineered constructs into target cells or tissues (e.g. AAV, LNP, electroporation).",
};

export const STATUS_DESCRIPTIONS: Record<string, string> = {
  "seed": "Initial dossier created from known references. Citations, validation data, and scores are placeholders awaiting source-backed curation.",
  "normalized": "Data ingested and normalized from external sources, but not yet reviewed by a human curator.",
  "curated": "Fully reviewed: citations verified, validation observations confirmed, scores computed from evidence.",
  "deprecated": "No longer recommended: superseded by a better tool, retracted, or found to be unreliable.",
};

export const MATURITY_DESCRIPTIONS: Record<string, string> = {
  "research": "Early-stage: demonstrated in academic research settings only.",
  "preclinical": "Validated in animal models or advanced in vitro systems with translational intent.",
  "clinical": "In human clinical trials or with clinical-grade manufacturing evidence.",
  "deployed": "Commercially available, FDA-approved, or in routine production use.",
};

export const SOURCE_TYPE_DESCRIPTIONS: Record<string, string> = {
  "review": "A review or meta-analysis that surveys the field rather than presenting original data.",
  "primary_paper": "An original research article presenting new experimental results.",
  "trial_record": "A clinical trial registration or results record (e.g. ClinicalTrials.gov).",
  "database_entry": "A structured record from a curated database (e.g. UniProt, Addgene, PDB).",
  "protocol": "A detailed laboratory protocol or methods paper.",
  "benchmark": "A systematic comparison study benchmarking multiple tools or methods.",
  "preprint": "A manuscript posted to a preprint server (e.g. bioRxiv) before peer review.",
};

export const CLAIM_POLARITY_DESCRIPTIONS: Record<string, string> = {
  "supports": "The evidence supports the claim or validates the tool's function as described.",
  "contradicts": "The evidence contradicts the claim—the tool did not perform as expected.",
  "mixed": "Results are ambiguous: partial support or context-dependent outcomes.",
  "neutral": "The source mentions the tool but does not provide evidence for or against.",
};

export const CITATION_ROLE_DESCRIPTIONS: Record<string, string> = {
  "foundational": "The original paper that first described or created this tool.",
  "best_review": "The most comprehensive review covering this tool's mechanism, applications, and limitations.",
  "independent_validation": "A study from an independent lab that reproduced or validated the tool's function.",
  "benchmark": "A head-to-head comparison of this tool against alternatives in the same category.",
  "protocol": "A detailed methods paper or protocol for using this tool in the lab.",
  "therapeutic": "Evidence of this tool's use in a therapeutic context: gene therapy, drug development, or clinical intervention.",
  "negative_result": "A study reporting failure, limitations, or unexpected problems with this tool.",
  "structural": "Structural biology data (crystal structure, cryo-EM) informing how this tool works at atomic resolution.",
  "database_reference": "A curated database record (e.g. Addgene plasmid, PDB entry) for this tool.",
};

export const BIO_SYSTEM_DESCRIPTIONS: Record<string, string> = {
  "cell_free": "Cell-free systems: purified protein, in vitro transcription/translation, or lysate-based assays.",
  "bacteria": "Bacterial hosts such as E. coli, demonstrating function in a prokaryotic context.",
  "yeast": "Yeast systems (S. cerevisiae, S. pombe), bridging prokaryotic simplicity and eukaryotic biology.",
  "mammalian_cell_line": "Immortalized mammalian cell lines (e.g. HEK293, HeLa, CHO) showing function in eukaryotic cells.",
  "primary_cells": "Primary cells isolated directly from tissue, providing more physiologically relevant context than cell lines.",
  "organoid": "3D organoid cultures that recapitulate tissue architecture and cell-type diversity.",
  "mouse": "Mouse models in vivo, demonstrating function in a living mammalian organism.",
  "large_animal": "Large animal models (e.g. non-human primate, pig) providing translational data closer to human physiology.",
  "human_clinical": "Human clinical trials or clinical-grade applications in patients.",
};

export const OBSERVATION_TYPE_DESCRIPTIONS: Record<string, string> = {
  "mechanistic_demo": "An experiment demonstrating the tool's core mechanism of action (e.g. light-induced dimerization confirmed by co-IP).",
  "application_demo": "A downstream application using this tool to achieve a biological goal (e.g. optogenetic gene activation in neurons).",
  "benchmark": "A quantitative comparison against alternative tools measuring the same output.",
  "therapeutic_use": "Use in a therapeutic or clinical context: gene therapy, drug development, or patient treatment.",
  "manufacturing_use": "Use in biomanufacturing, industrial fermentation, or production-scale applications.",
  "failed_attempt": "A documented failure: the tool did not work as expected in this context. Valuable negative data.",
};

export const SUCCESS_OUTCOME_DESCRIPTIONS: Record<string, string> = {
  "success": "The tool performed as expected with clear positive results.",
  "mixed": "Partial success: some metrics met expectations while others fell short, or results were context-dependent.",
  "failed": "The tool did not achieve the intended outcome in this experiment.",
};

export const WORKFLOW_FAMILY_DESCRIPTIONS: Record<string, string> = {
  "fast_screen": "A rapid workflow for testing a small number of candidates with minimal cloning (days to one week).",
  "standard_construct": "A typical construct-build-test cycle: design, clone, verify, express, assay (one to three weeks).",
  "library_selection": "A multi-round selection workflow starting from a molecular library (e.g. phage display, FACS sorting).",
  "in_vivo_pilot": "An in vivo experiment requiring packaging, delivery, and animal work (weeks to months).",
  "custom": "A user-defined workflow that does not fit standard templates.",
};

export const STEP_TYPE_DESCRIPTIONS: Record<string, string> = {
  "design": "Computational or manual design of the candidate sequence, construct, or library.",
  "dna_acquisition": "Ordering or synthesizing DNA: gene fragments, oligos, or full-length genes from a vendor.",
  "assembly": "Molecular cloning or assembly of DNA parts into a functional construct (e.g. Gibson, Golden Gate).",
  "transformation": "Introducing DNA into bacterial cells for amplification or screening.",
  "colony_screen": "Screening bacterial colonies to identify correct clones after transformation.",
  "sequence_verification": "Sanger or NGS sequencing to confirm the construct matches the intended design.",
  "transfection": "Introducing DNA/RNA into mammalian or eukaryotic cells for expression.",
  "expression": "Growing cells and expressing the construct to produce functional protein.",
  "selection_round": "One round of selection or enrichment from a molecular library (e.g. phage display, FACS).",
  "assay": "Functional measurement: fluorescence, binding, activity, or phenotypic readout.",
  "analysis": "Data analysis and interpretation of experimental results.",
  "decision": "Go/no-go decision point based on accumulated data.",
  "packaging": "Packaging DNA/RNA into delivery vehicles (e.g. AAV, LNP).",
  "delivery": "Delivering the packaged construct to target cells or tissues in vivo.",
};

export const METRIC_DESCRIPTIONS: Record<string, string> = {
  "fold_induction": "Ratio of output signal in the ON state vs OFF state. Higher is better.",
  "repression_efficiency": "Fraction of target expression that is silenced (0–1). Higher means more complete repression.",
  "dark_state_leak": "Residual activity in the OFF/unstimulated state. Lower is better for tight control.",
  "on_kinetics_minutes": "Time to reach half-maximal activation after stimulus onset. Faster enables tighter temporal control.",
  "off_kinetics_minutes": "Time to return to half-maximal after stimulus removal. Faster enables reversible control.",
  "affinity_kd": "Dissociation constant for the binding interaction. Lower Kd means tighter binding.",
  "viability_percent": "Percentage of cells surviving after tool expression or treatment. Higher is less toxic.",
  "toxicity_signal": "Qualitative or quantitative indicator of cytotoxicity from the tool or its stimulus.",
  "editing_efficiency_percent": "Fraction of target loci successfully edited. Higher means more on-target activity.",
  "localization_precision": "Spatial resolution of subcellular targeting (e.g. nuclear vs cytoplasmic enrichment ratio).",
  "signal_to_noise": "Ratio of specific signal to background noise. Higher indicates cleaner readout.",
  "tissue_penetration_compatibility": "Qualitative rating of whether the tool's stimulus can reach deep tissues in vivo.",
};

export const MECHANISM_DESCRIPTIONS: Record<string, string> = {
  "heterodimerization": "Two different proteins are brought together by a stimulus, enabling recruitment or complex formation.",
  "oligomerization": "A protein self-associates into multimers upon stimulation, enabling clustering or activation.",
  "conformational_uncaging": "A stimulus triggers a structural change that exposes a previously hidden functional element.",
  "membrane_recruitment": "A protein is recruited to a membrane surface (e.g. plasma membrane) by a stimulus.",
  "photocleavage": "Light breaks a covalent bond, irreversibly releasing a caged peptide or domain.",
  "dna_binding": "A protein binds DNA in a stimulus-dependent manner to regulate gene expression.",
  "rna_binding": "A protein or RNA element binds RNA to control translation or stability.",
  "degradation": "A stimulus triggers targeted degradation of a protein via the proteasome or other pathways.",
  "translation_control": "Post-transcriptional regulation of mRNA translation rate or efficiency.",
};

export const TECHNIQUE_DESCRIPTIONS: Record<string, string> = {
  "computational_design": "In silico design of protein sequences, structures, or circuits using algorithms or machine learning.",
  "selection_enrichment": "Experimental selection from a library to enrich for variants with desired properties.",
  "directed_evolution": "Iterative mutagenesis and selection to evolve improved biological parts.",
  "sequence_verification": "Confirming construct identity by Sanger or next-generation sequencing.",
  "functional_assay": "Measuring the activity or performance of an engineered part in a biological context.",
  "structural_characterization": "Determining 3D structure via X-ray crystallography, cryo-EM, or NMR.",
  "delivery_optimization": "Optimizing the vehicle, route, or formulation for delivering constructs to target cells or tissues.",
};

export const TARGET_PROCESS_DESCRIPTIONS: Record<string, string> = {
  "transcription": "Regulation of gene transcription (activation, repression, or modification of mRNA synthesis).",
  "translation": "Control of mRNA translation into protein.",
  "localization": "Control of subcellular localization (e.g. nuclear import/export, membrane targeting).",
  "degradation": "Targeted degradation of proteins or RNA molecules.",
  "signaling": "Activation or modulation of intracellular signaling pathways.",
  "editing": "Genome or epigenome editing at specific loci.",
  "selection": "Enrichment or screening of variants from a molecular library.",
  "manufacturing": "Biomanufacturing or industrial-scale production applications.",
  "diagnostic": "Diagnostic or biosensing applications for detecting analytes or biomarkers.",
};

export const MODALITY_DESCRIPTIONS: Record<string, string> = {
  "light": "Controlled by light wavelength and intensity (optogenetic).",
  "chemical": "Controlled by small molecules, drugs, or chemical inducers.",
  "thermal": "Controlled by temperature changes.",
  "electrical": "Controlled by electrical stimulation.",
  "mechanical": "Controlled by physical force or mechanical stress.",
  "magnetic": "Controlled by magnetic fields.",
  "sequence": "Takes a DNA/RNA/protein sequence as input.",
  "structure": "Takes a 3D molecular structure as input.",
  "conformational_change": "Produces a structural/conformational change in a protein or domain.",
  "transcription": "Activates or represses gene transcription.",
  "translation": "Controls mRNA translation into protein.",
  "localization": "Controls subcellular localization (e.g. nuclear, membrane, cytoplasmic).",
  "degradation": "Triggers targeted protein or RNA degradation.",
  "signaling": "Activates or modulates a cell signaling pathway.",
  "editing": "Performs genome or epigenome editing.",
  "selection": "Enriches or selects variants from a library.",
  "assay_readout": "Provides a measurable experimental readout.",
  "analysis": "Produces a computational analysis or prediction.",
};

export const SCORE_DESCRIPTIONS: Record<string, string> = {
  "evidence_strength_score": "Strength of the published evidence base: paper count, citation quality, and breadth of experimental support.",
  "replication_score": "Degree of independent reproduction: how many distinct labs, institutions, and biological contexts have confirmed the finding.",
  "practicality_score": "Ease of real-world use: accounts for known failure modes, setup complexity, cost, and documented pitfalls.",
  "translatability_score": "Path toward therapeutic or deployed use: regulatory precedent, in vivo data, clinical trials, and manufacturing readiness.",
};

export const VALIDATION_ROLLUP_DESCRIPTIONS: Record<string, string> = {
  "has_cell_free_validation": "At least one successful observation in a cell-free system.",
  "has_bacterial_validation": "At least one successful observation in bacterial hosts.",
  "has_mammalian_cell_validation": "At least one successful observation in mammalian cell lines.",
  "has_mouse_in_vivo_validation": "At least one successful observation in mouse models in vivo.",
  "has_human_clinical_validation": "Evidence from human clinical trials or clinical-grade applications.",
  "has_therapeutic_use": "Used in a therapeutic context: drug development, gene therapy, or clinical intervention.",
  "has_independent_replication": "Independently replicated by a lab unaffiliated with the original authors.",
};

export const PROBLEM_LINK_DESCRIPTIONS: Record<string, string> = {
  "mechanistic_match_score": "How well the tool's mechanism aligns with the problem's biological requirements.",
  "context_match_score": "Whether the tool has been validated in the relevant biological context (organism, cell type, tissue).",
  "throughput_match_score": "Whether the tool's throughput matches the scale needed for the problem.",
  "time_to_first_test_score": "Estimated calendar time from decision to first experimental result.",
  "cost_to_first_test_score": "Estimated direct cost (reagents + services) to reach first experimental result.",
  "replication_confidence_modifier": "Adjustment based on how well the tool has been independently replicated.",
  "practicality_modifier": "Adjustment for known failure modes, setup complexity, and documented pitfalls.",
  "translatability_modifier": "Adjustment for regulatory precedent, clinical data, and manufacturing readiness.",
  "overall_gap_applicability_score": "Composite score representing how well this tool fits the stated problem.",
};

