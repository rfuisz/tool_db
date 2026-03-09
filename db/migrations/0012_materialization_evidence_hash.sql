-- Track evidence hash to skip re-materialization when nothing changed
ALTER TABLE toolkit_item
  ADD COLUMN IF NOT EXISTS materialization_evidence_hash text DEFAULT NULL;

COMMENT ON COLUMN toolkit_item.materialization_evidence_hash IS
  'SHA-256 of evidence inputs (claims, citations, validations) at last materialization. NULL means never materialized or pre-hash.';
