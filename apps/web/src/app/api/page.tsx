import Link from "next/link";

const structuredQueryExample = `curl -X POST https://your-host/api/query \\
  -H "Content-Type: application/json" \\
  -d '{
    "item_filters": {
      "mechanism": ["photocleavage"],
      "has_mouse_in_vivo_validation": true,
      "limit": 5
    }
  }'`;

const promptQueryExample = `curl -X POST https://your-host/api/query \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Which tools have mouse validation and independent replication?"
  }'`;

export default function ApiDocsPage() {
  return (
    <div className="pt-8">
      <header className="mb-12">
        <p className="small-caps mb-4">API Access</p>
        <h1 className="mb-4">Query the database directly</h1>
        <p className="max-w-3xl text-lg leading-relaxed text-ink-secondary">
          The hosted site exposes read-only JSON endpoints alongside the visual
          interface. Use structured filters when you want predictable
          programmatic access, or send a natural-language prompt when you want
          the site to translate a question into database filters for you.
        </p>
      </header>

      <section className="mb-12 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="border border-edge bg-surface p-6">
          <h2 className="mb-4 text-ink">Endpoints</h2>
          <div className="space-y-4 text-sm leading-relaxed text-ink-secondary">
            <p>
              <code>GET /api/items</code> searches items by text, type,
              mechanism, technique, family, maturity, status, and validation
              flags.
            </p>
            <p>
              <code>GET /api/items/[slug]</code> returns one full item record
              with citations, validations, and score rollups.
            </p>
            <p>
              <code>GET /api/extracted-workflows</code> searches extracted
              workflows by text, mechanism, and technique.
            </p>
            <p>
              <code>POST /api/query</code> accepts either structured filters or
              a prompt and returns matching items and workflows.
            </p>
          </div>
        </div>

        <div className="border border-edge bg-surface p-6">
          <h2 className="mb-4 text-ink">How It Works</h2>
          <div className="space-y-4 text-sm leading-relaxed text-ink-secondary">
            <p>
              Structured mode is best for apps, scripts, and dashboards that
              need predictable filters and stable payloads.
            </p>
            <p>
              Prompt mode is best when you want to ask a direct question in
              plain language and let the service translate it into the available
              database filters.
            </p>
            <p>
              Both modes use the same evidence-first data model surfaced in the
              UI, including citations, validation context, and workflow
              metadata.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-12 border border-edge bg-surface p-6">
        <p className="small-caps mb-3">Authentication And Limits</p>
        <div className="space-y-3 text-sm leading-relaxed text-ink-secondary">
          <p>
            The server uses its own upstream provider key to interpret prompt
            queries. End users do not need that provider key.
          </p>
          <p>
            If the hosted deployment sets{" "}
            <code>TOOL_DB_QUERY_CLIENT_API_KEY</code>, clients should send{" "}
            <code>x-api-key</code> or <code>Authorization: Bearer ...</code>{" "}
            with requests to
            <code> /api/query</code>.
          </p>
          <p>
            That prompt endpoint can also be rate-limited to protect the
            lower-cost public LLM key. When the limit is exceeded, the service
            returns <code>429</code> plus
            <code> Retry-After</code> and <code>X-RateLimit-*</code> headers.
          </p>
          <p>
            If no dedicated prompt-query LLM key is configured,{" "}
            <code>/api/query</code> falls back to plain text search over items
            and workflows instead of failing.
          </p>
        </div>
      </section>

      <section className="mb-12 grid gap-6 lg:grid-cols-2">
        <div className="border border-edge bg-surface p-5">
          <p className="small-caps mb-3">Structured Query Example</p>
          <p className="mb-3 text-sm leading-relaxed text-ink-muted">
            Add <code>x-api-key: YOUR_SITE_KEY</code> only if this deployment
            requires a client key.
          </p>
          <pre className="overflow-x-auto font-data text-xs leading-relaxed text-ink-secondary">
            <code>{structuredQueryExample}</code>
          </pre>
        </div>
        <div className="border border-edge bg-surface p-5">
          <p className="small-caps mb-3">Prompt Query Example</p>
          <p className="mb-3 text-sm leading-relaxed text-ink-muted">
            Add <code>x-api-key: YOUR_SITE_KEY</code> only if this deployment
            requires a client key.
          </p>
          <pre className="overflow-x-auto font-data text-xs leading-relaxed text-ink-secondary">
            <code>{promptQueryExample}</code>
          </pre>
        </div>
      </section>

      <section className="border border-edge bg-surface p-6">
        <p className="small-caps mb-3">Related Pages</p>
        <p className="text-sm leading-relaxed text-ink-secondary">
          Explore the dataset visually in{" "}
          <Link href="/items" className="text-accent hover:text-accent-hover">
            the collection browser
          </Link>{" "}
          and review DBTL templates in{" "}
          <Link
            href="/workflows"
            className="text-accent hover:text-accent-hover"
          >
            workflow views
          </Link>
          .
        </p>
      </section>
    </div>
  );
}
