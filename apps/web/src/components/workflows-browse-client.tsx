"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { FilterSelect } from "@/components/filter-select";
import type { ExtractedWorkflowSummary } from "@/lib/types";

const PAGE_SIZE_OPTIONS = [10, 50, 100] as const;

type WorkflowSearchResponse = {
  total: number;
  limit: number;
  offset: number;
  workflows: ExtractedWorkflowSummary[];
};

function buildSearchParams(filters: {
  mechanismFilter: string;
  techniqueFilter: string;
  searchQuery: string;
  sortBy: string;
  hasStages: string;
  pageSize: number;
  offset: number;
}): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.mechanismFilter) params.set("mechanism", filters.mechanismFilter);
  if (filters.techniqueFilter) params.set("technique", filters.techniqueFilter);
  if (filters.searchQuery.trim()) params.set("q", filters.searchQuery.trim());
  if (filters.hasStages === "yes") params.set("has_stages", "true");
  if (filters.hasStages === "detailed") params.set("has_steps", "true");
  params.set("sort", filters.sortBy);
  params.set("limit", String(filters.pageSize));
  params.set("offset", String(filters.offset));
  return params;
}

function WorkflowCard({ workflow }: { workflow: ExtractedWorkflowSummary }) {
  const doc = workflow.source_document;
  const year = doc?.publication_year;

  return (
    <article className="border-b border-edge py-6">
      <div className="mb-1.5 flex items-baseline justify-between gap-4">
        <h3 className="text-lg text-ink">
          {workflow.workflow_objective ?? "Untitled workflow"}
        </h3>
        {workflow.protocol_family && (
          <span className="small-caps shrink-0 text-ink-muted">
            {workflow.protocol_family}
          </span>
        )}
      </div>

      <div className="mb-2 flex flex-wrap items-center gap-1.5 font-ui text-xs">
        {doc?.title && (
          doc.doi ? (
            <a
              href={`https://doi.org/${doc.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="underline decoration-edge decoration-1 underline-offset-2 text-ink-secondary transition-colors hover:text-accent hover:decoration-accent"
            >
              {doc.title}
            </a>
          ) : (
            <span className="text-ink-secondary">{doc.title}</span>
          )
        )}
        {doc?.journal_or_source && (
          <span className="italic text-ink-muted">{doc.journal_or_source}</span>
        )}
        {year && (
          <span className="font-data text-ink-muted">{year}</span>
        )}
      </div>

      <div className="mb-2 flex flex-wrap items-center gap-1.5 font-ui text-xs">
        {workflow.target_mechanisms.map((m) => (
          <Link
            key={m}
            href={`/items?mechanism=${m}`}
            className="inline-block rounded bg-surface-alt px-1.5 py-0.5 text-ink-muted transition-colors hover:bg-edge hover:text-ink"
          >
            {m.replace(/_/g, " ")}
          </Link>
        ))}
        {workflow.target_techniques.map((t) => (
          <Link
            key={t}
            href={`/items?technique=${t}`}
            className="inline-block rounded bg-surface-alt px-1.5 py-0.5 text-ink-muted transition-colors hover:bg-edge hover:text-ink"
          >
            {t.replace(/_/g, " ")}
          </Link>
        ))}
        {workflow.involved_items.map((item, idx) => (
          item.item_slug ? (
            <Link
              key={`${item.slug}-${idx}`}
              href={`/items/${item.item_slug}`}
              className="inline-block rounded bg-surface-alt px-1.5 py-0.5 text-ink transition-colors hover:bg-edge hover:text-accent"
            >
              {item.display_name}
            </Link>
          ) : (
            <span
              key={`${item.slug}-${idx}`}
              className="inline-block rounded bg-surface-alt px-1.5 py-0.5 text-ink-secondary"
            >
              {item.display_name}
            </span>
          )
        ))}
      </div>

      {workflow.why_workflow_works && (
        <p className="mb-3 line-clamp-2 text-[15px] leading-relaxed text-ink-secondary">
          {workflow.why_workflow_works}
        </p>
      )}

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5 font-data text-xs text-ink-muted">
          {workflow.stages.length > 0 && (
            <span>{workflow.stages.length} stages</span>
          )}
          {workflow.steps.length > 0 && (
            <span>{workflow.steps.length} steps</span>
          )}
          {workflow.involved_items.length > 0 && (
            <span>{workflow.involved_items.length} tools</span>
          )}
        </div>

        <div className="flex gap-4">
          {workflow.stages.length > 0 && (
            <details className="group">
              <summary className="cursor-pointer font-ui text-xs text-ink-muted hover:text-ink list-none [&::-webkit-details-marker]:hidden">
                <span className="group-open:hidden">Stages &rsaquo;</span>
                <span className="hidden group-open:inline">Hide &lsaquo;</span>
              </summary>
            </details>
          )}
          {workflow.steps.length > 0 && (
            <details className="group">
              <summary className="cursor-pointer font-ui text-xs text-ink-muted hover:text-ink list-none [&::-webkit-details-marker]:hidden">
                <span className="group-open:hidden">Steps &rsaquo;</span>
                <span className="hidden group-open:inline">Hide &lsaquo;</span>
              </summary>
            </details>
          )}
        </div>
      </div>

      {workflow.stages.length > 0 && (
        <details className="mt-3 group/stages">
          <summary className="cursor-pointer font-ui text-xs text-ink-muted hover:text-ink list-none [&::-webkit-details-marker]:hidden">
            <span className="group-open/stages:hidden">
              Show {workflow.stages.length} stage{workflow.stages.length !== 1 ? "s" : ""} &rsaquo;
            </span>
            <span className="hidden group-open/stages:inline">
              Hide stages &lsaquo;
            </span>
          </summary>
          <ol className="mt-2 space-y-1 text-sm">
            {workflow.stages.map((stage, si) => (
              <li key={si} className="flex gap-2">
                <span className="shrink-0 font-data text-xs text-ink-faint">
                  {stage.stage_order}.
                </span>
                <div>
                  <span className="font-ui font-medium text-ink">
                    {stage.stage_name}
                  </span>
                  <span className="ml-1 small-caps text-ink-muted">
                    {stage.stage_kind}
                  </span>
                  {stage.why_stage_exists && (
                    <p className="mt-0.5 text-sm leading-relaxed text-ink-secondary">
                      {stage.why_stage_exists}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </details>
      )}

      {workflow.steps.length > 0 && (
        <details className="mt-2 group/steps">
          <summary className="cursor-pointer font-ui text-xs text-ink-muted hover:text-ink list-none [&::-webkit-details-marker]:hidden">
            <span className="group-open/steps:hidden">
              Show {workflow.steps.length} step{workflow.steps.length !== 1 ? "s" : ""} &rsaquo;
            </span>
            <span className="hidden group-open/steps:inline">
              Hide steps &lsaquo;
            </span>
          </summary>
          <ol className="mt-2 space-y-1 text-sm">
            {workflow.steps.map((step, si) => (
              <li key={si} className="flex gap-2">
                <span className="shrink-0 font-data text-xs text-ink-faint">
                  {step.step_order}.
                </span>
                <div>
                  <span className="font-ui font-medium text-ink">
                    {step.step_name}
                  </span>
                  {step.item_role && (
                    <span className="ml-1 small-caps text-ink-muted">
                      {step.item_role}
                    </span>
                  )}
                  {step.purpose && (
                    <p className="mt-0.5 text-sm leading-relaxed text-ink-secondary">{step.purpose}</p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </details>
      )}
    </article>
  );
}

export function WorkflowsBrowseClient({
  initialWorkflows,
  initialTotal,
  filterOptions,
}: {
  initialWorkflows: ExtractedWorkflowSummary[];
  initialTotal: number;
  filterOptions: {
    mechanisms: string[];
    techniques: string[];
  };
}) {
  const [mechanismFilter, setMechanismFilter] = useState("");
  const [techniqueFilter, setTechniqueFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("year");
  const [hasStages, setHasStages] = useState("");
  const [pageSize, setPageSize] =
    useState<(typeof PAGE_SIZE_OPTIONS)[number]>(50);
  const [offset, setOffset] = useState(0);
  const [visibleWorkflows, setVisibleWorkflows] = useState(initialWorkflows);
  const [totalCount, setTotalCount] = useState(initialTotal);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const cacheRef = useRef(
    new Map<string, WorkflowSearchResponse>([
      [
        buildSearchParams({
          mechanismFilter: "",
          techniqueFilter: "",
          searchQuery: "",
          sortBy: "year",
          hasStages: "",
          pageSize: 50,
          offset: 0,
        }).toString(),
        { total: initialTotal, limit: 50, offset: 0, workflows: initialWorkflows },
      ],
    ]),
  );
  const inFlightRef = useRef(new Set<string>());

  useEffect(() => {
    const controller = new AbortController();
    const params = buildSearchParams({
      mechanismFilter,
      techniqueFilter,
      searchQuery,
      sortBy,
      hasStages,
      pageSize,
      offset,
    });
    const cacheKey = params.toString();

    async function fetchPage(
      requestedParams: URLSearchParams,
      options: { foreground: boolean },
    ) {
      const key = requestedParams.toString();
      if (cacheRef.current.has(key)) return cacheRef.current.get(key)!;
      if (inFlightRef.current.has(key)) return null;

      inFlightRef.current.add(key);
      if (options.foreground) {
        setIsLoading(true);
        setErrorMessage(null);
      }

      try {
        const response = await fetch(`/api/extracted-workflows?${key}`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`Status ${response.status}`);
        const payload = (await response.json()) as WorkflowSearchResponse;
        cacheRef.current.set(key, payload);
        return payload;
      } catch {
        if (controller.signal.aborted) return null;
        if (options.foreground) setErrorMessage("Could not load workflows.");
        return null;
      } finally {
        inFlightRef.current.delete(key);
        if (options.foreground && !controller.signal.aborted) setIsLoading(false);
      }
    }

    async function loadWorkflows() {
      const cached = cacheRef.current.get(cacheKey);
      if (cached) {
        setVisibleWorkflows(cached.workflows);
        setTotalCount(cached.total);
        setErrorMessage(null);
      }
      const payload = await fetchPage(params, { foreground: !cached });
      if (payload) {
        setVisibleWorkflows(payload.workflows);
        setTotalCount(payload.total);
      }

      const resolvedTotal = payload?.total ?? cached?.total ?? 0;
      const prevOff = offset > 0 ? Math.max(0, offset - pageSize) : null;
      const nextOff = offset + pageSize < resolvedTotal ? offset + pageSize : null;
      for (const adj of [prevOff, nextOff]) {
        if (adj === null) continue;
        void fetchPage(
          buildSearchParams({ mechanismFilter, techniqueFilter, searchQuery, sortBy, hasStages, pageSize, offset: adj }),
          { foreground: false },
        );
      }
    }

    void loadWorkflows();
    return () => controller.abort();
  }, [mechanismFilter, techniqueFilter, searchQuery, sortBy, hasStages, pageSize, offset]);

  const activeFilterCount =
    (mechanismFilter ? 1 : 0) +
    (techniqueFilter ? 1 : 0) +
    (hasStages ? 1 : 0);

  const currentPage = Math.floor(offset / pageSize) + 1;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const rangeStart = totalCount === 0 ? 0 : offset + 1;
  const rangeEnd = Math.min(totalCount, offset + visibleWorkflows.length);

  const mechanismOptions = [
    { value: "", label: "All mechanisms" },
    ...filterOptions.mechanisms.map((m) => ({
      value: m,
      label: m.replace(/_/g, " "),
    })),
  ];
  const techniqueOptions = [
    { value: "", label: "All techniques" },
    ...filterOptions.techniques.map((t) => ({
      value: t,
      label: t.replace(/_/g, " "),
    })),
  ];
  const detailOptions = [
    { value: "", label: "All workflows" },
    { value: "yes", label: "Has stages" },
    { value: "detailed", label: "Has steps" },
  ];
  const sortOptions = [
    { value: "year", label: "Year" },
    { value: "objective", label: "Objective" },
    { value: "stages", label: "Most stages" },
    { value: "steps", label: "Most steps" },
  ];

  const canGoPrev = offset > 0 && !isLoading;
  const canGoNext = currentPage < totalPages && !isLoading;

  const paginationControls = (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={() => setOffset((c) => Math.max(0, c - pageSize))}
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
        onClick={() =>
          setOffset((c) => Math.min(c + pageSize, Math.max(0, totalCount - pageSize)))
        }
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
        <h1 className="mb-3">Workflows</h1>
        <p className="max-w-xl text-lg text-ink-secondary">
          Engineering campaigns extracted from the literature showing how tools
          are used together across design, build, test, and learn steps.
        </p>
        <p className="mt-2 text-ink-secondary">
          {totalCount} workflow{totalCount !== 1 ? "s" : ""}
          {activeFilterCount > 0 &&
            ` matching ${activeFilterCount} filter${activeFilterCount > 1 ? "s" : ""}`}
          {isLoading && " · updating"}
        </p>
      </header>

      <div className="mb-8 flex flex-wrap items-center gap-3 font-ui text-sm">
        <input
          type="text"
          placeholder="Search\u2026"
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setOffset(0);
          }}
          className="h-9 w-52 border-b border-edge bg-transparent px-0 text-ink placeholder-ink-muted outline-none transition-colors focus:border-accent"
        />

        <FilterSelect
          value={mechanismFilter}
          onChange={(v) => { setMechanismFilter(v); setOffset(0); }}
          options={mechanismOptions}
          placeholder="All mechanisms"
        />
        <FilterSelect
          value={techniqueFilter}
          onChange={(v) => { setTechniqueFilter(v); setOffset(0); }}
          options={techniqueOptions}
          placeholder="All techniques"
        />
        <FilterSelect
          value={hasStages}
          onChange={(v) => { setHasStages(v); setOffset(0); }}
          options={detailOptions}
          placeholder="All workflows"
        />

        <div className="ml-auto flex items-center gap-2 text-ink-muted">
          <span className="small-caps">Sort</span>
          <FilterSelect
            value={sortBy}
            onChange={(v) => { setSortBy(v); setOffset(0); }}
            options={sortOptions}
            placeholder="Year"
          />
        </div>

        {activeFilterCount > 0 && (
          <button
            onClick={() => {
              setMechanismFilter("");
              setTechniqueFilter("");
              setHasStages("");
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
          {mechanismFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {mechanismFilter.replace(/_/g, " ")}
              <button onClick={() => setMechanismFilter("")} className="text-ink-muted hover:text-accent">&times;</button>
            </span>
          )}
          {techniqueFilter && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {techniqueFilter.replace(/_/g, " ")}
              <button onClick={() => setTechniqueFilter("")} className="text-ink-muted hover:text-accent">&times;</button>
            </span>
          )}
          {hasStages && (
            <span className="flex items-center gap-1 border-b border-accent pb-0.5">
              {hasStages === "detailed" ? "Has steps" : "Has stages"}
              <button onClick={() => setHasStages("")} className="text-ink-muted hover:text-accent">&times;</button>
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
            {PAGE_SIZE_OPTIONS.map((size) => (
              <button
                key={size}
                type="button"
                onClick={() => { setPageSize(size); setOffset(0); }}
                className={`border-b pb-0.5 font-data text-xs transition-colors ${
                  pageSize === size
                    ? "border-accent text-accent"
                    : "border-transparent text-ink-muted hover:border-edge hover:text-ink"
                }`}
              >
                {size}
              </button>
            ))}
            <span className="text-ink-muted">workflows</span>
          </div>
          {paginationControls}
        </div>
      </div>

      {errorMessage ? (
        <p className="py-20 text-center text-danger">{errorMessage}</p>
      ) : totalCount === 0 ? (
        <p className="py-20 text-center text-ink-muted">
          No workflows match the current filters.
        </p>
      ) : (
        <div>
          {visibleWorkflows.map((wf) => (
            <WorkflowCard key={wf.workflow_id} workflow={wf} />
          ))}
          <div className="mt-8 flex justify-end border-t border-edge pt-4 font-ui text-sm">
            {paginationControls}
          </div>
        </div>
      )}
    </div>
  );
}
