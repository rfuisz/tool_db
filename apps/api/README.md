# API App

FastAPI service exposing the backend read layer.

When `DATABASE_URL` is set, the read layer prefers Postgres so hosted deployments can surface the same canonical data being loaded by the worker pipeline. Without `DATABASE_URL`, it falls back to the checked-in `knowledge/` artifacts.

- public read APIs
- curation write APIs
- ingestion control endpoints

## Current Endpoints

- `GET /healthz`
- `GET /api/v1/vocabularies`
- `GET /api/v1/source-registry`
- `GET /api/v1/items`
- `GET /api/v1/items-browse`
- `GET /api/v1/items/{slug}`
- `GET /api/v1/workflows`
- `GET /api/v1/workflows/{slug}`
- `GET /api/v1/admin/import-db`
- `POST /api/v1/admin/import-db`

## Run Locally

```bash
.venv/bin/python -m apps.api.main
```

## Render

The repo-root `render.yaml` blueprint deploys this service with:

- `DATABASE_URL` from a managed Render Postgres instance
- `preDeployCommand: python -m apps.worker.main run-migrations`
- a private-service network boundary so only your own Render services can reach it

Migrations are applied on each deploy. Data is synced to hosted Postgres separately via the incremental sync mechanism.

For one-off curator syncs from localhost, the hosted web app can proxy a SQL dump upload into `POST /api/v1/admin/import-db`. Protect that path with `TOOL_DB_ADMIN_SYNC_KEY` on both the web and API services; callers must send it via `x-api-key` or `Authorization: Bearer`.
