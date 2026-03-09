alter table gap_field
  add column if not exists slug text;

create unique index if not exists gap_field_slug_uidx
  on gap_field (slug)
  where slug is not null;

alter table gap_item
  add column if not exists slug text;

create unique index if not exists gap_item_slug_uidx
  on gap_item (slug)
  where slug is not null;

alter table gap_capability
  add column if not exists slug text;

create unique index if not exists gap_capability_slug_uidx
  on gap_capability (slug)
  where slug is not null;

create table if not exists gap_item_capability (
  gap_item_id uuid not null references gap_item(id) on delete cascade,
  gap_capability_id uuid not null references gap_capability(id) on delete cascade,
  primary key (gap_item_id, gap_capability_id)
);

create table if not exists gap_capability_resource (
  gap_capability_id uuid not null references gap_capability(id) on delete cascade,
  gap_resource_id uuid not null references gap_resource(id) on delete cascade,
  primary key (gap_capability_id, gap_resource_id)
);

update gap_field
set slug = nullif(payload->>'slug', '')
where slug is null;

update gap_item
set slug = nullif(coalesce(payload->'external_ids'->>'gap_map_slug', payload->>'slug'), '')
where slug is null;
