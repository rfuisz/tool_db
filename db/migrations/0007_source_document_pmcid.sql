alter table source_document
  add column if not exists pmcid text;

create index if not exists source_document_pmcid_idx
  on source_document (pmcid)
  where pmcid is not null;
