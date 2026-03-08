# API App

FastAPI service exposing the backend read layer over the repo's seeded knowledge artifacts.

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
