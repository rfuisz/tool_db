ALTER TABLE workflow_template
  ADD COLUMN IF NOT EXISTS protocol_family text,
  ADD COLUMN IF NOT EXISTS engineered_system_family text,
  ADD COLUMN IF NOT EXISTS why_workflow_works text,
  ADD COLUMN IF NOT EXISTS priority_logic text,
  ADD COLUMN IF NOT EXISTS validation_strategy text;

ALTER TABLE workflow_stage_template
  ADD COLUMN IF NOT EXISTS why_stage_exists text,
  ADD COLUMN IF NOT EXISTS decision_gate_reason text;

ALTER TABLE workflow_step_template
  ADD COLUMN IF NOT EXISTS step_order int,
  ADD COLUMN IF NOT EXISTS purpose text,
  ADD COLUMN IF NOT EXISTS why_this_step_now text,
  ADD COLUMN IF NOT EXISTS decision_gate_reason text,
  ADD COLUMN IF NOT EXISTS advance_criteria text,
  ADD COLUMN IF NOT EXISTS failure_criteria text,
  ADD COLUMN IF NOT EXISTS validation_focus text,
  ADD COLUMN IF NOT EXISTS target_property_axes text[] not null default '{}'::text[],
  ADD COLUMN IF NOT EXISTS target_mechanisms text[] not null default '{}'::text[],
  ADD COLUMN IF NOT EXISTS target_techniques text[] not null default '{}'::text[];

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'workflow_step_template_workflow_template_id_step_name_key'
  ) THEN
    ALTER TABLE workflow_step_template
      ADD CONSTRAINT workflow_step_template_workflow_template_id_step_name_key
      UNIQUE (workflow_template_id, step_name);
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS workflow_mechanism (
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  mechanism_name text not null,
  primary key (workflow_template_id, mechanism_name)
);

CREATE TABLE IF NOT EXISTS workflow_technique (
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  technique_name text not null,
  primary key (workflow_template_id, technique_name)
);

CREATE TABLE IF NOT EXISTS workflow_design_goal (
  id uuid primary key default gen_random_uuid(),
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  goal_name text not null,
  goal_kind text not null default 'property_axis',
  rationale text,
  source_document_id uuid references source_document(id) on delete set null,
  unique (workflow_template_id, goal_name, goal_kind)
);

CREATE TABLE IF NOT EXISTS workflow_item_role (
  id uuid primary key default gen_random_uuid(),
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  item_id uuid not null references toolkit_item(id) on delete cascade,
  role_name text not null,
  workflow_stage_template_id uuid references workflow_stage_template(id) on delete set null,
  workflow_step_template_id uuid references workflow_step_template(id) on delete set null,
  notes text,
  source_document_id uuid references source_document(id) on delete set null,
  unique (workflow_template_id, item_id, role_name, workflow_stage_template_id, workflow_step_template_id)
);

CREATE TABLE IF NOT EXISTS extracted_workflow_observation (
  id uuid primary key default gen_random_uuid(),
  packet_fingerprint text not null references extracted_packet(packet_fingerprint) on delete cascade,
  source_document_id uuid not null references source_document(id) on delete cascade,
  extraction_run_id uuid references extraction_run(id) on delete set null,
  packet_kind text not null,
  local_id text not null,
  workflow_local_id text,
  workflow_candidate_id uuid references extracted_item_candidate(id) on delete set null,
  workflow_objective text,
  protocol_family text,
  engineered_system_family text,
  target_property_axes text[] not null default '{}'::text[],
  target_mechanisms text[] not null default '{}'::text[],
  target_techniques text[] not null default '{}'::text[],
  why_workflow_works text,
  workflow_priority_logic text,
  validation_strategy text,
  decision_gate_strategy text,
  evidence_text text,
  source_locator jsonb not null default '{}'::jsonb,
  unresolved_ambiguities jsonb not null default '[]'::jsonb,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (packet_fingerprint, local_id)
);

CREATE INDEX IF NOT EXISTS extracted_workflow_observation_candidate_idx
  ON extracted_workflow_observation (workflow_candidate_id);

CREATE TABLE IF NOT EXISTS extracted_workflow_stage_observation (
  id uuid primary key default gen_random_uuid(),
  packet_fingerprint text not null references extracted_packet(packet_fingerprint) on delete cascade,
  source_document_id uuid not null references source_document(id) on delete cascade,
  extraction_run_id uuid references extraction_run(id) on delete set null,
  packet_kind text not null,
  local_id text not null,
  workflow_local_id text,
  workflow_candidate_id uuid references extracted_item_candidate(id) on delete set null,
  stage_name text not null,
  stage_kind text not null,
  stage_order int not null,
  search_modality text,
  input_candidate_count int,
  output_candidate_count int,
  candidate_unit text,
  selection_basis text,
  counterselection_basis text,
  enriches_for_axes text[] not null default '{}'::text[],
  guards_against_axes text[] not null default '{}'::text[],
  preserves_downstream_property_axes text[] not null default '{}'::text[],
  why_stage_exists text,
  advance_criteria text,
  decision_gate_reason text,
  bottleneck_risk text,
  higher_fidelity_than_previous boolean,
  source_locator jsonb not null default '{}'::jsonb,
  unresolved_ambiguities jsonb not null default '[]'::jsonb,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (packet_fingerprint, local_id)
);

CREATE INDEX IF NOT EXISTS extracted_workflow_stage_observation_candidate_idx
  ON extracted_workflow_stage_observation (workflow_candidate_id);

CREATE TABLE IF NOT EXISTS extracted_workflow_step_observation (
  id uuid primary key default gen_random_uuid(),
  packet_fingerprint text not null references extracted_packet(packet_fingerprint) on delete cascade,
  source_document_id uuid not null references source_document(id) on delete cascade,
  extraction_run_id uuid references extraction_run(id) on delete set null,
  packet_kind text not null,
  local_id text not null,
  workflow_local_id text,
  workflow_candidate_id uuid references extracted_item_candidate(id) on delete set null,
  workflow_observation_local_id text,
  stage_local_id text,
  stage_name text,
  step_name text not null,
  step_order int not null,
  step_type text,
  item_local_ids text[] not null default '{}'::text[],
  item_role text,
  purpose text,
  why_this_step_now text,
  decision_gate_reason text,
  advance_criteria text,
  failure_criteria text,
  validation_focus text,
  target_property_axes text[] not null default '{}'::text[],
  target_mechanisms text[] not null default '{}'::text[],
  target_techniques text[] not null default '{}'::text[],
  input_artifact text,
  output_artifact text,
  duration_hours double precision,
  queue_time_hours double precision,
  direct_cost_usd double precision,
  success boolean,
  source_locator jsonb not null default '{}'::jsonb,
  unresolved_ambiguities jsonb not null default '[]'::jsonb,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (packet_fingerprint, local_id)
);

CREATE INDEX IF NOT EXISTS extracted_workflow_step_observation_candidate_idx
  ON extracted_workflow_step_observation (workflow_candidate_id);
