---
id: item_phyb_pif
canonical_name: PhyB/PIF
item_type: multi_component_switch
status: curated
primary_input_modality: light
primary_output_modality: signaling
families:
  - phytochrome
synonyms:
  - PhyB-PIF
  - phytochrome B / phytochrome-interacting factor
last_reviewed: 2026-03-08
---

# PhyB/PIF

## Summary

`PhyB/PIF` is a red/far-red light-inducible interaction system. This dossier is currently grounded by a mammalian enablement paper that supports genetically encoded signaling control without exogenous chromophore supply.

## Mechanism

The system uses light-regulated interaction between `PhyB` and `PIF` to control recruitment or signaling outputs, with practical performance depending on chromophore availability.

## Inputs

- light

## Outputs

- inducible interaction
- signaling control

## Components

- `PhyB`
- `PIF`

## Validation Contexts

The currently curated paper supports mammalian-cell use with an internal PCB-synthesis cassette, but does not identify a specific cell line in the abstract.

## Replication Notes

This item is useful to surface now, but replication and canonical history remain incomplete until the original `PhyB/PIF` switch-defining literature is curated into the dossier.

## Practical Limitations

Chromophore supply is a first-class practicality constraint for this system. The current evidence slice focuses on mammalian enablement rather than broad comparative deployment.

## Ranked Citations

1. Mammalian enablement: 2017 PNAS, "Efficient synthesis of phycocyanobilin in mammalian cells for optogenetic control of cell signaling" (`10.1073/pnas.1707190114`)
2. `TODO`: add the original switch-defining `PhyB/PIF` paper

## Open Questions

- Which founding `PhyB/PIF` paper should anchor the canonical origin citation?
- How large is the practical penalty from chromophore supply in different host contexts?
