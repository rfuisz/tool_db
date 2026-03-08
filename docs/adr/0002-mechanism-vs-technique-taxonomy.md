# ADR 0002: Separate Mechanism and Technique Taxonomies

## Status

Accepted

## Context

The original `mechanism_families` vocabulary mixed biophysical mechanisms (photocleavage, heterodimerization, conformational uncaging) with engineering methodology categories (computational design, selection/enrichment, sequence verification). These are fundamentally different kinds of concepts:

- A **mechanism** describes *how a molecular tool works* at the biophysical level.
- A **technique** describes *what category of engineering activity* a method-type item belongs to.

Lumping them together made the "Explore by mechanism" axis conceptually incoherent and would mislead users navigating by mechanism into expecting biophysical similarity where none exists.

## Decision

Split `mechanism_families` into two separate controlled vocabularies:

- `mechanism_families` — biophysical mechanisms only (heterodimerization, oligomerization, conformational uncaging, membrane recruitment, photocleavage, DNA binding, RNA binding, degradation, translation control).
- `technique_families` — engineering methodology categories (computational design, selection/enrichment, directed evolution, sequence verification, functional assay, structural characterization, delivery optimization).

Add a corresponding `item_technique` table in the canonical schema, parallel to `item_mechanism`. Update the viewer to expose "Explore by technique" as a separate navigation axis.

## Consequences

- Molecular tool items (protein_domain, multi_component_switch, rna_element) use `mechanisms`.
- Method-type items (engineering_method, computation_method, assay_method) use `techniques`.
- Some items may carry both (e.g., a delivery harness with a biophysical mechanism and an associated technique).
- The four top-level navigational axes for items are: mechanism, technique, component family, and validation context.
