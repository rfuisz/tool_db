create extension if not exists pgcrypto;
create extension if not exists vector;

create type item_type as enum (
  'protein_domain',
  'multi_component_switch',
  'rna_element',
  'construct_pattern',
  'engineering_method',
  'assay_method',
  'computation_method',
  'delivery_harness'
);

create type item_status as enum ('seed', 'normalized', 'curated', 'deprecated');
create type maturity_stage as enum ('research', 'preclinical', 'clinical', 'deployed');
create type modality as enum (
  'light',
  'chemical',
  'thermal',
  'electrical',
  'mechanical',
  'magnetic',
  'sequence',
  'structure',
  'conformational_change',
  'transcription',
  'translation',
  'localization',
  'degradation',
  'signaling',
  'recombination',
  'editing',
  'selection',
  'assay_readout',
  'analysis'
);

create type property_value_type as enum ('bool', 'int', 'float', 'text', 'enum', 'json');
create type source_type as enum (
  'review',
  'primary_paper',
  'trial_record',
  'database_entry',
  'protocol',
  'benchmark',
  'preprint'
);
create type claim_polarity as enum ('supports', 'contradicts', 'mixed', 'neutral');
create type citation_role as enum (
  'foundational',
  'best_review',
  'independent_validation',
  'benchmark',
  'protocol',
  'therapeutic',
  'negative_result',
  'structural',
  'database_reference'
);
create type observation_type as enum (
  'mechanistic_demo',
  'application_demo',
  'benchmark',
  'therapeutic_use',
  'manufacturing_use',
  'failed_attempt'
);
create type biological_system_level as enum (
  'cell_free',
  'bacteria',
  'yeast',
  'mammalian_cell_line',
  'primary_cells',
  'organoid',
  'mouse',
  'large_animal',
  'human_clinical'
);
create type success_outcome as enum ('success', 'mixed', 'failed');
create type workflow_family as enum (
  'fast_screen',
  'standard_construct',
  'library_selection',
  'in_vivo_pilot',
  'custom'
);
create type throughput_class as enum ('single', 'low', 'medium', 'high', 'library_scale');
create type workflow_step_type as enum (
  'design',
  'dna_acquisition',
  'assembly',
  'transformation',
  'colony_screen',
  'sequence_verification',
  'transfection',
  'expression',
  'selection_round',
  'assay',
  'analysis',
  'decision',
  'packaging',
  'delivery'
);
create type workflow_stage_kind as enum (
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
create type workflow_search_modality as enum (
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

create table toolkit_item (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  canonical_name text not null,
  item_type item_type not null,
  family text,
  summary text,
  status item_status not null default 'seed',
  maturity_stage maturity_stage not null default 'research',
  first_publication_year int,
  primary_input_modality modality,
  primary_output_modality modality,
  external_ids jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table protein_domain_profile (
  item_id uuid primary key references toolkit_item(id) on delete cascade,
  source_organism text,
  domain_family text,
  monomeric_or_oligomeric text,
  requires_exogenous_cofactor boolean,
  cofactor_name text,
  spectral_min_nm numeric(6,2),
  spectral_max_nm numeric(6,2),
  reversible boolean,
  genetic_payload_bp_estimate int,
  notes text
);

create table switch_profile (
  item_id uuid primary key references toolkit_item(id) on delete cascade,
  partner_requirement text,
  component_count int,
  switching_mode text,
  default_state text,
  recovery_mode text,
  dark_state_behavior text
);

create table engineering_method_profile (
  item_id uuid primary key references toolkit_item(id) on delete cascade,
  method_family text,
  display_or_selection_mode text,
  library_type text,
  genotype_phenotype_linkage text,
  typical_rounds int,
  readout_mode text,
  throughput_class throughput_class
);

create table computation_method_profile (
  item_id uuid primary key references toolkit_item(id) on delete cascade,
  method_family text,
  input_artifact_type text,
  output_artifact_type text,
  gpu_required boolean,
  inference_scale text,
  design_stage text,
  deterministic_or_stochastic text
);

create table assay_method_profile (
  item_id uuid primary key references toolkit_item(id) on delete cascade,
  assay_family text,
  resolution_type text,
  throughput_class throughput_class,
  sample_type text,
  outsourceable boolean
);

create table property_definition (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  applies_to_item_type item_type,
  value_type property_value_type not null,
  unit text,
  controlled_vocabulary text,
  description text not null
);

create table item_property_value (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  property_id uuid not null references property_definition(id) on delete cascade,
  value_bool boolean,
  value_int bigint,
  value_float double precision,
  value_text text,
  value_json jsonb,
  source_claim_id uuid,
  confidence numeric(4,3),
  unique (item_id, property_id, source_claim_id)
);

create table item_synonym (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  synonym text not null,
  source_document_id uuid,
  unique (item_id, synonym)
);

create table item_component (
  id uuid primary key default gen_random_uuid(),
  parent_item_id uuid not null references toolkit_item(id) on delete cascade,
  component_item_id uuid not null references toolkit_item(id) on delete restrict,
  component_role text,
  stoichiometry text,
  notes text
);

create table item_mechanism (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  mechanism_name text not null,
  evidence_note text
);

create table item_technique (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  technique_name text not null,
  evidence_note text
);

create table item_target_process (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  target_process text not null
);

create table item_related_item (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  related_item_id uuid not null references toolkit_item(id) on delete cascade,
  relation_type text not null,
  notes text
);

create table item_facet (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  facet_name text not null,
  facet_value text not null,
  evidence_note text,
  unique (item_id, facet_name, facet_value)
);

create table item_explainer (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  explainer_kind text not null,
  title text,
  body text not null,
  evidence_payload jsonb not null default '{}'::jsonb,
  derived_version text not null default 'v1',
  updated_at timestamptz not null default now(),
  unique (item_id, explainer_kind)
);

create table item_comparison (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  related_item_id uuid not null references toolkit_item(id) on delete cascade,
  relation_type text not null,
  summary text not null,
  strengths jsonb not null default '[]'::jsonb,
  weaknesses jsonb not null default '[]'::jsonb,
  overlap_reasons jsonb not null default '[]'::jsonb,
  evidence_payload jsonb not null default '{}'::jsonb,
  derived_version text not null default 'v1',
  updated_at timestamptz not null default now(),
  unique (item_id, related_item_id, relation_type)
);

create table source_document (
  id uuid primary key default gen_random_uuid(),
  source_type source_type not null,
  title text not null,
  doi text,
  pmid text,
  pmcid text,
  openalex_id text,
  semantic_scholar_id text,
  nct_id text,
  publication_year int,
  journal_or_source text,
  abstract_text text,
  fulltext_license_status text,
  is_retracted boolean not null default false,
  retraction_metadata jsonb not null default '{}'::jsonb,
  raw_payload_ref text,
  created_at timestamptz not null default now()
);

create table source_chunk (
  id uuid primary key default gen_random_uuid(),
  source_document_id uuid not null references source_document(id) on delete cascade,
  chunk_index int not null,
  text text not null,
  section_label text,
  page_or_locator text,
  embedding vector(1536),
  unique (source_document_id, chunk_index)
);

create table extraction_run (
  id uuid primary key default gen_random_uuid(),
  source_document_id uuid references source_document(id) on delete cascade,
  packet_kind text not null,
  schema_version text not null,
  model_name text,
  prompt_version text,
  status text not null default 'completed',
  raw_payload_ref text,
  created_at timestamptz not null default now()
);

create table extracted_claim (
  id uuid primary key default gen_random_uuid(),
  source_document_id uuid not null references source_document(id) on delete cascade,
  source_chunk_id uuid references source_chunk(id) on delete set null,
  extraction_run_id uuid references extraction_run(id) on delete set null,
  claim_type text not null,
  claim_text_normalized text not null,
  polarity claim_polarity not null default 'neutral',
  confidence_model numeric(4,3),
  confidence_curator numeric(4,3),
  needs_review boolean not null default true,
  context jsonb not null default '{}'::jsonb,
  source_locator jsonb not null default '{}'::jsonb,
  unresolved_ambiguities jsonb not null default '[]'::jsonb
);

create table claim_subject_link (
  id uuid primary key default gen_random_uuid(),
  claim_id uuid not null references extracted_claim(id) on delete cascade,
  item_id uuid not null references toolkit_item(id) on delete cascade,
  subject_role text not null
);

alter table item_property_value
  add constraint item_property_value_source_claim_fk
  foreign key (source_claim_id) references extracted_claim(id) on delete set null;

alter table item_synonym
  add constraint item_synonym_source_document_fk
  foreign key (source_document_id) references source_document(id) on delete set null;

create table claim_metric (
  id uuid primary key default gen_random_uuid(),
  claim_id uuid not null references extracted_claim(id) on delete cascade,
  metric_name text not null,
  operator text,
  value_num double precision,
  value_text text,
  unit text,
  condition_text text
);

create table item_citation (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  source_document_id uuid not null references source_document(id) on delete cascade,
  citation_role citation_role not null,
  importance_rank int not null,
  why_this_matters text not null,
  unique (item_id, source_document_id, citation_role)
);

create table validation_observation (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  source_document_id uuid not null references source_document(id) on delete cascade,
  construct_name text,
  observation_type observation_type not null,
  biological_system_level biological_system_level not null,
  species text,
  strain_or_model text,
  cell_type text,
  tissue text,
  subcellular_target text,
  delivery_mode text,
  cargo_or_effector text,
  success_outcome success_outcome not null,
  assay_description text,
  independent_lab_cluster_id text,
  institution_cluster_id text,
  notes text,
  source_locator jsonb not null default '{}'::jsonb
);

create table validation_metric_value (
  id uuid primary key default gen_random_uuid(),
  validation_observation_id uuid not null references validation_observation(id) on delete cascade,
  metric_name text not null,
  value_num double precision,
  unit text,
  qualifier text,
  condition_text text
);

create table replication_summary (
  item_id uuid primary key references toolkit_item(id) on delete cascade,
  score_version text not null,
  primary_paper_count int not null default 0,
  independent_primary_paper_count int not null default 0,
  distinct_last_author_clusters int not null default 0,
  distinct_institutions int not null default 0,
  distinct_biological_contexts int not null default 0,
  years_since_first_report int,
  downstream_application_count int not null default 0,
  review_to_primary_ratio numeric(8,3),
  same_lab_fraction numeric(8,3),
  contradiction_count int not null default 0,
  retraction_or_correction_count int not null default 0,
  implementation_count_external int,
  orphan_tool_flag boolean not null default false,
  practicality_penalties jsonb not null default '[]'::jsonb,
  evidence_strength_score numeric(8,3),
  replication_score numeric(8,3),
  practicality_score numeric(8,3),
  translatability_score numeric(8,3),
  computed_at timestamptz not null default now(),
  explanation jsonb not null default '{}'::jsonb
);

create table workflow_template (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  workflow_family workflow_family not null,
  objective text not null,
  throughput_class throughput_class,
  protocol_family text,
  engineered_system_family text,
  why_workflow_works text,
  priority_logic text,
  validation_strategy text,
  recommended_for text,
  default_parallelization_assumption text,
  notes text
);

create table workflow_stage_template (
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
  why_stage_exists text,
  advance_criteria text,
  decision_gate_reason text,
  bottleneck_risk text,
  higher_fidelity_than_previous boolean,
  notes text,
  unique (workflow_template_id, stage_order)
);

create table workflow_step_template (
  id uuid primary key default gen_random_uuid(),
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  workflow_stage_template_id uuid references workflow_stage_template(id) on delete set null,
  step_name text not null,
  step_order int,
  step_type workflow_step_type not null,
  purpose text,
  why_this_step_now text,
  decision_gate_reason text,
  advance_criteria text,
  failure_criteria text,
  validation_focus text,
  target_property_axes text[] not null default '{}'::text[],
  target_mechanisms text[] not null default '{}'::text[],
  target_techniques text[] not null default '{}'::text[],
  duration_p10_hours numeric(10,2),
  duration_typical_hours numeric(10,2),
  duration_p90_hours numeric(10,2),
  queue_time_typical_hours numeric(10,2),
  hands_on_hours numeric(10,2),
  direct_cost_usd_typical numeric(12,2),
  outsourced boolean not null default false,
  parallelizable boolean not null default false,
  failure_probability numeric(5,4),
  output_artifact text,
  input_artifact text,
  notes text,
  unique (workflow_template_id, step_name)
);

create table workflow_mechanism (
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  mechanism_name text not null,
  primary key (workflow_template_id, mechanism_name)
);

create table workflow_technique (
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  technique_name text not null,
  primary key (workflow_template_id, technique_name)
);

create table workflow_design_goal (
  id uuid primary key default gen_random_uuid(),
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  goal_name text not null,
  goal_kind text not null default 'property_axis',
  rationale text,
  source_document_id uuid references source_document(id) on delete set null,
  unique (workflow_template_id, goal_name, goal_kind)
);

create table workflow_item_role (
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

create table workflow_edge (
  id uuid primary key default gen_random_uuid(),
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  from_step_id uuid not null references workflow_step_template(id) on delete cascade,
  to_step_id uuid not null references workflow_step_template(id) on delete cascade,
  edge_type text not null default 'depends_on'
);

create table workflow_assumption (
  id uuid primary key default gen_random_uuid(),
  workflow_template_id uuid references workflow_template(id) on delete cascade,
  workflow_stage_template_id uuid references workflow_stage_template(id) on delete cascade,
  workflow_step_template_id uuid references workflow_step_template(id) on delete cascade,
  assumption_kind text not null,
  assumption_name text not null,
  value_num double precision,
  value_text text,
  unit text,
  rationale text,
  source_document_id uuid references source_document(id) on delete set null
);

create table workflow_instance_observation (
  id uuid primary key default gen_random_uuid(),
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  workflow_step_template_id uuid references workflow_step_template(id) on delete set null,
  observed_at timestamptz not null default now(),
  lab_or_group text,
  duration_hours double precision,
  queue_time_hours double precision,
  direct_cost_usd double precision,
  success boolean,
  notes text
);

create table gap_field (
  id uuid primary key default gen_random_uuid(),
  external_gap_field_id text not null unique,
  slug text unique,
  name text not null,
  payload jsonb not null default '{}'::jsonb
);

create table gap_item (
  id uuid primary key default gen_random_uuid(),
  external_gap_item_id text not null unique,
  gap_field_id uuid references gap_field(id) on delete set null,
  slug text unique,
  title text not null,
  payload jsonb not null default '{}'::jsonb
);

create table gap_capability (
  id uuid primary key default gen_random_uuid(),
  external_gap_capability_id text not null unique,
  slug text unique,
  name text not null,
  payload jsonb not null default '{}'::jsonb
);

create table gap_resource (
  id uuid primary key default gen_random_uuid(),
  external_gap_resource_id text not null unique,
  title text not null,
  payload jsonb not null default '{}'::jsonb
);

create table gap_item_capability (
  gap_item_id uuid not null references gap_item(id) on delete cascade,
  gap_capability_id uuid not null references gap_capability(id) on delete cascade,
  primary key (gap_item_id, gap_capability_id)
);

create table gap_capability_resource (
  gap_capability_id uuid not null references gap_capability(id) on delete cascade,
  gap_resource_id uuid not null references gap_resource(id) on delete cascade,
  primary key (gap_capability_id, gap_resource_id)
);

create table item_problem_link (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  gap_item_id uuid references gap_item(id) on delete set null,
  problem_label text not null,
  why_this_item_helps text not null,
  source_kind text not null,
  overall_score numeric(8,3),
  evidence_payload jsonb not null default '{}'::jsonb,
  derived_version text not null default 'v1',
  updated_at timestamptz not null default now(),
  unique (item_id, problem_label, source_kind)
);

create table item_gap_link (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  gap_item_id uuid not null references gap_item(id) on delete cascade,
  score_version text not null,
  mechanistic_match_score numeric(8,3),
  context_match_score numeric(8,3),
  throughput_match_score numeric(8,3),
  time_to_first_test_score numeric(8,3),
  cost_to_first_test_score numeric(8,3),
  replication_confidence_modifier numeric(8,3),
  practicality_modifier numeric(8,3),
  translatability_modifier numeric(8,3),
  overall_gap_applicability_score numeric(8,3),
  why_it_might_help text,
  assumptions text,
  missing_evidence text,
  unique (item_id, gap_item_id, score_version)
);

create view item_validation_rollup_v1 as
select
  ti.id as item_id,
  bool_or(vo.biological_system_level = 'cell_free' and vo.success_outcome = 'success') as has_cell_free_validation,
  bool_or(vo.biological_system_level = 'bacteria' and vo.success_outcome = 'success') as has_bacterial_validation,
  bool_or(vo.biological_system_level = 'mammalian_cell_line' and vo.success_outcome = 'success') as has_mammalian_cell_validation,
  bool_or(vo.biological_system_level = 'mouse' and vo.success_outcome = 'success') as has_mouse_in_vivo_validation,
  bool_or(vo.biological_system_level = 'human_clinical' and vo.success_outcome = 'success') as has_human_clinical_validation,
  bool_or(vo.observation_type = 'therapeutic_use' and vo.success_outcome in ('success', 'mixed')) as has_therapeutic_use,
  bool_or(vo.independent_lab_cluster_id is not null) as has_independent_replication
from toolkit_item ti
left join validation_observation vo on vo.item_id = ti.id
group by ti.id;

create table extracted_packet (
  id uuid primary key default gen_random_uuid(),
  packet_fingerprint text not null unique,
  source_document_id uuid not null references source_document(id) on delete cascade,
  extraction_run_id uuid references extraction_run(id) on delete set null,
  packet_kind text not null,
  schema_version text not null,
  packet_path text,
  packet_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table extracted_item_candidate (
  id uuid primary key default gen_random_uuid(),
  packet_fingerprint text not null references extracted_packet(packet_fingerprint) on delete cascade,
  source_document_id uuid not null references source_document(id) on delete cascade,
  extraction_run_id uuid references extraction_run(id) on delete set null,
  packet_kind text not null,
  local_id text not null,
  candidate_type text not null,
  slug text not null,
  canonical_name text not null,
  item_type text,
  aliases text[] not null default '{}'::text[],
  external_ids jsonb not null default '{}'::jsonb,
  evidence_text text,
  matched_item_id uuid references toolkit_item(id) on delete set null,
  matched_slug text,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (packet_fingerprint, local_id)
);

create table extracted_claim_candidate (
  id uuid primary key default gen_random_uuid(),
  packet_fingerprint text not null references extracted_packet(packet_fingerprint) on delete cascade,
  source_document_id uuid not null references source_document(id) on delete cascade,
  extraction_run_id uuid references extraction_run(id) on delete set null,
  packet_kind text not null,
  local_id text not null,
  claim_type text not null,
  claim_text_normalized text not null,
  polarity text not null,
  context jsonb not null default '{}'::jsonb,
  metrics jsonb not null default '[]'::jsonb,
  source_locator jsonb not null default '{}'::jsonb,
  unresolved_ambiguities jsonb not null default '[]'::jsonb,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (packet_fingerprint, local_id)
);

create table extracted_claim_subject_candidate (
  id uuid primary key default gen_random_uuid(),
  extracted_claim_candidate_id uuid not null references extracted_claim_candidate(id) on delete cascade,
  extracted_item_candidate_id uuid not null references extracted_item_candidate(id) on delete cascade,
  subject_role text not null default 'subject',
  unique (extracted_claim_candidate_id, extracted_item_candidate_id, subject_role)
);

create table extracted_workflow_observation (
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

create table extracted_workflow_stage_observation (
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

create table extracted_workflow_step_observation (
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
