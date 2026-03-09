import { getGaps } from "@/lib/backend-data";

export default async function GapsPage() {
  const gaps = await getGaps();

  return (
    <div>
      <header className="mb-16">
        <h1 className="mb-3">Gap Map Relationships</h1>
        <p className="max-w-3xl text-lg text-ink-secondary">
          Problem statements from Convergent Research&apos;s Gap Map, normalized
          into fields, foundational capabilities, and related resources so they
          can become explainable targets for toolkit matching.
        </p>
      </header>

      {gaps.length === 0 ? (
        <p className="text-ink-muted">
          No normalized Gap Map relationships are available yet in the current
          backend.
        </p>
      ) : (
        <div className="space-y-6">
          {gaps.map((gap) => (
            <details
              key={gap.external_gap_item_id}
              className="border border-edge bg-surface p-5"
            >
              <summary className="cursor-pointer list-none">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-xl text-ink">{gap.title}</h2>
                    {gap.field ? (
                      <p className="mt-1 font-ui text-xs uppercase tracking-wide text-ink-muted">
                        {gap.field.name}
                      </p>
                    ) : null}
                  </div>
                  <div className="font-data text-xs tabular-nums text-ink-muted">
                    {gap.capability_count} capabilities
                  </div>
                </div>
              </summary>

              {gap.description ? (
                <p className="mt-4 max-w-4xl leading-relaxed text-ink-secondary">
                  {gap.description}
                </p>
              ) : null}

              {gap.tags.length > 0 ? (
                <p className="mt-4 font-ui text-sm text-ink-secondary">
                  Tags: {gap.tags.join(", ")}
                </p>
              ) : null}

              <div className="mt-6 space-y-4">
                {gap.capabilities.map((capability) => (
                  <section key={capability.external_gap_capability_id}>
                    <h3 className="text-lg text-ink">{capability.name}</h3>
                    {capability.description ? (
                      <p className="mt-1 max-w-3xl text-sm leading-relaxed text-ink-secondary">
                        {capability.description}
                      </p>
                    ) : null}
                    {capability.tags.length > 0 ? (
                      <p className="mt-2 font-ui text-xs uppercase tracking-wide text-ink-muted">
                        {capability.tags.join(" · ")}
                      </p>
                    ) : null}
                    {capability.resources.length > 0 ? (
                      <ul className="mt-3 space-y-2">
                        {capability.resources.map((resource) => (
                          <li
                            key={resource.external_gap_resource_id}
                            className="border-l-2 border-accent/30 pl-3"
                          >
                            <p className="font-ui text-sm text-ink">
                              {resource.url ? (
                                <a
                                  href={resource.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-brand hover:text-accent"
                                >
                                  {resource.title}
                                </a>
                              ) : (
                                resource.title
                              )}
                            </p>
                            {resource.summary ? (
                              <p className="mt-1 text-sm leading-relaxed text-ink-secondary">
                                {resource.summary}
                              </p>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </section>
                ))}
              </div>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
