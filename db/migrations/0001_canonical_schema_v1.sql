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

create table source_document (
  id uuid primary key default gen_random_uuid(),
  source_type source_type not null,
  title text not null,
  doi text,
  pmid text,
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
  needs_review boolean not null default true
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
  notes text
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
  recommended_for text,
  default_parallelization_assumption text,
  notes text
);

create table workflow_step_template (
  id uuid primary key default gen_random_uuid(),
  workflow_template_id uuid not null references workflow_template(id) on delete cascade,
  step_name text not null,
  step_type workflow_step_type not null,
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
  notes text
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
  name text not null,
  payload jsonb not null default '{}'::jsonb
);

create table gap_item (
  id uuid primary key default gen_random_uuid(),
  external_gap_item_id text not null unique,
  gap_field_id uuid references gap_field(id) on delete set null,
  title text not null,
  payload jsonb not null default '{}'::jsonb
);

create table gap_capability (
  id uuid primary key default gen_random_uuid(),
  external_gap_capability_id text not null unique,
  name text not null,
  payload jsonb not null default '{}'::jsonb
);

create table gap_resource (
  id uuid primary key default gen_random_uuid(),
  external_gap_resource_id text not null unique,
  title text not null,
  payload jsonb not null default '{}'::jsonb
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
