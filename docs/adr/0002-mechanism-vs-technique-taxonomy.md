# ADR 0002: Separate Mechanism and Technique Taxonomies

## Status

Accepted

## Context

The original `mechanism_families` vocabulary mixed biophysical mechanisms (photocleavage, heterodimerization, conformational uncaging) with engineering methodology categories (computational design, selection/enrichment, sequence verification). These are fundamentally different kinds of concepts:

- A **mechanism** describes *how a molecular tool works* at the biophysical level.
- A **technique** describes *what category of engineering activity* a method-type item belongs to.

Lumping them together made the "Explore by mechanism" axis conceptually incoherent and would mislead users navigating by mechanism into expecting biophysical similarity where none exists.

## Decision

Split `mechanism_families` into two separate controlled vocabularies, and treat them as different hierarchies rather than sibling browse facets:

- `mechanism_families` — biophysical mechanisms only (heterodimerization, oligomerization, conformational uncaging, membrane recruitment, photocleavage, DNA binding, RNA binding, degradation, translation control).
- `technique_families` — engineering methodology categories (computational design, selection/enrichment, directed evolution, sequence verification, functional assay, structural characterization, delivery optimization).

Add a corresponding `item_technique` table in the canonical schema, parallel to `item_mechanism`. Update the viewer to expose "Explore by technique" as a separate navigation axis.

The collection model is therefore two-axis beneath workflows:

- **Mechanism branch** — `mechanism -> architecture -> component`
- **Technique branch** — high-level engineering practice / approach -> concrete method

In this framing:

- Mechanisms are the highest-level composition concepts.
- Architectures are composed arrangements that realize one or more mechanisms.
- Components are the lowest-level parts or sequence-defined elements used within architectures.
- Techniques describe high-level engineering practices or approaches.
- Methods are concrete engineering methods, computational methods, and assay methods.
- Delivery strategies are grouped with the mechanism branch as deployment architectures rather than with methods.
- Workflows are where technique choices are applied to build, validate, or operationalize a target composition.

## Consequences

- Mechanism-branch item types map to the lower mechanism layers:
- `protein_domain` and `rna_element` belong to the `component` layer.
- `multi_component_switch`, `construct_pattern`, and `delivery_harness` belong to the `architecture` layer.
- Technique-branch item types map to the `method` layer:
- `engineering_method`, `computation_method`, and `assay_method` are methods.
- Mechanisms should be presented above architecture and component classes in UX and documentation, not merely as another filter beside them.
- Workflows should be explained as the place where a technique is used to obtain, screen, measure, or deliver an engineered composition.
