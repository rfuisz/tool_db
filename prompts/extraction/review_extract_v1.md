# Review Extract v1

Convert one review or synthesis source into a `review_extract_v1` packet.

## Rules

- Extract broad, source-backed summaries and candidate toolkit items.
- Do not invent experiment-level validation observations that are not directly stated in the review.
- Use `recommended_seed_item_local_ids` only for entities that appear central enough to seed curation.
- If the source lacks enough detail to support extraction, leave arrays empty and explain the evidence boundary in `unresolved_ambiguities`.

## Output Contract

Validate against `schemas/extraction/review_extract.v1.schema.json`.
