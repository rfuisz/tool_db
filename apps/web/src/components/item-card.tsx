import Link from "next/link";
import type { ToolkitItem } from "@/lib/types";
import { ITEM_TYPE_LABELS } from "@/lib/vocabularies";
import { ScoreBar } from "./score-bar";
import { ValidationDots } from "./validation-dots";

export function ItemCard({ item }: { item: ToolkitItem }) {
  return (
    <Link
      href={`/items/${item.slug}`}
      className="group block border-b border-edge py-6 transition-colors hover:border-accent"
    >
      {/* Top line: name + type */}
      <div className="mb-1.5 flex items-baseline justify-between gap-4">
        <h3 className="text-lg text-ink group-hover:text-accent">
          {item.canonical_name}
        </h3>
        <span className="small-caps shrink-0">
          {ITEM_TYPE_LABELS[item.item_type]}
        </span>
      </div>

      {/* Metadata line */}
      <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1 font-ui text-xs text-ink-muted">
        {item.family && <span>{item.family}</span>}
        {item.first_publication_year && <span>Since {item.first_publication_year}</span>}
        {item.mechanisms.map((m) => (
          <span key={m} className="text-ink-faint">{m.replace(/_/g, " ")}</span>
        ))}
        {item.techniques.map((t) => (
          <span key={t} className="text-ink-faint">{t.replace(/_/g, " ")}</span>
        ))}
      </div>

      {/* Summary */}
      {item.summary && (
        <p className="mb-3 line-clamp-2 text-[15px] leading-relaxed text-ink-secondary">
          {item.summary}
        </p>
      )}

      {/* Scores + validation */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        {item.validation_rollup ? (
          <ValidationDots rollup={item.validation_rollup} />
        ) : item.status === "seed" ? (
          <span className="font-ui text-xs italic text-caution">seed &mdash; awaiting curation</span>
        ) : null}

        {item.replication_summary ? (
          <div className="flex gap-4 font-data text-xs tabular-nums text-ink-muted">
            {item.replication_summary.evidence_strength_score !== null && (
              <span>Ev <strong className="text-ink">{Math.round(item.replication_summary.evidence_strength_score * 100)}</strong></span>
            )}
            {item.replication_summary.replication_score !== null && (
              <span>Rep <strong className="text-ink">{Math.round(item.replication_summary.replication_score * 100)}</strong></span>
            )}
            {item.replication_summary.practicality_score !== null && (
              <span>Pr <strong className="text-ink">{Math.round(item.replication_summary.practicality_score * 100)}</strong></span>
            )}
          </div>
        ) : null}
      </div>
    </Link>
  );
}
