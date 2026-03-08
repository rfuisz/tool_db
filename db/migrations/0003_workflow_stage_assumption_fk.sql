ALTER TABLE workflow_assumption
  ADD COLUMN IF NOT EXISTS workflow_stage_template_id uuid;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'workflow_assumption_workflow_stage_template_id_fkey'
  ) THEN
    ALTER TABLE workflow_assumption
      ADD CONSTRAINT workflow_assumption_workflow_stage_template_id_fkey
      FOREIGN KEY (workflow_stage_template_id)
      REFERENCES workflow_stage_template(id)
      ON DELETE CASCADE;
  END IF;
END
$$;
