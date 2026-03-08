# Database Entry Extract v1

Convert one structured database entry into a `database_entry_extract_v1` packet.

## Rules

- Preserve the source record faithfully.
- Do not invent canonical IDs.
- Only emit claims directly supported by the entry fields.
- Use `unresolved_ambiguities` when the entry cannot be mapped cleanly into the current ontology.

## Output Contract

Validate against `schemas/extraction/database_entry_extract.v1.schema.json`.

## Harness Notes

- The caller caches JSON extraction responses against the full request payload, so prompt edits intentionally create a new cache key.
- Keep instructions deterministic and source-focused so repeated runs for the same job can reuse the cache safely.
