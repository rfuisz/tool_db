import Link from "next/link";

import { ScoreBreakdown } from "@/components/score-bar";
import type { GapDetail, GapFieldSummary } from "@/lib/types";
import { getGaps } from "@/lib/backend-data";
import { renderInlineTitle } from "@/lib/render-inline-title";

function formatLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function getCandidateToolCount(gap: GapDetail): number {
  return gap.candidate_tools?.length ?? 0;
}

function getTopGapScore(gap: GapDetail): number {
  return Math.max(
    0,
    ...(gap.candidate_tools ?? []).map(
      (tool) => tool.overall_gap_applicability_score ?? 0,
    ),
  );
}

interface FieldGroup {
  field: GapFieldSummary;
  gaps: GapDetail[];
  totalLinks: number;
  topScore: number;
}

function buildFieldGroups(gaps: GapDetail[]): FieldGroup[] {
  const groupMap = new Map<string, FieldGroup>();
  for (const gap of gaps) {
    const fieldName = gap.field?.name ?? "Uncategorized";
    const fieldKey = gap.field?.external_gap_field_id ?? "uncategorized";
    if (!groupMap.has(fieldKey)) {
      groupMap.set(fieldKey, {
        field: gap.field ?? {
          external_gap_field_id: "uncategorized",
          slug: null,
          name: "Uncategorized",
        },
        gaps: [],
        totalLinks: 0,
        topScore: 0,
      });
    }
    const group = groupMap.get(fieldKey)!;
    group.gaps.push(gap);
    group.totalLinks += getCandidateToolCount(gap);
    group.topScore = Math.max(group.topScore, getTopGapScore(gap));
  }
  return Array.from(groupMap.values()).sort(
    (a, b) => b.totalLinks - a.totalLinks || b.gaps.length - a.gaps.length,
  );
}

function coverageColor(ratio: number): string {
  if (ratio >= 0.7) return "bg-green-500/80";
  if (ratio >= 0.4) return "bg-yellow-500/70";
  if (ratio > 0) return "bg-orange-500/60";
  return "bg-zinc-700/40";
}

function scoreColor(score: number): string {
  if (score >= 0.6) return "text-green-400";
  if (score >= 0.4) return "text-yellow-400";
  if (score > 0) return "text-orange-400";
  return "text-ink-muted";
}

function renderFieldOverview(groups: FieldGroup[], totalGaps: number) {
  const connectedGapCount = groups.reduce(
    (sum, g) =>
      sum + g.gaps.filter((gap) => getCandidateToolCount(gap) > 0).length,
    0,
  );
  const totalLinks = groups.reduce((sum, g) => sum + g.totalLinks, 0);

  return (
    <section className="mb-12">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl text-ink">Coverage by Field</h2>
          <p className="mt-1 text-sm text-ink-secondary">
            {connectedGapCount} of {totalGaps} gaps have at least one candidate
            tool ({totalLinks} total tool-gap connections)
          </p>
        </div>
        <div className="flex gap-3 font-ui text-[11px] uppercase tracking-wide text-ink-muted">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-green-500/80" />
            &gt;70% connected
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-yellow-500/70" />
            40–70%
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-orange-500/60" />
            &lt;40%
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-sm bg-zinc-700/40" />
            None
          </span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {groups.map((group) => {
          const connected = group.gaps.filter(
            (g) => getCandidateToolCount(g) > 0,
          ).length;
          const ratio =
            group.gaps.length > 0 ? connected / group.gaps.length : 0;
          return (
            <a
              key={group.field.external_gap_field_id}
              href={`#field-${group.field.external_gap_field_id}`}
              className="group border border-edge bg-surface p-3 transition hover:border-accent/40"
            >
              <div className="mb-2 flex items-center gap-2">
                <span
                  className={`inline-block h-2 w-2 rounded-full ${coverageColor(ratio)}`}
                />
                <span className="truncate font-ui text-xs text-ink group-hover:text-accent">
                  {group.field.name}
                </span>
              </div>
              <div className="font-data text-xs tabular-nums text-ink-muted">
                {group.gaps.length} gaps · {connected} connected
              </div>
              {group.topScore > 0 ? (
                <div
                  className={`mt-1 font-data text-xs tabular-nums ${scoreColor(group.topScore)}`}
                >
                  Best: {Math.round(group.topScore * 100)}%
                </div>
              ) : null}
            </a>
          );
        })}
      </div>
    </section>
  );
}

function renderGapCard(gap: GapDetail) {
  const candidateTools = gap.candidate_tools ?? [];
  const capabilities = gap.capabilities ?? [];
  const topScore = getTopGapScore(gap);

  return (
    <details
      key={gap.external_gap_item_id}
      className="border border-edge bg-surface p-5"
    >
      <summary className="cursor-pointer list-none">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <h3 className="text-lg leading-snug text-ink">{gap.title}</h3>
            <div className="mt-1.5 flex flex-wrap items-center gap-2">
              {gap.field ? (
                <span className="font-ui text-xs uppercase tracking-wide text-ink-muted">
                  {gap.field.name}
                </span>
              ) : null}
              {capabilities.length > 0 ? (
                <span className="font-data text-xs text-ink-muted">
                  · {capabilities.length} capabilities
                </span>
              ) : null}
            </div>
          </div>
          <div className="flex items-center gap-3 text-right">
            {candidateTools.length > 0 ? (
              <>
                <div>
                  <p className="font-ui text-[11px] uppercase tracking-wide text-ink-muted">
                    Tools
                  </p>
                  <p className="font-data text-lg tabular-nums text-ink">
                    {candidateTools.length}
                  </p>
                </div>
                <div>
                  <p className="font-ui text-[11px] uppercase tracking-wide text-ink-muted">
                    Best
                  </p>
                  <p
                    className={`font-data text-lg tabular-nums ${scoreColor(topScore)}`}
                  >
                    {Math.round(topScore * 100)}%
                  </p>
                </div>
              </>
            ) : (
              <span className="font-ui text-xs text-ink-muted">
                No tool matches
              </span>
            )}
          </div>
        </div>
      </summary>

      {gap.description ? (
        <p className="mt-4 max-w-4xl leading-relaxed text-ink-secondary">
          {gap.description}
        </p>
      ) : null}

      {gap.tags.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {gap.tags.map((tag) => (
            <span
              key={tag}
              className="border border-edge bg-surface-alt px-2 py-0.5 font-ui text-xs text-ink-muted"
            >
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      {capabilities.length > 0 ? (
        <section className="mt-6">
          <h4 className="mb-3 font-ui text-xs uppercase tracking-wide text-ink-muted">
            Foundational Capabilities
          </h4>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {capabilities.map((capability) => (
              <div
                key={capability.external_gap_capability_id}
                className="border border-edge bg-surface-alt p-3"
              >
                <p className="font-ui text-sm font-medium text-ink">
                  {capability.name}
                </p>
                {capability.description ? (
                  <p className="mt-1 text-xs leading-relaxed text-ink-secondary line-clamp-3">
                    {capability.description}
                  </p>
                ) : null}
                {capability.resources.length > 0 ? (
                  <p className="mt-2 font-data text-xs text-ink-muted">
                    {capability.resources.length} resources
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="mt-6">
        <h4 className="mb-3 font-ui text-xs uppercase tracking-wide text-ink-muted">
          Candidate Tools
        </h4>
        {candidateTools.length > 0 ? (
          <div className="space-y-4">
            {candidateTools.map((tool) => (
              <article
                key={tool.item_slug}
                className="border border-edge bg-surface-alt p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <Link
                      href={`/items/${tool.item_slug}`}
                      className="text-lg text-brand hover:text-accent"
                    >
                      {renderInlineTitle(tool.canonical_name)}
                    </Link>
                    <p className="mt-1 font-ui text-xs uppercase tracking-wide text-ink-muted">
                      {formatLabel(tool.item_type)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-ui text-[11px] uppercase tracking-wide text-ink-muted">
                      Gap applicability
                    </p>
                    <p
                      className={`font-data text-lg tabular-nums ${scoreColor(tool.overall_gap_applicability_score ?? 0)}`}
                    >
                      {tool.overall_gap_applicability_score !== null
                        ? Math.round(tool.overall_gap_applicability_score * 100)
                        : "—"}
                    </p>
                  </div>
                </div>

                {tool.summary ? (
                  <p className="mt-3 max-w-4xl text-sm leading-relaxed text-ink-secondary">
                    {renderInlineTitle(tool.summary)}
                  </p>
                ) : null}

                {tool.why_it_might_help ? (
                  <p className="mt-3 text-sm leading-relaxed text-ink">
                    {tool.why_it_might_help}
                  </p>
                ) : null}

                <div className="mt-4">
                  <ScoreBreakdown
                    scores={[
                      {
                        label: "Mechanistic",
                        value: tool.mechanistic_match_score,
                        explanationKey: "mechanistic_match_score",
                      },
                      {
                        label: "Context",
                        value: tool.context_match_score,
                        explanationKey: "context_match_score",
                      },
                      {
                        label: "Throughput",
                        value: tool.throughput_match_score,
                        explanationKey: "throughput_match_score",
                      },
                      {
                        label: "First test time",
                        value: tool.time_to_first_test_score,
                        explanationKey: "time_to_first_test_score",
                      },
                      {
                        label: "First test cost",
                        value: tool.cost_to_first_test_score,
                        explanationKey: "cost_to_first_test_score",
                      },
                      {
                        label: "Replication",
                        value: tool.replication_confidence_modifier,
                        explanationKey: "replication_confidence_modifier",
                      },
                      {
                        label: "Practicality",
                        value: tool.practicality_modifier,
                        explanationKey: "practicality_modifier",
                      },
                      {
                        label: "Translatability",
                        value: tool.translatability_modifier,
                        explanationKey: "translatability_modifier",
                      },
                    ]}
                  />
                </div>

                {tool.assumptions ? (
                  <p className="mt-4 text-sm text-ink-secondary">
                    <span className="font-ui uppercase tracking-wide text-ink-muted">
                      Assumptions:
                    </span>{" "}
                    {tool.assumptions}
                  </p>
                ) : null}

                {tool.missing_evidence ? (
                  <p className="mt-2 text-sm text-caution">
                    <span className="font-ui uppercase tracking-wide text-ink-muted">
                      Missing evidence:
                    </span>{" "}
                    {tool.missing_evidence}
                  </p>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <p className="text-sm text-ink-muted">
            No candidate tools matched this gap. This may be because the gap
            describes a domain (e.g. astrophysics, social science) where the
            current biotech-focused toolkit has limited relevance, or because
            the gap requires capability types not yet well-represented in the
            database.
          </p>
        )}
      </section>
    </details>
  );
}

export default async function GapsPage() {
  const gaps = await getGaps();
  const fieldGroups = buildFieldGroups(gaps);

  const rankedGaps = [...gaps].sort((left, right) => {
    const connectionDelta =
      getCandidateToolCount(right) - getCandidateToolCount(left);
    if (connectionDelta !== 0) return connectionDelta;
    const scoreDelta = getTopGapScore(right) - getTopGapScore(left);
    if (scoreDelta !== 0) return scoreDelta;
    const capabilityDelta = right.capability_count - left.capability_count;
    if (capabilityDelta !== 0) return capabilityDelta;
    return left.title.localeCompare(right.title);
  });

  return (
    <div>
      <header className="mb-12">
        <h1 className="mb-3">Gap Map</h1>
        <p className="max-w-3xl text-lg text-ink-secondary">
          Problem statements from Convergent Research&apos;s Gap Map across{" "}
          {fieldGroups.length} scientific fields, scored against{" "}
          {
            new Set(
              gaps.flatMap(
                (g) => g.candidate_tools?.map((t) => t.item_slug) ?? [],
              ),
            ).size
          }{" "}
          toolkit items for mechanistic fit, practicality, and translatability.
        </p>
      </header>

      {gaps.length === 0 ? (
        <p className="text-ink-muted">
          No normalized Gap Map relationships are available yet in the current
          backend.
        </p>
      ) : (
        <>
          {renderFieldOverview(fieldGroups, gaps.length)}

          {fieldGroups.map((group) => {
            const sortedGaps = [...group.gaps].sort((a, b) => {
              const toolDelta =
                getCandidateToolCount(b) - getCandidateToolCount(a);
              if (toolDelta !== 0) return toolDelta;
              return getTopGapScore(b) - getTopGapScore(a);
            });
            const connected = sortedGaps.filter(
              (g) => getCandidateToolCount(g) > 0,
            );
            const unconnected = sortedGaps.filter(
              (g) => getCandidateToolCount(g) === 0,
            );
            return (
              <section
                key={group.field.external_gap_field_id}
                id={`field-${group.field.external_gap_field_id}`}
                className="mb-10 scroll-mt-8"
              >
                <div className="mb-4 flex items-end justify-between border-b border-edge pb-3">
                  <div>
                    <h2 className="text-xl text-ink">{group.field.name}</h2>
                    <p className="mt-1 font-data text-xs tabular-nums text-ink-muted">
                      {group.gaps.length} gaps · {group.totalLinks} tool
                      connections
                      {group.topScore > 0
                        ? ` · best match ${Math.round(group.topScore * 100)}%`
                        : ""}
                    </p>
                  </div>
                </div>
                <div className="space-y-4">
                  {connected.map((gap) => renderGapCard(gap))}
                  {unconnected.length > 0 && connected.length > 0 ? (
                    <div className="border-t border-edge/50 pt-4">
                      <p className="mb-3 font-ui text-xs uppercase tracking-wide text-ink-muted">
                        {unconnected.length} unmatched{" "}
                        {unconnected.length === 1 ? "gap" : "gaps"}
                      </p>
                    </div>
                  ) : null}
                  {unconnected.map((gap) => renderGapCard(gap))}
                </div>
              </section>
            );
          })}
        </>
      )}
    </div>
  );
}
