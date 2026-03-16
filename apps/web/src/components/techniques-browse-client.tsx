"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { FilterSelect } from "@/components/filter-select";

type TechniqueConcept = {
  key: string;
  label: string;
  description: string;
  totalCount: number;
};

type SortKey = "name" | "items";

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "items", label: "Total Items" },
  { value: "name", label: "Name" },
];

function matchesSearch(concept: TechniqueConcept, query: string): boolean {
  if (!query) return true;
  const lower = query.toLowerCase();
  return (
    concept.label.toLowerCase().includes(lower) ||
    concept.key.toLowerCase().includes(lower) ||
    concept.description.toLowerCase().includes(lower)
  );
}

export function TechniquesBrowseClient({
  concepts,
}: {
  concepts: TechniqueConcept[];
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("items");

  const filtered = useMemo(() => {
    const matched = concepts.filter((c) => matchesSearch(c, searchQuery));
    const sorted = [...matched];
    if (sortBy === "items") {
      sorted.sort((a, b) => b.totalCount - a.totalCount);
    } else {
      sorted.sort((a, b) => a.label.localeCompare(b.label));
    }
    return sorted;
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
                  {concept.totalCount} items
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                {concept.description}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
