"""Broad discovery query sets for scaling the toolkit beyond the original optogenetics seed.

Strategy:
- Start from high-citation review papers in each domain (they catalog dozens of tools each)
- Branch out with domain-specific primary queries
- Each topic area is independent so the caller can select subsets
- All queries are designed to surface *engineered tools/systems*, not raw biology

I/O note: Always parallelise calls to literature APIs. OpenAlex has low RPM so
use its semaphore; OpenAI/Europe PMC can handle high concurrency.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Review-paper queries (high yield: each review names 10-50 tools)
# ---------------------------------------------------------------------------

REVIEW_QUERIES: List[str] = [
    # Optogenetics - broader than seed
    "optogenetic tools review",
    "optogenetic systems for gene expression review",
    "light-inducible protein systems review",
    "photoswitchable proteins review",
    "optogenetic actuators review",
    "LOV domain engineering review",
    "phytochrome-based optogenetics review",
    "BLUF domain optogenetics review",
    "cryptochrome optogenetics review",
    "optogenetics in mammalian cells review",
    "optogenetic gene circuits review",

    # Ultrasound neuromodulation & sonogenetics
    "focused ultrasound neuromodulation review",
    "sonogenetics review",
    "ultrasound-responsive tools review",
    "mechanosensitive channels ultrasound review",
    "focused ultrasound gene delivery review",
    "ultrasound-triggered drug release review",
    "acoustic reporter genes review",
    "gas vesicle ultrasound imaging review",

    # Chemogenetics / DREADDs
    "chemogenetic tools review",
    "DREADD designer receptors review",
    "chemogenetic actuators review",
    "chemical-genetic switches review",
    "small molecule inducible systems review",
    "ligand-inducible gene expression review",
    "rapamycin inducible dimerization review",
    "abscisic acid inducible systems review",
    "auxin-inducible degron review",
    "chemical inducers of dimerization review",

    # Cell therapy engineering
    "CAR-T cell engineering tools review",
    "synthetic receptors cell therapy review",
    "synNotch receptor engineering review",
    "logic-gated cell therapy review",
    "safety switches cell therapy review",
    "inducible kill switch cell therapy review",
    "armored CAR-T review",
    "universal CAR-T platform review",
    "synthetic biology cell therapy review",
    "chimeric antigen receptor design review",
    "TCR engineering review",
    "engineered T cell review",
    "allogeneic cell therapy engineering review",
    "iPSC-derived cell therapy tools review",
    "gene editing cell therapy review",

    # Synthetic biology tools broadly
    "synthetic gene circuits review",
    "genetic toggle switch review",
    "synthetic gene oscillator review",
    "riboswitch engineering review",
    "RNA-based genetic circuits review",
    "CRISPR-based gene regulation review",
    "CRISPRa CRISPRi tools review",
    "base editing tools review",
    "prime editing review",
    "epigenome editing tools review",
    "gene drive engineering review",
    "protein switches synthetic biology review",
    "split protein systems review",
    "inteins protein engineering review",
    "protein scaffolds synthetic biology review",
    "directed evolution tools review",
    "high-throughput screening synthetic biology review",
    "cell-free systems synthetic biology review",
    "minimal cell engineering review",
    "biosensor engineering review",
    "genetically encoded biosensors review",
    "genetically encoded indicators review",

    # Delivery & manufacturing
    "AAV engineering review",
    "lentiviral vector engineering review",
    "lipid nanoparticle mRNA delivery review",
    "non-viral gene delivery tools review",
    "electroporation gene delivery review",
    "exosome engineering delivery review",
    "virus-like particle engineering review",

    # Genome & transcriptome tools
    "programmable nucleases review",
    "zinc finger nuclease review",
    "TALEN engineering review",
    "Cas9 variants engineering review",
    "Cas12 Cas13 tools review",
    "RNA editing tools review",
    "anti-CRISPR proteins review",
    "transposon-based gene delivery review",
    "site-specific recombinases review",
    "Cre lox FLP engineering review",

    # Magnetogenetics & thermogenetics
    "magnetogenetics review",
    "magnetic nanoparticle cell control review",
    "thermogenetics review",
    "temperature-sensitive tools biology review",

    # Electrogenetics
    "electrogenetics review",
    "electrically inducible gene expression review",

    # Tissue engineering tools
    "organoid engineering tools review",
    "3D bioprinting tools review",
    "scaffold-free tissue engineering review",
    "microfluidics cell engineering review",
]

# ---------------------------------------------------------------------------
# Primary-paper topic queries (find specific tool papers)
# ---------------------------------------------------------------------------

OPTOGENETICS_QUERIES: List[str] = [
    "\"optogenetic tool\" characterization",
    "\"light-inducible\" protein engineering",
    "\"photoactivatable\" CRISPR",
    "\"optogenetic switch\" mammalian",
    "\"light-controlled\" transcription",
    "\"photoswitchable\" dimerizer",
    "\"LOV domain\" engineering",
    "\"light-oxygen-voltage\" tool",
    "\"CRY2\" \"CIB1\" optogenetic",
    "\"PhyB\" \"PIF\" optogenetic",
    "\"iLID\" \"SspB\" optogenetic",
    "\"Magnets\" optogenetic dimerizer",
    "\"BphP1\" optogenetic",
    "\"Dronpa\" optogenetic",
    "\"pdDronpa\" caging",
    "\"TULIP\" optogenetic",
    "\"opto-CRISPR\"",
    "\"light-inducible nuclear export\"",
    "\"optogenetic clustering\"",
    "\"CatchBond\" optogenetic",
    "\"photocleavable\" protein",
    "\"Kaede\" photoconversion tool",
    "\"EOS\" fluorescent protein photoconversion",
    "\"mMaple\" photoconversion",
    "\"miniSOG\" optogenetic",
    "\"FLARE\" optogenetic",
    "\"Cal-Light\" optogenetic",
    "optogenetic gene expression benchmark",
    "light-gated channel engineering",
    "channelrhodopsin engineering variant",
    "halorhodopsin engineering tool",
    "archaerhodopsin engineering tool",
    "opsin engineering variant characterization",
]

ULTRASOUND_QUERIES: List[str] = [
    "\"focused ultrasound\" tool",
    "\"sonogenetics\" engineered",
    "\"acoustic reporter\" gene",
    "\"gas vesicle\" engineered",
    "\"mechanosensitive\" channel ultrasound tool",
    "\"Piezo1\" ultrasound activation",
    "\"MscL\" ultrasound gate",
    "\"TRPV1\" ultrasound activation",
    "\"TRPA1\" ultrasound activation",
    "ultrasound-triggered gene expression",
    "sono-optogenetics",
    "\"ultrasound\" \"gene delivery\" tool",
    "\"focused ultrasound\" blood-brain barrier tool",
    "\"microbubble\" gene delivery",
    "\"acoustic\" droplet vaporization tool",
    "high-intensity focused ultrasound ablation tool",
]

CHEMOGENETICS_QUERIES: List[str] = [
    "DREADD hM3Dq hM4Di characterization",
    "\"designer receptor\" \"exclusively activated\"",
    "\"chemical genetic\" switch",
    "\"rapamycin\" dimerization system",
    "\"abscisic acid\" inducible system",
    "\"gibberellin\" inducible dimerization",
    "\"auxin-inducible degron\" AID tool",
    "\"Shield1\" destabilizing domain",
    "\"trimethoprim\" DHFR stabilization",
    "\"doxycycline\" inducible tet system",
    "\"cumate\" inducible system",
    "\"tamoxifen\" ERT2 inducible",
    "\"PSAM\" \"PSEM\" chemogenetic",
    "\"chemical inducer\" \"proximity\"",
    "\"bump-and-hole\" kinase tool",
    "\"HaloTag\" ligand tool",
    "\"SNAP-tag\" tool",
    "\"TMP-tag\" tool",
]

CELL_THERAPY_QUERIES: List[str] = [
    "\"CAR-T\" engineering tool",
    "\"synNotch\" synthetic receptor",
    "\"chimeric antigen receptor\" design variant",
    "\"logic gate\" CAR T cell",
    "\"safety switch\" cell therapy",
    "\"iCasp9\" kill switch",
    "\"EGFRt\" safety switch",
    "\"herpes simplex thymidine kinase\" kill switch",
    "\"universal CAR\" platform",
    "\"anti-HLA\" CAR",
    "\"TRAC\" disruption CAR",
    "\"armored\" CAR cytokine",
    "\"4-1BB\" \"CD28\" costimulatory domain",
    "\"TRuC\" T cell receptor fusion",
    "\"SUPRA CAR\" split",
    "\"GoCAR\" cell therapy",
    "\"on-switch CAR\"",
    "\"synthetic cytokine receptor\" cell therapy",
    "\"orthogonal IL-2\" cell therapy",
    "\"DARIC\" dimerizable CAR",
    "\"RevCAR\" switchable",
    "\"B2M\" knockout allogeneic",
    "\"base editing\" T cell",
    "\"multiplex CRISPR\" T cell",
]

SYNBIO_TOOLS_QUERIES: List[str] = [
    "\"genetic toggle switch\" synthetic",
    "\"repressilator\" synthetic circuit",
    "\"genetic oscillator\" engineered",
    "\"riboswitch\" engineered tool",
    "\"toehold switch\" RNA sensor",
    "\"STAR\" small transcription activating RNA",
    "\"CRISPRa\" tool characterization",
    "\"CRISPRi\" tool characterization",
    "\"dCas9\" activator repressor tool",
    "\"base editor\" \"ABE\" \"CBE\" tool",
    "\"prime editor\" tool",
    "\"epigenome editor\" tool",
    "\"split Cas9\" tool",
    "\"anti-CRISPR\" protein tool",
    "\"transposase\" engineering tool",
    "\"Sleeping Beauty\" transposon tool",
    "\"piggyBac\" transposon tool",
    "\"phiC31\" integrase tool",
    "\"Bxb1\" integrase tool",
    "\"Cre\" \"lox\" recombinase tool",
    "\"FLP\" \"FRT\" recombinase tool",
    "\"Dre\" \"rox\" recombinase tool",
    "\"zinc finger\" nuclease tool",
    "\"TALEN\" tool",
    "\"meganuclease\" engineering",
    "\"Cas12a\" \"Cas12b\" tool",
    "\"Cas13\" RNA tool",
    "\"CasRx\" RNA knockdown",
    "\"inteins\" split protein tool",
    "\"SpyTag\" \"SpyCatcher\" protein tool",
    "\"SnoopTag\" \"SnoopCatcher\" tool",
    "\"protein scaffold\" synthetic biology",
    "\"degron\" engineered tool",
    "\"nanobody\" intracellular tool",
    "\"DARPin\" engineered tool",
    "\"affibody\" engineered tool",
    "\"genetically encoded\" calcium indicator",
    "\"genetically encoded\" voltage indicator",
    "\"genetically encoded\" biosensor",
    "\"GCaMP\" calcium indicator",
    "\"iGluSnFR\" glutamate sensor",
    "\"dLight\" dopamine sensor",
    "\"GRAB\" neurotransmitter sensor",
]

DELIVERY_QUERIES: List[str] = [
    "\"AAV\" serotype engineering",
    "\"AAV9\" \"AAV-PHP.eB\" delivery",
    "\"lentiviral\" vector engineering tool",
    "\"lipid nanoparticle\" mRNA tool",
    "\"ionizable lipid\" LNP tool",
    "\"electroporation\" gene delivery tool",
    "\"nucleofection\" tool",
    "\"exosome\" engineered delivery",
    "\"virus-like particle\" delivery tool",
    "\"cell-penetrating peptide\" delivery",
    "\"nanoparticle\" gene delivery tool",
    "\"polymer\" gene delivery tool",
    "\"mRNA\" delivery tool engineering",
    "\"self-amplifying RNA\" tool",
    "\"circular RNA\" tool",
    "\"ribonucleoprotein\" delivery CRISPR",
]

MAGNETOGENETICS_THERMO_ELECTRO_QUERIES: List[str] = [
    "\"magnetogenetics\" tool",
    "\"magnetic nanoparticle\" cell activation",
    "\"ferritin\" magnetogenetics",
    "\"TRPV1\" magnetic activation",
    "\"magneto\" channel tool",
    "\"thermogenetics\" tool",
    "\"temperature-sensitive\" mutant tool",
    "\"TRPV1\" thermal activation tool",
    "\"electrogenetics\" tool",
    "\"electrically inducible\" gene expression",
    "\"DART\" electrically actuated tool",
    "\"redox\" responsive genetic tool",
]


def get_all_discovery_queries() -> Dict[str, List[str]]:
    """Return all query sets keyed by topic."""
    return {
        "reviews": REVIEW_QUERIES,
        "optogenetics": OPTOGENETICS_QUERIES,
        "ultrasound": ULTRASOUND_QUERIES,
        "chemogenetics": CHEMOGENETICS_QUERIES,
        "cell_therapy": CELL_THERAPY_QUERIES,
        "synbio_tools": SYNBIO_TOOLS_QUERIES,
        "delivery": DELIVERY_QUERIES,
        "magneto_thermo_electro": MAGNETOGENETICS_THERMO_ELECTRO_QUERIES,
    }


def get_flat_query_list(topics: Optional[List[str]] = None) -> List[str]:
    """Return a deduplicated flat list of queries, optionally filtered by topic."""
    all_sets = get_all_discovery_queries()
    if topics:
        selected = {k: v for k, v in all_sets.items() if k in topics}
    else:
        selected = all_sets
    seen: set = set()
    out: List[str] = []
    for queries in selected.values():
        for q in queries:
            q_lower = q.strip().lower()
            if q_lower not in seen:
                seen.add(q_lower)
                out.append(q)
    return out


def get_review_filter_expr() -> str:
    """OpenAlex filter expression to restrict to review articles."""
    return "type:review"
