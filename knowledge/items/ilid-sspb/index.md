---
id: item_ilid_sspb
canonical_name: iLID/SspB
item_type: multi_component_switch
status: curated
primary_input_modality: light
primary_output_modality: signaling
families:
  - LOV
synonyms:
  - iLID
  - improved light inducible dimer
last_reviewed: 2026-03-08
---

# iLID/SspB

## Summary

iLID/SspB is a blue-light-inducible interaction switch built by embedding the SsrA peptide inside the `AsLOV2` C-terminal helix and using `SspB` as the light-enabled binding partner.

## Mechanism

In the dark, the embedded SsrA motif is sterically constrained. Blue-light activation undocks the `AsLOV2` C-terminal helix and exposes SsrA for `SspB` binding.

## Inputs

- light

## Outputs

- inducible interaction
- conditional recruitment
- reversible signaling control

## Components

- `AsLOV2`
- `SsrA peptide`
- `SspB`

## Validation Contexts

The founding paper reports functional utility in mammalian cell culture for subcellular localization and reversible control of small GTPase signaling, but the abstract does not name the exact cell line.

## Replication Notes

The dossier currently has one founding engineering paper plus one comparative characterization paper. Replication scoring should stay conservative until more independent downstream use is curated.

## Practical Limitations

Current evidence is abstract-level only for this dossier slice, so exact host sensitivity, dark leak, off-kinetics, and construct-geometry penalties still need fuller curation.

## Ranked Citations

1. Foundational: 2014 PNAS, "Engineering an improved light-induced dimer (iLID) for controlling the localization and activity of signaling proteins" (`10.1073/pnas.1417910112`)
2. Benchmark: 2015 ACS Synthetic Biology, "Correlating in Vitro and in Vivo Activities of Light-Inducible Dimers: A Cellular Optogenetics Guide" (`10.1021/acssynbio.5b00119`)

## Open Questions

- How robust is `iLID/SspB` across different effector fusions and subcellular destinations?
- Which construct topologies most strongly affect dark-state leak and response range?
