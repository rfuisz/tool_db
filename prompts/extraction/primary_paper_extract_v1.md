# Primary Paper Extract v1

Convert one literature source into a `primary_paper_extract_v1` packet.

## Rules

- Extract only source-backed claims.
- Keep claims, contexts, metrics, and validation observations separate.
- Use empty arrays rather than invented content when the source text is insufficient.
- Put any unresolved merge, subject, or context uncertainty into `unresolved_ambiguities`.

## Output Contract

Validate against `schemas/extraction/primary_paper_extract.v1.schema.json`.
