import type {
  ToolkitItem,
  WorkflowTemplate,
} from "./types";

export const ITEMS: ToolkitItem[] = [
  {
    "id": "a1000000-0000-0000-0000-000000000011",
    "slug": "ilid",
    "canonical_name": "iLID",
    "item_type": "protein_domain",
    "family": "LOV",
    "summary": "iLID is included as a plausible toolkit component for benchmarking control of localization using LOV logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2014,
    "primary_input_modality": "light",
    "primary_output_modality": "localization",
    "mechanisms": [
      "heterodimerization",
      "conformational_uncaging"
    ],
    "techniques": [
      "directed_evolution"
    ],
    "target_processes": [
      "localization"
    ],
    "synonyms": [
      "light-inducible dimer",
      "iLID-SspB",
      "LOV2-SsrA"
    ],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 3,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 12,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.12,
      "replication_score": 0.35,
      "practicality_score": 0.59,
      "translatability_score": 0.76
    },
    "citations": [
      {
        "id": "c100",
        "source_document_id": "d100",
        "citation_role": "foundational",
        "importance_rank": 1,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d100",
          "source_type": "protocol",
          "title": "ILID study 1",
          "doi": "10.5710/sci.2100.648",
          "pmid": "79617024",
          "publication_year": 2016,
          "journal_or_source": "Nature Biotechnology",
          "is_retracted": false
        }
      },
      {
        "id": "c101",
        "source_document_id": "d101",
        "citation_role": "best_review",
        "importance_rank": 2,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d101",
          "source_type": "review",
          "title": "ILID study 2",
          "doi": "10.7984/sci.2101.898",
          "pmid": "4194120",
          "publication_year": 2014,
          "journal_or_source": "Nature Methods",
          "is_retracted": false
        }
      },
      {
        "id": "c102",
        "source_document_id": "d102",
        "citation_role": "independent_validation",
        "importance_rank": 3,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d102",
          "source_type": "database",
          "title": "ILID study 3",
          "doi": "10.1151/acssynbio.2102.322",
          "pmid": "5826468",
          "publication_year": 2020,
          "journal_or_source": "Science",
          "is_retracted": false
        }
      },
      {
        "id": "c103",
        "source_document_id": "d103",
        "citation_role": "benchmark",
        "importance_rank": 4,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d103",
          "source_type": "preprint",
          "title": "ILID study 4",
          "doi": "10.8669/nmeth.2103.707",
          "pmid": "65371772",
          "publication_year": 2022,
          "journal_or_source": "Nature Biotechnology",
          "is_retracted": false
        }
      },
      {
        "id": "c104",
        "source_document_id": "d104",
        "citation_role": "protocol",
        "importance_rank": 5,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d104",
          "source_type": "review",
          "title": "ILID study 5",
          "doi": "10.5067/sci.2104.217",
          "pmid": "29738394",
          "publication_year": 2009,
          "journal_or_source": "Nature Methods",
          "is_retracted": true
        }
      }
    ],
    "validations": [
      {
        "id": "v100",
        "item_id": "a1000000-0000-0000-0000-000000000011",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "ILID-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 28.19,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.18,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v101",
        "item_id": "a1000000-0000-0000-0000-000000000011",
        "observation_type": "application_demo",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "ILID-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 18.54,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.16,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v102",
        "item_id": "a1000000-0000-0000-0000-000000000011",
        "observation_type": "benchmark",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "ILID-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 26.52,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.24,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000012",
    "slug": "sspb",
    "canonical_name": "SspB micro",
    "item_type": "protein_domain",
    "family": "LOV",
    "summary": "SspB micro is included as a plausible toolkit component for benchmarking control of localization using LOV logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2014,
    "primary_input_modality": "structure",
    "primary_output_modality": "localization",
    "mechanisms": [
      "heterodimerization"
    ],
    "techniques": [],
    "target_processes": [
      "localization"
    ],
    "synonyms": [
      "SspB nano",
      "SspB micro",
      "iLID binder"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 0,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 12,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.18,
      "replication_score": 0.41,
      "practicality_score": 0.63,
      "translatability_score": 0.81
    },
    "citations": [
      {
        "id": "c105",
        "source_document_id": "d105",
        "citation_role": "therapeutic",
        "importance_rank": 1,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d105",
          "source_type": "review",
          "title": "SSPB study 1",
          "doi": "10.6064/mcell.2105.200",
          "pmid": "72411773",
          "publication_year": 2009,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      },
      {
        "id": "c106",
        "source_document_id": "d106",
        "citation_role": "negative_result",
        "importance_rank": 2,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d106",
          "source_type": "protocol",
          "title": "SSPB study 2",
          "doi": "10.1612/cell.2106.955",
          "pmid": "1902869",
          "publication_year": 2020,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v103",
        "item_id": "a1000000-0000-0000-0000-000000000012",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "success",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "SSPB-test-1",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 18.49,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.02,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v104",
        "item_id": "a1000000-0000-0000-0000-000000000012",
        "observation_type": "manufacturing_use",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "SSPB-test-2",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 1.85,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v105",
        "item_id": "a1000000-0000-0000-0000-000000000012",
        "observation_type": "failed_attempt",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "SSPB-test-3",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 17.35,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.19,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000013",
    "slug": "bphp1",
    "canonical_name": "BphP1",
    "item_type": "protein_domain",
    "family": "phytochrome",
    "summary": "BphP1 is included as a plausible toolkit component for benchmarking control of localization using phytochrome logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2016,
    "primary_input_modality": "light",
    "primary_output_modality": "localization",
    "mechanisms": [
      "heterodimerization",
      "membrane_recruitment"
    ],
    "techniques": [
      "directed_evolution"
    ],
    "target_processes": [
      "localization"
    ],
    "synonyms": [
      "near-IR photosensor",
      "BphP1-QPAS1 ancestor",
      "bacterial phytochrome 1"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 10,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.22,
      "replication_score": 0.48,
      "practicality_score": 0.67,
      "translatability_score": 0.85
    },
    "citations": [
      {
        "id": "c107",
        "source_document_id": "d107",
        "citation_role": "structural",
        "importance_rank": 1,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d107",
          "source_type": "journal_article",
          "title": "BPHP1 study 1",
          "doi": "10.4895/sci.2107.982",
          "pmid": "49545193",
          "publication_year": 2024,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      },
      {
        "id": "c108",
        "source_document_id": "d108",
        "citation_role": "database_reference",
        "importance_rank": 2,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d108",
          "source_type": "database",
          "title": "BPHP1 study 2",
          "doi": "10.5160/acssynbio.2108.307",
          "pmid": "86185676",
          "publication_year": 2024,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v106",
        "item_id": "a1000000-0000-0000-0000-000000000013",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "mixed",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "BPHP1-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 28.84,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.09,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v107",
        "item_id": "a1000000-0000-0000-0000-000000000013",
        "observation_type": "application_demo",
        "biological_system_level": "large_animal",
        "species": "Canis lupus familiaris",
        "cell_type": "retinal tissue",
        "delivery_mode": "subretinal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "BPHP1-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 16.24,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v108",
        "item_id": "a1000000-0000-0000-0000-000000000013",
        "observation_type": "benchmark",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "BPHP1-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 23.25,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.05,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000014",
    "slug": "ppsr2",
    "canonical_name": "PpsR2",
    "item_type": "protein_domain",
    "family": "phytochrome",
    "summary": "PpsR2 is included as a plausible toolkit component for benchmarking control of signaling using phytochrome logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2016,
    "primary_input_modality": "structure",
    "primary_output_modality": "localization",
    "mechanisms": [
      "heterodimerization",
      "dna_binding"
    ],
    "techniques": [],
    "target_processes": [
      "signaling"
    ],
    "synonyms": [
      "PpsR2 binder",
      "Q-PAS1-like repressor",
      "BphP partner"
    ],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 2,
      "distinct_institutions": 3,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 10,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.29,
      "replication_score": 0.52,
      "practicality_score": 0.71,
      "translatability_score": 0.89
    },
    "citations": [
      {
        "id": "c109",
        "source_document_id": "d109",
        "citation_role": "foundational",
        "importance_rank": 1,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d109",
          "source_type": "database",
          "title": "PPSR2 study 1",
          "doi": "10.4847/cell.2109.444",
          "pmid": "53674441",
          "publication_year": 2022,
          "journal_or_source": "Nature Methods",
          "is_retracted": false
        }
      },
      {
        "id": "c110",
        "source_document_id": "d110",
        "citation_role": "best_review",
        "importance_rank": 2,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d110",
          "source_type": "review",
          "title": "PPSR2 study 2",
          "doi": "10.3667/mcell.2110.412",
          "pmid": "31356797",
          "publication_year": 2020,
          "journal_or_source": "ACS Synthetic Biology",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v109",
        "item_id": "a1000000-0000-0000-0000-000000000014",
        "observation_type": "therapeutic_use",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "PPSR2-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 25.08,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 9.16,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v110",
        "item_id": "a1000000-0000-0000-0000-000000000014",
        "observation_type": "manufacturing_use",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "PPSR2-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 7.78,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v111",
        "item_id": "a1000000-0000-0000-0000-000000000014",
        "observation_type": "failed_attempt",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "failed",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "PPSR2-test-3",
        "independent_lab_cluster_id": null,
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 22.09,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 20.47,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000015",
    "slug": "dronpa",
    "canonical_name": "pdDronpa1",
    "item_type": "protein_domain",
    "family": "fluorescent_protein",
    "summary": "pdDronpa1 is included as a plausible toolkit component for benchmarking control of cell state using fluorescent_protein logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2011,
    "primary_input_modality": "light",
    "primary_output_modality": "localization",
    "mechanisms": [
      "conformational_uncaging",
      "oligomerization"
    ],
    "techniques": [],
    "target_processes": [],
    "synonyms": [
      "photodissociable Dronpa",
      "pdDronpa",
      "Dronpa145N"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 15,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.35,
      "replication_score": 0.59,
      "practicality_score": 0.76,
      "translatability_score": 0.93
    },
    "citations": [
      {
        "id": "c111",
        "source_document_id": "d111",
        "citation_role": "independent_validation",
        "importance_rank": 1,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d111",
          "source_type": "preprint",
          "title": "DRONPA study 1",
          "doi": "10.4799/nmeth.2111.483",
          "pmid": "30027075",
          "publication_year": 2018,
          "journal_or_source": "Cell",
          "is_retracted": false
        }
      },
      {
        "id": "c112",
        "source_document_id": "d112",
        "citation_role": "benchmark",
        "importance_rank": 2,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d112",
          "source_type": "journal_article",
          "title": "DRONPA study 2",
          "doi": "10.3033/cell.2112.463",
          "pmid": "53515234",
          "publication_year": 2018,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v112",
        "item_id": "a1000000-0000-0000-0000-000000000015",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "success",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "DRONPA-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 29.26,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 12.31,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v113",
        "item_id": "a1000000-0000-0000-0000-000000000015",
        "observation_type": "application_demo",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "DRONPA-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 24.63,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v114",
        "item_id": "a1000000-0000-0000-0000-000000000015",
        "observation_type": "benchmark",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "DRONPA-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 21.91,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 24.35,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000016",
    "slug": "vvd",
    "canonical_name": "VVD",
    "item_type": "protein_domain",
    "family": "LOV",
    "summary": "VVD is included as a plausible toolkit component for benchmarking control of cell state using LOV logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2012,
    "primary_input_modality": "light",
    "primary_output_modality": "localization",
    "mechanisms": [
      "oligomerization"
    ],
    "techniques": [],
    "target_processes": [],
    "synonyms": [
      "Vivid",
      "fungal LOV dimer",
      "white-collar interactor"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 0,
      "distinct_last_author_clusters": 2,
      "distinct_institutions": 3,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 14,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.41,
      "replication_score": 0.63,
      "practicality_score": 0.81,
      "translatability_score": 0.97
    },
    "citations": [
      {
        "id": "c113",
        "source_document_id": "d113",
        "citation_role": "protocol",
        "importance_rank": 1,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d113",
          "source_type": "review",
          "title": "VVD study 1",
          "doi": "10.1065/nmeth.2113.256",
          "pmid": "67530048",
          "publication_year": 2018,
          "journal_or_source": "Cell",
          "is_retracted": false
        }
      },
      {
        "id": "c114",
        "source_document_id": "d114",
        "citation_role": "therapeutic",
        "importance_rank": 2,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d114",
          "source_type": "database",
          "title": "VVD study 2",
          "doi": "10.3943/sci.2114.332",
          "pmid": "95772859",
          "publication_year": 2004,
          "journal_or_source": "Cell",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v115",
        "item_id": "a1000000-0000-0000-0000-000000000016",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mouse",
        "species": "Danio rerio",
        "cell_type": "whole animal",
        "delivery_mode": "microinjection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "VVD-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 9.54,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 22.09,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v116",
        "item_id": "a1000000-0000-0000-0000-000000000016",
        "observation_type": "manufacturing_use",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "VVD-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 29.64,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v117",
        "item_id": "a1000000-0000-0000-0000-000000000016",
        "observation_type": "failed_attempt",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "failed",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "VVD-test-3",
        "independent_lab_cluster_id": null,
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 29.78,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 13.53,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000017",
    "slug": "uvr8",
    "canonical_name": "UVR8",
    "item_type": "protein_domain",
    "family": "UVR8",
    "summary": "UVR8 is included as a plausible toolkit component for benchmarking control of cell state using UVR8 logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2012,
    "primary_input_modality": "light",
    "primary_output_modality": "localization",
    "mechanisms": [
      "oligomerization",
      "dna_binding"
    ],
    "techniques": [],
    "target_processes": [],
    "synonyms": [
      "UV-B photoreceptor",
      "UVR8 core",
      "plant UV sensor"
    ],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 14,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.48,
      "replication_score": 0.67,
      "practicality_score": 0.85,
      "translatability_score": 0.12
    },
    "citations": [
      {
        "id": "c115",
        "source_document_id": "d115",
        "citation_role": "negative_result",
        "importance_rank": 1,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d115",
          "source_type": "protocol",
          "title": "UVR8 study 1",
          "doi": "10.4949/acssynbio.2115.607",
          "pmid": "37648019",
          "publication_year": 2011,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      },
      {
        "id": "c116",
        "source_document_id": "d116",
        "citation_role": "structural",
        "importance_rank": 2,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d116",
          "source_type": "protocol",
          "title": "UVR8 study 2",
          "doi": "10.7025/sci.2116.523",
          "pmid": "59387762",
          "publication_year": 2011,
          "journal_or_source": "Science",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v118",
        "item_id": "a1000000-0000-0000-0000-000000000017",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "UVR8-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 16.14,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 12.17,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v119",
        "item_id": "a1000000-0000-0000-0000-000000000017",
        "observation_type": "application_demo",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "UVR8-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 22.06,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v120",
        "item_id": "a1000000-0000-0000-0000-000000000017",
        "observation_type": "benchmark",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "UVR8-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 9.38,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 7.34,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000018",
    "slug": "cop1",
    "canonical_name": "COP1 WD40",
    "item_type": "protein_domain",
    "family": "UVR8",
    "summary": "COP1 WD40 is included as a plausible toolkit component for benchmarking control of localization using UVR8 logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2012,
    "primary_input_modality": "structure",
    "primary_output_modality": "localization",
    "mechanisms": [
      "membrane_recruitment"
    ],
    "techniques": [],
    "target_processes": [
      "localization"
    ],
    "synonyms": [
      "COP1 WD40 repeat",
      "constitutive photomorphogenesis 1",
      "COP1 domain"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 14,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.52,
      "replication_score": 0.71,
      "practicality_score": 0.89,
      "translatability_score": 0.18
    },
    "citations": [
      {
        "id": "c117",
        "source_document_id": "d117",
        "citation_role": "database_reference",
        "importance_rank": 1,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d117",
          "source_type": "database",
          "title": "COP1 study 1",
          "doi": "10.8471/nbt.2117.449",
          "pmid": "39831665",
          "publication_year": 2018,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      },
      {
        "id": "c118",
        "source_document_id": "d118",
        "citation_role": "foundational",
        "importance_rank": 2,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d118",
          "source_type": "database",
          "title": "COP1 study 2",
          "doi": "10.8456/cell.2118.253",
          "pmid": "42240439",
          "publication_year": 2011,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v121",
        "item_id": "a1000000-0000-0000-0000-000000000018",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "success",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "COP1-test-1",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 14.23,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 24.3,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v122",
        "item_id": "a1000000-0000-0000-0000-000000000018",
        "observation_type": "manufacturing_use",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "COP1-test-2",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 11.14,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v123",
        "item_id": "a1000000-0000-0000-0000-000000000018",
        "observation_type": "failed_attempt",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "COP1-test-3",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 6.8,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 17.66,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000019",
    "slug": "magnets",
    "canonical_name": "nMag/pMag",
    "item_type": "protein_domain",
    "family": "LOV",
    "summary": "nMag/pMag is included as a plausible toolkit component for benchmarking control of cell state using LOV logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2017,
    "primary_input_modality": "light",
    "primary_output_modality": "localization",
    "mechanisms": [
      "heterodimerization",
      "oligomerization"
    ],
    "techniques": [
      "directed_evolution"
    ],
    "target_processes": [],
    "synonyms": [
      "Magnet pair",
      "nMagHigh1/pMagHigh1",
      "light-inducible dimer"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 9,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.59,
      "replication_score": 0.76,
      "practicality_score": 0.93,
      "translatability_score": 0.22
    },
    "citations": [
      {
        "id": "c119",
        "source_document_id": "d119",
        "citation_role": "best_review",
        "importance_rank": 1,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d119",
          "source_type": "review",
          "title": "MAGNETS study 1",
          "doi": "10.7671/sci.2119.296",
          "pmid": "34467848",
          "publication_year": 2011,
          "journal_or_source": "Nature Chemical Biology",
          "is_retracted": false
        }
      },
      {
        "id": "c120",
        "source_document_id": "d120",
        "citation_role": "independent_validation",
        "importance_rank": 2,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d120",
          "source_type": "preprint",
          "title": "MAGNETS study 2",
          "doi": "10.8096/nmeth.2120.643",
          "pmid": "95865036",
          "publication_year": 2020,
          "journal_or_source": "bioRxiv",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v124",
        "item_id": "a1000000-0000-0000-0000-000000000019",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "MAGNETS-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 12.69,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.09,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v125",
        "item_id": "a1000000-0000-0000-0000-000000000019",
        "observation_type": "application_demo",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "MAGNETS-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 5.73,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v126",
        "item_id": "a1000000-0000-0000-0000-000000000019",
        "observation_type": "benchmark",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "MAGNETS-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 1.84,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.18,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000020",
    "slug": "phylov",
    "canonical_name": "phiLOV",
    "item_type": "protein_domain",
    "family": "BLUF",
    "summary": "phiLOV is included as a plausible toolkit component for benchmarking control of diagnostic using BLUF logic.",
    "status": "normalized",
    "maturity_stage": "research",
    "first_publication_year": 2013,
    "primary_input_modality": "light",
    "primary_output_modality": "assay_readout",
    "mechanisms": [
      "conformational_uncaging"
    ],
    "techniques": [],
    "target_processes": [
      "diagnostic"
    ],
    "synonyms": [
      "phiLOV2.1",
      "flavin fluorescent tag",
      "LOV fluorophore"
    ],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": false
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 0,
      "distinct_last_author_clusters": 1,
      "distinct_institutions": 2,
      "distinct_biological_contexts": 1,
      "years_since_first_report": 13,
      "downstream_application_count": 0,
      "orphan_tool_flag": true,
      "practicality_penalties": [
        "sparse independent replication"
      ],
      "evidence_strength_score": 0.63,
      "replication_score": 0.81,
      "practicality_score": 0.97,
      "translatability_score": 0.29
    },
    "citations": [
      {
        "id": "c121",
        "source_document_id": "d121",
        "citation_role": "benchmark",
        "importance_rank": 1,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d121",
          "source_type": "review",
          "title": "PHYLOV study 1",
          "doi": "10.3121/nbt.2121.960",
          "pmid": "31351447",
          "publication_year": 2014,
          "journal_or_source": "Nature Biotechnology",
          "is_retracted": true
        }
      }
    ],
    "validations": [
      {
        "id": "v127",
        "item_id": "a1000000-0000-0000-0000-000000000020",
        "observation_type": "therapeutic_use",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "PHYLOV-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 10.24,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 21.7,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000021",
    "slug": "miniSOG",
    "canonical_name": "miniSOG",
    "item_type": "protein_domain",
    "family": "flavin",
    "summary": "miniSOG is included as a plausible toolkit component for benchmarking control of degradation, degradation using flavin logic.",
    "status": "deprecated",
    "maturity_stage": "clinical",
    "first_publication_year": 2011,
    "primary_input_modality": "light",
    "primary_output_modality": "degradation",
    "mechanisms": [
      "degradation",
      "photocleavage"
    ],
    "techniques": [
      "directed_evolution"
    ],
    "target_processes": [
      "degradation",
      "degradation"
    ],
    "synonyms": [
      "mini Singlet Oxygen Generator",
      "miniSOG2",
      "phototoxic flavoprotein"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 2,
      "distinct_institutions": 3,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 15,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [
        "deprecated due to phototoxic cargo burden",
        "high dark toxicity in prolonged illumination",
        "poor suitability for therapeutic deployment"
      ],
      "evidence_strength_score": 0.67,
      "replication_score": 0.85,
      "practicality_score": 0.12,
      "translatability_score": 0.35
    },
    "citations": [
      {
        "id": "c122",
        "source_document_id": "d122",
        "citation_role": "protocol",
        "importance_rank": 1,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d122",
          "source_type": "protocol",
          "title": "MINISOG study 1",
          "doi": "10.7311/nmeth.2122.470",
          "pmid": "44383882",
          "publication_year": 2011,
          "journal_or_source": "Molecular Cell",
          "is_retracted": false
        }
      },
      {
        "id": "c123",
        "source_document_id": "d123",
        "citation_role": "therapeutic",
        "importance_rank": 2,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d123",
          "source_type": "database",
          "title": "MINISOG study 2",
          "doi": "10.9202/sci.2123.448",
          "pmid": "24457509",
          "publication_year": 2020,
          "journal_or_source": "bioRxiv",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v128",
        "item_id": "a1000000-0000-0000-0000-000000000021",
        "observation_type": "manufacturing_use",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "MINISOG-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 5.87,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 8.28,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v129",
        "item_id": "a1000000-0000-0000-0000-000000000021",
        "observation_type": "failed_attempt",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "MINISOG-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 19.75,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v130",
        "item_id": "a1000000-0000-0000-0000-000000000021",
        "observation_type": "failed_attempt",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "failed",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "MINISOG-test-3",
        "independent_lab_cluster_id": null,
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 6.62,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 13.94,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000022",
    "slug": "tulips",
    "canonical_name": "LOVpep",
    "item_type": "protein_domain",
    "family": "LOV",
    "summary": "LOVpep is included as a plausible toolkit component for benchmarking control of cell state using LOV logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2009,
    "primary_input_modality": "light",
    "primary_output_modality": "localization",
    "mechanisms": [
      "heterodimerization",
      "conformational_uncaging"
    ],
    "techniques": [
      "directed_evolution"
    ],
    "target_processes": [],
    "synonyms": [
      "TULIPs",
      "LOVpep/ePDZ",
      "light-inducible dimer"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 17,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.71,
      "replication_score": 0.89,
      "practicality_score": 0.18,
      "translatability_score": 0.41
    },
    "citations": [
      {
        "id": "c124",
        "source_document_id": "d124",
        "citation_role": "negative_result",
        "importance_rank": 1,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d124",
          "source_type": "database",
          "title": "TULIPS study 1",
          "doi": "10.4558/nbt.2124.563",
          "pmid": "41655416",
          "publication_year": 2016,
          "journal_or_source": "Science",
          "is_retracted": false
        }
      },
      {
        "id": "c125",
        "source_document_id": "d125",
        "citation_role": "structural",
        "importance_rank": 2,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d125",
          "source_type": "database",
          "title": "TULIPS study 2",
          "doi": "10.2658/acssynbio.2125.735",
          "pmid": "2009246",
          "publication_year": 2004,
          "journal_or_source": "Molecular Cell",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v131",
        "item_id": "a1000000-0000-0000-0000-000000000022",
        "observation_type": "application_demo",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "TULIPS-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 4.57,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.08,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v132",
        "item_id": "a1000000-0000-0000-0000-000000000022",
        "observation_type": "benchmark",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "TULIPS-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 8.5,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v133",
        "item_id": "a1000000-0000-0000-0000-000000000022",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "TULIPS-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 17.62,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.31,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000023",
    "slug": "cry2cib1",
    "canonical_name": "CRY2/CIB1",
    "item_type": "multi_component_switch",
    "family": "cryptochrome",
    "summary": "CRY2/CIB1 is included as a plausible toolkit component for benchmarking control of cell state using cryptochrome logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2013,
    "primary_input_modality": "light",
    "primary_output_modality": "signaling",
    "mechanisms": [
      "heterodimerization",
      "membrane_recruitment"
    ],
    "techniques": [
      "directed_evolution"
    ],
    "target_processes": [],
    "synonyms": [
      "CRY2-CIBN",
      "cryptochrome-CIB1",
      "blue-light dimerizer"
    ],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 3,
      "independent_primary_paper_count": 2,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 13,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.76,
      "replication_score": 0.93,
      "practicality_score": 0.22,
      "translatability_score": 0.48
    },
    "citations": [
      {
        "id": "c126",
        "source_document_id": "d126",
        "citation_role": "database_reference",
        "importance_rank": 1,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d126",
          "source_type": "database",
          "title": "CRY2CIB1 study 1",
          "doi": "10.7699/sci.2126.357",
          "pmid": "23658009",
          "publication_year": 2022,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      },
      {
        "id": "c127",
        "source_document_id": "d127",
        "citation_role": "foundational",
        "importance_rank": 2,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d127",
          "source_type": "review",
          "title": "CRY2CIB1 study 2",
          "doi": "10.6470/acssynbio.2127.880",
          "pmid": "34113031",
          "publication_year": 2014,
          "journal_or_source": "ACS Synthetic Biology",
          "is_retracted": false
        }
      },
      {
        "id": "c128",
        "source_document_id": "d128",
        "citation_role": "best_review",
        "importance_rank": 3,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d128",
          "source_type": "review",
          "title": "CRY2CIB1 study 3",
          "doi": "10.7237/mcell.2128.725",
          "pmid": "78394715",
          "publication_year": 2016,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      },
      {
        "id": "c129",
        "source_document_id": "d129",
        "citation_role": "independent_validation",
        "importance_rank": 4,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d129",
          "source_type": "review",
          "title": "CRY2CIB1 study 4",
          "doi": "10.2702/acssynbio.2129.623",
          "pmid": "47273200",
          "publication_year": 2016,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      },
      {
        "id": "c130",
        "source_document_id": "d130",
        "citation_role": "benchmark",
        "importance_rank": 5,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d130",
          "source_type": "journal_article",
          "title": "CRY2CIB1 study 5",
          "doi": "10.2425/cell.2130.442",
          "pmid": "74547601",
          "publication_year": 2014,
          "journal_or_source": "Cell",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v134",
        "item_id": "a1000000-0000-0000-0000-000000000023",
        "observation_type": "manufacturing_use",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "CRY2CIB1-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 28.37,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.27,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v135",
        "item_id": "a1000000-0000-0000-0000-000000000023",
        "observation_type": "failed_attempt",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "CRY2CIB1-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 17.49,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.03,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v136",
        "item_id": "a1000000-0000-0000-0000-000000000023",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "CRY2CIB1-test-3",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 23.52,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.33,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000024",
    "slug": "phybpif",
    "canonical_name": "PhyB/PIF",
    "item_type": "multi_component_switch",
    "family": "phytochrome",
    "summary": "PhyB/PIF is included as a plausible toolkit component for benchmarking control of localization using phytochrome logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2009,
    "primary_input_modality": "light",
    "primary_output_modality": "signaling",
    "mechanisms": [
      "heterodimerization",
      "membrane_recruitment"
    ],
    "techniques": [],
    "target_processes": [
      "localization"
    ],
    "synonyms": [
      "PhyB-PIF6",
      "red-light dimerizer",
      "phytochrome interacting factor"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 2,
      "distinct_institutions": 3,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 17,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.81,
      "replication_score": 0.97,
      "practicality_score": 0.29,
      "translatability_score": 0.52
    },
    "citations": [
      {
        "id": "c131",
        "source_document_id": "d131",
        "citation_role": "protocol",
        "importance_rank": 1,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d131",
          "source_type": "database",
          "title": "PHYBPIF study 1",
          "doi": "10.5194/sci.2131.180",
          "pmid": "78924602",
          "publication_year": 2004,
          "journal_or_source": "Science",
          "is_retracted": false
        }
      },
      {
        "id": "c132",
        "source_document_id": "d132",
        "citation_role": "therapeutic",
        "importance_rank": 2,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d132",
          "source_type": "journal_article",
          "title": "PHYBPIF study 2",
          "doi": "10.2933/mcell.2132.548",
          "pmid": "34281939",
          "publication_year": 2020,
          "journal_or_source": "bioRxiv",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v137",
        "item_id": "a1000000-0000-0000-0000-000000000024",
        "observation_type": "application_demo",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "PHYBPIF-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 4.06,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.07,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v138",
        "item_id": "a1000000-0000-0000-0000-000000000024",
        "observation_type": "benchmark",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "PHYBPIF-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 5.91,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v139",
        "item_id": "a1000000-0000-0000-0000-000000000024",
        "observation_type": "failed_attempt",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "failed",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "PHYBPIF-test-3",
        "independent_lab_cluster_id": null,
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 19.64,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.22,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000025",
    "slug": "gbggrip",
    "canonical_name": "Gβγ-GRIP",
    "item_type": "multi_component_switch",
    "family": "membrane_recruitment",
    "summary": "A chemogenetic membrane recruitment cassette that couples Gβγ release to GRIP-domain relocalization. Sparse data were entered intentionally to emulate an early-stage record.",
    "status": "seed",
    "maturity_stage": "research",
    "first_publication_year": null,
    "primary_input_modality": "magnetic",
    "primary_output_modality": "signaling",
    "mechanisms": [
      "membrane_recruitment"
    ],
    "techniques": [
      "delivery_optimization"
    ],
    "target_processes": [
      "signaling",
      "signaling"
    ],
    "synonyms": [
      "Gβγ-GRIP",
      "GRIP recruitment cassette"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": false
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 0,
      "independent_primary_paper_count": 0,
      "distinct_last_author_clusters": 1,
      "distinct_institutions": 1,
      "distinct_biological_contexts": 1,
      "years_since_first_report": 8,
      "downstream_application_count": 0,
      "orphan_tool_flag": true,
      "practicality_penalties": [
        "sparse independent replication"
      ],
      "evidence_strength_score": 0.85,
      "replication_score": 0.12,
      "practicality_score": 0.35,
      "translatability_score": 0.59
    },
    "citations": [],
    "validations": [
      {
        "id": "v140",
        "item_id": "a1000000-0000-0000-0000-000000000025",
        "observation_type": "manufacturing_use",
        "biological_system_level": "primary_cells",
        "species": null,
        "cell_type": null,
        "delivery_mode": null,
        "success_outcome": "mixed",
        "assay_description": null,
        "construct_name": null,
        "independent_lab_cluster_id": "lab-4",
        "metrics": []
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000026",
    "slug": "cry2-cib1-spa1",
    "canonical_name": "CRY2/CIB1/SPA1",
    "item_type": "multi_component_switch",
    "family": "cryptochrome",
    "summary": "CRY2/CIB1/SPA1 is included as a plausible toolkit component for benchmarking control of transcription, transcription using cryptochrome logic.",
    "status": "curated",
    "maturity_stage": "preclinical",
    "first_publication_year": 2019,
    "primary_input_modality": "light",
    "primary_output_modality": "transcription",
    "mechanisms": [
      "heterodimerization",
      "dna_binding",
      "translation_control"
    ],
    "techniques": [],
    "target_processes": [
      "transcription",
      "transcription"
    ],
    "synonyms": [
      "CRY2/CIB1/SPA1",
      "three-component blue-light transcription switch",
      "SPA1 amplifier"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 7,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.89,
      "replication_score": 0.18,
      "practicality_score": 0.41,
      "translatability_score": 0.63
    },
    "citations": [
      {
        "id": "c133",
        "source_document_id": "d133",
        "citation_role": "negative_result",
        "importance_rank": 1,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d133",
          "source_type": "journal_article",
          "title": "CRY2CIB1SPA1 study 1",
          "doi": "10.6781/nmeth.2133.708",
          "pmid": "68399243",
          "publication_year": 2014,
          "journal_or_source": "Cell",
          "is_retracted": false
        }
      },
      {
        "id": "c134",
        "source_document_id": "d134",
        "citation_role": "structural",
        "importance_rank": 2,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d134",
          "source_type": "preprint",
          "title": "CRY2CIB1SPA1 study 2",
          "doi": "10.3459/mcell.2134.433",
          "pmid": "55906310",
          "publication_year": 2018,
          "journal_or_source": "Nature Methods",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v141",
        "item_id": "a1000000-0000-0000-0000-000000000026",
        "observation_type": "failed_attempt",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "mixed",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "CRY2CIB1SPA1-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 8.73,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 18.38,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v142",
        "item_id": "a1000000-0000-0000-0000-000000000026",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "CRY2CIB1SPA1-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 9.24,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v143",
        "item_id": "a1000000-0000-0000-0000-000000000026",
        "observation_type": "application_demo",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "CRY2CIB1SPA1-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 2.1,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 1.32,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000027",
    "slug": "abipyl",
    "canonical_name": "ABI/PYL",
    "item_type": "multi_component_switch",
    "family": "ABA",
    "summary": "ABI/PYL is included as a plausible toolkit component for benchmarking control of cell state using ABA logic.",
    "status": "curated",
    "maturity_stage": "clinical",
    "first_publication_year": 2012,
    "primary_input_modality": "chemical",
    "primary_output_modality": "signaling",
    "mechanisms": [
      "heterodimerization"
    ],
    "techniques": [
      "directed_evolution"
    ],
    "target_processes": [],
    "synonyms": [
      "ABA switch",
      "PYL-ABI",
      "abscisic acid dimerizer"
    ],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 2,
      "distinct_institutions": 3,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 14,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.93,
      "replication_score": 0.22,
      "practicality_score": 0.48,
      "translatability_score": 0.67
    },
    "citations": [
      {
        "id": "c135",
        "source_document_id": "d135",
        "citation_role": "database_reference",
        "importance_rank": 1,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d135",
          "source_type": "database",
          "title": "ABIPYL study 1",
          "doi": "10.5699/acssynbio.2135.531",
          "pmid": "13960270",
          "publication_year": 2018,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      },
      {
        "id": "c136",
        "source_document_id": "d136",
        "citation_role": "foundational",
        "importance_rank": 2,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d136",
          "source_type": "journal_article",
          "title": "ABIPYL study 2",
          "doi": "10.1417/mcell.2136.995",
          "pmid": "66282053",
          "publication_year": 2014,
          "journal_or_source": "Nature Methods",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v144",
        "item_id": "a1000000-0000-0000-0000-000000000027",
        "observation_type": "benchmark",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "ABIPYL-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 27.36,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.14,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v145",
        "item_id": "a1000000-0000-0000-0000-000000000027",
        "observation_type": "therapeutic_use",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "ABIPYL-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 7.54,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v146",
        "item_id": "a1000000-0000-0000-0000-000000000027",
        "observation_type": "failed_attempt",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "failed",
        "assay_description": "plate reader induction assay",
        "construct_name": "ABIPYL-test-3",
        "independent_lab_cluster_id": null,
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 22.51,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.13,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000028",
    "slug": "fkbp-frb",
    "canonical_name": "FKBP/FRB",
    "item_type": "multi_component_switch",
    "family": "rapalog",
    "summary": "FKBP/FRB is included as a plausible toolkit component for benchmarking control of localization using rapalog logic.",
    "status": "curated",
    "maturity_stage": "clinical",
    "first_publication_year": 1994,
    "primary_input_modality": "chemical",
    "primary_output_modality": "signaling",
    "mechanisms": [
      "heterodimerization",
      "membrane_recruitment"
    ],
    "techniques": [],
    "target_processes": [
      "localization"
    ],
    "synonyms": [
      "FKBP12-FRB",
      "rapamycin dimerizer",
      "rapalog switch",
      "CID",
      "chemical inducer of dimerization",
      "FRB/FKBP"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 2,
      "independent_primary_paper_count": 2,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 32,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.97,
      "replication_score": 0.29,
      "practicality_score": 0.52,
      "translatability_score": 0.71
    },
    "citations": [
      {
        "id": "c137",
        "source_document_id": "d137",
        "citation_role": "best_review",
        "importance_rank": 1,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d137",
          "source_type": "review",
          "title": "FKBPFRB study 1",
          "doi": "10.1327/sci.2137.274",
          "pmid": "73556670",
          "publication_year": 2022,
          "journal_or_source": "Molecular Cell",
          "is_retracted": false
        }
      },
      {
        "id": "c138",
        "source_document_id": "d138",
        "citation_role": "independent_validation",
        "importance_rank": 2,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d138",
          "source_type": "review",
          "title": "FKBPFRB study 2",
          "doi": "10.8877/sci.2138.321",
          "pmid": "74804771",
          "publication_year": 2014,
          "journal_or_source": "Nature Biotechnology",
          "is_retracted": false
        }
      },
      {
        "id": "c139",
        "source_document_id": "d139",
        "citation_role": "benchmark",
        "importance_rank": 3,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d139",
          "source_type": "protocol",
          "title": "FKBPFRB study 3",
          "doi": "10.9316/sci.2139.438",
          "pmid": "91686452",
          "publication_year": 2018,
          "journal_or_source": "eLife",
          "is_retracted": false
        }
      },
      {
        "id": "c140",
        "source_document_id": "d140",
        "citation_role": "protocol",
        "importance_rank": 4,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d140",
          "source_type": "database",
          "title": "FKBPFRB study 4",
          "doi": "10.6020/nmeth.2140.118",
          "pmid": "33871642",
          "publication_year": 2004,
          "journal_or_source": "ACS Synthetic Biology",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v147",
        "item_id": "a1000000-0000-0000-0000-000000000028",
        "observation_type": "failed_attempt",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "mixed",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "FKBPFRB-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 26.34,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.3,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v148",
        "item_id": "a1000000-0000-0000-0000-000000000028",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "success",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "FKBPFRB-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 7.17,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v149",
        "item_id": "a1000000-0000-0000-0000-000000000028",
        "observation_type": "application_demo",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "FKBPFRB-test-3",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 5.5,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "dark_state_leak",
            "value_num": 0.13,
            "unit": "fraction",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000029",
    "slug": "theo",
    "canonical_name": "Theophylline aptazyme",
    "item_type": "rna_element",
    "family": "aptazyme",
    "summary": "Theophylline aptazyme is included as a plausible toolkit component for benchmarking control of translation using aptazyme logic.",
    "status": "curated",
    "maturity_stage": "preclinical",
    "first_publication_year": 2004,
    "primary_input_modality": "chemical",
    "primary_output_modality": "translation",
    "mechanisms": [
      "rna_binding",
      "translation_control"
    ],
    "techniques": [],
    "target_processes": [
      "translation"
    ],
    "synonyms": [
      "theophylline aptazyme",
      "Theo-off ribozyme",
      "small-molecule riboswitch"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 22,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.12,
      "replication_score": 0.35,
      "practicality_score": 0.59,
      "translatability_score": 0.76
    },
    "citations": [
      {
        "id": "c141",
        "source_document_id": "d141",
        "citation_role": "therapeutic",
        "importance_rank": 1,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d141",
          "source_type": "protocol",
          "title": "THEO study 1",
          "doi": "10.1009/sci.2141.758",
          "pmid": "64595592",
          "publication_year": 2018,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      },
      {
        "id": "c142",
        "source_document_id": "d142",
        "citation_role": "negative_result",
        "importance_rank": 2,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d142",
          "source_type": "database",
          "title": "THEO study 2",
          "doi": "10.2903/sci.2142.965",
          "pmid": "47543198",
          "publication_year": 2024,
          "journal_or_source": "Nature Chemical Biology",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v150",
        "item_id": "a1000000-0000-0000-0000-000000000029",
        "observation_type": "benchmark",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "THEO-test-1",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 21.89,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 13.74,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v151",
        "item_id": "a1000000-0000-0000-0000-000000000029",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "THEO-test-2",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 26.13,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v152",
        "item_id": "a1000000-0000-0000-0000-000000000029",
        "observation_type": "manufacturing_use",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "THEO-test-3",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 19.26,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 4.31,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000030",
    "slug": "toehold",
    "canonical_name": "Toehold switch",
    "item_type": "rna_element",
    "family": "toehold",
    "summary": "Toehold switch is included as a plausible toolkit component for benchmarking control of translation using toehold logic.",
    "status": "curated",
    "maturity_stage": "preclinical",
    "first_publication_year": 2014,
    "primary_input_modality": "sequence",
    "primary_output_modality": "translation",
    "mechanisms": [
      "translation_control",
      "rna_binding"
    ],
    "techniques": [
      "sequence_verification"
    ],
    "target_processes": [
      "translation"
    ],
    "synonyms": [
      "toehold sensor",
      "RNA toehold switch",
      "programmable translational gate"
    ],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 2,
      "distinct_institutions": 3,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 12,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.18,
      "replication_score": 0.41,
      "practicality_score": 0.63,
      "translatability_score": 0.81
    },
    "citations": [
      {
        "id": "c143",
        "source_document_id": "d143",
        "citation_role": "structural",
        "importance_rank": 1,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d143",
          "source_type": "review",
          "title": "TOEHOLD study 1",
          "doi": "10.6826/nbt.2143.941",
          "pmid": "19428486",
          "publication_year": 2018,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      },
      {
        "id": "c144",
        "source_document_id": "d144",
        "citation_role": "database_reference",
        "importance_rank": 2,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d144",
          "source_type": "database",
          "title": "TOEHOLD study 2",
          "doi": "10.8691/nbt.2144.662",
          "pmid": "39670551",
          "publication_year": 2004,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v153",
        "item_id": "a1000000-0000-0000-0000-000000000030",
        "observation_type": "failed_attempt",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "TOEHOLD-test-1",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 28.31,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 14.6,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v154",
        "item_id": "a1000000-0000-0000-0000-000000000030",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "TOEHOLD-test-2",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 26.17,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v155",
        "item_id": "a1000000-0000-0000-0000-000000000030",
        "observation_type": "failed_attempt",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "failed",
        "assay_description": "plate reader induction assay",
        "construct_name": "TOEHOLD-test-3",
        "independent_lab_cluster_id": null,
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 9.0,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 19.14,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000031",
    "slug": "ms2gated",
    "canonical_name": "MS2-gated riboswitch",
    "item_type": "rna_element",
    "family": "riboswitch",
    "summary": "MS2-gated riboswitch is included as a plausible toolkit component for benchmarking control of translation using riboswitch logic.",
    "status": "seed",
    "maturity_stage": "research",
    "first_publication_year": 2018,
    "primary_input_modality": "structure",
    "primary_output_modality": "translation",
    "mechanisms": [
      "rna_binding",
      "translation_control"
    ],
    "techniques": [
      "sequence_verification"
    ],
    "target_processes": [
      "translation"
    ],
    "synonyms": [
      "MS2 riboregulator",
      "coat-protein gated switch"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": false
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 0,
      "independent_primary_paper_count": 0,
      "distinct_last_author_clusters": 1,
      "distinct_institutions": 1,
      "distinct_biological_contexts": 0,
      "years_since_first_report": 8,
      "downstream_application_count": 0,
      "orphan_tool_flag": true,
      "practicality_penalties": [
        "sparse independent replication"
      ],
      "evidence_strength_score": 0.22,
      "replication_score": 0.48,
      "practicality_score": 0.67,
      "translatability_score": 0.85
    },
    "citations": [],
    "validations": []
  },
  {
    "id": "a1000000-0000-0000-0000-000000000032",
    "slug": "split-intein",
    "canonical_name": "Split intein reconstitution",
    "item_type": "construct_pattern",
    "family": "reconstitution",
    "summary": "Split intein reconstitution is included as a plausible toolkit component for benchmarking control of editing, editing using reconstitution logic.",
    "status": "curated",
    "maturity_stage": "preclinical",
    "first_publication_year": 2007,
    "primary_input_modality": "thermal",
    "primary_output_modality": "editing",
    "mechanisms": [
      "conformational_uncaging"
    ],
    "techniques": [],
    "target_processes": [
      "editing",
      "editing"
    ],
    "synonyms": [
      "split intein",
      "protein trans-splicing",
      "conditional ligation"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 19,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.29,
      "replication_score": 0.52,
      "practicality_score": 0.71,
      "translatability_score": 0.89
    },
    "citations": [
      {
        "id": "c145",
        "source_document_id": "d145",
        "citation_role": "foundational",
        "importance_rank": 1,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d145",
          "source_type": "preprint",
          "title": "SPLITINTEIN study 1",
          "doi": "10.9262/mcell.2145.288",
          "pmid": "85682672",
          "publication_year": 2009,
          "journal_or_source": "Nature Biotechnology",
          "is_retracted": false
        }
      },
      {
        "id": "c146",
        "source_document_id": "d146",
        "citation_role": "best_review",
        "importance_rank": 2,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d146",
          "source_type": "review",
          "title": "SPLITINTEIN study 2",
          "doi": "10.2522/cell.2146.106",
          "pmid": "35004210",
          "publication_year": 2022,
          "journal_or_source": "bioRxiv",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v156",
        "item_id": "a1000000-0000-0000-0000-000000000032",
        "observation_type": "benchmark",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "SPLITINTEIN-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "editing_efficiency_percent",
            "value_num": 22.0,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "viability_percent",
            "value_num": 77.7,
            "unit": "%",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v157",
        "item_id": "a1000000-0000-0000-0000-000000000032",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "success",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "SPLITINTEIN-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "editing_efficiency_percent",
            "value_num": 40.4,
            "unit": "%",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v158",
        "item_id": "a1000000-0000-0000-0000-000000000032",
        "observation_type": "manufacturing_use",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "SPLITINTEIN-test-3",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "editing_efficiency_percent",
            "value_num": 43.4,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "viability_percent",
            "value_num": 53.3,
            "unit": "%",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000033",
    "slug": "split-cre",
    "canonical_name": "N/C-split Cre recombinase",
    "item_type": "construct_pattern",
    "family": "reconstitution",
    "summary": "N/C-split Cre recombinase is included as a plausible toolkit component for benchmarking control of editing, editing using reconstitution logic.",
    "status": "curated",
    "maturity_stage": "clinical",
    "first_publication_year": 2009,
    "primary_input_modality": "conformational_change",
    "primary_output_modality": "editing",
    "mechanisms": [
      "conformational_uncaging",
      "dna_binding"
    ],
    "techniques": [],
    "target_processes": [
      "editing",
      "editing"
    ],
    "synonyms": [
      "split Cre",
      "N/C split Cre",
      "reconstituted Cre"
    ],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 17,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.35,
      "replication_score": 0.59,
      "practicality_score": 0.76,
      "translatability_score": 0.93
    },
    "citations": [
      {
        "id": "c147",
        "source_document_id": "d147",
        "citation_role": "independent_validation",
        "importance_rank": 1,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d147",
          "source_type": "preprint",
          "title": "SPLITCRE study 1",
          "doi": "10.1724/sci.2147.175",
          "pmid": "14273007",
          "publication_year": 2014,
          "journal_or_source": "eLife",
          "is_retracted": false
        }
      },
      {
        "id": "c148",
        "source_document_id": "d148",
        "citation_role": "benchmark",
        "importance_rank": 2,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d148",
          "source_type": "preprint",
          "title": "SPLITCRE study 2",
          "doi": "10.4513/nmeth.2148.217",
          "pmid": "22283323",
          "publication_year": 2004,
          "journal_or_source": "Nature Biotechnology",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v159",
        "item_id": "a1000000-0000-0000-0000-000000000033",
        "observation_type": "failed_attempt",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "SPLITCRE-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "editing_efficiency_percent",
            "value_num": 47.6,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "viability_percent",
            "value_num": 59.9,
            "unit": "%",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v160",
        "item_id": "a1000000-0000-0000-0000-000000000033",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "SPLITCRE-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "editing_efficiency_percent",
            "value_num": 6.1,
            "unit": "%",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v161",
        "item_id": "a1000000-0000-0000-0000-000000000033",
        "observation_type": "application_demo",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "SPLITCRE-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "editing_efficiency_percent",
            "value_num": 57.7,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "viability_percent",
            "value_num": 57.3,
            "unit": "%",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000034",
    "slug": "phagedisplay",
    "canonical_name": "Phage display enrichment",
    "item_type": "engineering_method",
    "family": "display",
    "summary": "Phage display enrichment is included as a plausible toolkit component for benchmarking control of selection, manufacturing using display logic.",
    "status": "curated",
    "maturity_stage": "deployed",
    "first_publication_year": 1985,
    "primary_input_modality": "selection",
    "primary_output_modality": "selection",
    "mechanisms": [],
    "techniques": [
      "selection_enrichment"
    ],
    "target_processes": [
      "selection",
      "manufacturing"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 41,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.41,
      "replication_score": 0.63,
      "practicality_score": 0.81,
      "translatability_score": 0.97
    },
    "citations": [
      {
        "id": "c149",
        "source_document_id": "d149",
        "citation_role": "protocol",
        "importance_rank": 1,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d149",
          "source_type": "database",
          "title": "PHAGEDISPLAY study 1",
          "doi": "10.3402/nmeth.2149.686",
          "pmid": "39998977",
          "publication_year": 2018,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      },
      {
        "id": "c150",
        "source_document_id": "d150",
        "citation_role": "therapeutic",
        "importance_rank": 2,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d150",
          "source_type": "journal_article",
          "title": "PHAGEDISPLAY study 2",
          "doi": "10.4692/nmeth.2150.457",
          "pmid": "6287957",
          "publication_year": 2016,
          "journal_or_source": "ACS Synthetic Biology",
          "is_retracted": true
        }
      }
    ],
    "validations": [
      {
        "id": "v162",
        "item_id": "a1000000-0000-0000-0000-000000000034",
        "observation_type": "benchmark",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "mixed",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "PHAGEDISPLAY-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 10.61,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 1.9,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v163",
        "item_id": "a1000000-0000-0000-0000-000000000034",
        "observation_type": "manufacturing_use",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "PHAGEDISPLAY-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 15.32,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v164",
        "item_id": "a1000000-0000-0000-0000-000000000034",
        "observation_type": "manufacturing_use",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "PHAGEDISPLAY-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 25.16,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 22.57,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000035",
    "slug": "yeastdisplay",
    "canonical_name": "Yeast surface display",
    "item_type": "engineering_method",
    "family": "display",
    "summary": "Yeast surface display is included as a plausible toolkit component for benchmarking control of selection, manufacturing using display logic.",
    "status": "curated",
    "maturity_stage": "deployed",
    "first_publication_year": 2000,
    "primary_input_modality": "selection",
    "primary_output_modality": "selection",
    "mechanisms": [],
    "techniques": [
      "selection_enrichment"
    ],
    "target_processes": [
      "selection",
      "manufacturing"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 2,
      "distinct_institutions": 3,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 26,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.48,
      "replication_score": 0.67,
      "practicality_score": 0.85,
      "translatability_score": 0.12
    },
    "citations": [
      {
        "id": "c151",
        "source_document_id": "d151",
        "citation_role": "negative_result",
        "importance_rank": 1,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d151",
          "source_type": "database",
          "title": "YEASTDISPLAY study 1",
          "doi": "10.1000/nbt.2151.596",
          "pmid": "14178222",
          "publication_year": 2009,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      },
      {
        "id": "c152",
        "source_document_id": "d152",
        "citation_role": "structural",
        "importance_rank": 2,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d152",
          "source_type": "database",
          "title": "YEASTDISPLAY study 2",
          "doi": "10.8132/nbt.2152.354",
          "pmid": "97522319",
          "publication_year": 1998,
          "journal_or_source": "Cell",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v165",
        "item_id": "a1000000-0000-0000-0000-000000000035",
        "observation_type": "failed_attempt",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "YEASTDISPLAY-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 27.7,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 6.92,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v166",
        "item_id": "a1000000-0000-0000-0000-000000000035",
        "observation_type": "manufacturing_use",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "success",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "YEASTDISPLAY-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 23.87,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v167",
        "item_id": "a1000000-0000-0000-0000-000000000035",
        "observation_type": "failed_attempt",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "failed",
        "assay_description": "functional viability and localization assay",
        "construct_name": "YEASTDISPLAY-test-3",
        "independent_lab_cluster_id": null,
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 7.98,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 7.6,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000036",
    "slug": "pace",
    "canonical_name": "PACE",
    "item_type": "engineering_method",
    "family": "continuous_evolution",
    "summary": "PACE is included as a plausible toolkit component for benchmarking control of selection using continuous_evolution logic.",
    "status": "curated",
    "maturity_stage": "preclinical",
    "first_publication_year": 2011,
    "primary_input_modality": "selection",
    "primary_output_modality": "selection",
    "mechanisms": [],
    "techniques": [
      "selection_enrichment"
    ],
    "target_processes": [
      "selection"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 15,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.52,
      "replication_score": 0.71,
      "practicality_score": 0.89,
      "translatability_score": 0.18
    },
    "citations": [
      {
        "id": "c153",
        "source_document_id": "d153",
        "citation_role": "database_reference",
        "importance_rank": 1,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d153",
          "source_type": "database",
          "title": "PACE study 1",
          "doi": "10.1377/sci.2153.735",
          "pmid": "64381865",
          "publication_year": 2014,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      },
      {
        "id": "c154",
        "source_document_id": "d154",
        "citation_role": "foundational",
        "importance_rank": 2,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d154",
          "source_type": "database",
          "title": "PACE study 2",
          "doi": "10.2540/cell.2154.803",
          "pmid": "33739844",
          "publication_year": 2022,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v168",
        "item_id": "a1000000-0000-0000-0000-000000000036",
        "observation_type": "benchmark",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "mixed",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "PACE-test-1",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 10.35,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 18.17,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v169",
        "item_id": "a1000000-0000-0000-0000-000000000036",
        "observation_type": "manufacturing_use",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "PACE-test-2",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 25.36,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v170",
        "item_id": "a1000000-0000-0000-0000-000000000036",
        "observation_type": "manufacturing_use",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "PACE-test-3",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 3.44,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 21.47,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000037",
    "slug": "facsseq",
    "canonical_name": "FACS-Seq",
    "item_type": "engineering_method",
    "family": "screening",
    "summary": "FACS-Seq is included as a plausible toolkit component for benchmarking control of selection using screening logic.",
    "status": "curated",
    "maturity_stage": "preclinical",
    "first_publication_year": 2016,
    "primary_input_modality": "analysis",
    "primary_output_modality": "selection",
    "mechanisms": [],
    "techniques": [
      "selection_enrichment",
      "sequence_verification"
    ],
    "target_processes": [
      "selection"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 10,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.59,
      "replication_score": 0.76,
      "practicality_score": 0.93,
      "translatability_score": 0.22
    },
    "citations": [
      {
        "id": "c155",
        "source_document_id": "d155",
        "citation_role": "best_review",
        "importance_rank": 1,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d155",
          "source_type": "review",
          "title": "FACSSEQ study 1",
          "doi": "10.2825/cell.2155.165",
          "pmid": "6029800",
          "publication_year": 2022,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      },
      {
        "id": "c156",
        "source_document_id": "d156",
        "citation_role": "independent_validation",
        "importance_rank": 2,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d156",
          "source_type": "protocol",
          "title": "FACSSEQ study 2",
          "doi": "10.5626/nbt.2156.653",
          "pmid": "37567176",
          "publication_year": 2024,
          "journal_or_source": "Nature Chemical Biology",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v171",
        "item_id": "a1000000-0000-0000-0000-000000000037",
        "observation_type": "failed_attempt",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "FACSSEQ-test-1",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 2.58,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 10.68,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v172",
        "item_id": "a1000000-0000-0000-0000-000000000037",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "FACSSEQ-test-2",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 3.16,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v173",
        "item_id": "a1000000-0000-0000-0000-000000000037",
        "observation_type": "application_demo",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "FACSSEQ-test-3",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 7.77,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 8.21,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000038",
    "slug": "celluspot",
    "canonical_name": "CelluSpot peptide arrays",
    "item_type": "engineering_method",
    "family": "peptide_array",
    "summary": "CelluSpot peptide arrays is included as a plausible toolkit component for benchmarking control of diagnostic using peptide_array logic.",
    "status": "normalized",
    "maturity_stage": "research",
    "first_publication_year": 2010,
    "primary_input_modality": "mechanical",
    "primary_output_modality": "selection",
    "mechanisms": [
      "dna_binding"
    ],
    "techniques": [],
    "target_processes": [
      "diagnostic"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": false
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 0,
      "independent_primary_paper_count": 0,
      "distinct_last_author_clusters": 1,
      "distinct_institutions": 1,
      "distinct_biological_contexts": 1,
      "years_since_first_report": 16,
      "downstream_application_count": 0,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.63,
      "replication_score": 0.81,
      "practicality_score": 0.97,
      "translatability_score": 0.29
    },
    "citations": [],
    "validations": [
      {
        "id": "v174",
        "item_id": "a1000000-0000-0000-0000-000000000038",
        "observation_type": "benchmark",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "CELLUSPOT-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": []
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000039",
    "slug": "deeplibrary",
    "canonical_name": "Deep mutational library scan",
    "item_type": "engineering_method",
    "family": "screening",
    "summary": "Deep mutational library scan is included as a plausible toolkit component for benchmarking control of manufacturing using screening logic.",
    "status": "normalized",
    "maturity_stage": "preclinical",
    "first_publication_year": 2015,
    "primary_input_modality": "sequence",
    "primary_output_modality": "selection",
    "mechanisms": [],
    "techniques": [
      "selection_enrichment",
      "sequence_verification"
    ],
    "target_processes": [
      "manufacturing"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": false
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 0,
      "independent_primary_paper_count": 0,
      "distinct_last_author_clusters": 1,
      "distinct_institutions": 1,
      "distinct_biological_contexts": 1,
      "years_since_first_report": 11,
      "downstream_application_count": 0,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.67,
      "replication_score": 0.85,
      "practicality_score": 0.12,
      "translatability_score": 0.35
    },
    "citations": [],
    "validations": [
      {
        "id": "v175",
        "item_id": "a1000000-0000-0000-0000-000000000039",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "mixed",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "DEEPLIBRARY-test-1",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 3.2,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 21.97,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000040",
    "slug": "mammaliandirected",
    "canonical_name": "Mammalian directed evolution",
    "item_type": "engineering_method",
    "family": "evolution",
    "summary": "Mammalian directed evolution is included as a plausible toolkit component for benchmarking control of selection, manufacturing using evolution logic.",
    "status": "normalized",
    "maturity_stage": "research",
    "first_publication_year": 2021,
    "primary_input_modality": "selection",
    "primary_output_modality": "selection",
    "mechanisms": [],
    "techniques": [
      "selection_enrichment"
    ],
    "target_processes": [
      "selection",
      "manufacturing"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 0,
      "distinct_last_author_clusters": 2,
      "distinct_institutions": 3,
      "distinct_biological_contexts": 2,
      "years_since_first_report": 5,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.71,
      "replication_score": 0.89,
      "practicality_score": 0.18,
      "translatability_score": 0.41
    },
    "citations": [
      {
        "id": "c157",
        "source_document_id": "d157",
        "citation_role": "benchmark",
        "importance_rank": 1,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d157",
          "source_type": "protocol",
          "title": "MAMMALIANDIRECTED study 1",
          "doi": "10.1280/nbt.2157.887",
          "pmid": "34650342",
          "publication_year": 2024,
          "journal_or_source": "Cell",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v176",
        "item_id": "a1000000-0000-0000-0000-000000000040",
        "observation_type": "manufacturing_use",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "MAMMALIANDIRECTED-test-1",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 22.8,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 17.93,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v177",
        "item_id": "a1000000-0000-0000-0000-000000000040",
        "observation_type": "failed_attempt",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "MAMMALIANDIRECTED-test-2",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 13.95,
            "unit": "x",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000041",
    "slug": "flow",
    "canonical_name": "Flow cytometry profiling",
    "item_type": "assay_method",
    "family": "cytometry",
    "summary": "Flow cytometry profiling is included as a plausible toolkit component for benchmarking control of diagnostic using cytometry logic.",
    "status": "curated",
    "maturity_stage": "clinical",
    "first_publication_year": 1974,
    "primary_input_modality": "assay_readout",
    "primary_output_modality": "analysis",
    "mechanisms": [],
    "techniques": [
      "functional_assay"
    ],
    "target_processes": [
      "diagnostic"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 52,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.76,
      "replication_score": 0.93,
      "practicality_score": 0.22,
      "translatability_score": 0.48
    },
    "citations": [
      {
        "id": "c158",
        "source_document_id": "d158",
        "citation_role": "protocol",
        "importance_rank": 1,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d158",
          "source_type": "protocol",
          "title": "FLOW study 1",
          "doi": "10.4718/mcell.2158.497",
          "pmid": "88788482",
          "publication_year": 2014,
          "journal_or_source": "Nature Methods",
          "is_retracted": false
        }
      },
      {
        "id": "c159",
        "source_document_id": "d159",
        "citation_role": "therapeutic",
        "importance_rank": 2,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d159",
          "source_type": "review",
          "title": "FLOW study 2",
          "doi": "10.9046/nmeth.2159.884",
          "pmid": "6395854",
          "publication_year": 2018,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v178",
        "item_id": "a1000000-0000-0000-0000-000000000041",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "FLOW-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 10.86,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 620.7,
            "unit": "nM",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v179",
        "item_id": "a1000000-0000-0000-0000-000000000041",
        "observation_type": "application_demo",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "FLOW-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 22.86,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v180",
        "item_id": "a1000000-0000-0000-0000-000000000041",
        "observation_type": "benchmark",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "FLOW-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 19.3,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 171.0,
            "unit": "nM",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000042",
    "slug": "spr",
    "canonical_name": "SPR/BLI affinity",
    "item_type": "assay_method",
    "family": "binding",
    "summary": "SPR/BLI affinity is included as a plausible toolkit component for benchmarking control of diagnostic using binding logic.",
    "status": "curated",
    "maturity_stage": "clinical",
    "first_publication_year": 1991,
    "primary_input_modality": "assay_readout",
    "primary_output_modality": "analysis",
    "mechanisms": [],
    "techniques": [
      "functional_assay",
      "structural_characterization"
    ],
    "target_processes": [
      "diagnostic"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 35,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.81,
      "replication_score": 0.97,
      "practicality_score": 0.29,
      "translatability_score": 0.52
    },
    "citations": [
      {
        "id": "c160",
        "source_document_id": "d160",
        "citation_role": "negative_result",
        "importance_rank": 1,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d160",
          "source_type": "journal_article",
          "title": "SPR study 1",
          "doi": "10.4967/sci.2160.994",
          "pmid": "17604039",
          "publication_year": 2014,
          "journal_or_source": "ACS Synthetic Biology",
          "is_retracted": false
        }
      },
      {
        "id": "c161",
        "source_document_id": "d161",
        "citation_role": "structural",
        "importance_rank": 2,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d161",
          "source_type": "review",
          "title": "SPR study 2",
          "doi": "10.3917/cell.2161.132",
          "pmid": "17289954",
          "publication_year": 2009,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v181",
        "item_id": "a1000000-0000-0000-0000-000000000042",
        "observation_type": "therapeutic_use",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "mixed",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "SPR-test-1",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 11.77,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 334.2,
            "unit": "nM",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v182",
        "item_id": "a1000000-0000-0000-0000-000000000042",
        "observation_type": "manufacturing_use",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "SPR-test-2",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 17.73,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v183",
        "item_id": "a1000000-0000-0000-0000-000000000042",
        "observation_type": "failed_attempt",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "SPR-test-3",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 11.06,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 815.1,
            "unit": "nM",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000043",
    "slug": "cryoem",
    "canonical_name": "Cryo-EM structural readout",
    "item_type": "assay_method",
    "family": "structure",
    "summary": "Cryo-EM structural readout is included as a plausible toolkit component for benchmarking control of diagnostic using structure logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2013,
    "primary_input_modality": "structure",
    "primary_output_modality": "analysis",
    "mechanisms": [],
    "techniques": [
      "functional_assay",
      "structural_characterization"
    ],
    "target_processes": [
      "diagnostic"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 13,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.85,
      "replication_score": 0.12,
      "practicality_score": 0.35,
      "translatability_score": 0.59
    },
    "citations": [
      {
        "id": "c162",
        "source_document_id": "d162",
        "citation_role": "database_reference",
        "importance_rank": 1,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d162",
          "source_type": "database",
          "title": "CRYOEM study 1",
          "doi": "10.9180/cell.2162.696",
          "pmid": "99877132",
          "publication_year": 1998,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      },
      {
        "id": "c163",
        "source_document_id": "d163",
        "citation_role": "foundational",
        "importance_rank": 2,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d163",
          "source_type": "protocol",
          "title": "CRYOEM study 2",
          "doi": "10.4433/mcell.2163.524",
          "pmid": "73407751",
          "publication_year": 2011,
          "journal_or_source": "Science",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v184",
        "item_id": "a1000000-0000-0000-0000-000000000043",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "success",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "CRYOEM-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 12.65,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 321.7,
            "unit": "nM",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v185",
        "item_id": "a1000000-0000-0000-0000-000000000043",
        "observation_type": "application_demo",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "CRYOEM-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 17.54,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v186",
        "item_id": "a1000000-0000-0000-0000-000000000043",
        "observation_type": "benchmark",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "CRYOEM-test-3",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 10.84,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 82.7,
            "unit": "nM",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000044",
    "slug": "alphascreen",
    "canonical_name": "AlphaScreen proximity assay",
    "item_type": "assay_method",
    "family": "proximity",
    "summary": "AlphaScreen proximity assay is included as a plausible toolkit component for benchmarking control of diagnostic using proximity logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2001,
    "primary_input_modality": "assay_readout",
    "primary_output_modality": "analysis",
    "mechanisms": [],
    "techniques": [
      "functional_assay"
    ],
    "target_processes": [
      "diagnostic"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 25,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.89,
      "replication_score": 0.18,
      "practicality_score": 0.41,
      "translatability_score": 0.63
    },
    "citations": [
      {
        "id": "c164",
        "source_document_id": "d164",
        "citation_role": "best_review",
        "importance_rank": 1,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d164",
          "source_type": "review",
          "title": "ALPHASCREEN study 1",
          "doi": "10.6136/mcell.2164.432",
          "pmid": "50159686",
          "publication_year": 2014,
          "journal_or_source": "Cell",
          "is_retracted": false
        }
      },
      {
        "id": "c165",
        "source_document_id": "d165",
        "citation_role": "independent_validation",
        "importance_rank": 2,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d165",
          "source_type": "database",
          "title": "ALPHASCREEN study 2",
          "doi": "10.2553/mcell.2165.235",
          "pmid": "35033600",
          "publication_year": 2004,
          "journal_or_source": "Molecular Cell",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v187",
        "item_id": "a1000000-0000-0000-0000-000000000044",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "mixed",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "ALPHASCREEN-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 17.88,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 94.5,
            "unit": "nM",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v188",
        "item_id": "a1000000-0000-0000-0000-000000000044",
        "observation_type": "manufacturing_use",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "ALPHASCREEN-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 9.36,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v189",
        "item_id": "a1000000-0000-0000-0000-000000000044",
        "observation_type": "failed_attempt",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "ALPHASCREEN-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 18.76,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 845.1,
            "unit": "nM",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000045",
    "slug": "elisa",
    "canonical_name": "ELISA secretion panel",
    "item_type": "assay_method",
    "family": "immunoassay",
    "summary": "ELISA secretion panel is included as a plausible toolkit component for benchmarking control of diagnostic using immunoassay logic.",
    "status": "curated",
    "maturity_stage": "clinical",
    "first_publication_year": 1971,
    "primary_input_modality": "assay_readout",
    "primary_output_modality": "analysis",
    "mechanisms": [],
    "techniques": [
      "functional_assay"
    ],
    "target_processes": [
      "diagnostic"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 55,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.93,
      "replication_score": 0.22,
      "practicality_score": 0.48,
      "translatability_score": 0.67
    },
    "citations": [
      {
        "id": "c166",
        "source_document_id": "d166",
        "citation_role": "benchmark",
        "importance_rank": 1,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d166",
          "source_type": "database",
          "title": "ELISA study 1",
          "doi": "10.9185/nmeth.2166.410",
          "pmid": "10871772",
          "publication_year": 2016,
          "journal_or_source": "Molecular Cell",
          "is_retracted": false
        }
      },
      {
        "id": "c167",
        "source_document_id": "d167",
        "citation_role": "protocol",
        "importance_rank": 2,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d167",
          "source_type": "journal_article",
          "title": "ELISA study 2",
          "doi": "10.8965/nbt.2167.469",
          "pmid": "82640981",
          "publication_year": 2022,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v190",
        "item_id": "a1000000-0000-0000-0000-000000000045",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "ELISA-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 1.81,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 549.5,
            "unit": "nM",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v191",
        "item_id": "a1000000-0000-0000-0000-000000000045",
        "observation_type": "application_demo",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "ELISA-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 20.18,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v192",
        "item_id": "a1000000-0000-0000-0000-000000000045",
        "observation_type": "benchmark",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "ELISA-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "signal_to_noise",
            "value_num": 20.56,
            "unit": "ratio",
            "qualifier": null
          },
          {
            "metric_name": "affinity_kd",
            "value_num": 749.5,
            "unit": "nM",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000046",
    "slug": "alphafold2",
    "canonical_name": "AlphaFold2",
    "item_type": "computation_method",
    "family": "structure_modeling",
    "summary": "AlphaFold2 is included as a plausible toolkit component for benchmarking control of cell state using structure_modeling logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2021,
    "primary_input_modality": "sequence",
    "primary_output_modality": "structure",
    "mechanisms": [],
    "techniques": [
      "computational_design"
    ],
    "target_processes": [],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 5,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.97,
      "replication_score": 0.29,
      "practicality_score": 0.52,
      "translatability_score": 0.71
    },
    "citations": [
      {
        "id": "c168",
        "source_document_id": "d168",
        "citation_role": "therapeutic",
        "importance_rank": 1,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d168",
          "source_type": "database",
          "title": "ALPHAFOLD2 study 1",
          "doi": "10.7520/nbt.2168.931",
          "pmid": "80085412",
          "publication_year": 2024,
          "journal_or_source": "eLife",
          "is_retracted": false
        }
      },
      {
        "id": "c169",
        "source_document_id": "d169",
        "citation_role": "negative_result",
        "importance_rank": 2,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d169",
          "source_type": "review",
          "title": "ALPHAFOLD2 study 2",
          "doi": "10.2226/sci.2169.113",
          "pmid": "26890628",
          "publication_year": 2020,
          "journal_or_source": "Nature Chemical Biology",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v193",
        "item_id": "a1000000-0000-0000-0000-000000000046",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "mixed",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "ALPHAFOLD2-test-1",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 11.49,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 20.81,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v194",
        "item_id": "a1000000-0000-0000-0000-000000000046",
        "observation_type": "manufacturing_use",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "ALPHAFOLD2-test-2",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 12.67,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v195",
        "item_id": "a1000000-0000-0000-0000-000000000046",
        "observation_type": "failed_attempt",
        "biological_system_level": "organoid",
        "species": "C. elegans",
        "cell_type": "whole worm",
        "delivery_mode": "microinjection",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "ALPHAFOLD2-test-3",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 27.31,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 18.46,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000047",
    "slug": "esmfold",
    "canonical_name": "ESMFold",
    "item_type": "computation_method",
    "family": "language_model",
    "summary": "ESMFold is included as a plausible toolkit component for benchmarking control of cell state using language_model logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2022,
    "primary_input_modality": "sequence",
    "primary_output_modality": "structure",
    "mechanisms": [],
    "techniques": [
      "computational_design"
    ],
    "target_processes": [],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 4,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.12,
      "replication_score": 0.35,
      "practicality_score": 0.59,
      "translatability_score": 0.76
    },
    "citations": [
      {
        "id": "c170",
        "source_document_id": "d170",
        "citation_role": "structural",
        "importance_rank": 1,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d170",
          "source_type": "protocol",
          "title": "ESMFOLD study 1",
          "doi": "10.4821/cell.2170.426",
          "pmid": "49971759",
          "publication_year": 2022,
          "journal_or_source": "Nature Chemical Biology",
          "is_retracted": false
        }
      },
      {
        "id": "c171",
        "source_document_id": "d171",
        "citation_role": "database_reference",
        "importance_rank": 2,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d171",
          "source_type": "database",
          "title": "ESMFOLD study 2",
          "doi": "10.1125/sci.2171.930",
          "pmid": "22501700",
          "publication_year": 2009,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v196",
        "item_id": "a1000000-0000-0000-0000-000000000047",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "ESMFOLD-test-1",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 19.88,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 11.67,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v197",
        "item_id": "a1000000-0000-0000-0000-000000000047",
        "observation_type": "application_demo",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "ESMFOLD-test-2",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 19.6,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v198",
        "item_id": "a1000000-0000-0000-0000-000000000047",
        "observation_type": "benchmark",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "ESMFOLD-test-3",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 2.28,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 23.07,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000048",
    "slug": "proteinmpnn",
    "canonical_name": "ProteinMPNN",
    "item_type": "computation_method",
    "family": "sequence_design",
    "summary": "ProteinMPNN is included as a plausible toolkit component for benchmarking control of cell state using sequence_design logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2022,
    "primary_input_modality": "structure",
    "primary_output_modality": "sequence",
    "mechanisms": [],
    "techniques": [
      "computational_design"
    ],
    "target_processes": [],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 4,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.18,
      "replication_score": 0.41,
      "practicality_score": 0.63,
      "translatability_score": 0.81
    },
    "citations": [
      {
        "id": "c172",
        "source_document_id": "d172",
        "citation_role": "foundational",
        "importance_rank": 1,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d172",
          "source_type": "preprint",
          "title": "PROTEINMPNN study 1",
          "doi": "10.4282/mcell.2172.111",
          "pmid": "99539688",
          "publication_year": 2018,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      },
      {
        "id": "c173",
        "source_document_id": "d173",
        "citation_role": "best_review",
        "importance_rank": 2,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d173",
          "source_type": "review",
          "title": "PROTEINMPNN study 2",
          "doi": "10.9288/sci.2173.689",
          "pmid": "56436663",
          "publication_year": 2018,
          "journal_or_source": "ACS Synthetic Biology",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v199",
        "item_id": "a1000000-0000-0000-0000-000000000048",
        "observation_type": "therapeutic_use",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "PROTEINMPNN-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 17.72,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 16.14,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v200",
        "item_id": "a1000000-0000-0000-0000-000000000048",
        "observation_type": "manufacturing_use",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "PROTEINMPNN-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 2.55,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v201",
        "item_id": "a1000000-0000-0000-0000-000000000048",
        "observation_type": "failed_attempt",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "PROTEINMPNN-test-3",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 19.43,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 8.37,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000049",
    "slug": "rfdiffusion",
    "canonical_name": "RFdiffusion",
    "item_type": "computation_method",
    "family": "backbone_generation",
    "summary": "RFdiffusion is included as a plausible toolkit component for benchmarking control of cell state using backbone_generation logic.",
    "status": "curated",
    "maturity_stage": "research",
    "first_publication_year": 2023,
    "primary_input_modality": "structure",
    "primary_output_modality": "structure",
    "mechanisms": [],
    "techniques": [
      "computational_design"
    ],
    "target_processes": [],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": false,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 3,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.22,
      "replication_score": 0.48,
      "practicality_score": 0.67,
      "translatability_score": 0.85
    },
    "citations": [
      {
        "id": "c174",
        "source_document_id": "d174",
        "citation_role": "independent_validation",
        "importance_rank": 1,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d174",
          "source_type": "protocol",
          "title": "RFDIFFUSION study 1",
          "doi": "10.6760/acssynbio.2174.449",
          "pmid": "42763089",
          "publication_year": 2020,
          "journal_or_source": "eLife",
          "is_retracted": false
        }
      },
      {
        "id": "c175",
        "source_document_id": "d175",
        "citation_role": "benchmark",
        "importance_rank": 2,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d175",
          "source_type": "database",
          "title": "RFDIFFUSION study 2",
          "doi": "10.8461/nbt.2175.225",
          "pmid": "46351783",
          "publication_year": 2004,
          "journal_or_source": "bioRxiv",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v202",
        "item_id": "a1000000-0000-0000-0000-000000000049",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "success",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "RFDIFFUSION-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 25.1,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 12.4,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v203",
        "item_id": "a1000000-0000-0000-0000-000000000049",
        "observation_type": "application_demo",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "RFDIFFUSION-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 28.03,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v204",
        "item_id": "a1000000-0000-0000-0000-000000000049",
        "observation_type": "benchmark",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "success",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "RFDIFFUSION-test-3",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 21.4,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 21.91,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000050",
    "slug": "rosetta",
    "canonical_name": "Rosetta design",
    "item_type": "computation_method",
    "family": "energy_model",
    "summary": "Rosetta design is included as a plausible toolkit component for benchmarking control of cell state using energy_model logic.",
    "status": "curated",
    "maturity_stage": "deployed",
    "first_publication_year": 1999,
    "primary_input_modality": "structure",
    "primary_output_modality": "sequence",
    "mechanisms": [],
    "techniques": [
      "computational_design"
    ],
    "target_processes": [],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 3,
      "independent_primary_paper_count": 2,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 27,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [],
      "evidence_strength_score": 0.29,
      "replication_score": 0.52,
      "practicality_score": 0.71,
      "translatability_score": 0.89
    },
    "citations": [
      {
        "id": "c176",
        "source_document_id": "d176",
        "citation_role": "protocol",
        "importance_rank": 1,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d176",
          "source_type": "protocol",
          "title": "ROSETTA study 1",
          "doi": "10.2018/acssynbio.2176.761",
          "pmid": "5196094",
          "publication_year": 2020,
          "journal_or_source": "Science",
          "is_retracted": false
        }
      },
      {
        "id": "c177",
        "source_document_id": "d177",
        "citation_role": "therapeutic",
        "importance_rank": 2,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d177",
          "source_type": "review",
          "title": "ROSETTA study 2",
          "doi": "10.6893/cell.2177.186",
          "pmid": "11644231",
          "publication_year": 1998,
          "journal_or_source": "Cell",
          "is_retracted": false
        }
      },
      {
        "id": "c178",
        "source_document_id": "d178",
        "citation_role": "negative_result",
        "importance_rank": 3,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d178",
          "source_type": "review",
          "title": "ROSETTA study 3",
          "doi": "10.3427/nmeth.2178.912",
          "pmid": "5898414",
          "publication_year": 2022,
          "journal_or_source": "Science",
          "is_retracted": false
        }
      },
      {
        "id": "c179",
        "source_document_id": "d179",
        "citation_role": "structural",
        "importance_rank": 4,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d179",
          "source_type": "protocol",
          "title": "ROSETTA study 4",
          "doi": "10.9216/acssynbio.2179.652",
          "pmid": "56278342",
          "publication_year": 2020,
          "journal_or_source": "Nature Chemical Biology",
          "is_retracted": false
        }
      },
      {
        "id": "c180",
        "source_document_id": "d180",
        "citation_role": "database_reference",
        "importance_rank": 5,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d180",
          "source_type": "database",
          "title": "ROSETTA study 5",
          "doi": "10.7398/acssynbio.2180.318",
          "pmid": "61361312",
          "publication_year": 2024,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v205",
        "item_id": "a1000000-0000-0000-0000-000000000050",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "ROSETTA-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 12.86,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 3.92,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v206",
        "item_id": "a1000000-0000-0000-0000-000000000050",
        "observation_type": "manufacturing_use",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "ROSETTA-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 1.8,
            "unit": "x",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v207",
        "item_id": "a1000000-0000-0000-0000-000000000050",
        "observation_type": "failed_attempt",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "ROSETTA-test-3",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "fold_induction",
            "value_num": 21.79,
            "unit": "x",
            "qualifier": null
          },
          {
            "metric_name": "signal_to_noise",
            "value_num": 18.43,
            "unit": "ratio",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000051",
    "slug": "chai1",
    "canonical_name": "Chai-1",
    "item_type": "computation_method",
    "family": "multimodal_structure",
    "summary": null,
    "status": "seed",
    "maturity_stage": "research",
    "first_publication_year": 2024,
    "primary_input_modality": "sequence",
    "primary_output_modality": "structure",
    "mechanisms": [],
    "techniques": [
      "computational_design"
    ],
    "target_processes": [],
    "synonyms": [],
    "validation_rollup": null,
    "replication_summary": null,
    "citations": [],
    "validations": []
  },
  {
    "id": "a1000000-0000-0000-0000-000000000052",
    "slug": "aav",
    "canonical_name": "AAV serotype harness",
    "item_type": "delivery_harness",
    "family": "viral",
    "summary": "AAV serotype harnesses are included here as delivery abstractions rather than as single capsid sequences. In practice, a delivery harness item is the operational package that determines where a control system can actually be tested, what dose window is realistic, what tissue compartment receives cargo, which manufacturing constraints dominate, and which immune liabilities appear before the payload itself has a fair chance to work. AAV therefore stress-tests the viewer in several ways. The same basic harness can support reporter cargo, genome editors, split effectors, transcriptional regulators, degron fusions, or optogenetic modules, yet the relevant evidence depends on promoter choice, cassette length, serotype, route of administration, animal species, pre-existing antibodies, and whether the readout is expression, editing, biodistribution, toxicity, or functional rescue. In curated datasets that mixture often produces citations spanning foundational virology, capsid engineering, biodistribution surveys, toxicology, clinical translation, and negative results related to liver injury or dorsal root ganglion findings. Validation records also naturally span cell lines, primary cells, mouse studies, large-animal studies, and human clinical use. That makes AAV a useful adversarial case for sort order, score breakdowns, and citation rendering, because the item is neither a single molecular switch nor a single assay. It is a deployment scaffold whose practical value depends on context. A user may see strong translational evidence and assume universal utility, but the fine print matters: packaging capacity is limited, redosing is difficult, manufacturing comparability can be messy, and tissue access is serotype- and route-dependent. In other words, this is the glamorous viral bus with a very small trunk and a habit of attracting immunology paperwork. It also forces validation rollups to handle cases where some studies are clear mechanistic successes while others are mixed because expression is present but function is weak, or because efficacy appears only in one tissue compartment. For translational readers that distinction matters: delivery is not binary, and an apparently successful AAV deployment can still fail operationally because the cassette is too large, the promoter is wrong for the cell state, the route underperforms, or a safety signal appears only after scaling dose. That messy realism is precisely why the harness belongs in a mock database.",
    "status": "curated",
    "maturity_stage": "clinical",
    "first_publication_year": 2001,
    "primary_input_modality": "structure",
    "primary_output_modality": "localization",
    "mechanisms": [],
    "techniques": [
      "delivery_optimization"
    ],
    "target_processes": [
      "localization"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": true,
      "has_bacterial_validation": true,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 3,
      "independent_primary_paper_count": 2,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 25,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [
        "payload size constraints",
        "dose and CMC complexity",
        "repeat dosing uncertainty"
      ],
      "evidence_strength_score": 0.35,
      "replication_score": 0.59,
      "practicality_score": 0.76,
      "translatability_score": 0.93
    },
    "citations": [
      {
        "id": "c181",
        "source_document_id": "d181",
        "citation_role": "foundational",
        "importance_rank": 1,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d181",
          "source_type": "database",
          "title": "AAV study 1",
          "doi": "10.2141/sci.2181.656",
          "pmid": "9096646",
          "publication_year": 2011,
          "journal_or_source": "Nucleic Acids Research",
          "is_retracted": false
        }
      },
      {
        "id": "c182",
        "source_document_id": "d182",
        "citation_role": "best_review",
        "importance_rank": 2,
        "why_this_matters": "Compact review used to summarize design space and caveats.",
        "document": {
          "id": "d182",
          "source_type": "review",
          "title": "AAV study 2",
          "doi": "10.2289/nbt.2182.652",
          "pmid": "31690785",
          "publication_year": 2020,
          "journal_or_source": "PNAS",
          "is_retracted": false
        }
      },
      {
        "id": "c183",
        "source_document_id": "d183",
        "citation_role": "independent_validation",
        "importance_rank": 3,
        "why_this_matters": "Independent group reproduced the behavior in a different context.",
        "document": {
          "id": "d183",
          "source_type": "journal_article",
          "title": "AAV study 3",
          "doi": "10.6894/acssynbio.2183.555",
          "pmid": "92024542",
          "publication_year": 2014,
          "journal_or_source": "ACS Synthetic Biology",
          "is_retracted": false
        }
      },
      {
        "id": "c184",
        "source_document_id": "d184",
        "citation_role": "benchmark",
        "importance_rank": 4,
        "why_this_matters": "Head-to-head data useful for ranking against alternatives.",
        "document": {
          "id": "d184",
          "source_type": "preprint",
          "title": "AAV study 4",
          "doi": "10.2239/cell.2184.136",
          "pmid": "24834246",
          "publication_year": 2004,
          "journal_or_source": "eLife",
          "is_retracted": false
        }
      },
      {
        "id": "c185",
        "source_document_id": "d185",
        "citation_role": "protocol",
        "importance_rank": 5,
        "why_this_matters": "Contains procedural details that explain reproducibility.",
        "document": {
          "id": "d185",
          "source_type": "review",
          "title": "AAV study 5",
          "doi": "10.1455/sci.2185.560",
          "pmid": "86856658",
          "publication_year": 2014,
          "journal_or_source": "Nature Biotechnology",
          "is_retracted": false
        }
      },
      {
        "id": "c186",
        "source_document_id": "d186",
        "citation_role": "therapeutic",
        "importance_rank": 6,
        "why_this_matters": "Connects the component to disease-relevant or translational use.",
        "document": {
          "id": "d186",
          "source_type": "protocol",
          "title": "AAV study 6",
          "doi": "10.3747/cell.2186.220",
          "pmid": "59500593",
          "publication_year": 2004,
          "journal_or_source": "Nature Biotechnology",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v208",
        "item_id": "a1000000-0000-0000-0000-000000000052",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "cell_free",
        "species": null,
        "cell_type": null,
        "delivery_mode": "cell-free translation",
        "success_outcome": "success",
        "assay_description": "cell-free reporter kinetics",
        "construct_name": "AAV-test-1",
        "independent_lab_cluster_id": "lab-3",
        "metrics": [
          {
            "metric_name": "viability_percent",
            "value_num": 45.0,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "toxicity_signal",
            "value_num": 3.25,
            "unit": "AU",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v209",
        "item_id": "a1000000-0000-0000-0000-000000000052",
        "observation_type": "therapeutic_use",
        "biological_system_level": "bacteria",
        "species": "E. coli",
        "cell_type": "E. coli BL21",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "plate reader induction assay",
        "construct_name": "AAV-test-2",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "viability_percent",
            "value_num": 98.1,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "toxicity_signal",
            "value_num": 0.94,
            "unit": "AU",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v210",
        "item_id": "a1000000-0000-0000-0000-000000000052",
        "observation_type": "benchmark",
        "biological_system_level": "yeast",
        "species": "S. cerevisiae",
        "cell_type": "BY4741",
        "delivery_mode": "plasmid transformation",
        "success_outcome": "success",
        "assay_description": "flow cytometry reporter assay",
        "construct_name": "AAV-test-3",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "viability_percent",
            "value_num": 91.8,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "toxicity_signal",
            "value_num": 1.25,
            "unit": "AU",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000053",
    "slug": "lnp",
    "canonical_name": "LNP IV formulation",
    "item_type": "delivery_harness",
    "family": "nanoparticle",
    "summary": "LNP IV formulation is included as a plausible toolkit component for benchmarking control of localization using nanoparticle logic.",
    "status": "curated",
    "maturity_stage": "clinical",
    "first_publication_year": 2018,
    "primary_input_modality": "chemical",
    "primary_output_modality": "localization",
    "mechanisms": [],
    "techniques": [
      "delivery_optimization"
    ],
    "target_processes": [
      "localization"
    ],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": true,
      "has_mouse_in_vivo_validation": false,
      "has_human_clinical_validation": false,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 2,
      "distinct_institutions": 3,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 8,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [
        "payload size constraints",
        "dose and CMC complexity",
        "repeat dosing uncertainty"
      ],
      "evidence_strength_score": 0.41,
      "replication_score": 0.63,
      "practicality_score": 0.81,
      "translatability_score": 0.97
    },
    "citations": [
      {
        "id": "c187",
        "source_document_id": "d187",
        "citation_role": "negative_result",
        "importance_rank": 1,
        "why_this_matters": "Documents a limitation, failure mode, or safety concern.",
        "document": {
          "id": "d187",
          "source_type": "journal_article",
          "title": "LNP study 1",
          "doi": "10.8168/sci.2187.205",
          "pmid": "45920155",
          "publication_year": 2004,
          "journal_or_source": "ACS Synthetic Biology",
          "is_retracted": false
        }
      },
      {
        "id": "c188",
        "source_document_id": "d188",
        "citation_role": "structural",
        "importance_rank": 2,
        "why_this_matters": "Supports mechanism with structure or biophysical mapping.",
        "document": {
          "id": "d188",
          "source_type": "database",
          "title": "LNP study 2",
          "doi": "10.7107/acssynbio.2188.290",
          "pmid": "36238527",
          "publication_year": 2009,
          "journal_or_source": "bioRxiv",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v211",
        "item_id": "a1000000-0000-0000-0000-000000000053",
        "observation_type": "therapeutic_use",
        "biological_system_level": "mammalian_cell_line",
        "species": "human",
        "cell_type": "HEK293T",
        "delivery_mode": "transient transfection",
        "success_outcome": "success",
        "assay_description": "live-cell microscopy and reporter quantification",
        "construct_name": "LNP-test-1",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "viability_percent",
            "value_num": 95.5,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "toxicity_signal",
            "value_num": 2.9,
            "unit": "AU",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v212",
        "item_id": "a1000000-0000-0000-0000-000000000053",
        "observation_type": "therapeutic_use",
        "biological_system_level": "primary_cells",
        "species": "human",
        "cell_type": "primary cortical neurons",
        "delivery_mode": "lentiviral transduction",
        "success_outcome": "success",
        "assay_description": "functional viability and localization assay",
        "construct_name": "LNP-test-2",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "viability_percent",
            "value_num": 60.2,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "toxicity_signal",
            "value_num": 0.41,
            "unit": "AU",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v213",
        "item_id": "a1000000-0000-0000-0000-000000000053",
        "observation_type": "failed_attempt",
        "biological_system_level": "organoid",
        "species": "human",
        "cell_type": "cerebral organoid",
        "delivery_mode": "electroporation",
        "success_outcome": "failed",
        "assay_description": "3D confocal imaging and qPCR",
        "construct_name": "LNP-test-3",
        "independent_lab_cluster_id": null,
        "metrics": [
          {
            "metric_name": "viability_percent",
            "value_num": 49.9,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "toxicity_signal",
            "value_num": 0.34,
            "unit": "AU",
            "qualifier": null
          }
        ]
      }
    ]
  },
  {
    "id": "a1000000-0000-0000-0000-000000000054",
    "slug": "electroporation",
    "canonical_name": "Electroporation pulse program",
    "item_type": "delivery_harness",
    "family": null,
    "summary": "Electroporation pulse program is included as a plausible toolkit component for benchmarking control of cell state using physical logic.",
    "status": "curated",
    "maturity_stage": "clinical",
    "first_publication_year": 1982,
    "primary_input_modality": "electrical",
    "primary_output_modality": "localization",
    "mechanisms": [],
    "techniques": [
      "delivery_optimization"
    ],
    "target_processes": [],
    "synonyms": [],
    "validation_rollup": {
      "has_cell_free_validation": false,
      "has_bacterial_validation": false,
      "has_mammalian_cell_validation": false,
      "has_mouse_in_vivo_validation": true,
      "has_human_clinical_validation": true,
      "has_therapeutic_use": true,
      "has_independent_replication": true
    },
    "replication_summary": {
      "score_version": "v1",
      "primary_paper_count": 1,
      "independent_primary_paper_count": 1,
      "distinct_last_author_clusters": 3,
      "distinct_institutions": 4,
      "distinct_biological_contexts": 3,
      "years_since_first_report": 44,
      "downstream_application_count": 1,
      "orphan_tool_flag": false,
      "practicality_penalties": [
        "cell-type-specific viability loss"
      ],
      "evidence_strength_score": 0.48,
      "replication_score": 0.67,
      "practicality_score": 0.85,
      "translatability_score": 0.12
    },
    "citations": [
      {
        "id": "c189",
        "source_document_id": "d189",
        "citation_role": "database_reference",
        "importance_rank": 1,
        "why_this_matters": "Convenient sequence or construct reference used by practitioners.",
        "document": {
          "id": "d189",
          "source_type": "database",
          "title": "ELECTROPORATION study 1",
          "doi": "10.1238/cell.2189.808",
          "pmid": "42454030",
          "publication_year": 2018,
          "journal_or_source": "Addgene / Benchling Registry",
          "is_retracted": false
        }
      },
      {
        "id": "c190",
        "source_document_id": "d190",
        "citation_role": "foundational",
        "importance_rank": 2,
        "why_this_matters": "Earliest practical report establishing the core architecture.",
        "document": {
          "id": "d190",
          "source_type": "database",
          "title": "ELECTROPORATION study 2",
          "doi": "10.2690/nbt.2190.347",
          "pmid": "8431708",
          "publication_year": 2018,
          "journal_or_source": "eLife",
          "is_retracted": false
        }
      }
    ],
    "validations": [
      {
        "id": "v214",
        "item_id": "a1000000-0000-0000-0000-000000000054",
        "observation_type": "mechanistic_demo",
        "biological_system_level": "mouse",
        "species": "Mus musculus",
        "cell_type": "hepatocyte",
        "delivery_mode": "AAV injection",
        "success_outcome": "success",
        "assay_description": "in vivo imaging and tissue harvest",
        "construct_name": "ELECTROPORATION-test-1",
        "independent_lab_cluster_id": "lab-4",
        "metrics": [
          {
            "metric_name": "viability_percent",
            "value_num": 94.2,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "toxicity_signal",
            "value_num": 1.59,
            "unit": "AU",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v215",
        "item_id": "a1000000-0000-0000-0000-000000000054",
        "observation_type": "therapeutic_use",
        "biological_system_level": "large_animal",
        "species": "Macaca mulatta",
        "cell_type": "retinal tissue",
        "delivery_mode": "intravitreal AAV injection",
        "success_outcome": "success",
        "assay_description": "biodistribution and safety panel",
        "construct_name": "ELECTROPORATION-test-2",
        "independent_lab_cluster_id": "lab-1",
        "metrics": [
          {
            "metric_name": "viability_percent",
            "value_num": 68.9,
            "unit": "%",
            "qualifier": null
          }
        ]
      },
      {
        "id": "v216",
        "item_id": "a1000000-0000-0000-0000-000000000054",
        "observation_type": "benchmark",
        "biological_system_level": "human_clinical",
        "species": "human",
        "cell_type": "solid tumor biopsy",
        "delivery_mode": "AAV local administration",
        "success_outcome": "success",
        "assay_description": "biopsy and circulating biomarker analysis",
        "construct_name": "ELECTROPORATION-test-3",
        "independent_lab_cluster_id": "lab-2",
        "metrics": [
          {
            "metric_name": "viability_percent",
            "value_num": 77.8,
            "unit": "%",
            "qualifier": null
          },
          {
            "metric_name": "toxicity_signal",
            "value_num": 1.64,
            "unit": "AU",
            "qualifier": null
          }
        ]
      }
    ]
  }
];

export const WORKFLOWS: WorkflowTemplate[] = [
  {
    "id": "w010",
    "slug": "3-hour-fast-screen",
    "name": "3-hour Fast Reporter Screen",
    "workflow_family": "fast_screen",
    "objective": "Rapidly compare switch variants in transient reporter format.",
    "throughput_class": "high",
    "recommended_for": "Early triage of light- or chemical-gated constructs in HEK293T cells.",
    "steps": [
      {
        "id": "ws100",
        "step_name": "Design reporter plate map",
        "step_type": "design",
        "duration_typical_hours": 0.5,
        "hands_on_hours": 0.5,
        "direct_cost_usd_typical": 10,
        "parallelizable": true,
        "failure_probability": 0.05,
        "input_artifact": "variant list",
        "output_artifact": "plate map"
      },
      {
        "id": "ws101",
        "step_name": "Transient transfection",
        "step_type": "transfection",
        "duration_typical_hours": 1.0,
        "hands_on_hours": 1.0,
        "direct_cost_usd_typical": 60,
        "parallelizable": true,
        "failure_probability": 0.15,
        "input_artifact": "DNA mixes",
        "output_artifact": "transfected cells"
      },
      {
        "id": "ws102",
        "step_name": "Assay and analysis",
        "step_type": "assay",
        "duration_typical_hours": 3.0,
        "hands_on_hours": 0.5,
        "direct_cost_usd_typical": 20,
        "parallelizable": true,
        "failure_probability": 0.08,
        "input_artifact": "transfected cells",
        "output_artifact": "ranked hits"
      }
    ]
  },
  {
    "id": "w011",
    "slug": "standard-construct-build",
    "name": "Standard Construct Build and Verify",
    "workflow_family": "standard_construct",
    "objective": "Assemble a single construct, verify sequence, and generate a first-pass functional readout.",
    "throughput_class": "low",
    "recommended_for": "Routine construct generation before moving into stable formats.",
    "steps": [
      {
        "id": "ws103",
        "step_name": "Design junctions and primers",
        "step_type": "design",
        "duration_typical_hours": 2,
        "hands_on_hours": 1.5,
        "direct_cost_usd_typical": 25,
        "parallelizable": false,
        "failure_probability": 0.08,
        "input_artifact": "domain architecture",
        "output_artifact": "primer plan"
      },
      {
        "id": "ws104",
        "step_name": "Order or synthesize DNA",
        "step_type": "dna_acquisition",
        "duration_typical_hours": 72,
        "hands_on_hours": 0.2,
        "direct_cost_usd_typical": 180,
        "parallelizable": false,
        "failure_probability": 0.03,
        "input_artifact": "primer plan",
        "output_artifact": "DNA fragments"
      },
      {
        "id": "ws105",
        "step_name": "Assembly reaction",
        "step_type": "assembly",
        "duration_typical_hours": 2,
        "hands_on_hours": 1.2,
        "direct_cost_usd_typical": 35,
        "parallelizable": false,
        "failure_probability": 0.12,
        "input_artifact": "DNA fragments",
        "output_artifact": "assembled plasmid"
      },
      {
        "id": "ws106",
        "step_name": "Bacterial transformation",
        "step_type": "transformation",
        "duration_typical_hours": 16,
        "hands_on_hours": 0.5,
        "direct_cost_usd_typical": 8,
        "parallelizable": true,
        "failure_probability": 0.06,
        "input_artifact": "assembled plasmid",
        "output_artifact": "colonies"
      },
      {
        "id": "ws107",
        "step_name": "Colony PCR screen",
        "step_type": "colony_screen",
        "duration_typical_hours": 3,
        "hands_on_hours": 1.0,
        "direct_cost_usd_typical": 18,
        "parallelizable": true,
        "failure_probability": 0.18,
        "input_artifact": "colonies",
        "output_artifact": "candidate clones"
      },
      {
        "id": "ws108",
        "step_name": "Sanger verification",
        "step_type": "sequence_verification",
        "duration_typical_hours": 24,
        "hands_on_hours": 0.4,
        "direct_cost_usd_typical": 35,
        "parallelizable": false,
        "failure_probability": 0.07,
        "input_artifact": "candidate clones",
        "output_artifact": "sequence-verified plasmid"
      },
      {
        "id": "ws109",
        "step_name": "Transient expression",
        "step_type": "expression",
        "duration_typical_hours": 24,
        "hands_on_hours": 0.7,
        "direct_cost_usd_typical": 55,
        "parallelizable": true,
        "failure_probability": 0.1,
        "input_artifact": "sequence-verified plasmid",
        "output_artifact": "expressing cells"
      },
      {
        "id": "ws110",
        "step_name": "Functional assay",
        "step_type": "assay",
        "duration_typical_hours": 4,
        "hands_on_hours": 1.2,
        "direct_cost_usd_typical": 40,
        "parallelizable": true,
        "failure_probability": 0.15,
        "input_artifact": "expressing cells",
        "output_artifact": "QC report"
      }
    ]
  },
  {
    "id": "w012",
    "slug": "library-selection-campaign",
    "name": "Library Selection Campaign",
    "workflow_family": "library_selection",
    "objective": "Run pooled diversification, enrichment, sequencing, and hit calling.",
    "throughput_class": "library_scale",
    "recommended_for": "Directed evolution of binders, switches, or linker regions.",
    "steps": [
      {
        "id": "ws111",
        "step_name": "Define library objective",
        "step_type": "design",
        "duration_typical_hours": 3,
        "hands_on_hours": 2,
        "direct_cost_usd_typical": 0,
        "parallelizable": false,
        "failure_probability": 0.05,
        "input_artifact": "target specification",
        "output_artifact": "library spec"
      },
      {
        "id": "ws112",
        "step_name": "Acquire degenerate oligos",
        "step_type": "dna_acquisition",
        "duration_typical_hours": 120,
        "hands_on_hours": 0.2,
        "direct_cost_usd_typical": 450,
        "parallelizable": false,
        "failure_probability": 0.02,
        "input_artifact": "library spec",
        "output_artifact": "oligo pool"
      },
      {
        "id": "ws113",
        "step_name": "Assemble pooled library",
        "step_type": "assembly",
        "duration_typical_hours": 6,
        "hands_on_hours": 4,
        "direct_cost_usd_typical": 350,
        "parallelizable": false,
        "failure_probability": 0.2,
        "input_artifact": "oligo pool",
        "output_artifact": "pooled plasmid library"
      },
      {
        "id": "ws114",
        "step_name": "Transform library host",
        "step_type": "transformation",
        "duration_typical_hours": 18,
        "hands_on_hours": 2,
        "direct_cost_usd_typical": 120,
        "parallelizable": false,
        "failure_probability": 0.18,
        "input_artifact": "pooled plasmid library",
        "output_artifact": "library cells"
      },
      {
        "id": "ws115",
        "step_name": "Selection round 1",
        "step_type": "selection_round",
        "duration_typical_hours": 20,
        "hands_on_hours": 4,
        "direct_cost_usd_typical": 500,
        "parallelizable": false,
        "failure_probability": 0.3,
        "input_artifact": "library cells",
        "output_artifact": "enriched pool 1"
      },
      {
        "id": "ws116",
        "step_name": "Selection round 2",
        "step_type": "selection_round",
        "duration_typical_hours": 20,
        "hands_on_hours": 4,
        "direct_cost_usd_typical": 500,
        "parallelizable": false,
        "failure_probability": 0.25,
        "input_artifact": "enriched pool 1",
        "output_artifact": "enriched pool 2"
      },
      {
        "id": "ws117",
        "step_name": "Sequence enriched pool",
        "step_type": "sequence_verification",
        "duration_typical_hours": 36,
        "hands_on_hours": 1.5,
        "direct_cost_usd_typical": 900,
        "parallelizable": true,
        "failure_probability": 0.08,
        "input_artifact": "enriched pool 2",
        "output_artifact": "NGS counts"
      },
      {
        "id": "ws118",
        "step_name": "Analyze enrichment",
        "step_type": "analysis",
        "duration_typical_hours": 8,
        "hands_on_hours": 3,
        "direct_cost_usd_typical": 250,
        "parallelizable": true,
        "failure_probability": 0.06,
        "input_artifact": "NGS counts",
        "output_artifact": "ranked variants"
      },
      {
        "id": "ws119",
        "step_name": "Go/no-go review",
        "step_type": "decision",
        "duration_typical_hours": 1,
        "hands_on_hours": 1,
        "direct_cost_usd_typical": 0,
        "parallelizable": false,
        "failure_probability": 0.05,
        "input_artifact": "ranked variants",
        "output_artifact": "campaign decision"
      }
    ]
  },
  {
    "id": "w013",
    "slug": "mouse-pilot-delivery",
    "name": "Mouse Pilot Delivery Study",
    "workflow_family": "in_vivo_pilot",
    "objective": "Package a lead construct and measure early in vivo delivery, activity, and safety.",
    "throughput_class": "single",
    "recommended_for": "Preclinical go/no-go after strong in vitro evidence.",
    "steps": [
      {
        "id": "ws120",
        "step_name": "Finalize payload design",
        "step_type": "design",
        "duration_typical_hours": 4,
        "hands_on_hours": 2,
        "direct_cost_usd_typical": 0,
        "parallelizable": false,
        "failure_probability": 0.05,
        "input_artifact": "lead construct",
        "output_artifact": "payload design"
      },
      {
        "id": "ws121",
        "step_name": "Package vector",
        "step_type": "packaging",
        "duration_typical_hours": 168,
        "hands_on_hours": 6,
        "direct_cost_usd_typical": 2800,
        "parallelizable": false,
        "failure_probability": 0.22,
        "input_artifact": "payload design",
        "output_artifact": "test article"
      },
      {
        "id": "ws122",
        "step_name": "Dose preparation",
        "step_type": "delivery",
        "duration_typical_hours": 2,
        "hands_on_hours": 1,
        "direct_cost_usd_typical": 120,
        "parallelizable": false,
        "failure_probability": 0.05,
        "input_artifact": "test article",
        "output_artifact": "dose syringes"
      },
      {
        "id": "ws123",
        "step_name": "Mouse administration",
        "step_type": "delivery",
        "duration_typical_hours": 4,
        "hands_on_hours": 4,
        "direct_cost_usd_typical": 900,
        "parallelizable": false,
        "failure_probability": 0.12,
        "input_artifact": "dose syringes",
        "output_artifact": "dosed mice"
      },
      {
        "id": "ws124",
        "step_name": "Expression window",
        "step_type": "expression",
        "duration_typical_hours": 336,
        "hands_on_hours": 0.5,
        "direct_cost_usd_typical": 0,
        "parallelizable": false,
        "failure_probability": 0.02,
        "input_artifact": "dosed mice",
        "output_artifact": "study animals"
      },
      {
        "id": "ws125",
        "step_name": "Terminal assay",
        "step_type": "assay",
        "duration_typical_hours": 10,
        "hands_on_hours": 5,
        "direct_cost_usd_typical": 700,
        "parallelizable": true,
        "failure_probability": 0.1,
        "input_artifact": "study animals",
        "output_artifact": "tissue panels"
      },
      {
        "id": "ws126",
        "step_name": "Data analysis",
        "step_type": "analysis",
        "duration_typical_hours": 12,
        "hands_on_hours": 4,
        "direct_cost_usd_typical": 350,
        "parallelizable": true,
        "failure_probability": 0.07,
        "input_artifact": "tissue panels",
        "output_artifact": "pilot report"
      }
    ]
  },
  {
    "id": "w014",
    "slug": "custom-organoid-imaging",
    "name": "Custom Organoid Imaging Workflow",
    "workflow_family": "custom",
    "objective": "Evaluate localization and toxicity in organoids under patterned stimulation.",
    "throughput_class": "medium",
    "recommended_for": "Spatial control systems that need microscopy-rich evidence.",
    "steps": [
      {
        "id": "ws127",
        "step_name": "Patterned stimulation design",
        "step_type": "design",
        "duration_typical_hours": 3,
        "hands_on_hours": 2,
        "direct_cost_usd_typical": 0,
        "parallelizable": false,
        "failure_probability": 0.08,
        "input_artifact": "experimental objective",
        "output_artifact": "stimulation plan"
      },
      {
        "id": "ws128",
        "step_name": "Prepare organoids",
        "step_type": "expression",
        "duration_typical_hours": 48,
        "hands_on_hours": 3,
        "direct_cost_usd_typical": 600,
        "parallelizable": false,
        "failure_probability": 0.12,
        "input_artifact": "cell stocks",
        "output_artifact": "ready organoids"
      },
      {
        "id": "ws129",
        "step_name": "Electroporate payloads",
        "step_type": "delivery",
        "duration_typical_hours": 3,
        "hands_on_hours": 2,
        "direct_cost_usd_typical": 140,
        "parallelizable": true,
        "failure_probability": 0.22,
        "input_artifact": "ready organoids",
        "output_artifact": "transduced organoids"
      },
      {
        "id": "ws130",
        "step_name": "Parallel imaging runs",
        "step_type": "assay",
        "duration_typical_hours": 12,
        "hands_on_hours": 4,
        "direct_cost_usd_typical": 480,
        "parallelizable": true,
        "failure_probability": 0.14,
        "input_artifact": "transduced organoids",
        "output_artifact": "image stacks"
      },
      {
        "id": "ws131",
        "step_name": "Segmentation and quantification",
        "step_type": "analysis",
        "duration_typical_hours": 10,
        "hands_on_hours": 3,
        "direct_cost_usd_typical": 160,
        "parallelizable": true,
        "failure_probability": 0.09,
        "input_artifact": "image stacks",
        "output_artifact": "organoid metrics"
      }
    ]
  },
  {
    "id": "w015",
    "slug": "cheap-cell-free-gate-check",
    "name": "Cheap Cell-Free Gate Check",
    "workflow_family": "fast_screen",
    "objective": "Check whether a switch architecture has any measurable dynamic range before cell work.",
    "throughput_class": "single",
    "recommended_for": "Very early feasibility and classroom-scale prototyping.",
    "steps": [
      {
        "id": "ws132",
        "step_name": "Assemble reporter mix",
        "step_type": "assembly",
        "duration_typical_hours": 1,
        "hands_on_hours": 1,
        "direct_cost_usd_typical": 18,
        "parallelizable": false,
        "failure_probability": 0.1,
        "input_artifact": "DNA templates",
        "output_artifact": "reaction mix"
      },
      {
        "id": "ws133",
        "step_name": "Run plate reader assay",
        "step_type": "assay",
        "duration_typical_hours": 2,
        "hands_on_hours": 0.3,
        "direct_cost_usd_typical": 22,
        "parallelizable": true,
        "failure_probability": 0.12,
        "input_artifact": "reaction mix",
        "output_artifact": "kinetics traces"
      },
      {
        "id": "ws134",
        "step_name": "Accept or discard",
        "step_type": "decision",
        "duration_typical_hours": 0.5,
        "hands_on_hours": 0.5,
        "direct_cost_usd_typical": 0,
        "parallelizable": false,
        "failure_probability": 0.05,
        "input_artifact": "kinetics traces",
        "output_artifact": "feasibility call"
      }
    ]
  },
  {
    "id": "w016",
    "slug": "clinical-biomarker-bridging",
    "name": "Clinical Biomarker Bridging Workflow",
    "workflow_family": "custom",
    "objective": "Bridge preclinical signal to biopsy and blood-based biomarker readouts in an early clinical setting.",
    "throughput_class": "low",
    "recommended_for": "Programs already operating with clinical samples and regulated assay support.",
    "steps": [
      {
        "id": "ws135",
        "step_name": "Protocol design",
        "step_type": "design",
        "duration_typical_hours": 12,
        "hands_on_hours": 6,
        "direct_cost_usd_typical": 0,
        "parallelizable": false,
        "failure_probability": 0.06,
        "input_artifact": "clinical question",
        "output_artifact": "protocol"
      },
      {
        "id": "ws136",
        "step_name": "Acquire biopsies and plasma",
        "step_type": "dna_acquisition",
        "duration_typical_hours": 72,
        "hands_on_hours": 2,
        "direct_cost_usd_typical": 1200,
        "parallelizable": false,
        "failure_probability": 0.1,
        "input_artifact": "protocol",
        "output_artifact": "clinical specimens"
      },
      {
        "id": "ws137",
        "step_name": "Sample accessioning",
        "step_type": "sequence_verification",
        "duration_typical_hours": 4,
        "hands_on_hours": 2,
        "direct_cost_usd_typical": 140,
        "parallelizable": true,
        "failure_probability": 0.03,
        "input_artifact": "clinical specimens",
        "output_artifact": "tracked specimens"
      },
      {
        "id": "ws138",
        "step_name": "Multiplex ELISA",
        "step_type": "assay",
        "duration_typical_hours": 8,
        "hands_on_hours": 4,
        "direct_cost_usd_typical": 650,
        "parallelizable": true,
        "failure_probability": 0.08,
        "input_artifact": "tracked specimens",
        "output_artifact": "protein panel"
      },
      {
        "id": "ws139",
        "step_name": "Targeted sequencing",
        "step_type": "sequence_verification",
        "duration_typical_hours": 24,
        "hands_on_hours": 4,
        "direct_cost_usd_typical": 1800,
        "parallelizable": true,
        "failure_probability": 0.09,
        "input_artifact": "tracked specimens",
        "output_artifact": "sequence panel"
      },
      {
        "id": "ws140",
        "step_name": "Integrated analysis",
        "step_type": "analysis",
        "duration_typical_hours": 16,
        "hands_on_hours": 6,
        "direct_cost_usd_typical": 950,
        "parallelizable": false,
        "failure_probability": 0.05,
        "input_artifact": "protein panel and sequence panel",
        "output_artifact": "bridged dataset"
      },
      {
        "id": "ws141",
        "step_name": "Decision review",
        "step_type": "decision",
        "duration_typical_hours": 2,
        "hands_on_hours": 2,
        "direct_cost_usd_typical": 0,
        "parallelizable": false,
        "failure_probability": 0.04,
        "input_artifact": "bridged dataset",
        "output_artifact": "clinical action memo"
      }
    ]
  }
];
