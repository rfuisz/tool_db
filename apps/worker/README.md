# Worker App

Worker-side utilities and future background jobs for ingestion and scoring.

- source syncs
- extraction orchestration
- normalization
- replication scoring
- workflow rollups
- gap-link scoring

## Local Database

Use the repo's local PostgreSQL setup rather than SQLite for canonical data:

```bash
docker compose -f docker-compose.local.yml up -d
```

Set:

```bash
DATABASE_URL=postgresql://tooldb:tooldb@localhost:5432/tooldb
```

## Current Utility

Validate an extraction packet against the repo's JSON Schemas:

```bash
.venv/bin/python -m apps.worker.main review_extract_v1 tests/fixtures/review_extract_v1.sample.json
```

Export seed snapshots:

```bash
.venv/bin/python -m apps.worker.main export-seeds db/seeds
```

Load seed items and workflows into Postgres:

```bash
.venv/bin/python -m apps.worker.main load-seed-bundle
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

Harvest a much broader first-pass corpus:

```bash
.venv/bin/python -m apps.worker.main harvest-real-data --artifact-dir data/pipeline-artifacts/first-pass-harvest
```

This expands source queries from the checked-in seed bundle and controlled vocabularies, paginates across OpenAlex and Semantic Scholar, and pulls a much larger raw corpus than the smoke-test path.

Build typed extraction artifacts from fetched real data:

```bash
.venv/bin/python -m apps.worker.main build-real-extraction-artifacts data/pipeline-artifacts/real-data-smoke-test/manifest.json data/pipeline-artifacts/real-extraction-seed
```

This currently creates:

- deterministic `database_entry_extract_v1` packets for a slice of Gap Map gaps
- `primary_paper_extract_v1` metadata scaffolds for a slice of OpenAlex works
- `primary_paper_extract_v1` and `review_extract_v1` metadata scaffolds for a slice of Semantic Scholar papers
- structured Semantic Scholar summary artifacts for fetched search hits
- structured OptoBase search-summary artifacts for fetched HTML result pages
- LLM extraction job files that a future GPT-5.4 caller can execute

Build a deterministic trial packet from a raw ClinicalTrials.gov payload wrapper:

```bash
.venv/bin/python -m apps.worker.main build-clinicaltrials-packet tmp/clinicaltrials-actt.json tmp/clinicaltrials-actt.trial_extract_v1.json
```

Parse a raw OptoBase search wrapper into a structured staging artifact:

```bash
.venv/bin/python -m apps.worker.main parse-optobase-search data/raw/optobase/search_html/aslov2.json tmp/aslov2.optobase_summary.json
```

Run one LLM extraction job:

```bash
.venv/bin/python -m apps.worker.main run-extraction-job data/pipeline-artifacts/real-extraction-seed/openalex/jobs/optogenetics.llm_extraction_job_v1.json
```

LLM extraction calls now go through one shared JSON-call harness with disk cache and retry handling:

- cached responses are stored under `data/llm-cache/`
- cache keys are hashed from the full request contract, including model, base URL, call purpose, messages, temperature, and response format
- identical extraction or repair prompts reuse cached JSON; changing the prompt text, schema text, or job payload produces a new cache key
- retryable transport failures and `408/409/429/5xx` responses back off and retry automatically before the worker fails

Relevant settings:

- `LLM_CACHE_ENABLED` to disable cache reads and writes
- `LLM_RETRY_ATTEMPTS` to change total attempts
- `LLM_RETRY_BASE_DELAY_SECONDS` and `LLM_RETRY_MAX_DELAY_SECONDS` to tune exponential backoff

Prompt harness guidance:

- keep prompts deterministic and avoid incidental churn if you want stable cache hits
- treat prompt edits as intentional cache invalidation for future extraction runs

Agent test-visibility guidance:

- repo-level `tests/` is hidden from Cursor-style agent search by default via `.cursorignore`
- reveal the suite intentionally with `python scripts/agent_test_visibility.py show`
- restore the barrier with `python scripts/agent_test_visibility.py hide`
- check current state with `python scripts/agent_test_visibility.py status`

Run a small batch of LLM extraction jobs:

```bash
.venv/bin/python -m apps.worker.main run-extraction-batch data/pipeline-artifacts/real-extraction-seed/openalex/jobs --limit 50
```

Run all eligible jobs in a directory:

```bash
.venv/bin/python -m apps.worker.main run-extraction-batch data/pipeline-artifacts/real-extraction-seed/openalex/jobs --limit 0
```

Ingest a directory of checked-in packet files:

```bash
.venv/bin/python -m apps.worker.main ingest-packet-batch data/extractions --apply --review-output-dir data/review-queue/batch
```

Populate local Postgres from the checked-in literature extraction packets plus Gap Map packet artifacts:

```bash
.venv/bin/python -m apps.worker.main populate-local-db --review-output-dir data/review-queue/populate-local-db --manifest-path data/pipeline-artifacts/populate-local-db/report.json
```

This command:

- applies any pending migrations
- loads the seed bundle into canonical `toolkit_item` and `workflow_template` tables
- ingests `data/extractions/*.json`
- ingests `data/pipeline-artifacts/real-extraction-seed/gap_map/*.database_entry_extract_v1.json`
- writes normalized packets, load plans, execution reports, and review-queue artifacts under `data/pipeline-artifacts/populate-local-db/`
