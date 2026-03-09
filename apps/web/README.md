# BioControl Toolkit — Web Viewer

Next.js frontend for the BioControl Toolkit DB. Serves the public and curator-facing item browser, validation matrix, score breakdowns, and DBTL workflow viewer.

## Development

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Pages

| Route           | Description                                                        |
| --------------- | ------------------------------------------------------------------ |
| `/`             | Dashboard with stats, type/mechanism/technique/family entry points |
| `/items`        | Browse and filter toolkit items                                    |
| `/items/[slug]` | Item detail — validation matrix, scores, citations                 |
| `/gaps`         | Gap Map browser with normalized capabilities and resources         |
| `/workflows`    | DBTL workflow templates with step timelines                        |

## API

The web app now exposes read-only JSON endpoints alongside the UI:

| Route               | Description                                                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `/api/items`        | Filterable item search with `q`, `type`, `mechanism`, `technique`, `family`, `maturity_stage`, `status`, and validation booleans |
| `/api/items/[slug]` | Full item payload for one canonical item                                                                                         |
| `/api/workflows`    | Workflow search with `q` and `workflow_family`                                                                                   |
| `/api/query`        | Structured or prompt-driven query endpoint                                                                                       |

### Prompt Query LLM

`POST /api/query` can parse natural-language prompts into structured filters. To keep hosted prompt traffic separate from other LLM use, set:

```bash
TOOL_DB_QUERY_UPSTREAM_API_KEY=...
TOOL_DB_QUERY_UPSTREAM_BASE_URL=https://api.openai.com/v1
TOOL_DB_QUERY_UPSTREAM_MODEL=gpt-5-nano
```

These are server-side upstream provider settings used by your deployment. API consumers do not need to provide this key. If those variables are unset, the route falls back to plain text search over items and workflows instead of failing.

### Query Endpoint Protection

`/api/query` also supports lightweight protection for public hosting:

```bash
TOOL_DB_QUERY_CLIENT_API_KEY=...
TOOL_DB_QUERY_RATE_LIMIT_MAX_REQUESTS=30
TOOL_DB_QUERY_RATE_LIMIT_WINDOW_MS=60000
```

- `TOOL_DB_QUERY_CLIENT_API_KEY` is a site-issued key for callers to your hosted endpoint. It is separate from your upstream OpenAI or compatible provider key.
- If `TOOL_DB_QUERY_CLIENT_API_KEY` is set, clients must send `x-api-key: ...` or `Authorization: Bearer ...`.
- If `TOOL_DB_QUERY_RATE_LIMIT_MAX_REQUESTS` is greater than `0`, the app applies a simple in-memory per-IP rate limit and returns standard `429`/`Retry-After` headers when exceeded.
- This limiter is intentionally lightweight and best-effort. It is useful for a single hosted app instance, but if you later run multiple instances you will probably want a shared store like Redis.

## Deployment (Render)

The app uses `output: "standalone"` in `next.config.ts` for optimized production builds.

Recommended deployment is the repo-root `render.yaml` blueprint. It provisions:

- a managed PostgreSQL database
- a private Python API/data service that reads from Postgres when `DATABASE_URL` is set
- this Next.js web service pointed at that API

On each Render deploy, the API service runs:

```bash
python -m apps.worker.main populate-local-db
```

That means a normal git push is the hosted sync trigger: Render redeploys, reruns migrations, reloads the checked-in seed bundle, and ingests the checked-in packet artifacts into hosted Postgres before the new API version goes live.

The API is intentionally private on Render. The public site reaches it over Render's internal network using `TOOL_DB_API_HOST` and `TOOL_DB_API_PORT`, so you do not have to expose a second public endpoint just to keep the UI synced.

Important boundary:

- Render syncs checked-in repo state, not ad hoc local-only database mutations.
- If you changed data only in your local Postgres, export or check in the corresponding repo artifacts before pushing.
- The footer now renders a small deployment badge with the active service, branch, short commit, and API target so stale or mismatched Render services are easier to spot.
- When you run the web app on `localhost`, the top nav also exposes a `Sync Render DB` control that can overwrite the hosted Render Postgres database from your local Postgres after a confirmation prompt.

**Manual Render settings if you do not use the blueprint:**

- **Build command:** `cd apps/web && npm install && npm run build`
- **Start command:** `cd apps/web && node .next/standalone/server.js`
- **Root directory:** (repo root)
- **Environment:** `TOOL_DB_API_BASE_URL=https://<your-api-service>.onrender.com`

## Architecture Notes

- **Mock data layer** (`src/lib/mock-data.ts`) stands in until the API service is live. The type system in `src/lib/types.ts` mirrors the canonical Postgres schema so the swap will be straightforward.
- **Controlled vocabularies** (`src/lib/vocabularies.ts`) are derived from `schemas/canonical/controlled_vocabularies.v1.json`.
- All scores are rendered with visible breakdowns per the transparency requirements in the design spec.
