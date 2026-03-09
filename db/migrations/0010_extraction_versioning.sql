-- Migration 0010: Extraction versioning, entity match cache, and staleness tracking
--
-- Adds extraction_version to first-pass tables so we know which pipeline version
-- produced each row.  Adds derived_version to item_facet (which was missing it).
-- Creates entity_match_cache for persisting entity-resolution results across runs.
-- Backfills legacy rows with version stamps.

-- 1. Add extraction_version to extracted_item_candidate and extracted_claim_candidate
ALTER TABLE extracted_item_candidate
  ADD COLUMN IF NOT EXISTS extraction_version text;

ALTER TABLE extracted_claim_candidate
  ADD COLUMN IF NOT EXISTS extraction_version text;

-- 2. Add derived_version to item_facet (other derived tables already have it)
ALTER TABLE item_facet
  ADD COLUMN IF NOT EXISTS derived_version text;

-- 3. Backfill extraction_version on existing rows.
--    Rows with non-trivial freeform_explainers in raw_payload → extract_v2.
--    All others → extract_v1 (legacy).
UPDATE extracted_item_candidate
SET extraction_version = CASE
  WHEN raw_payload IS NOT NULL
    AND raw_payload ? 'freeform_explainers'
    AND raw_payload->>'freeform_explainers' IS DISTINCT FROM '{}'
    AND raw_payload->>'freeform_explainers' IS DISTINCT FROM 'null'
    AND raw_payload->>'freeform_explainers' IS DISTINCT FROM ''
  THEN 'extract_v2'
  ELSE 'extract_v1'
END
WHERE extraction_version IS NULL;

UPDATE extracted_claim_candidate
SET extraction_version = 'extract_v1'
WHERE extraction_version IS NULL;

-- 4. Backfill derived_version on item_facet where missing
UPDATE item_facet
SET derived_version = 'v1'
WHERE derived_version IS NULL;

-- 5. Entity match cache — persists slug → matched_item resolution across runs.
--    Invalidate when new toolkit_items are added or names/synonyms change.
CREATE TABLE IF NOT EXISTS entity_match_cache (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_slug text NOT NULL,
  candidate_name_norm text NOT NULL,
  candidate_aliases_hash text NOT NULL DEFAULT '',
  matched_item_id uuid REFERENCES toolkit_item(id) ON DELETE CASCADE,
  matched_slug text,
  match_method text,
  resolution_status text NOT NULL DEFAULT 'new_candidate',
  items_snapshot_count int NOT NULL DEFAULT 0,
  cached_at timestamptz NOT NULL DEFAULT now(),
  invalidated_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (candidate_slug, candidate_name_norm, candidate_aliases_hash)
);

-- Attach updated_at trigger (reusing the function from migration 0009)
DROP TRIGGER IF EXISTS trg_set_updated_at ON entity_match_cache;
CREATE TRIGGER trg_set_updated_at
  BEFORE UPDATE ON entity_match_cache
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 6. Populate extraction_run.prompt_version where still null
UPDATE extraction_run
SET prompt_version = 'unknown_legacy'
WHERE prompt_version IS NULL;
