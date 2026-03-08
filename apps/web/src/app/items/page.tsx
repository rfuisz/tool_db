"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import { ITEMS } from "@/lib/data";
import { ITEM_TYPE_LABELS, MECHANISM_LABELS, TECHNIQUE_LABELS } from "@/lib/vocabularies";
import type { ItemType } from "@/lib/types";
import { ItemCard } from "@/components/item-card";

function ItemsBrowseInner() {
  const searchParams = useSearchParams();
  const initialType = searchParams.get("type") ?? "";
  const initialMechanism = searchParams.get("mechanism") ?? "";
  const initialTechnique = searchParams.get("technique") ?? "";
  const initialFamily = searchParams.get("family") ?? "";

  const [typeFilter, setTypeFilter] = useState(initialType);
  const [mechanismFilter, setMechanismFilter] = useState(initialMechanism);
  const [techniqueFilter, setTechniqueFilter] = useState(initialTechnique);
  const [familyFilter, setFamilyFilter] = useState(initialFamily);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "evidence" | "replication" | "practicality" | "year">("name");

  const allTypes = useMemo(() => Array.from(new Set(ITEMS.map((i) => i.item_type))).sort(), []);
  const allMechanisms = useMemo(() => Array.from(new Set(ITEMS.flatMap((i) => i.mechanisms))).sort(), []);
  const allTechniques = useMemo(() => Array.from(new Set(ITEMS.flatMap((i) => i.techniques))).sort(), []);
  const allFamilies = useMemo(() => Array.from(new Set(ITEMS.map((i) => i.family).filter(Boolean) as string[])).sort(), []);

  const filtered = useMemo(() => {
    let result = ITEMS;
    if (typeFilter) result = result.filter((i) => i.item_type === typeFilter);
    if (mechanismFilter) result = result.filter((i) => i.mechanisms.includes(mechanismFilter));
    if (techniqueFilter) result = result.filter((i) => i.techniques.includes(techniqueFilter));
    if (familyFilter) result = result.filter((i) => i.family === familyFilter);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter((i) =>
        i.canonical_name.toLowerCase().includes(q) ||
        i.summary?.toLowerCase().includes(q) ||
        i.synonyms.some((s) => s.toLowerCase().includes(q))
      );
    }

    const sorted = [...result];
    switch (sortBy) {
      case "evidence": sorted.sort((a, b) => (b.replication_summary?.evidence_strength_score ?? 0) - (a.replication_summary?.evidence_strength_score ?? 0)); break;
      case "replication": sorted.sort((a, b) => (b.replication_summary?.replication_score ?? 0) - (a.replication_summary?.replication_score ?? 0)); break;
      case "practicality": sorted.sort((a, b) => (b.replication_summary?.practicality_score ?? 0) - (a.replication_summary?.practicality_score ?? 0)); break;
      case "year": sorted.sort((a, b) => (a.first_publication_year ?? 9999) - (b.first_publication_year ?? 9999)); break;
      default: sorted.sort((a, b) => a.canonical_name.localeCompare(b.canonical_name));
    }
    return sorted;
  }, [typeFilter, mechanismFilter, techniqueFilter, familyFilter, searchQuery, sortBy]);

  const activeFilterCount = (typeFilter ? 1 : 0) + (mechanismFilter ? 1 : 0) + (techniqueFilter ? 1 : 0) + (familyFilter ? 1 : 0);

  return (
    <div>
      <header className="mb-10">
        <h1 className="mb-2">Collection</h1>
        <p className="text-ink-secondary">
          {filtered.length} item{filtered.length !== 1 ? "s" : ""}
          {activeFilterCount > 0 && ` matching ${activeFilterCount} filter${activeFilterCount > 1 ? "s" : ""}`}
        </p>
      </header>

      {/* Filters */}
      <div className="mb-8 flex flex-wrap items-center gap-3 font-ui text-sm">
        <input
          type="text"
          placeholder={"Search\u2026"}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="h-9 w-52 border-b border-edge bg-transparent px-0 text-ink placeholder-ink-muted outline-none transition-colors focus:border-accent"
        />

        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
          className="h-9 border-b border-edge bg-transparent text-sm text-ink-secondary outline-none">
          <option value="">All types</option>
          {allTypes.map((t) => <option key={t} value={t}>{ITEM_TYPE_LABELS[t as ItemType]}</option>)}
        </select>

        <select value={mechanismFilter} onChange={(e) => setMechanismFilter(e.target.value)}
          className="h-9 border-b border-edge bg-transparent text-sm text-ink-secondary outline-none">
          <option value="">All mechanisms</option>
          {allMechanisms.map((m) => <option key={m} value={m}>{MECHANISM_LABELS[m] ?? m.replace(/_/g, " ")}</option>)}
        </select>

        <select value={techniqueFilter} onChange={(e) => setTechniqueFilter(e.target.value)}
          className="h-9 border-b border-edge bg-transparent text-sm text-ink-secondary outline-none">
          <option value="">All techniques</option>
          {allTechniques.map((t) => <option key={t} value={t}>{TECHNIQUE_LABELS[t] ?? t.replace(/_/g, " ")}</option>)}
        </select>

        <select value={familyFilter} onChange={(e) => setFamilyFilter(e.target.value)}
          className="h-9 border-b border-edge bg-transparent text-sm text-ink-secondary outline-none">
          <option value="">All families</option>
          {allFamilies.map((f) => <option key={f} value={f}>{f}</option>)}
        </select>

        <div className="ml-auto flex items-center gap-2 text-ink-muted">
          <span className="small-caps">Sort</span>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="h-9 border-b border-edge bg-transparent text-sm text-ink-secondary outline-none">
            <option value="name">Name</option>
            <option value="evidence">Evidence</option>
            <option value="replication">Replication</option>
            <option value="practicality">Practicality</option>
            <option value="year">Year</option>
          </select>
        </div>

        {activeFilterCount > 0 && (
          <button
            onClick={() => { setTypeFilter(""); setMechanismFilter(""); setTechniqueFilter(""); setFamilyFilter(""); setSearchQuery(""); }}
            className="text-xs text-accent hover:text-accent-hover"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Active filters */}
      {activeFilterCount > 0 && (
        <div className="mb-6 flex flex-wrap gap-3 font-ui text-xs text-ink-secondary">
          {typeFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {ITEM_TYPE_LABELS[typeFilter as ItemType]}
              <button onClick={() => setTypeFilter("")} className="text-ink-muted hover:text-accent">&times;</button>
            </span>
          )}
          {mechanismFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {MECHANISM_LABELS[mechanismFilter] ?? mechanismFilter.replace(/_/g, " ")}
              <button onClick={() => setMechanismFilter("")} className="text-ink-muted hover:text-accent">&times;</button>
            </span>
          )}
          {techniqueFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {TECHNIQUE_LABELS[techniqueFilter] ?? techniqueFilter.replace(/_/g, " ")}
              <button onClick={() => setTechniqueFilter("")} className="text-ink-muted hover:text-accent">&times;</button>
            </span>
          )}
          {familyFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {familyFilter}
              <button onClick={() => setFamilyFilter("")} className="text-ink-muted hover:text-accent">&times;</button>
            </span>
          )}
        </div>
      )}

      {/* Items list */}
      {filtered.length === 0 ? (
        <p className="py-20 text-center text-ink-muted">No items match the current filters.</p>
      ) : (
        <div>
          {filtered.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ItemsPage() {
  return (
    <Suspense fallback={<p className="text-ink-muted">Loading&hellip;</p>}>
      <ItemsBrowseInner />
    </Suspense>
  );
}
