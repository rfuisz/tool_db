"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { FirstPassLiveRefresh } from "@/components/first-pass-live-refresh";
import { renderInlineTitle } from "@/lib/render-inline-title";
import type { FirstPassEntitySummary } from "@/lib/types";

type BrowseScope = "all" | "items" | "methods" | "workflows";

const SCOPE_LABELS: Record<BrowseScope, string> = {
  all: "All concepts",
  items: "Items",
  methods: "Methods",
  workflows: "Workflows",
};

function formatLabel(value: string) {
  return value.replace(/_/g, " ");
}

function isMethodLikeItemType(itemType: string | null) {
  return Boolean(itemType && /(_method|_technique)$/.test(itemType));
}

function getEntityScope(entity: FirstPassEntitySummary): BrowseScope {
  if (entity.candidate_type === "workflow_template") {
    return "workflows";
  }
  if (isMethodLikeItemType(entity.item_type)) {
    return "methods";
  }
  return "items";
}

export function FirstPassBrowseClient({
  entities,
  title = "First-pass extracted concepts",
  description = "These records are loaded directly from extracted packets so you can judge whether the system is pulling out useful entities, methods, and workflows before deeper canonical cleanup.",
  defaultScope = "all",
}: {
  entities: FirstPassEntitySummary[];
  title?: string;
  description?: string;
  defaultScope?: BrowseScope;
}) {
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<BrowseScope>(defaultScope);
  const [sortBy, setSortBy] = useState<"sources" | "claims" | "name">(
    "sources",
  );

  const filtered = useMemo(() => {
    const lowered = query.trim().toLowerCase();
    const scoped =
      scope === "all"
        ? entities
        : entities.filter((entity) => getEntityScope(entity) === scope);
    const base = lowered
      ? scoped.filter((entity) => {
          const evidencePreviews = entity.evidence_previews ?? [];
          const claimPreviews = entity.claim_previews ?? [];
          const aliases = entity.aliases ?? [];
          const haystacks = [
            entity.canonical_name,
            entity.candidate_type,
            entity.item_type ?? "",
            entity.evidence_preview ?? "",
            ...evidencePreviews,
            ...claimPreviews,
            ...aliases,
          ].map((value) => value.toLowerCase());
          return haystacks.some((value) => value.includes(lowered));
        })
      : scoped;
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
  }, [entities, query, scope, sortBy]);

  const scopeCounts = useMemo(
    () => ({
      all: entities.length,
      items: entities.filter((entity) => getEntityScope(entity) === "items")
        .length,
      methods: entities.filter((entity) => getEntityScope(entity) === "methods")
        .length,
      workflows: entities.filter(
        (entity) => getEntityScope(entity) === "workflows",
      ).length,
    }),
    [entities],
  );

  return (
    <div>
      <header className="mb-10">
        <p className="small-caps mb-3">Bulk Extracted Review Layer</p>
        <h1 className="mb-3">{title}</h1>
        <p className="max-w-3xl text-ink-secondary">{description}</p>
        <div className="mt-4 flex flex-wrap gap-4 font-ui text-sm">
          <Link href="/first-pass" className="text-brand hover:text-accent">
            All concepts
          </Link>
          <Link href="/first-pass/methods" className="text-brand hover:text-accent">
            Methods
          </Link>
          <Link href="/first-pass/workflows" className="text-brand hover:text-accent">
            Workflows
          </Link>
        </div>
        <div className="mt-4">
          <FirstPassLiveRefresh />
        </div>
      </header>

      <div className="mb-8 flex flex-wrap items-center gap-3 font-ui text-sm">
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search extracted names, aliases, evidence..."
          className="h-9 w-80 border-b border-edge bg-transparent px-0 text-ink placeholder-ink-muted outline-none transition-colors focus:border-accent"
        />
        <div className="flex flex-wrap gap-2">
          {(Object.keys(SCOPE_LABELS) as BrowseScope[]).map((scopeOption) => (
            <button
              key={scopeOption}
              type="button"
              onClick={() => setScope(scopeOption)}
              className={`rounded border px-3 py-1 font-ui text-xs uppercase tracking-wide transition-colors ${
                scope === scopeOption
                  ? "border-accent text-accent"
                  : "border-edge text-ink-muted hover:border-accent/40 hover:text-ink-secondary"
              }`}
            >
              {SCOPE_LABELS[scopeOption]} ({scopeCounts[scopeOption]})
            </button>
          ))}
        </div>
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
          {filtered.length} extracted concept{filtered.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="space-y-4">
        {filtered.map((entity) => {
          const evidencePreviews = entity.evidence_previews ?? [];
          const claimPreviews = entity.claim_previews ?? [];
          const aliases = entity.aliases ?? [];
          const scopeLabel = SCOPE_LABELS[getEntityScope(entity)];
          const detailHref = `/first-pass/entities/${entity.candidate_type}/${entity.slug}`;

          return (
            <article
              key={`${entity.candidate_type}:${entity.slug}`}
              className="border border-edge bg-surface p-5"
            >
              <div className="mb-2 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <Link
                    href={detailHref}
                    className="text-lg text-ink hover:text-accent"
                  >
                    {renderInlineTitle(entity.canonical_name)}
                  </Link>
                  <div className="mt-1 flex flex-wrap gap-2 font-ui text-xs uppercase tracking-wide text-ink-muted">
                    <span>{scopeLabel}</span>
                    <span>{formatLabel(entity.candidate_type)}</span>
                    {entity.item_type ? <span>{formatLabel(entity.item_type)}</span> : null}
                  </div>
                </div>
                <div className="font-data text-xs tabular-nums text-ink-muted">
                  <div>{entity.source_document_count} sources</div>
                  <div>{entity.claim_count} claims</div>
                </div>
              </div>

              {entity.matched_slug ? (
                <p className="mb-2 font-ui text-xs text-valid">
                  Canonical match suggestion: <code>{entity.matched_slug}</code>
                </p>
              ) : null}

              {aliases.length > 0 ? (
                <p className="mb-2 font-ui text-xs text-ink-secondary">
                  Aliases: {aliases.slice(0, 5).join(", ")}
                </p>
              ) : null}

              {evidencePreviews.length > 0 ? (
                <div className="mb-3">
                  <p className="mb-2 font-ui text-xs uppercase tracking-wide text-ink-muted">
                    Evidence in collection view
                  </p>
                  <div className="space-y-2">
                    {evidencePreviews.map((preview, index) => (
                      <p
                        key={`${entity.candidate_type}-${entity.slug}-evidence-preview-${index}`}
                        className="text-sm leading-relaxed text-ink-secondary"
                      >
                        {preview}
                      </p>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="mb-3 text-sm text-ink-muted">
                  No evidence snippet captured.
                </p>
              )}

              {claimPreviews.length > 0 ? (
                <div className="mb-3">
                  <p className="mb-2 font-ui text-xs uppercase tracking-wide text-ink-muted">
                    Claim excerpts
                  </p>
                  <div className="space-y-2">
                    {claimPreviews.map((preview, index) => (
                      <blockquote
                        key={`${entity.candidate_type}-${entity.slug}-claim-preview-${index}`}
                        className="border-l-2 border-accent/30 pl-3 text-sm leading-relaxed text-ink-secondary"
                      >
                        {preview}
                      </blockquote>
                    ))}
                  </div>
                </div>
              ) : null}

              <Link
                href={detailHref}
                className="font-ui text-sm text-brand hover:text-accent"
              >
                Open provenance view →
              </Link>
            </article>
          );
        })}
      </div>
    </div>
  );
}
