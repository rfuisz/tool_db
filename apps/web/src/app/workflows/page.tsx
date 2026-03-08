import { WORKFLOWS } from "@/lib/data";
import { WORKFLOW_FAMILY_LABELS } from "@/lib/vocabularies";
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

            <div className="rounded-lg bg-surface p-6">
              <WorkflowTimeline steps={w.steps} />
            </div>

            <hr className="mt-16" />
          </section>
        ))}
      </div>
    </div>
  );
}
