import Link from "next/link";

import { ScoreBreakdown } from "@/components/score-bar";
import type { GapDetail } from "@/lib/types";
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

function renderGapCard(gap: GapDetail) {
  const candidateTools = gap.candidate_tools ?? [];

  return (
    <details
      key={gap.external_gap_item_id}
      className="border border-edge bg-surface p-5"
    >
      <summary className="cursor-pointer list-none">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl text-ink">{gap.title}</h2>
            {gap.field ? (
              <p className="mt-1 font-ui text-xs uppercase tracking-wide text-ink-muted">
                {gap.field.name}
              </p>
            ) : null}
          </div>
          <div className="font-data text-xs tabular-nums text-ink-muted">
            {gap.capability_count} capabilities
            {candidateTools.length > 0
              ? ` · ${candidateTools.length} candidate tools`
              : ""}
          </div>
        </div>
      </summary>

      {gap.description ? (
        <p className="mt-4 max-w-4xl leading-relaxed text-ink-secondary">
          {gap.description}
        </p>
      ) : null}

      {gap.tags.length > 0 ? (
        <p className="mt-4 font-ui text-sm text-ink-secondary">
          Tags: {gap.tags.join(", ")}
        </p>
      ) : null}

      <div className="mt-6 space-y-4">
        <section>
          <h3 className="text-lg text-ink">Candidate tools</h3>
          {candidateTools.length > 0 ? (
            <div className="mt-3 space-y-4">
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
                      <p className="font-data text-lg tabular-nums text-ink">
                        {tool.overall_gap_applicability_score !== null
                          ? Math.round(
                              tool.overall_gap_applicability_score * 100,
                            )
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
            <p className="mt-2 text-sm text-ink-muted">
              No candidate tools have been materialized for this gap yet.
            </p>
          )}
        </section>

        {gap.capabilities.map((capability) => (
          <section key={capability.external_gap_capability_id}>
            <h3 className="text-lg text-ink">{capability.name}</h3>
            {capability.description ? (
              <p className="mt-1 max-w-3xl text-sm leading-relaxed text-ink-secondary">
                {capability.description}
              </p>
            ) : null}
            {capability.tags.length > 0 ? (
              <p className="mt-2 font-ui text-xs uppercase tracking-wide text-ink-muted">
                {capability.tags.join(" · ")}
              </p>
            ) : null}
            {capability.resources.length > 0 ? (
              <ul className="mt-3 space-y-2">
                {capability.resources.map((resource) => (
                  <li
                    key={resource.external_gap_resource_id}
                    className="border-l-2 border-accent/30 pl-3"
                  >
                    <p className="font-ui text-sm text-ink">
                      {resource.url ? (
                        <a
                          href={resource.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-brand hover:text-accent"
                        >
                          {resource.title}
                        </a>
                      ) : (
                        resource.title
                      )}
                    </p>
                    {resource.summary ? (
                      <p className="mt-1 text-sm leading-relaxed text-ink-secondary">
                        {renderInlineTitle(resource.summary)}
                      </p>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ))}
      </div>
    </details>
  );
}

export default async function GapsPage() {
  const gaps = await getGaps();
  const rankedGaps = [...gaps].sort((left, right) => {
    const connectionDelta =
      getCandidateToolCount(right) - getCandidateToolCount(left);
    if (connectionDelta !== 0) {
      return connectionDelta;
    }

    const scoreDelta = getTopGapScore(right) - getTopGapScore(left);
    if (scoreDelta !== 0) {
      return scoreDelta;
    }

    const capabilityDelta = right.capability_count - left.capability_count;
    if (capabilityDelta !== 0) {
      return capabilityDelta;
    }

    return left.title.localeCompare(right.title);
  });
  const connectedGaps = rankedGaps.filter(
    (gap) => getCandidateToolCount(gap) > 0,
  );
  const featuredConnectedGaps = connectedGaps.slice(0, 6);
  const remainingGaps = rankedGaps.filter(
    (gap) =>
      !featuredConnectedGaps.some(
        (featuredGap) =>
          featuredGap.external_gap_item_id === gap.external_gap_item_id,
      ),
  );

  return (
    <div>
      <header className="mb-16">
        <h1 className="mb-3">Gap Map Relationships</h1>
        <p className="max-w-3xl text-lg text-ink-secondary">
          Problem statements from Convergent Research&apos;s Gap Map, normalized
          into fields, foundational capabilities, and related resources so they
          can become explainable targets for toolkit matching.
        </p>
      </header>

      {gaps.length === 0 ? (
        <p className="text-ink-muted">
          No normalized Gap Map relationships are available yet in the current
          backend.
        </p>
      ) : (
        <div className="space-y-10">
          {featuredConnectedGaps.length > 0 ? (
            <section>
              <div className="mb-5">
                <h2 className="text-2xl text-ink">Connected Gaps</h2>
                <p className="mt-2 max-w-3xl text-sm text-ink-secondary">
                  Prioritized by how many candidate tools were found and how
                  strong the best match looks.
                </p>
              </div>
              <div className="space-y-6">
                {featuredConnectedGaps.map((gap) => renderGapCard(gap))}
              </div>
            </section>
          ) : null}

          {remainingGaps.length > 0 ? (
            <section>
              <div className="mb-5">
                <h2 className="text-2xl text-ink">Other Gaps</h2>
                <p className="mt-2 max-w-3xl text-sm text-ink-secondary">
                  Remaining gaps are still available below, with connected ones
                  ranked ahead of unlinked entries.
                </p>
              </div>
              <div className="space-y-6">
                {remainingGaps.map((gap) => renderGapCard(gap))}
              </div>
            </section>
          ) : null}
        </div>
      )}
    </div>
  );
}
