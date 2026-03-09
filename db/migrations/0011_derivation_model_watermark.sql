-- Track which LLM model (if any) generated derived content.
-- Combined with derived_version, this lets the pipeline detect stale rows
-- when either the derivation logic OR the model changes.

ALTER TABLE item_explainer
  ADD COLUMN IF NOT EXISTS derivation_model text DEFAULT NULL;

ALTER TABLE replication_summary
  ADD COLUMN IF NOT EXISTS derivation_model text DEFAULT NULL;

ALTER TABLE item_comparison
  ADD COLUMN IF NOT EXISTS derivation_model text DEFAULT NULL;

ALTER TABLE item_problem_link
  ADD COLUMN IF NOT EXISTS derivation_model text DEFAULT NULL;

ALTER TABLE toolkit_item
  ADD COLUMN IF NOT EXISTS summary_derivation_model text DEFAULT NULL;

COMMENT ON COLUMN item_explainer.derivation_model IS
  'LLM model that generated the body text, or NULL for heuristic/rule-based derivation.';

COMMENT ON COLUMN toolkit_item.summary_derivation_model IS
  'LLM model that generated the summary, or NULL for extraction-derived summaries.';
