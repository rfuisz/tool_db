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
- `GET /api/v1/items/{slug}`
- `GET /api/v1/workflows`
- `GET /api/v1/workflows/{slug}`

## Run Locally

```bash
.venv/bin/python -m apps.api.main
```

## Render

The repo-root `render.yaml` blueprint deploys this service with:

- `DATABASE_URL` from a managed Render Postgres instance
- `preDeployCommand: python -m apps.worker.main populate-local-db`
- a private-service network boundary so only your own Render services can reach it

That makes each code push a hosted data refresh for the checked-in bundle and extraction artifacts.
