import type { WorkflowStep } from "@/lib/types";

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
        {[
          ["Wall time", formatHours(totalHours)],
          ["Hands-on", formatHours(totalHands)],
          ["Direct cost", formatCost(totalCost)],
        ].map(([label, value]) => (
          <div key={label}>
            <p className="text-xs text-ink-muted">{label}</p>
            <p className="font-display text-xl text-ink">{value}</p>
          </div>
        ))}
      </div>

      {/* Steps as a clean table-like layout */}
      <div className="space-y-0">
        {steps.map((step, idx) => (
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
              {step.parallelizable && (
                <span className="ml-2 text-xs text-brand">parallelizable</span>
              )}
              {step.failure_probability !== null && step.failure_probability > 0.05 && (
                <span className="ml-2 text-xs text-caution">
                  {Math.round(step.failure_probability * 100)}% fail
                </span>
              )}
            </div>
            <span className="font-data text-xs tabular-nums text-ink-muted">
              {formatHours(step.duration_typical_hours)}
            </span>
            <span className="w-16 text-right font-data text-xs tabular-nums text-ink-muted">
              {formatCost(step.direct_cost_usd_typical)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
