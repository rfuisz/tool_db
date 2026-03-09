"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { renderInlineTitle } from "@/lib/render-inline-title";
import type { ReplicationSummary } from "@/lib/types";

interface ListableItem {
  slug: string;
  canonical_name: string;
  summary: string | null;
  replication_summary?: ReplicationSummary | null;
}

type SortKey = "score" | "name" | "name-desc";

function listItemScore(item: ListableItem): number {
  const rs = item.replication_summary;
  if (!rs) return 0;
  return (
    (rs.evidence_strength_score ?? 0) +
    (rs.replication_score ?? 0) +
    (rs.practicality_score ?? 0)
  );
}

function matchesSearch(item: ListableItem, query: string): boolean {
  if (!query) return true;
  const lower = query.toLowerCase();
  return (
    item.canonical_name.toLowerCase().includes(lower) ||
    (item.summary?.toLowerCase().includes(lower) ?? false)
  );
}

export function SearchableItemList({
  title,
  items,
}: {
  title: string;
  items: ListableItem[];
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("score");

  const filtered = useMemo(() => {
    const matched = items.filter((i) => matchesSearch(i, searchQuery));
    const sorted = [...matched];
    switch (sortBy) {
      case "score":
        sorted.sort((a, b) => {
          const delta = listItemScore(b) - listItemScore(a);
          if (delta !== 0) return delta;
          return a.canonical_name.localeCompare(b.canonical_name);
        });
        break;
      case "name-desc":
        sorted.sort((a, b) => b.canonical_name.localeCompare(a.canonical_name));
        break;
      case "name":
      default:
        sorted.sort((a, b) => a.canonical_name.localeCompare(b.canonical_name));
        break;
    }
    return sorted;
  }, [items, searchQuery, sortBy]);

  if (items.length === 0) return null;

  return (
    <section className="mb-10">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <h2>{title}</h2>
        <span className="font-data text-sm text-ink-muted">
          {filtered.length} of {items.length}
        </span>
      </div>

      {items.length > 4 && (
        <div className="mb-4 flex flex-wrap items-center gap-3 font-ui text-sm">
          <input
            type="text"
            placeholder="Search…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 w-48 border-b border-edge bg-transparent px-0 text-ink placeholder-ink-muted outline-none transition-colors focus:border-accent"
          />
          <button
            type="button"
            onClick={() =>
              setSortBy(
                sortBy === "score"
                  ? "name"
                  : sortBy === "name"
                    ? "name-desc"
                    : "score",
              )
            }
            className="border-b border-edge pb-0.5 text-ink-muted transition-colors hover:border-accent hover:text-ink"
          >
            {sortBy === "score"
              ? "Score"
              : sortBy === "name"
                ? "A \u2192 Z"
                : "Z \u2192 A"}
          </button>
        </div>
      )}

      {filtered.length === 0 ? (
        <p className="py-8 text-center text-ink-muted">
          No items match your search.
        </p>
      ) : (
        <div className="space-y-4">
          {filtered.map((item) => (
            <article key={item.slug} className="border border-edge p-5">
              <Link
                href={`/items/${item.slug}`}
                className="text-lg text-brand hover:text-accent"
              >
                {renderInlineTitle(item.canonical_name)}
              </Link>
              {item.summary ? (
                <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                  {renderInlineTitle(item.summary)}
                </p>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
