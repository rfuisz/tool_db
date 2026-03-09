"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { FilterSelect } from "@/components/filter-select";
import type { TechniqueConceptSummary } from "@/lib/item-hierarchy";

type SortKey = "name" | "items" | "methods";

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "name", label: "Name" },
  { value: "items", label: "Total Items" },
  { value: "methods", label: "Methods" },
];

function matchesSearch(concept: TechniqueConceptSummary, query: string): boolean {
  if (!query) return true;
  const lower = query.toLowerCase();
  return (
    concept.label.toLowerCase().includes(lower) ||
    concept.key.toLowerCase().includes(lower) ||
    concept.description.toLowerCase().includes(lower) ||
    concept.summary.toLowerCase().includes(lower) ||
    concept.capabilities.some((c) => c.toLowerCase().includes(lower))
  );
}

function sortConcepts(
  concepts: TechniqueConceptSummary[],
  sort: SortKey,
): TechniqueConceptSummary[] {
  const sorted = [...concepts];
  switch (sort) {
    case "items":
      sorted.sort((a, b) => b.totalCount - a.totalCount);
      break;
    case "methods":
      sorted.sort((a, b) => b.methodCount - a.methodCount);
      break;
    case "name":
    default:
      sorted.sort((a, b) => a.label.localeCompare(b.label));
      break;
  }
  return sorted;
}

export function TechniquesBrowseClient({
  concepts,
}: {
  concepts: TechniqueConceptSummary[];
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("name");

  const filtered = useMemo(() => {
    const matched = concepts.filter((c) => matchesSearch(c, searchQuery));
    return sortConcepts(matched, sortBy);
  }, [concepts, searchQuery, sortBy]);

  return (
    <div>
      <div className="mb-8 flex flex-wrap items-center gap-3 font-ui text-sm">
        <input
          type="text"
          placeholder="Search techniques…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="h-9 w-64 border-b border-edge bg-transparent px-0 text-ink placeholder-ink-muted outline-none transition-colors focus:border-accent"
        />

        <div className="ml-auto flex items-center gap-2 text-ink-muted">
          <span className="small-caps">Sort</span>
          <FilterSelect
            value={sortBy}
            onChange={(v) => setSortBy(v as SortKey)}
            options={SORT_OPTIONS}
            placeholder="Name"
          />
        </div>

        <p className="w-full text-ink-secondary">
          {filtered.length} technique{filtered.length !== 1 ? "s" : ""}
          {searchQuery && " matching"}
        </p>
      </div>

      {filtered.length === 0 ? (
        <p className="py-20 text-center text-ink-muted">
          No techniques match your search.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {filtered.map((concept) => (
            <Link
              key={concept.key}
              href={`/techniques/${encodeURIComponent(concept.key)}`}
              className="group rounded border border-edge p-5 transition-colors hover:border-accent"
            >
              <div className="flex items-baseline justify-between gap-3">
                <h2 className="text-xl text-ink group-hover:text-accent">
                  {concept.label}
                </h2>
                <span className="font-data text-xs text-ink-muted">
                  {concept.totalCount}
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                {concept.description}
              </p>
              {concept.capabilities.length > 0 && (
                <p className="mt-2 font-ui text-xs text-ink-muted">
                  {concept.capabilities.join(" · ")}
                </p>
              )}
              <p className="mt-3 font-data text-xs text-ink-muted">
                {concept.methodCount} methods
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
