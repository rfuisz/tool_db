alter table extracted_claim
  add column if not exists context jsonb not null default '{}'::jsonb,
  add column if not exists source_locator jsonb not null default '{}'::jsonb,
  add column if not exists unresolved_ambiguities jsonb not null default '[]'::jsonb;

alter table validation_observation
  add column if not exists source_locator jsonb not null default '{}'::jsonb;

create table if not exists item_facet (
  id uuid primary key default gen_random_uuid(),
  item_id uuid not null references toolkit_item(id) on delete cascade,
  facet_name text not null,
  facet_value text not null,
  evidence_note text,
  unique (item_id, facet_name, facet_value)
);

create table if not exists item_explainer (
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

create table if not exists item_problem_link (
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

create table if not exists item_comparison (
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
