"use client";

import type { WorkflowStep } from "@/lib/types";
import { Tooltip } from "./tooltip";
import { STEP_TYPE_EXPLANATIONS } from "@/lib/explanations";

function formatHours(h: number | null): string {
  if (h === null) return "\u2014";
  if (h < 1) return `${Math.round(h * 60)}m`;
  if (h >= 24) return `~${Math.round(h / 24)}d`;
  return `${h}h`;
}

function formatCost(usd: number | null): string {
  if (usd === null) return "\u2014";
  if (usd === 0) return "$0";
  return `$${usd.toLocaleString()}`;
}

export function WorkflowTimeline({ steps }: { steps: WorkflowStep[] }) {
  const totalHours = steps.reduce((sum, s) => sum + (s.duration_typical_hours ?? 0), 0);
  const totalCost = steps.reduce((sum, s) => sum + (s.direct_cost_usd_typical ?? 0), 0);
  const totalHands = steps.reduce((sum, s) => sum + (s.hands_on_hours ?? 0), 0);

  return (
    <div className="font-ui">
      {/* Totals */}
      <div className="mb-8 flex gap-10">
        {([
          ["Wall time", formatHours(totalHours), "Total calendar time from start to finish, including wait times"],
          ["Hands-on", formatHours(totalHands), "Active bench time requiring human attention"],
          ["Direct cost", formatCost(totalCost), "Reagent and service costs, excluding labor"],
        ] as const).map(([label, value, tip]) => (
          <Tooltip key={label} content={tip} position="bottom">
            <span className="block cursor-help">
              <span className="block text-xs text-ink-muted">{label}</span>
              <span className="block font-display text-xl text-ink">{value}</span>
            </span>
          </Tooltip>
        ))}
      </div>

      {/* Steps */}
      <div className="space-y-0">
        {steps.map((step, idx) => {
          const stepExplanation = STEP_TYPE_EXPLANATIONS[step.step_type];
          return (
            <div
              key={step.id}
              className="flex items-baseline gap-4 border-b border-edge py-3 last:border-b-0"
            >
              <span className="w-5 shrink-0 font-data text-xs text-ink-muted">
                {idx + 1}
              </span>
              <div className="flex-1">
                <span className="font-body text-sm font-medium text-ink">
                  {step.step_name}
                </span>
                {stepExplanation && (
                  <Tooltip content={stepExplanation} position="bottom">
                    <span className="ml-1.5 cursor-help border-b border-dotted border-ink-faint text-xs text-ink-muted">
                      {step.step_type.replace(/_/g, " ")}
                    </span>
                  </Tooltip>
                )}
                {step.parallelizable && (
                  <Tooltip content="This step can run in parallel with adjacent steps, reducing total wall time" position="bottom">
                    <span className="ml-2 cursor-help text-xs text-brand">parallelizable</span>
                  </Tooltip>
                )}
                {step.failure_probability !== null && step.failure_probability > 0.05 && (
                  <Tooltip content={`${Math.round(step.failure_probability * 100)}% probability this step will need to be repeated`} position="bottom">
                    <span className="ml-2 cursor-help text-xs text-caution">
                      {Math.round(step.failure_probability * 100)}% fail
                    </span>
                  </Tooltip>
                )}
              </div>
              <Tooltip content={`Wall time: ${formatHours(step.duration_typical_hours)}${step.hands_on_hours ? ` (${formatHours(step.hands_on_hours)} hands-on)` : ""}`} position="top">
                <span className="cursor-help font-data text-xs tabular-nums text-ink-muted">
                  {formatHours(step.duration_typical_hours)}
                </span>
              </Tooltip>
              <Tooltip content={`Direct cost for this step (reagents, services)`} position="top">
                <span className="w-16 cursor-help text-right font-data text-xs tabular-nums text-ink-muted">
                  {formatCost(step.direct_cost_usd_typical)}
                </span>
              </Tooltip>
            </div>
          );
        })}
      </div>
    </div>
  );
}
