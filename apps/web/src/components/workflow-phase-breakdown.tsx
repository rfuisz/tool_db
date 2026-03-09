import type { WorkflowStep } from "@/lib/types";
import { getWorkflowPhases } from "@/lib/workflow-phases";

function formatHours(h: number): string {
  if (h <= 0) return "0h";
  if (h < 1) return `${Math.round(h * 60)}m`;
  if (h >= 24) return `~${Math.round(h / 24)}d`;
  return `${Math.round(h * 10) / 10}h`;
}

function formatCost(usd: number): string {
  if (usd <= 0) return "$0";
  return `$${usd.toLocaleString()}`;
}

export function WorkflowPhaseBreakdown({ steps }: { steps: WorkflowStep[] }) {
  const phases = getWorkflowPhases(steps);

  if (phases.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-edge bg-surface-alt p-5">
      <div className="mb-4">
        <p className="small-caps mb-2">Phase Breakdown</p>
        <p className="max-w-3xl text-sm leading-6 text-ink-secondary">
          A high-level view of how the workflow collapses into concrete lab or
          analysis steps.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-4">
        {phases.map((phase, index) => (
          <div
            key={phase.key}
            className="relative rounded-lg border border-edge bg-surface p-4"
          >
            {index < phases.length - 1 && (
              <div
                aria-hidden="true"
                className="hidden lg:block absolute top-1/2 -right-2 z-10 text-ink-faint"
              >
                →
              </div>
            )}

            <div className="mb-3">
              <div className="mb-1 flex items-center justify-between gap-3">
                <h3 className="font-display text-lg text-ink">{phase.label}</h3>
                <span className="font-data text-xs text-ink-muted">
                  {phase.steps.length} step{phase.steps.length === 1 ? "" : "s"}
                </span>
              </div>
              <p className="text-sm leading-6 text-ink-secondary">
                {phase.description}
              </p>
            </div>

            <div className="mb-4 flex gap-4 font-ui text-xs text-ink-muted">
              <span>
                Time:{" "}
                <span className="font-data text-ink">
                  {formatHours(phase.totalHours)}
                </span>
              </span>
              <span>
                Cost:{" "}
                <span className="font-data text-ink">
                  {formatCost(phase.totalCost)}
                </span>
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {phase.steps.map((step, stepIndex) => (
                <div
                  key={step.id}
                  className="rounded-md border border-edge bg-surface-alt px-3 py-2 text-sm text-ink-secondary"
                >
                  <span className="mr-2 font-data text-xs text-ink-muted">
                    {stepIndex + 1}
                  </span>
                  <span>{step.step_name}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
