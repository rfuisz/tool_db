"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { FilterSelect } from "@/components/filter-select";
import type { MechanismConceptSummary } from "@/lib/item-hierarchy";

type SortKey = "name" | "items" | "architectures" | "components";

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "name", label: "Name" },
  { value: "items", label: "Total Items" },
  { value: "architectures", label: "Architectures" },
  { value: "components", label: "Components" },
];

function matchesSearch(concept: MechanismConceptSummary, query: string): boolean {
  if (!query) return true;
  const lower = query.toLowerCase();
  return (
    concept.label.toLowerCase().includes(lower) ||
    concept.key.toLowerCase().includes(lower) ||
    concept.description.toLowerCase().includes(lower) ||
    concept.summary.toLowerCase().includes(lower) ||
    concept.capabilities.some((c) => c.toLowerCase().includes(lower)) ||
    concept.componentNames.some((c) => c.toLowerCase().includes(lower))
  );
}

function sortConcepts(
  concepts: MechanismConceptSummary[],
  sort: SortKey,
): MechanismConceptSummary[] {
  const sorted = [...concepts];
  switch (sort) {
    case "items":
      sorted.sort((a, b) => b.totalCount - a.totalCount);
      break;
    case "architectures":
      sorted.sort((a, b) => b.architectureCount - a.architectureCount);
      break;
    case "components":
      sorted.sort((a, b) => b.componentCount - a.componentCount);
      break;
    case "name":
    default:
      sorted.sort((a, b) => a.label.localeCompare(b.label));
      break;
  }
  return sorted;
}

export function MechanismsBrowseClient({
  concepts,
}: {
  concepts: MechanismConceptSummary[];
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
          placeholder="Search mechanisms\u2026"
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
          {filtered.length} mechanism{filtered.length !== 1 ? "s" : ""}
          {searchQuery && " matching"}
        </p>
      </div>

      {filtered.length === 0 ? (
        <p className="py-20 text-center text-ink-muted">
          No mechanisms match your search.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {filtered.map((concept) => (
            <Link
              key={concept.key}
              href={`/mechanisms/${encodeURIComponent(concept.key)}`}
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
              <div className="mt-3 flex gap-4 font-data text-xs text-ink-muted">
                <span>{concept.architectureCount} architectures</span>
                <span>{concept.componentCount} components</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
