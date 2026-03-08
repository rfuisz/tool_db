"use client";

import { useMemo, useState } from "react";

import { ItemCard } from "@/components/item-card";
import { FilterSelect } from "@/components/filter-select";
import {
  ITEM_TYPE_LABELS,
  MECHANISM_LABELS,
  TECHNIQUE_LABELS,
} from "@/lib/vocabularies";
import type { ItemType, ToolkitItem } from "@/lib/types";

type InitialFilters = {
  type?: string;
  mechanism?: string;
  technique?: string;
  family?: string;
};

export function ItemsBrowseClient({
  items,
  initialFilters,
}: {
  items: ToolkitItem[];
  initialFilters: InitialFilters;
}) {
  const initialType = initialFilters.type ?? "";
  const initialMechanism = initialFilters.mechanism ?? "";
  const initialTechnique = initialFilters.technique ?? "";
  const initialFamily = initialFilters.family ?? "";

  const [typeFilter, setTypeFilter] = useState(initialType);
  const [mechanismFilter, setMechanismFilter] = useState(initialMechanism);
  const [techniqueFilter, setTechniqueFilter] = useState(initialTechnique);
  const [familyFilter, setFamilyFilter] = useState(initialFamily);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<
    "name" | "evidence" | "replication" | "practicality" | "year"
  >("name");

  const allTypes = useMemo(
    () => Array.from(new Set(items.map((item) => item.item_type))).sort(),
    [items],
  );
  const allMechanisms = useMemo(
    () => Array.from(new Set(items.flatMap((item) => item.mechanisms))).sort(),
    [items],
  );
  const allTechniques = useMemo(
    () => Array.from(new Set(items.flatMap((item) => item.techniques))).sort(),
    [items],
  );
  const allFamilies = useMemo(
    () =>
      Array.from(
        new Set(items.map((item) => item.family).filter(Boolean) as string[]),
      ).sort(),
    [items],
  );

  const filtered = useMemo(() => {
    let result = items;
    if (typeFilter)
      result = result.filter((item) => item.item_type === typeFilter);
    if (mechanismFilter)
      result = result.filter((item) =>
        item.mechanisms.includes(mechanismFilter),
      );
    if (techniqueFilter)
      result = result.filter((item) =>
        item.techniques.includes(techniqueFilter),
      );
    if (familyFilter)
      result = result.filter((item) => item.family === familyFilter);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (item) =>
          item.canonical_name.toLowerCase().includes(q) ||
          item.summary?.toLowerCase().includes(q) ||
          item.synonyms.some((synonym) => synonym.toLowerCase().includes(q)),
      );
    }

    const sorted = [...result];
    switch (sortBy) {
      case "evidence":
        sorted.sort(
          (a, b) =>
            (b.replication_summary?.evidence_strength_score ?? 0) -
            (a.replication_summary?.evidence_strength_score ?? 0),
        );
        break;
      case "replication":
        sorted.sort(
          (a, b) =>
            (b.replication_summary?.replication_score ?? 0) -
            (a.replication_summary?.replication_score ?? 0),
        );
        break;
      case "practicality":
        sorted.sort(
          (a, b) =>
            (b.replication_summary?.practicality_score ?? 0) -
            (a.replication_summary?.practicality_score ?? 0),
        );
        break;
      case "year":
        sorted.sort(
          (a, b) =>
            (a.first_publication_year ?? 9999) -
            (b.first_publication_year ?? 9999),
        );
        break;
      default:
        sorted.sort((a, b) => a.canonical_name.localeCompare(b.canonical_name));
    }
    return sorted;
  }, [
    familyFilter,
    items,
    mechanismFilter,
    searchQuery,
    sortBy,
    techniqueFilter,
    typeFilter,
  ]);

  const activeFilterCount =
    (typeFilter ? 1 : 0) +
    (mechanismFilter ? 1 : 0) +
    (techniqueFilter ? 1 : 0) +
    (familyFilter ? 1 : 0);

  const typeOptions = [
    { value: "", label: "All types" },
    ...allTypes.map((type) => ({
      value: type,
      label: ITEM_TYPE_LABELS[type as ItemType],
    })),
  ];
  const mechanismOptions = [
    { value: "", label: "All mechanisms" },
    ...allMechanisms.map((mechanism) => ({
      value: mechanism,
      label: MECHANISM_LABELS[mechanism] ?? mechanism.replace(/_/g, " "),
    })),
  ];
  const techniqueOptions = [
    { value: "", label: "All techniques" },
    ...allTechniques.map((technique) => ({
      value: technique,
      label: TECHNIQUE_LABELS[technique] ?? technique.replace(/_/g, " "),
    })),
  ];
  const familyOptions = [
    { value: "", label: "All families" },
    ...allFamilies.map((family) => ({ value: family, label: family })),
  ];
  const sortOptions = [
    { value: "name", label: "Name" },
    { value: "evidence", label: "Evidence" },
    { value: "replication", label: "Replication" },
    { value: "practicality", label: "Practicality" },
    { value: "year", label: "Year" },
  ];

  return (
    <div>
      <header className="mb-10">
        <h1 className="mb-2">Collection</h1>
        <p className="text-ink-secondary">
          {filtered.length} item{filtered.length !== 1 ? "s" : ""}
          {activeFilterCount > 0 &&
            ` matching ${activeFilterCount} filter${activeFilterCount > 1 ? "s" : ""}`}
        </p>
      </header>

      <div className="mb-8 flex flex-wrap items-center gap-3 font-ui text-sm">
        <input
          type="text"
          placeholder={"Search\u2026"}
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          className="h-9 w-52 border-b border-edge bg-transparent px-0 text-ink placeholder-ink-muted outline-none transition-colors focus:border-accent"
        />

        <FilterSelect
          value={typeFilter}
          onChange={setTypeFilter}
          options={typeOptions}
          placeholder="All types"
        />
        <FilterSelect
          value={mechanismFilter}
          onChange={setMechanismFilter}
          options={mechanismOptions}
          placeholder="All mechanisms"
        />
        <FilterSelect
          value={techniqueFilter}
          onChange={setTechniqueFilter}
          options={techniqueOptions}
          placeholder="All techniques"
        />
        <FilterSelect
          value={familyFilter}
          onChange={setFamilyFilter}
          options={familyOptions}
          placeholder="All families"
        />

        <div className="ml-auto flex items-center gap-2 text-ink-muted">
          <span className="small-caps">Sort</span>
          <FilterSelect
            value={sortBy}
            onChange={(value) => setSortBy(value as typeof sortBy)}
            options={sortOptions}
            placeholder="Name"
          />
        </div>

        {activeFilterCount > 0 && (
          <button
            onClick={() => {
              setTypeFilter("");
              setMechanismFilter("");
              setTechniqueFilter("");
              setFamilyFilter("");
              setSearchQuery("");
            }}
            className="text-xs text-accent hover:text-accent-hover"
          >
            Clear all
          </button>
        )}
      </div>

      {activeFilterCount > 0 && (
        <div className="mb-6 flex flex-wrap gap-3 font-ui text-xs text-ink-secondary">
          {typeFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {ITEM_TYPE_LABELS[typeFilter as ItemType]}
              <button
                onClick={() => setTypeFilter("")}
                className="text-ink-muted hover:text-accent"
              >
                &times;
              </button>
            </span>
          )}
          {mechanismFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {MECHANISM_LABELS[mechanismFilter] ??
                mechanismFilter.replace(/_/g, " ")}
              <button
                onClick={() => setMechanismFilter("")}
                className="text-ink-muted hover:text-accent"
              >
                &times;
              </button>
            </span>
          )}
          {techniqueFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {TECHNIQUE_LABELS[techniqueFilter] ??
                techniqueFilter.replace(/_/g, " ")}
              <button
                onClick={() => setTechniqueFilter("")}
                className="text-ink-muted hover:text-accent"
              >
                &times;
              </button>
            </span>
          )}
          {familyFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {familyFilter}
              <button
                onClick={() => setFamilyFilter("")}
                className="text-ink-muted hover:text-accent"
              >
                &times;
              </button>
            </span>
          )}
        </div>
      )}

      {filtered.length === 0 ? (
        <p className="py-20 text-center text-ink-muted">
          No items match the current filters.
        </p>
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
