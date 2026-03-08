import { WORKFLOWS } from "@/lib/data";
import { WORKFLOW_FAMILY_LABELS } from "@/lib/vocabularies";
import { WorkflowPhaseBreakdown } from "@/components/workflow-phase-breakdown";
import { WorkflowTimeline } from "@/components/workflow-timeline";

export default function WorkflowsPage() {
  return (
    <div>
      <header className="mb-16">
        <h1 className="mb-3">Workflows</h1>
        <p className="max-w-xl text-lg text-ink-secondary">
          Design&#x2013;Build&#x2013;Test&#x2013;Learn loop archetypes with step-level
          timing and cost estimates.
        </p>
      </header>

      <div className="space-y-16">
        {WORKFLOWS.map((w) => (
          <section key={w.id} id={w.slug}>
            <div className="mb-6">
              <h2 className="mb-1 text-ink">{w.name}</h2>
              <p className="font-ui text-sm text-ink-muted">
                {WORKFLOW_FAMILY_LABELS[w.workflow_family]}
                {w.throughput_class && <> &middot; {w.throughput_class.replace(/_/g, " ")}</>}
              </p>
              <p className="mt-2 text-[15px] text-ink-secondary">{w.objective}</p>
              {w.recommended_for && (
                <p className="mt-1 font-ui text-xs text-ink-muted">
                  Recommended for: {w.recommended_for}
                </p>
              )}
            </div>

            <div className="mb-6">
              <WorkflowPhaseBreakdown steps={w.steps} />
            </div>

            <div className="rounded-lg bg-surface p-6">
              <WorkflowTimeline steps={w.steps} />
            </div>

            {(w.simple_summary ||
              (w.how_to_implement && w.how_to_implement.length > 0) ||
              (w.used_when && w.used_when.length > 0) ||
              (w.tradeoffs && w.tradeoffs.length > 0) ||
              (w.citations && w.citations.length > 0)) && (
              <div className="mt-6 grid gap-4 lg:grid-cols-2">
                {w.simple_summary && (
                  <div className="rounded-lg border border-edge bg-surface-alt p-5">
                    <p className="small-caps mb-3">Simple Summary</p>
                    <p className="text-sm leading-6 text-ink-secondary">
                      {w.simple_summary}
                    </p>
                  </div>
                )}

                {w.used_when && w.used_when.length > 0 && (
                  <div className="rounded-lg border border-edge bg-surface-alt p-5">
                    <p className="small-caps mb-3">Used When</p>
                    <ul className="space-y-2 text-sm leading-6 text-ink-secondary">
                      {w.used_when.map((note) => (
                        <li key={note}>{note}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {w.how_to_implement && w.how_to_implement.length > 0 && (
                  <div className="rounded-lg border border-edge bg-surface-alt p-5">
                    <p className="small-caps mb-3">How To Implement</p>
                    <ol className="space-y-2 text-sm leading-6 text-ink-secondary">
                      {w.how_to_implement.map((note, index) => (
                        <li key={note}>
                          <span className="mr-2 font-data text-ink-muted">
                            {index + 1}.
                          </span>
                          {note}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {w.tradeoffs && w.tradeoffs.length > 0 && (
                  <div className="rounded-lg border border-edge bg-surface-alt p-5">
                    <p className="small-caps mb-3">Tradeoffs</p>
                    <ul className="space-y-2 text-sm leading-6 text-ink-secondary">
                      {w.tradeoffs.map((note) => (
                        <li key={note}>{note}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {w.citations && w.citations.length > 0 && (
                  <div className="rounded-lg border border-edge bg-surface-alt p-5 lg:col-span-2">
                    <p className="small-caps mb-3">Key Citations</p>
                    <ul className="space-y-3">
                      {w.citations.map((citation) => (
                        <li key={citation.href} className="text-sm leading-6 text-ink-secondary">
                          <a
                            href={citation.href}
                            target="_blank"
                            rel="noreferrer"
                            className="text-brand hover:text-accent"
                          >
                            {citation.title}
                          </a>
                          <p className="text-ink-muted">{citation.note}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <hr className="mt-16" />
          </section>
        ))}
      </div>
    </div>
  );
}
