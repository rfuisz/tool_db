# Database Entry Extract v1

Convert one structured database entry into a `database_entry_extract_v1` packet.

## Rules

- Preserve the source record faithfully.
- Do not invent canonical IDs.
- Only emit claims directly supported by the entry fields.
- Use `unresolved_ambiguities` when the entry cannot be mapped cleanly into the current ontology.

## Output Contract

Validate against `schemas/extraction/database_entry_extract.v1.schema.json`.
