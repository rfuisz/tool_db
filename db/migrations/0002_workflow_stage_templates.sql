DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type
    WHERE typname = 'workflow_stage_kind'
  ) THEN
    CREATE TYPE workflow_stage_kind AS ENUM (
      'in_silico_filter',
      'library_design',
      'library_build',
      'broad_screen',
      'selection',
      'counter_screen',
      'recovery',
      'sequencing_readout',
      'hit_picking',
      'functional_characterization',
      'secondary_characterization',
      'confirmatory_validation',
      'in_vivo_validation',
      'decision_gate'
    );
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_type
    WHERE typname = 'workflow_search_modality'
  ) THEN
    CREATE TYPE workflow_search_modality AS ENUM (
      'in_silico',
      'display',
      'pooled_library',
      'cell_free',
      'cell_based',
      'biochemical',
      'sequencing',
      'structural',
      'animal'
    );
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS workflow_stage_template (
  id uuid primary key default gen_random_uuid(),
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  stage_name text not null,
  stage_kind workflow_stage_kind not null,
  stage_order int not null,
  search_modality workflow_search_modality,
  input_candidate_count_typical int,
  output_candidate_count_typical int,
  candidate_unit text,
  selection_basis text,
  counterselection_basis text,
  enriches_for_axes text[] not null default '{}'::text[],
  guards_against_axes text[] not null default '{}'::text[],
  preserves_downstream_property_axes text[] not null default '{}'::text[],
  advance_criteria text,
  bottleneck_risk text,
  higher_fidelity_than_previous boolean,
  notes text,
  unique (workflow_template_id, stage_order)
);

ALTER TABLE workflow_step_template
  ADD COLUMN IF NOT EXISTS workflow_stage_template_id uuid;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'workflow_step_template_workflow_stage_template_id_fkey'
  ) THEN
    ALTER TABLE workflow_step_template
      ADD CONSTRAINT workflow_step_template_workflow_stage_template_id_fkey
      FOREIGN KEY (workflow_stage_template_id)
      REFERENCES workflow_stage_template(id)
      ON DELETE SET NULL;
  END IF;
END
$$;
