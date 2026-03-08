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

| Route | Description |
|---|---|
| `/` | Dashboard with stats, type/mechanism/technique/family entry points |
| `/items` | Browse and filter toolkit items |
| `/items/[slug]` | Item detail — validation matrix, scores, citations |
| `/workflows` | DBTL workflow templates with step timelines |

## Deployment (Render)

The app uses `output: "standalone"` in `next.config.ts` for optimized production builds.

**Render settings:**

- **Build command:** `cd apps/web && npm install && npm run build`
- **Start command:** `cd apps/web && node .next/standalone/server.js`
- **Root directory:** (repo root)

## Architecture Notes

- **Mock data layer** (`src/lib/mock-data.ts`) stands in until the API service is live. The type system in `src/lib/types.ts` mirrors the canonical Postgres schema so the swap will be straightforward.
- **Controlled vocabularies** (`src/lib/vocabularies.ts`) are derived from `schemas/canonical/controlled_vocabularies.v1.json`.
- All scores are rendered with visible breakdowns per the transparency requirements in the design spec.
