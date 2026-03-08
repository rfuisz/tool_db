create table if not exists extracted_packet (
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

create table if not exists extracted_item_candidate (
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

create index if not exists extracted_item_candidate_slug_idx on extracted_item_candidate (slug);
create index if not exists extracted_item_candidate_candidate_type_idx on extracted_item_candidate (candidate_type);
create index if not exists extracted_item_candidate_matched_slug_idx on extracted_item_candidate (matched_slug);

create table if not exists extracted_claim_candidate (
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

create index if not exists extracted_claim_candidate_claim_type_idx on extracted_claim_candidate (claim_type);

create table if not exists extracted_claim_subject_candidate (
  id uuid primary key default gen_random_uuid(),
  extracted_claim_candidate_id uuid not null references extracted_claim_candidate(id) on delete cascade,
  extracted_item_candidate_id uuid not null references extracted_item_candidate(id) on delete cascade,
  subject_role text not null default 'subject',
  unique (extracted_claim_candidate_id, extracted_item_candidate_id, subject_role)
);
