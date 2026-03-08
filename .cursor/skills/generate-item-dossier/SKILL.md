---
name: generate-item-dossier
description: Generates or updates a toolkit item dossier from schema-backed evidence inputs. Use when creating `knowledge/items/*` artifacts, summarizing claims, ranking citations, or rolling validation and workflow evidence into a curator-friendly dossier.
---

# Generate Item Dossier

## Quick Start

When working on an item dossier:

1. Read the canonical item metadata and any existing dossier files.
2. Keep claims, contexts, and citations traceable to source-backed evidence.
3. Separate replication notes from practicality notes.
4. Prefer explicit evidence gaps over guessed summaries.

## Required Outputs

- `index.md` with stable sections
- `structured.yaml` with normalized seed fields
- ranked citations or explicit citation gaps
- validation and workflow-fit notes tied to evidence boundaries

## Guardrails

- Do not invent canonical IDs.
- Do not collapse contradictory evidence into a single positive summary.
- Do not label a public score without showing its breakdown inputs.
