import type { WorkflowTemplate } from "./types";

type WorkflowExplainer = Pick<
  WorkflowTemplate,
  "simple_summary" | "how_to_implement" | "used_when" | "tradeoffs" | "citations"
>;

export const WORKFLOW_EXPLAINERS: Record<string, WorkflowExplainer> = {
  "3-hour-fast-screen": {
    simple_summary:
      "Use a transient reporter assay to rank a small set of variants before investing in slower build-and-verify work.",
    how_to_implement: [
      "Keep the construct set tightly matched so differences are more likely to reflect biology than plate layout or transfection drift.",
      "Define the readout and controls up front: baseline or dark condition, stimulated condition, and a viability or expression control.",
      "Treat the output as a triage gate. Advance only variants that show clear separation, acceptable leak, and workable expression in the same assay window.",
    ],
    used_when: [
      "You already have a short list of candidate designs and need a same-day or next-day ranking.",
      "The main question is relative switch performance, not long-term stability or delivery behavior.",
      "You want to discard weak variants before cloning, stable integration, or animal work.",
    ],
    tradeoffs: [
      "Fast, but sensitive to transfection variability and plate effects.",
      "Reporter assays are good ranking tools but can miss localization, payload-size, or longer-term toxicity problems.",
      "A hit in transient format still needs confirmation in the host context that matters downstream.",
    ],
    citations: [
      {
        title:
          "Kim TK, Eberwine JH. Mammalian cell transfection: the present and the future. Anal Bioanal Chem. 2010.",
        href: "https://doi.org/10.1007/s00216-010-3821-6",
        note: "Useful background on transient transfection choices and their practical constraints.",
      },
    ],
  },
  "standard-construct-build": {
    simple_summary:
      "Build one construct carefully, verify the sequence, and then test function in the host system you actually care about.",
    how_to_implement: [
      "Freeze the architecture first: domains, linkers, tags, and promoter or backbone choices should be explicit before ordering DNA.",
      "Use a cloning method matched to construct complexity, then sequence-verify the exact junctions before interpreting assay results.",
      "Run the first functional assay in the intended host context so expression, localization, and leak are measured together rather than inferred.",
    ],
    used_when: [
      "Fusion geometry, linker length, trafficking, or expression context are likely to matter.",
      "You need an interpretable baseline construct before scaling to libraries or animal studies.",
      "A false positive from a fast screen would be expensive, so sequence confirmation is worth the time.",
    ],
    tradeoffs: [
      "Higher confidence than a fast screen, but much slower because DNA acquisition and verification dominate the timeline.",
      "Better for host-context effects, but lower throughput and more hands-on work per design.",
      "You reduce interpretation errors from bad constructs, but you pay in turnaround time and sequencing cost.",
    ],
    citations: [
      {
        title:
          "Gibson DG et al. Enzymatic assembly of DNA molecules up to several hundred kilobases. Nat Methods. 2009.",
        href: "https://doi.org/10.1038/nmeth.1318",
        note: "Foundational reference for the assembly step that underlies many modern construct-build loops.",
      },
      {
        title:
          "Kim TK, Eberwine JH. Mammalian cell transfection: the present and the future. Anal Bioanal Chem. 2010.",
        href: "https://doi.org/10.1007/s00216-010-3821-6",
        note: "Covers practical tradeoffs once the verified construct moves into host-cell testing.",
      },
    ],
  },
  "library-selection-campaign": {
    simple_summary:
      "Generate a diverse library, apply a selection or screen that matches the desired function, then sequence what survives so you can decide what to carry forward.",
    how_to_implement: [
      "Define the enrichment objective before library design so diversity is placed where selection pressure can actually discriminate variants.",
      "Track library quality and coverage early; poor assembly or bottlenecked transformations can dominate the campaign more than the selection itself.",
      "Pair enrichment with sequencing and analysis, because selected pools are only useful if you can explain which variants rose and why.",
    ],
    used_when: [
      "Single-design iteration is too slow or too uninformed for the problem.",
      "You need to search large sequence space for affinity, switching behavior, or stability improvements.",
      "A meaningful selection or high-throughput screen exists for the phenotype you care about.",
    ],
    tradeoffs: [
      "Much broader search than one-by-one engineering, but setup cost and analysis burden are substantially higher.",
      "Selections give scale, but the enrichment signal can drift away from the real downstream phenotype if assay pressure is poorly chosen.",
      "Library campaigns are powerful only when coverage, bottlenecks, and sequencing interpretation are managed explicitly.",
    ],
    citations: [
      {
        title:
          "Packer MS, Liu DR. Methods for the directed evolution of proteins. Nat Rev Genet. 2015.",
        href: "https://doi.org/10.1038/nrg3927",
        note: "Clear review of diversification, screening or selection strategy, and throughput tradeoffs.",
      },
    ],
  },
  "mouse-pilot-delivery": {
    simple_summary:
      "Take a lead construct into a small animal study only after in vitro evidence is strong enough that the main questions are delivery, biodistribution, activity, and early safety.",
    how_to_implement: [
      "Lock the payload, vector format, route, dose range, and assay plan before packaging so the animal study answers a narrow decision question.",
      "Measure both activity and distribution; a weak signal can reflect poor delivery rather than a bad payload.",
      "Include early safety and tolerability readouts in the same pilot so the result is useful for the next go or no-go decision.",
    ],
    used_when: [
      "You already have convincing cell-based evidence and need an in vivo reality check.",
      "Route, biodistribution, and tissue exposure are major uncertainties.",
      "The next stage depends on whether the construct survives packaging and shows acceptable early safety.",
    ],
    tradeoffs: [
      "Highest relevance among these common workflows, but slowest and most expensive.",
      "Animal results are more decision-relevant than in vitro assays, but much harder to debug when performance is weak.",
      "Delivery, exposure, efficacy, and toxicity become coupled, so negative results are often less cleanly interpretable.",
    ],
    citations: [
      {
        title:
          "Hordeaux J et al. Considerations for Preclinical Safety Assessment of Adeno-Associated Virus Gene Therapy Products. Toxicol Pathol. 2018.",
        href: "https://doi.org/10.1177/0192623318803867",
        note: "Useful framing for pilot-study design, biodistribution, and early safety readouts in AAV-style programs.",
      },
    ],
  },
  "cheap-cell-free-gate-check": {
    simple_summary:
      "Use a low-cost cell-free assay to answer the first question only: does this design show any measurable signal worth taking into cells?",
    how_to_implement: [
      "Use matched templates and simple controls so the first pass is about signal versus no signal, not about a polished benchmark.",
      "Read kinetics and background in the same run because a small absolute signal can still be unusable if leak is high.",
      "Advance only designs that clear a clear threshold; this workflow is best as a discard filter, not as final validation.",
    ],
    used_when: [
      "Budget is tight and you want to reject clearly weak designs before cell work.",
      "The readout can be reconstructed in a cell-free context without losing the key mechanism.",
      "You need a quick feasibility check for teaching, prototyping, or very early architecture triage.",
    ],
    tradeoffs: [
      "Very fast and cheap, but many cellular failure modes are invisible in extract-based systems.",
      "Good for ruling designs out, less reliable for proving they will work in vivo or even in cultured cells.",
      "Open systems are flexible, but platform choice and extract quality can change the apparent result.",
    ],
    citations: [
      {
        title:
          "Gregorio NE, Levine MZ, Oza JP. A User's Guide to Cell-Free Protein Synthesis. Methods Protoc. 2019.",
        href: "https://doi.org/10.3390/mps2010024",
        note: "Practical overview of how cell-free systems are run and where they help or mislead.",
      },
    ],
  },
};
