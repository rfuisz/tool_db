# ADR 0001: Evidence-First Foundation

## Status

Accepted

## Context

The domain is highly context-dependent. A tool can succeed in one host, fail in another, and later reappear in a different construct architecture or therapeutic context. Flat summary tables hide that reality and become difficult to trust.

## Decision

Model the repository around five intersecting layers:

1. toolkit items
2. claims and source evidence
3. validation contexts
4. replication and practicality rollups
5. DBTL workflow templates and observations

The canonical unit of truth is a source-backed claim evaluated in context. Summary booleans and public scores are derived outputs.

## Consequences

- Canonical schema is more verbose, but auditable.
- LLM extraction must land in typed intermediate packets first.
- Scoring functions need explicit breakdowns and versioning.
- Curation can resolve ambiguity without destroying provenance.
