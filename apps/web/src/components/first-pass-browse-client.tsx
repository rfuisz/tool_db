"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { FirstPassItemSummary } from "@/lib/types";

export function FirstPassBrowseClient({
  items,
}: {
  items: FirstPassItemSummary[];
}) {
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState<"sources" | "claims" | "name">("sources");

  const filtered = useMemo(() => {
    const lowered = query.trim().toLowerCase();
    const base = lowered
      ? items.filter((item) => {
          const haystacks = [
            item.canonical_name,
            item.item_type ?? "",
            item.evidence_preview ?? "",
            ...item.evidence_previews,
            ...item.claim_previews,
            ...item.aliases,
          ].map((value) => value.toLowerCase());
          return haystacks.some((value) => value.includes(lowered));
        })
      : items;
    return [...base].sort((a, b) => {
      if (sortBy === "claims") {
        return (
          b.claim_count - a.claim_count ||
          b.source_document_count - a.source_document_count ||
          a.canonical_name.localeCompare(b.canonical_name)
        );
      }
      if (sortBy === "name") {
        return a.canonical_name.localeCompare(b.canonical_name);
      }
      return (
        b.source_document_count - a.source_document_count ||
        b.claim_count - a.claim_count ||
        a.canonical_name.localeCompare(b.canonical_name)
      );
    });
  }, [items, query, sortBy]);

  return (
    <div>
      <header className="mb-10">
        <p className="small-caps mb-3">Bulk Extracted Review Layer</p>
        <h1 className="mb-3">First-pass extracted items</h1>
        <p className="max-w-3xl text-ink-secondary">
          These records are loaded directly from extracted packets so you can judge
          whether the system is pulling out useful entities and claims before
          deeper canonical cleanup.
        </p>
      </header>

      <div className="mb-8 flex flex-wrap items-center gap-3 font-ui text-sm">
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search extracted names, aliases, evidence..."
          className="h-9 w-80 border-b border-edge bg-transparent px-0 text-ink placeholder-ink-muted outline-none transition-colors focus:border-accent"
        />
        <select
          value={sortBy}
          onChange={(event) => setSortBy(event.target.value as typeof sortBy)}
          className="h-9 border-b border-edge bg-transparent font-ui text-ink outline-none"
        >
          <option value="sources">Most source documents</option>
          <option value="claims">Most linked claims</option>
          <option value="name">Name</option>
        </select>
        <span className="ml-auto text-ink-muted">
          {filtered.length} extracted item{filtered.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="space-y-4">
        {filtered.map((item) => (
          <article key={item.slug} className="border border-edge bg-surface p-5">
            <div className="mb-2 flex flex-wrap items-start justify-between gap-3">
              <div>
                <Link
                  href={`/first-pass/${item.slug}`}
                  className="text-lg text-ink hover:text-accent"
                >
                  {item.canonical_name}
                </Link>
                {item.item_type ? (
                  <p className="mt-1 font-ui text-xs uppercase tracking-wide text-ink-muted">
                    {item.item_type.replace(/_/g, " ")}
                  </p>
                ) : null}
              </div>
              <div className="font-data text-xs tabular-nums text-ink-muted">
                <div>{item.source_document_count} sources</div>
                <div>{item.claim_count} claims</div>
              </div>
            </div>

            {item.matched_slug ? (
              <p className="mb-2 font-ui text-xs text-valid">
                Canonical match suggestion: <code>{item.matched_slug}</code>
              </p>
            ) : null}

            {item.aliases.length > 0 ? (
              <p className="mb-2 font-ui text-xs text-ink-secondary">
                Aliases: {item.aliases.slice(0, 5).join(", ")}
              </p>
            ) : null}

            {item.evidence_previews.length > 0 ? (
              <div className="mb-3">
                <p className="mb-2 font-ui text-xs uppercase tracking-wide text-ink-muted">
                  Evidence in collection view
                </p>
                <div className="space-y-2">
                  {item.evidence_previews.map((preview) => (
                    <p key={preview} className="text-sm leading-relaxed text-ink-secondary">
                      {preview}
                    </p>
                  ))}
                </div>
              </div>
            ) : (
              <p className="mb-3 text-sm text-ink-muted">No evidence snippet captured.</p>
            )}

            {item.claim_previews.length > 0 ? (
              <div className="mb-3">
                <p className="mb-2 font-ui text-xs uppercase tracking-wide text-ink-muted">
                  Claim excerpts
                </p>
                <div className="space-y-2">
                  {item.claim_previews.map((preview) => (
                    <blockquote
                      key={preview}
                      className="border-l-2 border-accent/30 pl-3 text-sm leading-relaxed text-ink-secondary"
                    >
                      {preview}
                    </blockquote>
                  ))}
                </div>
              </div>
            ) : null}

            <Link
              href={`/first-pass/${item.slug}`}
              className="font-ui text-sm text-brand hover:text-accent"
            >
              Open provenance view →
            </Link>
          </article>
        ))}
      </div>
    </div>
  );
}
