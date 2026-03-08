# Seeds

Generated and curated seed artifacts live here.

- controlled vocabulary seeds
- initial workflow templates
- curated starter items
- source registry defaults

## Generate

```bash
.venv/bin/python -m apps.worker.main export-seeds db/seeds
```

This exports JSON snapshots from the repo's `knowledge/` and `schemas/` directories so later database loading can remain deterministic.
