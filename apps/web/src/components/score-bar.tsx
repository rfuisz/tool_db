function scoreColor(value: number): string {
  if (value >= 0.75) return "bg-emerald-500";
  if (value >= 0.5) return "bg-amber-400";
  return "bg-red-400";
}

export function ScoreBar({
  label,
  value,
  showValue = true,
}: {
  label: string;
  value: number | null;
  showValue?: boolean;
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

  return (
    <div className="flex items-center gap-2">
      <span className="w-24 shrink-0 text-xs text-ink-muted">{label}</span>
      <div className="h-1.5 flex-1 rounded-full bg-surface-alt">
        <div
          className={`h-1.5 rounded-full transition-all ${scoreColor(value)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showValue && (
        <span className="w-8 text-right font-data text-xs font-medium tabular-nums text-ink-secondary">
          {pct}
        </span>
      )}
    </div>
  );
}

export function ScoreBreakdown({
  scores,
}: {
  scores: { label: string; value: number | null }[];
}) {
  return (
    <div className="space-y-2 font-ui">
      {scores.map((s) => (
        <ScoreBar key={s.label} label={s.label} value={s.value} />
      ))}
    </div>
  );
}
