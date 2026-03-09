"use client";

import { Tooltip } from "./tooltip";
import { PROBLEM_LINK_DESCRIPTIONS, SCORE_DESCRIPTIONS } from "@/lib/explanations";

const LABEL_TO_KEY: Record<string, string> = {
  Evidence:        "evidence_strength_score",
  Replication:     "replication_score",
  Practicality:    "practicality_score",
  Translatability: "translatability_score",
};

function scoreColor(value: number): string {
  if (value >= 0.75) return "bg-emerald-500";
  if (value >= 0.5) return "bg-amber-400";
  return "bg-red-400";
}

export function ScoreBar({
  label,
  value,
  showValue = true,
  explanationKey,
}: {
  label: string;
  value: number | null;
  showValue?: boolean;
  explanationKey?: string;
}) {
  if (value === null) {
    return (
      <div className="flex items-center gap-2">
        <span className="w-24 shrink-0 text-xs text-ink-muted">{label}</span>
        <span className="text-xs text-ink-faint">&mdash;</span>
      </div>
    );
  }

  const pct = Math.round(value * 100);
  const key = explanationKey || LABEL_TO_KEY[label];
  const explanation =
    (key ? SCORE_DESCRIPTIONS[key] : undefined) ||
    (key ? PROBLEM_LINK_DESCRIPTIONS[key] : undefined);

  const labelEl = (
    <span className={`w-24 shrink-0 text-xs text-ink-muted ${explanation ? "cursor-help border-b border-dotted border-ink-faint" : ""}`}>
      {label}
    </span>
  );

  return (
    <div className="flex items-center gap-2">
      {explanation ? (
        <Tooltip content={explanation} position="bottom">
          {labelEl}
        </Tooltip>
      ) : (
        labelEl
      )}
      <div className="h-1.5 flex-1 rounded-full bg-surface-alt">
        <div
          className={`h-1.5 rounded-full transition-all ${scoreColor(value)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showValue && (
        <Tooltip
          content={`${pct}/100 — ${pct >= 75 ? "Strong" : pct >= 50 ? "Moderate" : "Weak"}`}
          position="bottom"
        >
          <span className="w-8 cursor-help text-right font-data text-xs font-medium tabular-nums text-ink-secondary">
            {pct}
          </span>
        </Tooltip>
      )}
    </div>
  );
}

export function ScoreBreakdown({
  scores,
}: {
  scores: { label: string; value: number | null; explanationKey?: string }[];
}) {
  return (
    <div className="space-y-2 font-ui">
      {scores.map((s) => (
        <ScoreBar
          key={s.label}
          label={s.label}
          value={s.value}
          explanationKey={s.explanationKey}
        />
      ))}
    </div>
  );
}
