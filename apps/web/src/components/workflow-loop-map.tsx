"use client";

import type { WorkflowStep } from "@/lib/types";
import { getWorkflowPhases, type WorkflowPhaseSummary } from "@/lib/workflow-phases";

function formatHours(hours: number): string {
  if (hours <= 0) return "0h";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours >= 24) return `~${Math.round(hours / 24)}d`;
  return `${Math.round(hours * 10) / 10}h`;
}

function formatCost(usd: number): string {
  if (usd <= 0) return "$0";
  return `$${usd.toLocaleString()}`;
}

function phaseCardClasses(key: WorkflowPhaseSummary["key"]): string {
  switch (key) {
    case "design":
      return "md:col-start-1 md:row-start-1";
    case "build":
      return "md:col-start-2 md:row-start-1";
    case "learn":
      return "md:col-start-1 md:row-start-2";
    case "test":
      return "md:col-start-2 md:row-start-2";
  }
}

export function WorkflowLoopMap({ steps }: { steps: WorkflowStep[] }) {
  const phases = getWorkflowPhases(steps, { includeEmpty: true });

  if (steps.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-edge bg-surface-alt p-5">
      <div className="mb-4">
        <p className="small-caps mb-2">Loop Map</p>
        <p className="max-w-3xl text-sm leading-6 text-ink-secondary">
          A schema-driven DBTL view that groups ordered workflow steps into
          design, build, test, and learn phases, then shows how the workflow
          loops back for the next iteration.
        </p>
      </div>

      <div className="mb-5 font-ui text-xs text-ink-muted md:hidden">
        Design → Build → Test → Learn → repeat
      </div>

      <div className="relative grid gap-4 md:grid-cols-2 md:grid-rows-2 md:gap-8">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 hidden md:block"
        >
          <span className="absolute top-[22%] left-1/2 -translate-x-1/2 text-lg text-accent/70 md:text-xl">
            →
          </span>
          <span className="absolute top-1/2 right-[22%] -translate-y-1/2 text-lg text-accent/70 md:text-xl">
            ↓
          </span>
          <span className="absolute bottom-[22%] left-1/2 -translate-x-1/2 text-lg text-accent/70 md:text-xl">
            ←
          </span>
          <span className="absolute top-1/2 left-[22%] -translate-y-1/2 text-lg text-accent/70 md:text-xl">
            ↑
          </span>
          <div className="absolute top-1/2 left-1/2 flex h-20 w-20 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-edge bg-surface/90 text-center md:h-24 md:w-24">
            <div>
              <p className="small-caps text-accent">DBTL</p>
              <p className="font-ui text-[11px] text-ink-muted">repeat</p>
            </div>
          </div>
        </div>

        {phases.map((phase) => {
          const visibleSteps = phase.steps.slice(0, 3);
          const hiddenStepCount = Math.max(0, phase.steps.length - visibleSteps.length);

          return (
            <div
              key={phase.key}
              className={`relative rounded-lg border border-edge bg-surface p-4 ${phaseCardClasses(phase.key)}`}
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-display text-lg text-ink">{phase.label}</h3>
                  <p className="text-sm leading-6 text-ink-secondary">
                    {phase.description}
                  </p>
                </div>
                <span className="font-data text-xs text-ink-muted">
                  {phase.steps.length} step{phase.steps.length === 1 ? "" : "s"}
                </span>
              </div>

              <div className="mb-4 flex flex-wrap gap-x-4 gap-y-1 font-ui text-xs text-ink-muted">
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
                {phase.parallelizableCount > 0 && (
                  <span>{phase.parallelizableCount} parallelizable</span>
                )}
                {phase.retryRiskCount > 0 && (
                  <span className="text-caution">
                    {phase.retryRiskCount} repeat-risk
                  </span>
                )}
              </div>

              {phase.stageNames.length > 0 && (
                <div className="mb-4 flex flex-wrap gap-2">
                  {phase.stageNames.map((stageName) => (
                    <span
                      key={stageName}
                      className="rounded-full bg-surface-alt px-2.5 py-1 font-ui text-[11px] text-ink-muted"
                    >
                      {stageName}
                    </span>
                  ))}
                </div>
              )}

              {phase.steps.length > 0 ? (
                <div className="space-y-2">
                  {visibleSteps.map((step, index) => (
                    <div
                      key={step.id}
                      className="rounded-md border border-edge bg-surface-alt px-3 py-2 text-sm text-ink-secondary"
                    >
                      <span className="mr-2 font-data text-xs text-ink-muted">
                        {index + 1}
                      </span>
                      <span>{step.step_name}</span>
                    </div>
                  ))}
                  {hiddenStepCount > 0 && (
                    <p className="font-ui text-xs text-ink-muted">
                      +{hiddenStepCount} more step
                      {hiddenStepCount === 1 ? "" : "s"} in this phase
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-sm leading-6 text-ink-muted">
                  No explicit {phase.label.toLowerCase()} step is present in this
                  workflow schema.
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
