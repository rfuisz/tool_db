---
id: item_licre
canonical_name: LiCre
item_type: multi_component_switch
status: curated
primary_input_modality: light
primary_output_modality: recombination
families:
  - recombinase
synonyms:
  - light-inducible Cre recombinase
last_reviewed: 2026-03-08
---

# LiCre

## Summary

`LiCre` is a single-chain optogenetic recombinase that uses an `AsLOV2` photosensor fused to a destabilized Cre variant to enable rapid blue-light activation.

## Mechanism

The founding paper describes `LiCre` as a single flavin-containing protein built from `AsLOV2` plus a Cre variant carrying destabilizing mutations, allowing light-dependent activation without an added small molecule.

## Inputs

- light

## Outputs

- recombinase activation
- light-controlled recombination

## Components

- `AsLOV2`
- destabilized Cre variant

## Validation Contexts

The founding paper reports successful use in yeast and in human cells, but the abstract does not specify the exact human cell model.

## Replication Notes

This item is currently anchored by its founding paper only. Independent reuse and context breadth should be treated as open curation work rather than assumed strength.

## Practical Limitations

Comparator systems are unnamed in the abstract, and the current curated slice does not yet capture dark leak magnitude, exact activation kinetics beyond "within minutes," or construct-specific deployment caveats.

## Ranked Citations

1. Foundational: 2021 eLife, "A single-chain and fast-responding light-inducible Cre recombinase as a novel optogenetic switch" (`10.7554/eLife.61268`)

## Open Questions

- Which split photo-Cre systems are the most relevant comparators for practical benchmarking?
- How stable is `LiCre` performance across different mammalian reporter architectures?
