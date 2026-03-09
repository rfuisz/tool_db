"use client";

import { useEffect, useRef, useState } from "react";

import { ItemCard } from "@/components/item-card";
import { FilterSelect } from "@/components/filter-select";
import {
  MECHANISM_HIERARCHY_SECTIONS,
  buildMechanismConceptSummaries,
  buildTechniqueConceptSummaries,
  getItemTaxonomyPosition,
  getOrderedItemTypes,
  TECHNIQUE_HIERARCHY_SECTIONS,
} from "@/lib/item-hierarchy";
import {
  ITEM_TYPE_LABELS,
  MECHANISM_LABELS,
  TECHNIQUE_LABELS,
} from "@/lib/vocabularies";
import type { ItemType, ToolkitItem } from "@/lib/types";

const PAGE_SIZE_OPTIONS = [10, 50, 100, 500] as const;

type InitialFilters = {
  type?: string;
  mechanism?: string;
  technique?: string;
  family?: string;
};

type FilterOptionsData = {
  types: string[];
  mechanisms: string[];
  techniques: string[];
  families: string[];
};

type ItemSearchResponse = {
  total: number;
  limit: number;
  offset: number;
  items: ToolkitItem[];
};

function buildItemSearchParams(filters: {
  typeFilter: string;
  mechanismFilter: string;
  techniqueFilter: string;
  familyFilter: string;
  searchQuery: string;
  sortBy: "name" | "evidence" | "replication" | "practicality" | "year";
  pageSize: number;
  offset: number;
}): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.typeFilter) params.set("type", filters.typeFilter);
  if (filters.mechanismFilter) params.set("mechanism", filters.mechanismFilter);
  if (filters.techniqueFilter) params.set("technique", filters.techniqueFilter);
  if (filters.familyFilter) params.set("family", filters.familyFilter);
  if (filters.searchQuery.trim()) params.set("q", filters.searchQuery.trim());
  params.set("sort", filters.sortBy);
  params.set("limit", String(filters.pageSize));
  params.set("offset", String(filters.offset));

  return params;
}

export function ItemsBrowseClient({
  allItems,
  initialItems,
  initialTotal,
  initialFilters,
  filterOptions,
}: {
  allItems: ToolkitItem[];
  initialItems: ToolkitItem[];
  initialTotal: number;
  initialFilters: InitialFilters;
  filterOptions: FilterOptionsData;
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
  const [pageSize, setPageSize] =
    useState<(typeof PAGE_SIZE_OPTIONS)[number]>(50);
  const [offset, setOffset] = useState(0);
  const [visibleItems, setVisibleItems] = useState(initialItems);
  const [totalCount, setTotalCount] = useState(initialTotal);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const cacheRef = useRef(
    new Map<string, ItemSearchResponse>([
      [
        buildItemSearchParams({
          typeFilter: initialType,
          mechanismFilter: initialMechanism,
          techniqueFilter: initialTechnique,
          familyFilter: initialFamily,
          searchQuery: "",
          sortBy: "name",
          pageSize: 50,
          offset: 0,
        }).toString(),
        {
          total: initialTotal,
          limit: 50,
          offset: 0,
          items: initialItems,
        },
      ],
    ]),
  );
  const inFlightRef = useRef(new Set<string>());

  useEffect(() => {
    const controller = new AbortController();
    const params = buildItemSearchParams({
      typeFilter,
      mechanismFilter,
      techniqueFilter,
      familyFilter,
      searchQuery,
      sortBy,
      pageSize,
      offset,
    });
    const cacheKey = params.toString();

    async function fetchPage(
      requestedParams: URLSearchParams,
      options: { foreground: boolean },
    ) {
      const key = requestedParams.toString();

      if (cacheRef.current.has(key)) {
        return cacheRef.current.get(key)!;
      }

      if (inFlightRef.current.has(key)) {
        return null;
      }

      inFlightRef.current.add(key);

      if (options.foreground) {
        setIsLoading(true);
        setErrorMessage(null);
      }

      try {
        const response = await fetch(`/api/items?${key}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const payload = (await response.json()) as ItemSearchResponse;
        cacheRef.current.set(key, payload);
        return payload;
      } catch {
        if (controller.signal.aborted) {
          return null;
        }
        if (options.foreground) {
          setErrorMessage("Could not load toolkit items right now.");
        }
        return null;
      } finally {
        inFlightRef.current.delete(key);
        if (options.foreground && !controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    async function loadItems() {
      const cached = cacheRef.current.get(cacheKey);
      if (cached) {
        setVisibleItems(cached.items);
        setTotalCount(cached.total);
        setErrorMessage(null);
      }

      const payload = await fetchPage(params, { foreground: !cached });
      if (payload) {
        setVisibleItems(payload.items);
        setTotalCount(payload.total);
      }

      const resolvedTotal = payload?.total ?? cached?.total ?? 0;
      const prevOffset = offset > 0 ? Math.max(0, offset - pageSize) : null;
      const nextOffset =
        offset + pageSize < resolvedTotal ? offset + pageSize : null;

      for (const adjacentOffset of [prevOffset, nextOffset]) {
        if (adjacentOffset === null) {
          continue;
        }

        const adjacentParams = buildItemSearchParams({
          typeFilter,
          mechanismFilter,
          techniqueFilter,
          familyFilter,
          searchQuery,
          sortBy,
          pageSize,
          offset: adjacentOffset,
        });

        void fetchPage(adjacentParams, { foreground: false });
      }
    }

    void loadItems();
    return () => controller.abort();
  }, [
    familyFilter,
    mechanismFilter,
    offset,
    pageSize,
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

  const currentPage = Math.floor(offset / pageSize) + 1;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const rangeStart = totalCount === 0 ? 0 : offset + 1;
  const rangeEnd = Math.min(totalCount, offset + visibleItems.length);
  const mechanismConcepts = buildMechanismConceptSummaries(allItems);
  const techniqueConcepts = buildTechniqueConceptSummaries(allItems);

  const typeOptions = [
    { value: "", label: "All item classes" },
    ...getOrderedItemTypes(filterOptions.types as ItemType[]).map((type) => {
      const position = getItemTaxonomyPosition(type);
      return {
        value: type,
        label: `${position.layerTitle} · ${ITEM_TYPE_LABELS[type]}`,
      };
    }),
  ];
  const mechanismOptions = [
    { value: "", label: "All mechanisms" },
    ...filterOptions.mechanisms.map((mechanism) => ({
      value: mechanism,
      label: MECHANISM_LABELS[mechanism] ?? mechanism.replace(/_/g, " "),
    })),
  ];
  const techniqueOptions = [
    { value: "", label: "All techniques" },
    ...filterOptions.techniques.map((technique) => ({
      value: technique,
      label: TECHNIQUE_LABELS[technique] ?? technique.replace(/_/g, " "),
    })),
  ];
  const familyOptions = [
    { value: "", label: "All families" },
    ...filterOptions.families.map((family) => ({ value: family, label: family })),
  ];
  const sortOptions = [
    { value: "name", label: "Name" },
    { value: "evidence", label: "Evidence" },
    { value: "replication", label: "Replication" },
    { value: "practicality", label: "Practicality" },
    { value: "year", label: "Year" },
  ];
  const canGoPrev = offset > 0 && !isLoading;
  const canGoNext = currentPage < totalPages && !isLoading;

  const goPrevPage = () => {
    setOffset((current) => Math.max(0, current - pageSize));
  };

  const goNextPage = () => {
    setOffset((current) =>
      Math.min(current + pageSize, Math.max(0, totalCount - pageSize)),
    );
  };

  const paginationControls = (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={goPrevPage}
        disabled={!canGoPrev}
        className="small-caps text-ink-muted transition-colors hover:text-ink disabled:cursor-not-allowed disabled:text-ink-faint"
      >
        Prev
      </button>
      <span className="font-data text-xs text-ink-muted">
        Page {currentPage} / {totalPages}
      </span>
      <button
        type="button"
        onClick={goNextPage}
        disabled={!canGoNext}
        className="small-caps text-ink-muted transition-colors hover:text-ink disabled:cursor-not-allowed disabled:text-ink-faint"
      >
        Next
      </button>
    </div>
  );

  return (
    <div>
      <header className="mb-10">
        <h1 className="mb-2">Toolkit Items</h1>
        <p className="max-w-3xl text-ink-secondary">
          Browse the toolkit beneath workflows. The mechanism branch runs{" "}
          <code>mechanism -&gt; architecture -&gt; component</code>, while
          the technique branch runs from high-level approaches down to concrete
          methods.
        </p>
        <p className="mt-2 text-ink-secondary">
          {totalCount} item{totalCount !== 1 ? "s" : ""}
          {activeFilterCount > 0 &&
            ` matching ${activeFilterCount} filter${activeFilterCount > 1 ? "s" : ""}`}
          {isLoading && " · updating"}
        </p>
      </header>

      <section className="mb-8 grid gap-6 lg:grid-cols-2">
        <div className="border border-edge p-4">
          <p className="small-caps mb-2 text-accent">Mechanism Branch</p>
          <div className="space-y-4">
            {MECHANISM_HIERARCHY_SECTIONS.map((section, index) => (
              <details key={section.id} className="group/layer">
                <summary className="cursor-pointer list-none [&::-webkit-details-marker]:hidden">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="small-caps mb-1 text-ink-muted">Layer {index + 1}</p>
                      <p className="font-display text-lg text-ink">
                        {section.title}
                      </p>
                    </div>
                    <span className="text-ink-muted transition-transform duration-200 group-open/layer:rotate-180">
                      ▾
                    </span>
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-ink-secondary">
                    {section.description}
                  </p>
                </summary>
                <div className="mt-3">
                  {section.id === "mechanism" ? (
                    <div className="grid gap-3">
                      {mechanismConcepts.map((concept) => {
                        const active = mechanismFilter === concept.key;
                        return (
                          <button
                            key={concept.key}
                            type="button"
                            onClick={() => {
                              setMechanismFilter(active ? "" : concept.key);
                              setOffset(0);
                            }}
                            className={`rounded border p-3 text-left transition-colors ${
                              active
                                ? "border-accent bg-brand-light"
                                : "border-edge hover:border-accent"
                            }`}
                          >
                            <div className="flex items-baseline justify-between gap-3">
                              <span
                                className={`font-display text-base ${
                                  active ? "text-accent" : "text-ink"
                                }`}
                              >
                                {MECHANISM_LABELS[concept.key] ?? concept.label}
                              </span>
                              <span className="font-data text-xs text-ink-muted">
                                {concept.totalCount}
                              </span>
                            </div>
                            <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                              {concept.summary}
                            </p>
                            <p className="mt-2 font-ui text-xs text-ink-muted">
                              {concept.architectureCount} architectures ·{" "}
                              {concept.componentCount} components
                            </p>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {getOrderedItemTypes(section.itemTypes ?? [])
                        .filter((type) => filterOptions.types.includes(type))
                        .map((type) => {
                          const active = typeFilter === type;
                          return (
                            <button
                              key={type}
                              type="button"
                              onClick={() => {
                                setTypeFilter(active ? "" : type);
                                setOffset(0);
                              }}
                              className={`border-b pb-0.5 font-ui text-sm transition-colors ${
                                active
                                  ? "border-accent text-accent"
                                  : "border-edge text-ink-secondary hover:border-accent hover:text-accent"
                              }`}
                            >
                              {ITEM_TYPE_LABELS[type]}
                            </button>
                          );
                        })}
                    </div>
                  )}
                </div>
              </details>
            ))}
          </div>
        </div>

        <div className="border border-edge p-4">
          <p className="small-caps mb-2 text-accent">Technique Branch</p>
          <div className="space-y-4">
            {TECHNIQUE_HIERARCHY_SECTIONS.map((section, index) => (
              <details key={section.id} className="group/layer">
                <summary className="cursor-pointer list-none [&::-webkit-details-marker]:hidden">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="small-caps mb-1 text-ink-muted">Layer {index + 1}</p>
                      <p className="font-display text-lg text-ink">
                        {section.title}
                      </p>
                    </div>
                    <span className="text-ink-muted transition-transform duration-200 group-open/layer:rotate-180">
                      ▾
                    </span>
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-ink-secondary">
                    {section.description}
                  </p>
                </summary>
                <div className="mt-3">
                  {section.id === "technique" ? (
                    <div className="grid gap-3">
                      {techniqueConcepts.map((concept) => {
                        const active = techniqueFilter === concept.key;
                        return (
                          <button
                            key={concept.key}
                            type="button"
                            onClick={() => {
                              setTechniqueFilter(active ? "" : concept.key);
                              setOffset(0);
                            }}
                            className={`rounded border p-3 text-left transition-colors ${
                              active
                                ? "border-accent bg-brand-light"
                                : "border-edge hover:border-accent"
                            }`}
                          >
                            <div className="flex items-baseline justify-between gap-3">
                              <span
                                className={`font-display text-base ${
                                  active ? "text-accent" : "text-ink"
                                }`}
                              >
                                {TECHNIQUE_LABELS[concept.key] ?? concept.label}
                              </span>
                              <span className="font-data text-xs text-ink-muted">
                                {concept.totalCount}
                              </span>
                            </div>
                            <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                              {concept.summary}
                            </p>
                            <p className="mt-2 font-ui text-xs text-ink-muted">
                              {concept.methodCount} methods
                            </p>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {getOrderedItemTypes(section.itemTypes ?? [])
                        .filter((type) => filterOptions.types.includes(type))
                        .map((type) => {
                          const active = typeFilter === type;
                          return (
                            <button
                              key={type}
                              type="button"
                              onClick={() => {
                                setTypeFilter(active ? "" : type);
                                setOffset(0);
                              }}
                              className={`border-b pb-0.5 font-ui text-sm transition-colors ${
                                active
                                  ? "border-accent text-accent"
                                  : "border-edge text-ink-secondary hover:border-accent hover:text-accent"
                              }`}
                            >
                              {ITEM_TYPE_LABELS[type]}
                            </button>
                          );
                        })}
                    </div>
                  )}
                </div>
              </details>
            ))}
          </div>
        </div>
      </section>

      <div className="mb-8 flex flex-wrap items-center gap-3 font-ui text-sm">
        <input
          type="text"
          placeholder={"Search\u2026"}
          value={searchQuery}
          onChange={(event) => {
            setSearchQuery(event.target.value);
            setOffset(0);
          }}
          className="h-9 w-52 border-b border-edge bg-transparent px-0 text-ink placeholder-ink-muted outline-none transition-colors focus:border-accent"
        />

        <FilterSelect
          value={typeFilter}
          onChange={(value) => {
            setTypeFilter(value);
            setOffset(0);
          }}
          options={typeOptions}
          placeholder="All item classes"
        />
        <FilterSelect
          value={mechanismFilter}
          onChange={(value) => {
            setMechanismFilter(value);
            setOffset(0);
          }}
          options={mechanismOptions}
          placeholder="All mechanisms"
        />
        <FilterSelect
          value={techniqueFilter}
          onChange={(value) => {
            setTechniqueFilter(value);
            setOffset(0);
          }}
          options={techniqueOptions}
          placeholder="All techniques"
        />
        <FilterSelect
          value={familyFilter}
          onChange={(value) => {
            setFamilyFilter(value);
            setOffset(0);
          }}
          options={familyOptions}
          placeholder="All families"
        />

        <div className="ml-auto flex items-center gap-2 text-ink-muted">
          <span className="small-caps">Sort</span>
          <FilterSelect
            value={sortBy}
            onChange={(value) => {
              setSortBy(value as typeof sortBy);
              setOffset(0);
            }}
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
              setOffset(0);
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

      <div className="mb-8 flex flex-wrap items-center justify-between gap-4 border-y border-edge py-3 font-ui text-sm">
        <p className="text-ink-secondary">
          Showing {rangeStart}-{rangeEnd} of {totalCount}
        </p>

        <div className="flex flex-wrap items-center gap-6">
          <div className="flex flex-wrap items-center gap-2">
            <span className="small-caps text-ink-muted">Load</span>
            {PAGE_SIZE_OPTIONS.map((size) => {
              const active = pageSize === size;
              return (
                <button
                  key={size}
                  type="button"
                  onClick={() => {
                    setPageSize(size);
                    setOffset(0);
                  }}
                  className={`border-b pb-0.5 font-data text-xs transition-colors ${
                    active
                      ? "border-accent text-accent"
                      : "border-transparent text-ink-muted hover:border-edge hover:text-ink"
                  }`}
                >
                  {size}
                </button>
              );
            })}
            <span className="text-ink-muted">items</span>
          </div>

          <div className="flex items-center gap-3">
            {paginationControls}
          </div>
        </div>
      </div>

      {errorMessage ? (
        <p className="py-20 text-center text-danger">{errorMessage}</p>
      ) : totalCount === 0 ? (
        <p className="py-20 text-center text-ink-muted">
          No items match the current filters.
        </p>
      ) : (
        <div>
          {visibleItems.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}

          <div className="mt-8 flex justify-end border-t border-edge pt-4 font-ui text-sm">
            {paginationControls}
          </div>
        </div>
      )}
    </div>
  );
}
