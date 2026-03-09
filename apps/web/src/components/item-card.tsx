"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ToolkitItem } from "@/lib/types";
import { renderInlineTitle, stripInlineTitleMarkup } from "@/lib/render-inline-title";
import {
  isSupportedTechnique,
  ITEM_TYPE_LABELS,
  MECHANISM_LABELS,
  TECHNIQUE_LABELS,
} from "@/lib/vocabularies";
import { Tooltip } from "./tooltip";
import { ValidationDots } from "./validation-dots";
import { ITEM_TYPE_DESCRIPTIONS, MECHANISM_DESCRIPTIONS, STATUS_DESCRIPTIONS, TECHNIQUE_DESCRIPTIONS } from "@/lib/explanations";

function Tag({
  label,
  href,
  tooltip,
}: {
  label: string;
  href: string;
  tooltip?: string;
}) {
  const inner = (
    <Link
      href={href}
      onClick={(e) => e.stopPropagation()}
      className="inline-block rounded bg-surface-alt px-1.5 py-0.5 text-ink-muted transition-colors hover:bg-edge hover:text-ink"
    >
      {label}
    </Link>
  );

  if (tooltip) {
    return (
      <Tooltip content={tooltip} position="bottom">
        {inner}
      </Tooltip>
    );
  }
  return inner;
}

export function ItemCard({ item }: { item: ToolkitItem }) {
  const router = useRouter();
  const plainTitle = stripInlineTitleMarkup(item.canonical_name);

  return (
    <article
      role="link"
      tabIndex={0}
      aria-label={`Open ${plainTitle}`}
      onClick={() => router.push(`/items/${item.slug}`)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          router.push(`/items/${item.slug}`);
        }
      }}
      className="group block cursor-pointer rounded-sm border-b border-edge py-6 outline-none transition-colors hover:border-accent focus-visible:border-accent focus-visible:ring-2 focus-visible:ring-brand/30"
    >
      {/* Top line: name + type */}
      <div className="mb-1.5 flex items-baseline justify-between gap-4">
        <h3 className="text-lg text-ink group-hover:text-accent">
          {renderInlineTitle(item.canonical_name)}
        </h3>
        <Tooltip
          content={
            ITEM_TYPE_DESCRIPTIONS[item.item_type] ??
            `Filter by ${ITEM_TYPE_LABELS[item.item_type]}`
          }
          position="bottom"
        >
          <Link
            href={`/items?type=${item.item_type}`}
            onClick={(e) => e.stopPropagation()}
            className="small-caps shrink-0 transition-colors hover:text-accent"
          >
            {ITEM_TYPE_LABELS[item.item_type]}
          </Link>
        </Tooltip>
      </div>

      {/* Metadata tags */}
      <div className="mb-2 flex flex-wrap items-center gap-1.5 font-ui text-xs">
        {item.family && (
          <Tag
            label={item.family}
            href={`/items?family=${item.family}`}
            tooltip={`Filter by family: ${item.family}`}
          />
        )}
        {item.first_publication_year && (
          <Tooltip content={`First published in ${item.first_publication_year}`} position="bottom">
            <span className="cursor-help px-1 text-ink-muted">
              Since {item.first_publication_year}
            </span>
          </Tooltip>
        )}
        {item.mechanisms.map((m) => (
          <Tag
            key={m}
            label={MECHANISM_LABELS[m] ?? m.replace(/_/g, " ")}
            href={`/items?mechanism=${m}`}
            tooltip={MECHANISM_DESCRIPTIONS[m]}
          />
        ))}
        {item.techniques.filter(isSupportedTechnique).map((t) => (
          <Tag
            key={t}
            label={TECHNIQUE_LABELS[t] ?? t.replace(/_/g, " ")}
            href={`/items?technique=${t}`}
            tooltip={TECHNIQUE_DESCRIPTIONS[t]}
          />
        ))}
        {item.status === "seed" && (
          <Tooltip content={STATUS_DESCRIPTIONS.seed} position="bottom">
            <span className="cursor-help italic text-caution">seed</span>
          </Tooltip>
        )}
      </div>

      {/* Summary */}
      {item.summary && (
        <p className="mb-3 line-clamp-2 text-[15px] leading-relaxed text-ink-secondary">
          {renderInlineTitle(item.summary)}
        </p>
      )}

      {/* Scores + validation */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        {item.validation_rollup ? (
          <ValidationDots rollup={item.validation_rollup} />
        ) : item.status === "seed" ? (
          <Tooltip content="Validation data will appear after source-backed curation is complete." position="bottom">
            <span className="cursor-help font-ui text-xs italic text-caution">awaiting curation</span>
          </Tooltip>
        ) : null}

        {item.replication_summary ? (
          <div className="flex gap-4 font-data text-xs tabular-nums text-ink-muted">
            {item.replication_summary.evidence_strength_score !== null && (
              <Tooltip content="Evidence strength: breadth and quality of published support" position="top">
                <span className="cursor-help">Ev <strong className="text-ink">{Math.round(item.replication_summary.evidence_strength_score * 100)}</strong></span>
              </Tooltip>
            )}
            {item.replication_summary.replication_score !== null && (
              <Tooltip content="Replication: independent reproduction across labs and contexts" position="top">
                <span className="cursor-help">Rep <strong className="text-ink">{Math.round(item.replication_summary.replication_score * 100)}</strong></span>
              </Tooltip>
            )}
            {item.replication_summary.practicality_score !== null && (
              <Tooltip content="Practicality: ease of use, accounting for known pitfalls" position="top">
                <span className="cursor-help">Pr <strong className="text-ink">{Math.round(item.replication_summary.practicality_score * 100)}</strong></span>
              </Tooltip>
            )}
          </div>
        ) : null}
      </div>
    </article>
  );
}
