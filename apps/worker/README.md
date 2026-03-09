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

To overwrite the hosted Render Postgres database from your local database, also set:

```bash
RENDER_DATABASE_URL=postgresql://...
```

Or let the sync script resolve the hosted connection string from the Render API:

```bash
RENDER_API_KEY=
RENDER_POSTGRES_ID=
# or:
RENDER_POSTGRES_NAME=tool-db-postgres
```

Then run:

```bash
./scripts/sync_render_db.py
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

Fetch a Europe PMC search payload:

```bash
.venv/bin/python -m apps.worker.main fetch-europepmc-search "optogenetic switch" --page-size 25 --page 1 --output-path tmp/europepmc-search.json
```

Fetch a PMC BioC full-text payload:

```bash
.venv/bin/python -m apps.worker.main fetch-pmc-fulltext PMC1234567 --output-path tmp/pmc-bioc.json
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

Recompute canonical item explainers, comparisons, facets, and scores after schema or derivation changes:

```bash
.venv/bin/python -m apps.worker.main materialize-item-details
```

This command now emits phase and progress logs during long runs. Use `LOG_LEVEL=DEBUG` if you want more verbose worker-side tracing.

## Full Pipeline (one command)

Run everything end-to-end: harvest, extract, ingest, materialize, LLM-synthesize, gap-link, and sync to production:

```bash
.venv/bin/python -m apps.worker.main run-pipeline
```

Use flags to skip steps you don't need:

```bash
# Skip the literature harvest (re-use cached data)
.venv/bin/python -m apps.worker.main run-pipeline --skip-harvest

# Skip harvest + extraction (just re-process existing data)
.venv/bin/python -m apps.worker.main run-pipeline --skip-harvest --skip-extract

# Skip Render sync (local-only run)
.venv/bin/python -m apps.worker.main run-pipeline --skip-sync
```

The pipeline phases, in order:

| # | Phase | What it does |
|---|-------|-------------|
| 1 | `migrations` | Apply any pending DB migrations |
| 2 | `harvest` | Pull literature from OpenAlex, Europe PMC, Semantic Scholar, OptoBase |
| 3 | `build-extraction-artifacts` | Build LLM extraction jobs from harvest data |
| 4 | `extraction` | Run LLM extraction on new jobs (parallelized at 64) |
| 5 | `ingest` | Ingest extraction packets into the DB |
| 6 | `first-pass-load` | Load first-pass extraction data |
| 7 | `materialize` | Heuristic derivation: scores, facets, comparisons |
| 8 | `synthesize` | LLM synthesis of explainers, summaries, mechanisms, techniques |
| 9 | `gap-links` | LLM gap-to-tool linking |
| 10 | `sync` | Push to Render production database |

Each derived row carries a `derivation_model` watermark (e.g. `gpt-5.4`) so the pipeline can detect when content was generated by a specific model vs. heuristic rules. Bump `MATERIALIZATION_VERSION` in `pipeline_versions.py` when synthesis prompts or derivation logic changes.

### Running individual steps

You can still run each step individually if needed. For example, to just re-synthesize:

```bash
.venv/bin/python -m apps.worker.main synthesize-item-profiles
```

Optionally scope the refresh to one or more item slugs:

```bash
.venv/bin/python -m apps.worker.main materialize-item-details licre phyb-pif
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

The broad harvester now also queries Europe PMC and can fetch a bounded set of PMC BioC full-text payloads for open-access papers discovered through Europe PMC.

OpenAlex-backed extraction artifacts now try to inherit richer Europe PMC / PMC evidence when DOI or PMID resolution succeeds, so downstream extraction jobs are less likely to stay title-and-abstract-only for open-access papers.

Build typed extraction artifacts from fetched real data:

```bash
.venv/bin/python -m apps.worker.main build-real-extraction-artifacts data/pipeline-artifacts/real-data-smoke-test/manifest.json data/pipeline-artifacts/real-extraction-seed
```

This currently creates:

- deterministic `database_entry_extract_v1` packets for a slice of Gap Map gaps
- `review_extract_v1` and `primary_paper_extract_v1` metadata scaffolds from Europe PMC search results, with section-aware PMC full-text previews attached when available
- `primary_paper_extract_v1` metadata scaffolds for a slice of OpenAlex works, enriched from Europe PMC / PMC when resolvable
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

For `toolkit_item` candidates, first-pass extraction should now capture both terse list fields and richer question-driven prose when the source supports it, especially:

- what the tool is doing
- what resources or prerequisites are required to execute it
- what problem it solves and does not solve
- what alternatives the source contrasts it against

That richer prose is expected to survive into canonical item explainers, problem-fit notes, and comparison copy with source provenance when the extraction is later promoted.

LLM extraction calls now go through one shared JSON-call harness with disk cache and retry handling:

- cached responses are stored under `data/llm-cache/`
- cache keys are hashed from the full request contract, including model, base URL, call purpose, messages, temperature, and response format
- identical extraction or repair prompts reuse cached JSON; changing the prompt text, schema text, or job payload produces a new cache key
- retryable transport failures and `408/409/429/5xx` responses back off and retry automatically before the worker fails

Optional browsing-backed web research can now enrich extraction job context before the main packet extraction step:

- enable it with `LLM_WEB_RESEARCH_ENABLED=true`
- it reuses the OpenAI-compatible credentials by default, but you can override them with `OPENAI_WEB_RESEARCH_*` or `LLM_WEB_RESEARCH_*`
- the artifact builder injects a structured `web_research_summary` into `input_context` when available
- that summary is meant to surface additional high-signal source leads and adjacent tool names with explicit provenance, not to bypass the evidence-first packet model
- the harvest query builder can also use the same browsing-capable model to fan out from strong seed tools into adjacent tool/component names and additional literature queries before OpenAlex / Europe PMC / Semantic Scholar fetches run
- raw upstream harvest payloads are now reused from `data/raw/` on rerun when the same source/query/page/fulltext key already exists, so repeated corpus harvests do not keep re-hitting OpenAlex / Europe PMC / PMC / Semantic Scholar / OptoBase for identical fetches

Concurrency rules:

- Always parallelize I/O-bound calls. Never loop serially over network fetches. Use `ThreadPoolExecutor` with `llm_max_concurrency` as the default pool width.
- OpenAI API calls can handle very high parallelism. Use the full `llm_max_concurrency` (default 64) pool for LLM extraction, web-research, and repair calls.
- OpenAlex has a low RPM limit. Live API calls are gated by a `threading.Semaphore(openalex_max_concurrency)` (default 3), but cached reads bypass the semaphore so reruns stay fast.
- Europe PMC, PMC BioC, Semantic Scholar, and OptoBase can use the full pool width.
- The `--limit` flag on `run-extraction-batch` defaults to `0` (run all eligible jobs). There is no secondary cap beyond `llm_max_concurrency`.

Relevant settings:

- `LLM_CACHE_ENABLED` to disable cache reads and writes
- `LLM_MAX_CONCURRENCY` to control how many extraction/enrichment/web-research workers run in parallel (default 64)
- `OPENALEX_MAX_CONCURRENCY` to cap simultaneous live OpenAlex API calls (default 3; cached reads are not gated)
- `LLM_RETRY_ATTEMPTS` to change total attempts
- `LLM_RETRY_BASE_DELAY_SECONDS` and `LLM_RETRY_MAX_DELAY_SECONDS` to tune exponential backoff
- `LLM_WEB_RESEARCH_ENABLED` to turn on the optional browsing-backed source-compilation step
- `LLM_WEB_RESEARCH_MODEL` and `LLM_WEB_RESEARCH_BASE_URL` to point that step at a browsing-capable OpenAI-compatible model/provider

Prompt harness guidance:

- keep prompts deterministic and avoid incidental churn if you want stable cache hits
- treat prompt edits as intentional cache invalidation for future extraction runs

Agent test-visibility guidance:

- repo-level `tests/` is hidden from Cursor-style agent search by default via `.cursorignore`
- reveal the suite intentionally with `python scripts/agent_test_visibility.py show`
- restore the barrier with `python scripts/agent_test_visibility.py hide`
- check current state with `python scripts/agent_test_visibility.py status`
- if you temporarily reveal `tests/` to inspect or edit them, put the barrier back before you finish the task so broad agent search does not silently start depending on hidden test internals

Run a small batch of LLM extraction jobs:

```bash
.venv/bin/python -m apps.worker.main run-extraction-batch data/pipeline-artifacts/real-extraction-seed/openalex/jobs --limit 50
```

Run all eligible jobs in a directory:

```bash
.venv/bin/python -m apps.worker.main run-extraction-batch data/pipeline-artifacts/real-extraction-seed/openalex/jobs --limit 0
```

Push concurrency higher for network-bound extraction:

```bash
LLM_MAX_CONCURRENCY=64 .venv/bin/python -m apps.worker.main run-extraction-batch data/pipeline-artifacts/real-extraction-seed/openalex/jobs --limit 0
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
- materializes canonical item facets, explainers, comparisons, problem links, and replication summaries
- writes normalized packets, load plans, execution reports, and review-queue artifacts under `data/pipeline-artifacts/populate-local-db/`

For first-pass reloads, the loader also backfills missing legacy list fields such as `workflow_observations`, `workflow_stage_observations`, `workflow_step_observations`, and `unresolved_ambiguities` with empty arrays before schema validation so older extraction packets remain loadable.
