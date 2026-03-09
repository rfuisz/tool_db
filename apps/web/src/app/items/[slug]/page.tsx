import { notFound } from "next/navigation";
import Link from "next/link";
import { getItemBySlug } from "@/lib/backend-data";
import { buildItemDetailFallbacks } from "@/lib/item-detail-fallbacks";
import { getItemTaxonomyPosition } from "@/lib/item-hierarchy";
import { renderInlineTitle, stripInlineTitleMarkup } from "@/lib/render-inline-title";
import { isSupportedTechnique } from "@/lib/vocabularies";
import { ScoreBreakdown } from "@/components/score-bar";
import { ValidationMatrix } from "@/components/validation-dots";
import { CitationList } from "@/components/citation-list";
import {
  TypeBadge,
  MaturityBadge,
  StatusBadge,
  ModalityLabel,
  MechanismTag,
  TechniqueTag,
} from "@/components/detail-tooltips";
import { ObservationRow } from "@/components/observation-row";
import { PaperLink } from "@/components/paper-link";

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-12">
      <p className="small-caps mb-4">{title}</p>
      {children}
    </section>
  );
}

export default async function ItemDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const item = await getItemBySlug(slug);
  if (!item) notFound();

  const rep = item.replication_summary;
  const plainTitle = stripInlineTitleMarkup(item.canonical_name);
  const explainers = item.explainers ?? [];
  const claims = item.claims ?? [];
  const itemFacets = item.item_facets ?? [];
  const comparisons = item.comparisons ?? [];
  const problemLinks = item.problem_links ?? [];
  const workflowRecommendations = item.workflow_recommendations ?? [];
  const explainerByKind = new Map(
    explainers.map((explainer) => [explainer.explainer_kind, explainer]),
  );
  const taxonomyPosition = getItemTaxonomyPosition(item.item_type);
  const fallback = buildItemDetailFallbacks(item, {
    axisTitle: taxonomyPosition.axisTitle,
    layerTitle: taxonomyPosition.layerTitle,
  });
  const visibleTechniques = item.techniques.filter(isSupportedTechnique);
  const approvalEvidence = item.approval_evidence;

  return (
    <div>
      {/* Breadcrumb */}
      <p className="mb-8 font-ui text-sm text-ink-muted">
        <Link href="/items" className="hover:text-accent">
          Toolkit
        </Link>
        <span className="mx-2 text-ink-faint">/</span>
        <span className="text-ink-secondary">{plainTitle}</span>
      </p>

      {/* Header */}
      <header className="mb-12">
        <h1 className="mb-3">{renderInlineTitle(item.canonical_name)}</h1>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-ui text-sm text-ink-muted">
          <TypeBadge type={item.item_type} />
          {item.family && (
            <>
              <span className="text-ink-faint">&middot;</span>
              <Link
                href={`/items?family=${item.family}`}
                className="transition-colors hover:text-accent"
              >
                {item.family}
              </Link>
            </>
          )}
          <span className="text-ink-faint">&middot;</span>
          <MaturityBadge stage={item.maturity_stage} />
          {item.first_publication_year && (
            <>
              <span className="text-ink-faint">&middot;</span>
              <span>Since {item.first_publication_year}</span>
            </>
          )}
          <StatusBadge status={item.status} />
        </div>
        {item.synonyms.length > 0 && (
          <p className="mt-2 font-ui text-sm text-ink-secondary">
            Also known as:{" "}
            {item.synonyms.map((synonym, index) => (
              <span key={synonym}>
                {index > 0 ? ", " : ""}
                {renderInlineTitle(synonym)}
              </span>
            ))}
          </p>
        )}
        <p className="mt-3 font-ui text-sm text-ink-secondary">
          Taxonomy: {taxonomyPosition.axisTitle} / {taxonomyPosition.layerTitle}.
          Workflows sit above the mechanism and technique branches rather than
          replacing them.
        </p>
      </header>

      <div className="grid gap-16 lg:grid-cols-[1fr_280px]">
        {/* Main column */}
        <div>
          {/* Summary */}
          <Section title="Summary">
            <p className="text-lg leading-relaxed text-ink-secondary">
              {item.summary ?? "No summary available."}
            </p>
          </Section>

          {(explainerByKind.get("usefulness") ||
            explainerByKind.get("problem_solved") ||
            fallback.usefulness ||
            fallback.problemSolved ||
            problemLinks.length > 0) && (
            <Section title="Usefulness & Problems">
              <div className="space-y-5">
                {(explainerByKind.get("usefulness") || fallback.usefulness) && (
                  <div>
                    <p className="mb-1 text-xs uppercase tracking-wide text-ink-muted">
                      Why this is useful
                    </p>
                    <p className="text-sm leading-relaxed text-ink-secondary">
                      {explainerByKind.get("usefulness")?.body ?? fallback.usefulness}
                    </p>
                  </div>
                )}
                {(explainerByKind.get("problem_solved") || fallback.problemSolved) && (
                  <div>
                    <p className="mb-1 text-xs uppercase tracking-wide text-ink-muted">
                      Problem solved
                    </p>
                    <p className="text-sm leading-relaxed text-ink-secondary">
                      {explainerByKind.get("problem_solved")?.body ?? fallback.problemSolved}
                    </p>
                  </div>
                )}
                {problemLinks.length > 0 && (
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-wide text-ink-muted">
                      Problem links
                    </p>
                    <div className="space-y-3">
                      {problemLinks.map((problem) => (
                        <div
                          key={`${problem.source_kind}-${problem.problem_label}`}
                          className="rounded border border-edge px-4 py-3"
                        >
                          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                            <p className="font-ui text-sm font-medium text-ink">
                              {problem.problem_label}
                            </p>
                            <span className="text-xs text-ink-faint">
                              {problem.source_kind === "gap_map"
                                ? "Gap map"
                                : "Derived"}
                            </span>
                            {problem.gap_slug && (
                              <Link
                                href={`/gaps/${problem.gap_slug}`}
                                className="text-xs text-accent hover:underline"
                              >
                                View gap
                              </Link>
                            )}
                          </div>
                          <p className="mt-1 text-sm leading-relaxed text-ink-secondary">
                            {problem.why_this_item_helps}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Section>
          )}

          {(workflowRecommendations.length > 0 ||
            fallback.workflowLikelyFit.length > 0 ||
            fallback.workflowMissingEvidence.length > 0) && (
            <Section title="Workflow Fit">
              <div className="space-y-3">
                {workflowRecommendations.map((recommendation) => (
                  <div
                    key={`${recommendation.workflow_slug}-${recommendation.role_name}-${recommendation.step_name ?? "step"}`}
                    className="rounded border border-edge px-4 py-3"
                  >
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                      <Link
                        href={`/workflows#${recommendation.workflow_slug}`}
                        className="font-ui text-sm font-medium text-accent hover:underline"
                      >
                        {recommendation.workflow_name}
                      </Link>
                      <span className="font-ui text-xs text-ink-muted">
                        {recommendation.role_name.replace(/_/g, " ")}
                      </span>
                      {recommendation.stage_name && (
                        <span className="font-ui text-xs text-ink-muted">
                          Stage: {recommendation.stage_name}
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-sm leading-relaxed text-ink-secondary">
                      {recommendation.notes ??
                        recommendation.objective ??
                        "Workflow-linked evidence is available for this item."}
                    </p>
                  </div>
                ))}
                {fallback.workflowLikelyFit.length > 0 && (
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-wide text-ink-muted">
                      Likely fit
                    </p>
                    <ul className="space-y-2 text-sm leading-relaxed text-ink-secondary">
                      {fallback.workflowLikelyFit.map((note) => (
                        <li key={note} className="flex gap-2">
                          <span className="shrink-0 text-ink-faint">&bull;</span>
                          <span>{note}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {fallback.workflowMissingEvidence.length > 0 && (
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-wide text-ink-muted">
                      Missing evidence
                    </p>
                    <ul className="space-y-2 text-sm leading-relaxed text-ink-muted">
                      {fallback.workflowMissingEvidence.map((note) => (
                        <li key={note} className="flex gap-2">
                          <span className="shrink-0 text-ink-faint">&bull;</span>
                          <span>{note}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Taxonomy, mechanism, technique, modality */}
          <Section title="Taxonomy & Function">
            <div className="grid gap-6 font-ui text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="mb-1 text-xs text-ink-muted">Primary hierarchy</p>
                <p className="text-ink">{taxonomyPosition.axisTitle}</p>
                <p className="mt-1 text-ink-secondary">
                  {taxonomyPosition.layerTitle}: {taxonomyPosition.description}
                </p>
              </div>
              <div>
                <p className="mb-1 text-xs text-ink-muted">Mechanisms</p>
                {item.mechanisms.length > 0 ? (
                  item.mechanisms.map((m) => (
                    <MechanismTag key={m} mechanism={m} />
                  ))
                ) : (
                  <p className="text-ink-muted">No mechanism tags yet.</p>
                )}
              </div>
              <div>
                <p className="mb-1 text-xs text-ink-muted">Techniques</p>
                {visibleTechniques.length > 0 ? (
                  visibleTechniques.map((t) => (
                    <TechniqueTag key={t} technique={t} />
                  ))
                ) : (
                  <p className="text-ink-muted">No technique tags yet.</p>
                )}
              </div>
              <div>
                <p className="mb-1 text-xs text-ink-muted">Target processes</p>
                {item.target_processes.length > 0 ? (
                  item.target_processes.map((p) => (
                    <span key={p} className="mr-2 text-ink-secondary">
                      {p}
                    </span>
                  ))
                ) : (
                  <p className="text-ink-muted">No target processes tagged yet.</p>
                )}
                <div className="mt-3 space-y-1">
                  {item.primary_input_modality && (
                    <ModalityLabel
                      modality={item.primary_input_modality}
                      direction="Input"
                    />
                  )}
                  {item.primary_output_modality && (
                    <ModalityLabel
                      modality={item.primary_output_modality}
                      direction="Output"
                    />
                  )}
                </div>
              </div>
            </div>
          </Section>

          {(explainerByKind.get("implementation_constraints") ||
            explainerByKind.get("limitations") ||
            itemFacets.length > 0) && (
            <Section title="Implementation Constraints">
              <div className="space-y-5">
                {itemFacets.length > 0 && (
                  <div className="flex flex-wrap gap-2 font-ui text-xs">
                    {itemFacets.map((facet) => (
                      <span
                        key={`${facet.facet_name}-${facet.facet_value}`}
                        className="rounded bg-surface-alt px-2 py-1 text-ink-secondary"
                        title={facet.evidence_note ?? undefined}
                      >
                        {facet.facet_name.replace(/_/g, " ")}:{" "}
                        {facet.facet_value.replace(/_/g, " ")}
                      </span>
                    ))}
                  </div>
                )}
                {explainerByKind.get("implementation_constraints") && (
                  <p className="text-sm leading-relaxed text-ink-secondary">
                    {explainerByKind.get("implementation_constraints")?.body}
                  </p>
                )}
                {explainerByKind.get("limitations") && (
                  <p className="text-sm leading-relaxed text-ink-secondary">
                    {explainerByKind.get("limitations")?.body}
                  </p>
                )}
              </div>
            </Section>
          )}

          {/* Validation Matrix */}
          {item.validation_rollup && (
            <Section title="Validation">
              <ValidationMatrix rollup={item.validation_rollup} />
            </Section>
          )}

          {/* Validation Observations */}
          {item.validations.length > 0 && (
            <Section title="Observations">
              <div>
                {item.validations.map((obs) => (
                  <ObservationRow key={obs.id} obs={obs} />
                ))}
              </div>
            </Section>
          )}

          {claims.length > 0 && (
            <Section title="Claims & Evidence">
              <div className="space-y-4">
                {claims.map((claim) => (
                  <article
                    key={claim.id}
                    className="rounded border border-edge px-4 py-4"
                  >
                    <div className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1 font-ui text-xs text-ink-muted">
                      <span className="font-semibold text-ink-secondary">
                        {claim.claim_type.replace(/_/g, " ")}
                      </span>
                      <span
                        className={
                          claim.polarity === "supports"
                            ? "text-valid"
                            : claim.polarity === "contradicts"
                              ? "text-danger"
                              : "text-ink-muted"
                        }
                      >
                        {claim.polarity}
                      </span>
                      {claim.needs_review && (
                        <span className="text-caution">needs review</span>
                      )}
                    </div>
                    <p className="text-sm leading-relaxed text-ink">
                      {claim.claim_text_normalized}
                    </p>
                    {typeof claim.source_locator?.quoted_text === "string" &&
                      claim.source_locator.quoted_text && (
                        <blockquote className="mt-3 border-l-2 border-edge pl-4 text-sm italic text-ink-secondary">
                          {claim.source_locator.quoted_text}
                        </blockquote>
                      )}
                    {claim.metrics.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 font-data text-xs text-ink-secondary">
                        {claim.metrics.map((metric, index) => (
                          <span key={`${claim.id}-metric-${index}`}>
                            {metric.metric_name.replace(/_/g, " ")}
                            {metric.value_num !== null
                              ? ` ${metric.value_num}`
                              : metric.value_text
                                ? ` ${metric.value_text}`
                                : ""}
                            {metric.unit ? ` ${metric.unit}` : ""}
                          </span>
                        ))}
                      </div>
                    )}
                    <p className="mt-3 font-ui text-xs text-ink-muted">
                      Source:{" "}
                      <PaperLink
                        document={claim.source_document}
                        className="font-medium text-ink-secondary"
                      >
                        {claim.source_document.title}
                      </PaperLink>
                    </p>
                  </article>
                ))}
              </div>
            </Section>
          )}

          {approvalEvidence &&
            (approvalEvidence.evidence_snippets.length > 0 ||
              approvalEvidence.claims.length > 0) && (
              <Section title="Approval Evidence">
                <div className="mb-4 flex flex-wrap gap-x-4 gap-y-1 font-ui text-xs text-ink-muted">
                  <span>
                    {approvalEvidence.source_document_count} source
                    {approvalEvidence.source_document_count === 1 ? "" : "s"}
                  </span>
                  <span>
                    {approvalEvidence.claim_count} linked approval claim
                    {approvalEvidence.claim_count === 1 ? "" : "s"}
                  </span>
                  {approvalEvidence.matched_first_pass_slugs.length > 0 && (
                    <span>
                      first-pass slug
                      {approvalEvidence.matched_first_pass_slugs.length === 1
                        ? ""
                        : "s"}{" "}
                      {approvalEvidence.matched_first_pass_slugs.join(", ")}
                    </span>
                  )}
                </div>

                {approvalEvidence.evidence_snippets.length > 0 && (
                  <div className="mb-6 space-y-3">
                    {approvalEvidence.evidence_snippets.map((snippet, index) => (
                      <article
                        key={`${snippet.source_document.id}-${index}`}
                        className="rounded border border-edge px-4 py-4"
                      >
                        <blockquote className="border-l-2 border-accent/30 pl-4 text-sm leading-relaxed text-ink-secondary">
                          {snippet.text}
                        </blockquote>
                        <p className="mt-3 font-ui text-xs text-ink-muted">
                          Source:{" "}
                          <PaperLink
                            document={snippet.source_document}
                            className="font-medium text-ink-secondary"
                          >
                            {snippet.source_document.title}
                          </PaperLink>
                        </p>
                      </article>
                    ))}
                  </div>
                )}

                {approvalEvidence.claims.length > 0 && (
                  <div className="space-y-4">
                    {approvalEvidence.claims.map((claim) => (
                      <article
                        key={claim.id}
                        className="rounded border border-edge px-4 py-4"
                      >
                        <div className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1 font-ui text-xs text-ink-muted">
                          <span className="font-semibold text-ink-secondary">
                            {claim.claim_type.replace(/_/g, " ")}
                          </span>
                          <span
                            className={
                              claim.polarity === "supports"
                                ? "text-valid"
                                : claim.polarity === "contradicts"
                                  ? "text-danger"
                                  : "text-ink-muted"
                            }
                          >
                            {claim.polarity}
                          </span>
                        </div>
                        <p className="text-sm leading-relaxed text-ink">
                          {claim.claim_text_normalized}
                        </p>
                        {typeof claim.source_locator?.quoted_text === "string" &&
                          claim.source_locator.quoted_text && (
                            <blockquote className="mt-3 border-l-2 border-edge pl-4 text-sm italic text-ink-secondary">
                              {claim.source_locator.quoted_text}
                            </blockquote>
                          )}
                        <p className="mt-3 font-ui text-xs text-ink-muted">
                          Source:{" "}
                          <PaperLink
                            document={claim.source_document}
                            className="font-medium text-ink-secondary"
                          >
                            {claim.source_document.title}
                          </PaperLink>
                        </p>
                      </article>
                    ))}
                  </div>
                )}
              </Section>
            )}

          {(explainerByKind.get("strengths") ||
            comparisons.length > 0 ||
            fallback.comparisonGuidance) && (
            <Section title="Comparisons">
              <div className="space-y-5">
                {(explainerByKind.get("strengths") || fallback.comparisonGuidance) && (
                  <p className="text-sm leading-relaxed text-ink-secondary">
                    {explainerByKind.get("strengths")?.body ??
                      fallback.comparisonGuidance}
                  </p>
                )}
                {comparisons.map((comparison) => (
                  <div
                    key={`${comparison.related_item_slug}-${comparison.relation_type}`}
                    className="rounded border border-edge px-4 py-4"
                  >
                    <div className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1">
                      <p className="font-ui text-sm font-medium text-ink">
                        Compared with{" "}
                        <Link
                          href={`/items/${comparison.related_item_slug}`}
                          className="text-accent hover:underline"
                        >
                          {renderInlineTitle(comparison.related_item_name)}
                        </Link>
                      </p>
                    </div>
                    <p className="text-sm leading-relaxed text-ink-secondary">
                      {comparison.summary}
                    </p>
                    {comparison.overlap_reasons.length > 0 && (
                      <p className="mt-2 font-ui text-xs text-ink-muted">
                        Shared frame: {comparison.overlap_reasons.join("; ")}
                      </p>
                    )}
                    {comparison.strengths.length > 0 && (
                      <p className="mt-2 text-sm text-ink-secondary">
                        Strengths here: {comparison.strengths.join("; ")}.
                      </p>
                    )}
                    {comparison.weaknesses.length > 0 && (
                      <p className="mt-1 text-sm text-ink-muted">
                        Relative tradeoffs: {comparison.weaknesses.join("; ")}.
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Citations */}
          <Section title="Ranked Citations">
            {item.citations.length > 0 ? (
              <CitationList citations={item.citations} />
            ) : (
              <p className="font-ui text-sm italic text-ink-muted">
                No citations yet. This item needs source-backed curation.
              </p>
            )}
          </Section>

          {/* Curation status */}
          {item.status === "seed" && (
            <Section title="Curation Status">
              <div className="rounded border border-caution-light bg-caution-light/30 px-5 py-4 font-ui text-sm text-caution">
                <p className="mb-2 font-semibold">
                  Seed dossier &mdash; not yet curator-complete
                </p>
                <ul className="list-inside list-disc space-y-1 text-ink-secondary">
                  <li>
                    Validation rollups and replication scores are pending
                    ingestion
                  </li>
                  <li>
                    Citation list may be incomplete or contain placeholders
                  </li>
                  <li>
                    Observation table will populate once evidence is curated
                  </li>
                </ul>
              </div>
            </Section>
          )}
        </div>

        {/* Sidebar */}
        <aside className="space-y-8">
          {rep ? (
            <>
              {/* Scores */}
              <div>
                <p className="small-caps mb-4">Scores</p>
                <ScoreBreakdown
                  scores={[
                    { label: "Evidence", value: rep.evidence_strength_score },
                    { label: "Replication", value: rep.replication_score },
                    { label: "Practicality", value: rep.practicality_score },
                    {
                      label: "Translatability",
                      value: rep.translatability_score,
                    },
                  ]}
                />
                <p className="mt-3 font-data text-[10px] text-ink-faint">
                  v{rep.score_version}
                </p>
              </div>

              <hr />

              {/* Replication Stats */}
              <div>
                <p className="small-caps mb-4">Replication</p>
                <dl className="space-y-2 font-ui text-sm">
                  {(
                    [
                      ["Papers", rep.primary_paper_count],
                      ["Independent", rep.independent_primary_paper_count],
                      ["Author clusters", rep.distinct_last_author_clusters],
                      ["Institutions", rep.distinct_institutions],
                      ["Bio contexts", rep.distinct_biological_contexts],
                      ["Years", rep.years_since_first_report ?? "\u2014"],
                      ["Applications", rep.downstream_application_count],
                    ] as [string, string | number][]
                  ).map(([label, value]) => (
                    <div key={label} className="flex justify-between">
                      <dt className="text-ink-muted">{label}</dt>
                      <dd className="font-data tabular-nums text-ink">
                        {String(value)}
                      </dd>
                    </div>
                  ))}
                  {rep.orphan_tool_flag && (
                    <p className="mt-2 text-sm text-danger">
                      Orphan tool &mdash; limited independent reuse
                    </p>
                  )}
                </dl>
                {rep.explanation &&
                  Object.keys(rep.explanation).length > 0 && (
                    <p className="mt-3 text-xs leading-relaxed text-ink-muted">
                      Computed from canonical claims, citations, validation
                      observations, and practical penalties in the current
                      database snapshot.
                    </p>
                  )}
              </div>

              {/* Practicality Penalties */}
              {rep.practicality_penalties.length > 0 && (
                <>
                  <hr />
                  <div>
                    <p className="small-caps mb-3 text-caution">Penalties</p>
                    <ul className="space-y-2">
                      {rep.practicality_penalties.map((p, i) => (
                        <li key={i} className="flex gap-2 text-sm text-caution">
                          <span className="shrink-0">&bull;</span>
                          <span className="font-body">{p}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
            </>
          ) : (
            <div>
              <p className="small-caps mb-4">Scores</p>
              <p className="font-ui text-sm italic text-ink-muted">
                {fallback.scoreStatus}
              </p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
