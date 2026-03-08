# Worker App

Worker-side utilities and future background jobs for ingestion and scoring.

- source syncs
- extraction orchestration
- normalization
- replication scoring
- workflow rollups
- gap-link scoring

## Current Utility

Validate an extraction packet against the repo's JSON Schemas:

```bash
.venv/bin/python -m apps.worker.main review_extract_v1 tests/fixtures/review_extract_v1.sample.json
```

Export seed snapshots:

```bash
.venv/bin/python -m apps.worker.main export-seeds db/seeds
```

Fetch an OpenAlex work payload:

```bash
.venv/bin/python -m apps.worker.main fetch-openalex-work W2741809807 --output-path tmp/openalex-work.json
```

Fetch a Semantic Scholar paper payload:

```bash
.venv/bin/python -m apps.worker.main fetch-semanticscholar-paper 10.1038/nature12373 --fields title,year,authors
```

Fetch a ClinicalTrials.gov study payload:

```bash
.venv/bin/python -m apps.worker.main fetch-clinicaltrials-study NCT04280705
```

Fetch a Gap Map dataset:

```bash
.venv/bin/python -m apps.worker.main fetch-gapmap-dataset gaps
```

Fetch an OptoBase search page:

```bash
.venv/bin/python -m apps.worker.main fetch-optobase-search --query "AsLOV2"
```

Without `--output-path`, source fetches are written to `data/raw/` as wrapped raw payload snapshots.

Normalize a typed extraction packet into merge-ready JSON:

```bash
.venv/bin/python -m apps.worker.main normalize-packet review_extract_v1 tests/fixtures/review_extract_v1.sample.json tmp/review.normalized.json
```

Build a conservative canonical load plan from normalized output:

```bash
.venv/bin/python -m apps.worker.main build-load-plan tmp/review.normalized.json tmp/review.load-plan.json
```

Dry-run or apply a load plan:

```bash
.venv/bin/python -m apps.worker.main execute-load-plan tmp/review.load-plan.json
```

```bash
.venv/bin/python -m apps.worker.main execute-load-plan tmp/review.load-plan.json --apply
```

In dry-run mode the worker writes review tasks for ambiguous actions without touching Postgres. In apply mode it executes unambiguous actions transactionally and still emits review-queue artifacts when needed.

Apply database migrations:

```bash
.venv/bin/python -m apps.worker.main run-migrations
```

Run the packet ingest pipeline end to end:

```bash
.venv/bin/python -m apps.worker.main ingest-packet review_extract_v1 tests/fixtures/review_extract_v1.sample.json
```

```bash
.venv/bin/python -m apps.worker.main ingest-packet review_extract_v1 tests/fixtures/review_extract_v1.sample.json --apply
```

Pull a modest real-data smoke-test batch:

```bash
.venv/bin/python -m apps.worker.main smoke-test-real-data
```

This fetches a small batch from literature/problem sources and writes a manifest plus raw payload snapshots so you can sanity-check entry counts and payload shape before heavier ingestion work.
