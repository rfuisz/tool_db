-- Migration 0009: Add updated_at tracking to all tables + sync_watermark
-- Enables incremental sync by letting us query "rows changed since time T".

-- 1. Reusable trigger function
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Add updated_at to tables that lack it (skip schema_migration)
DO $$
DECLARE
    tbl TEXT;
    tables_to_update TEXT[] := ARRAY[
        'assay_method_profile',
        'claim_metric',
        'claim_subject_link',
        'computation_method_profile',
        'engineering_method_profile',
        'extracted_claim',
        'extracted_claim_candidate',
        'extracted_claim_subject_candidate',
        'extracted_item_candidate',
        'extracted_packet',
        'extracted_workflow_observation',
        'extracted_workflow_stage_observation',
        'extracted_workflow_step_observation',
        'extraction_run',
        'gap_capability',
        'gap_capability_resource',
        'gap_field',
        'gap_item',
        'gap_item_capability',
        'gap_resource',
        'item_citation',
        'item_component',
        'item_facet',
        'item_gap_link',
        'item_mechanism',
        'item_property_value',
        'item_related_item',
        'item_synonym',
        'item_target_process',
        'item_technique',
        'property_definition',
        'protein_domain_profile',
        'replication_summary',
        'source_chunk',
        'source_document',
        'switch_profile',
        'validation_metric_value',
        'validation_observation',
        'workflow_assumption',
        'workflow_design_goal',
        'workflow_edge',
        'workflow_instance_observation',
        'workflow_item_role',
        'workflow_mechanism',
        'workflow_stage_template',
        'workflow_step_template',
        'workflow_technique',
        'workflow_template'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables_to_update LOOP
        EXECUTE format(
            'ALTER TABLE %I ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()',
            tbl
        );
    END LOOP;
END $$;

-- 3. Attach set_updated_at trigger to ALL tables with updated_at
--    (includes the 4 that already had it + the 48 just added)
DO $$
DECLARE
    tbl TEXT;
    all_tracked TEXT[] := ARRAY[
        'assay_method_profile',
        'claim_metric',
        'claim_subject_link',
        'computation_method_profile',
        'engineering_method_profile',
        'extracted_claim',
        'extracted_claim_candidate',
        'extracted_claim_subject_candidate',
        'extracted_item_candidate',
        'extracted_packet',
        'extracted_workflow_observation',
        'extracted_workflow_stage_observation',
        'extracted_workflow_step_observation',
        'extraction_run',
        'gap_capability',
        'gap_capability_resource',
        'gap_field',
        'gap_item',
        'gap_item_capability',
        'gap_resource',
        'item_citation',
        'item_comparison',
        'item_component',
        'item_explainer',
        'item_facet',
        'item_gap_link',
        'item_mechanism',
        'item_problem_link',
        'item_property_value',
        'item_related_item',
        'item_synonym',
        'item_target_process',
        'item_technique',
        'property_definition',
        'protein_domain_profile',
        'replication_summary',
        'source_chunk',
        'source_document',
        'switch_profile',
        'toolkit_item',
        'validation_metric_value',
        'validation_observation',
        'workflow_assumption',
        'workflow_design_goal',
        'workflow_edge',
        'workflow_instance_observation',
        'workflow_item_role',
        'workflow_mechanism',
        'workflow_stage_template',
        'workflow_step_template',
        'workflow_technique',
        'workflow_template'
    ];
BEGIN
    FOREACH tbl IN ARRAY all_tracked LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_set_updated_at ON %I',
            tbl
        );
        EXECUTE format(
            'CREATE TRIGGER trg_set_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION set_updated_at()',
            tbl
        );
    END LOOP;
END $$;

-- 4. Sync watermark table (lives on both local and Render; Render's copy tracks last sync time)
CREATE TABLE IF NOT EXISTS sync_watermark (
    id TEXT PRIMARY KEY DEFAULT 'default',
    last_synced_at TIMESTAMPTZ NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
INSERT INTO sync_watermark (id, last_synced_at)
VALUES ('default', '1970-01-01T00:00:00Z')
ON CONFLICT DO NOTHING;
