import { notFound } from "next/navigation";
import Link from "next/link";
import { getItemBySlug } from "@/lib/backend-data";
import { getItemTaxonomyPosition } from "@/lib/item-hierarchy";
import { renderInlineTitle, stripInlineTitleMarkup } from "@/lib/render-inline-title";
import { isSupportedTechnique } from "@/lib/vocabularies";
import type { SourceDocument, ExtractedWorkflow, ItemRelationLink } from "@/lib/types";
import { ScoreBreakdown } from "@/components/score-bar";
import { ValidationMatrix } from "@/components/validation-dots";
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
import { CITATION_ROLE_LABELS } from "@/lib/vocabularies";

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

function sourceAnchor(documentId: string) {
  return `#source-${documentId}`;
}

function claimAnchor(claimId: string) {
  return `#claim-${claimId}`;
}

function citationAnchor(citationId: string) {
  return `#citation-${citationId}`;
}

function getLocatorRows(locator: Record<string, unknown>) {
  const entries: Array<{ label: string; value: string }> = [];
  if (typeof locator.section_label === "string" && locator.section_label.trim()) {
    entries.push({ label: "Section", value: locator.section_label });
  }
  if (typeof locator.page_or_locator === "string" && locator.page_or_locator.trim()) {
    entries.push({ label: "Page / locator", value: locator.page_or_locator });
  }
  if (typeof locator.chunk_index === "number") {
    entries.push({ label: "Chunk", value: String(locator.chunk_index) });
  }
  return entries;
}

type EvidenceSource = {
  document: SourceDocument;
  supportText?: string | null;
  evidenceText?: string | null;
  extractField?: string | null;
};

function extractMarkdownBullets(
  markdown: string | null | undefined,
  heading: string,
): string[] {
  if (!markdown) {
    return [];
  }
  const escapedHeading = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = markdown.match(
    new RegExp(`^## ${escapedHeading}\\s*\\n([\\s\\S]*?)(?=^##\\s|\\Z)`, "m"),
  );
  const section = match?.[1] ?? "";
  return section
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => /^(-|\d+\.)\s+/.test(line))
    .map((line) =>
      line
        .replace(/^(-|\d+\.)\s+/, "")
        .replace(/`([^`]+)`/g, "$1")
        .trim(),
    )
    .filter(Boolean);
}

function getEvidenceSources(
  payload: Record<string, unknown> | undefined,
): EvidenceSource[] {
  const rawSources = payload?.sources;
  if (!Array.isArray(rawSources)) {
    return [];
  }
  const parsedSources: EvidenceSource[] = [];
  for (const source of rawSources) {
    if (!source || typeof source !== "object") {
      continue;
    }
    const sourceRecord = source as Record<string, unknown>;
    const rawDocument = sourceRecord.document;
    if (!rawDocument || typeof rawDocument !== "object") {
      continue;
    }
    const document = rawDocument as Record<string, unknown>;
    const id = typeof document.id === "string" ? document.id : null;
    const title = typeof document.title === "string" ? document.title : null;
    const sourceType =
      typeof document.source_type === "string" ? document.source_type : null;
    if (!id || !title || !sourceType) {
      continue;
    }
    parsedSources.push({
      document: {
        id,
        title,
        source_type: sourceType,
        publication_year:
          typeof document.publication_year === "number"
            ? document.publication_year
            : null,
        journal_or_source:
          typeof document.journal_or_source === "string"
            ? document.journal_or_source
            : null,
        doi: typeof document.doi === "string" ? document.doi : null,
        pmid: typeof document.pmid === "string" ? document.pmid : null,
        is_retracted: Boolean(document.is_retracted),
      },
      supportText:
        typeof sourceRecord.support_text === "string"
          ? sourceRecord.support_text
          : null,
      evidenceText:
        typeof sourceRecord.evidence_text === "string"
          ? sourceRecord.evidence_text
          : null,
      extractField:
        typeof sourceRecord.extract_field === "string"
          ? sourceRecord.extract_field
          : null,
    });
  }
  return parsedSources;
}

function EvidenceSources({
  payload,
}: {
  payload?: Record<string, unknown>;
}) {
  const sources = getEvidenceSources(payload);
  if (sources.length === 0) {
    return null;
  }
  return (
    <div className="mt-3 space-y-2">
      {sources.map((source, index) => (
        <div
          key={`${source.document.id}-${index}`}
          className="rounded bg-surface-alt px-3 py-2"
        >
          <p className="font-ui text-xs text-ink-muted">
            Source:{" "}
            <PaperLink
              document={source.document}
              className="font-medium text-ink-secondary"
            >
              {renderInlineTitle(source.document.title)}
            </PaperLink>
          </p>
          {source.supportText && (
            <p className="mt-1 text-sm leading-relaxed text-ink-secondary">
              {renderInlineTitle(source.supportText)}
            </p>
          )}
        </div>
      ))}
    </div>
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
  const claims = (item.claims ?? []).filter(
    (claim, i, arr) => arr.findIndex((c) => c.id === claim.id) === i,
  );
  const itemFacets = item.item_facets ?? [];
  const comparisons = item.comparisons ?? [];
  const problemLinks = item.problem_links ?? [];
  const sortedCitations = [...item.citations].sort(
    (left, right) => left.importance_rank - right.importance_rank,
  );
  const workflowRecommendations = item.workflow_recommendations ?? [];
  const extractedWorkflows: ExtractedWorkflow[] = item.extracted_workflows ?? [];
  const explainerByKind = new Map(
    explainers.map((explainer) => [explainer.explainer_kind, explainer]),
  );
  const taxonomyPosition = getItemTaxonomyPosition(item.item_type);
  const workflowLikelyFit = extractMarkdownBullets(
    item.workflow_fit_markdown,
    "Likely Fit",
  );
  const workflowMissingEvidence = extractMarkdownBullets(
    item.workflow_fit_markdown,
    "Missing Evidence",
  );
  const visibleTechniques = item.techniques.filter(isSupportedTechnique);
  const parentItems: ItemRelationLink[] = item.parent_items ?? [];
  const childItems: ItemRelationLink[] = item.child_items ?? [];
  const hasHierarchy = parentItems.length > 0 || childItems.length > 0;
  const approvalEvidence = item.approval_evidence;
  const sourceDocumentsById = new Map<string, SourceDocument>();
  for (const citation of sortedCitations) {
    sourceDocumentsById.set(citation.document.id, citation.document);
  }
  for (const claim of claims) {
    sourceDocumentsById.set(claim.source_document.id, claim.source_document);
  }
  const sourceDocuments = Array.from(sourceDocumentsById.values());
  const sourceIndexById = new Map(
    sourceDocuments.map((document, index) => [document.id, index + 1]),
  );
  const claimNumberById = new Map(claims.map((claim, index) => [claim.id, index + 1]));
  const citationNumberById = new Map(
    sortedCitations.map((citation, index) => [citation.id, index + 1]),
  );
  const claimsBySourceId = new Map<string, typeof claims>();
  const citationsBySourceId = new Map<string, typeof sortedCitations>();
  for (const claim of claims) {
    const existing = claimsBySourceId.get(claim.source_document.id) ?? [];
    if (!existing.some((c) => c.id === claim.id)) {
      existing.push(claim);
    }
    claimsBySourceId.set(claim.source_document.id, existing);
  }
  for (const citation of sortedCitations) {
    const existing = citationsBySourceId.get(citation.document.id) ?? [];
    if (!existing.some((c) => c.id === citation.id)) {
      existing.push(citation);
    }
    citationsBySourceId.set(citation.document.id, existing);
  }

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

      {hasHierarchy && (
        <section className="mb-12 rounded border border-edge bg-surface-alt px-5 py-4">
          <p className="small-caps mb-3">Assembly Hierarchy</p>
          <div className="space-y-3">
            {parentItems.length > 0 && (
              <div>
                <p className="mb-1.5 font-ui text-xs font-medium uppercase tracking-wide text-ink-muted">
                  Part of
                </p>
                <ul className="space-y-1.5">
                  {parentItems.map((parent) => (
                    <li key={parent.slug} className="flex items-center gap-2">
                      <span className="text-ink-faint" aria-hidden="true">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
                          <path fillRule="evenodd" d="M4.5 2A2.5 2.5 0 0 0 2 4.5v2.879a2.5 2.5 0 0 0 .732 1.767l4.5 4.5a2.5 2.5 0 0 0 3.536 0l2.878-2.878a2.5 2.5 0 0 0 0-3.536l-4.5-4.5A2.5 2.5 0 0 0 7.379 2H4.5ZM5 6a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clipRule="evenodd" />
                        </svg>
                      </span>
                      <Link
                        href={`/items/${parent.slug}`}
                        className="font-ui text-sm font-medium text-accent hover:underline"
                      >
                        {renderInlineTitle(parent.canonical_name)}
                      </Link>
                      {parent.item_type && (
                        <span className="rounded bg-surface px-1.5 py-0.5 font-ui text-[10px] text-ink-muted">
                          {parent.item_type.replace(/_/g, " ")}
                        </span>
                      )}
                      <span className="font-ui text-xs text-ink-muted">
                        &larr; this item is a component
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {childItems.length > 0 && (
              <div>
                <p className="mb-1.5 font-ui text-xs font-medium uppercase tracking-wide text-ink-muted">
                  Components
                </p>
                <ul className="space-y-1.5">
                  {childItems.map((child) => (
                    <li key={child.slug} className="flex items-center gap-2">
                      <span className="text-ink-faint" aria-hidden="true">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
                          <path d="M8.5 4.5a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0ZM10.9 12.006c.11.542-.348.994-.9.994H2c-.553 0-1.01-.452-.902-.994a5.002 5.002 0 0 1 9.803 0ZM14.002 12h-1.59a2.556 2.556 0 0 0-.04-.29 6.476 6.476 0 0 0-1.167-2.603 3.002 3.002 0 0 1 3.633 1.911c.18.522-.283.982-.836.982ZM12 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
                        </svg>
                      </span>
                      <Link
                        href={`/items/${child.slug}`}
                        className="font-ui text-sm font-medium text-accent hover:underline"
                      >
                        {renderInlineTitle(child.canonical_name)}
                      </Link>
                      {child.item_type && (
                        <span className="rounded bg-surface px-1.5 py-0.5 font-ui text-[10px] text-ink-muted">
                          {child.item_type.replace(/_/g, " ")}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}

      <div className="grid gap-16 lg:grid-cols-[1fr_280px]">
        {/* Main column */}
        <div>
          {/* Summary */}
          <Section title="Summary">
            <p className="text-lg leading-relaxed text-ink-secondary">
              {item.summary ? renderInlineTitle(item.summary) : "No summary available."}
            </p>
          </Section>

          <Section title="Usefulness & Problems">
            <div className="space-y-5">
              {explainerByKind.get("usefulness") && (
                <div>
                  <p className="mb-1 text-xs uppercase tracking-wide text-ink-muted">
                    Why this is useful
                  </p>
                  <p className="text-sm leading-relaxed text-ink-secondary">
                    {renderInlineTitle(explainerByKind.get("usefulness")!.body)}
                  </p>
                  <EvidenceSources
                    payload={explainerByKind.get("usefulness")?.evidence_payload}
                  />
                </div>
              )}
              {explainerByKind.get("problem_solved") && (
                <div>
                  <p className="mb-1 text-xs uppercase tracking-wide text-ink-muted">
                    Problem solved
                  </p>
                  <p className="text-sm leading-relaxed text-ink-secondary">
                    {renderInlineTitle(explainerByKind.get("problem_solved")!.body)}
                  </p>
                  <EvidenceSources
                    payload={explainerByKind.get("problem_solved")?.evidence_payload}
                  />
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
                              : problem.source_kind === "literature_extract"
                                ? "Literature"
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
                          {renderInlineTitle(problem.why_this_item_helps)}
                        </p>
                        <EvidenceSources payload={problem.evidence_payload} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {!explainerByKind.get("usefulness") &&
                !explainerByKind.get("problem_solved") &&
                problemLinks.length === 0 && (
                  <p className="font-ui text-sm italic text-ink-muted">
                    No literature-backed usefulness or problem-fit explainer has
                    been materialized for this record yet.
                  </p>
                )}
            </div>
          </Section>

          {(extractedWorkflows.length > 0 ||
            workflowRecommendations.length > 0 ||
            workflowLikelyFit.length > 0 ||
            workflowMissingEvidence.length > 0) && (
            <Section title="Published Workflows">
              <div className="space-y-4">
                {extractedWorkflows.map((wf, index) => {
                  const doc = wf.source_document;
                  const year = doc?.publication_year;
                  return (
                    <div
                      key={`extracted-wf-${index}`}
                      className="rounded border border-edge px-4 py-3"
                    >
                      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                        {doc?.title && (
                          <p className="font-ui text-sm font-medium text-ink">
                            {doc.doi ? (
                              <a
                                href={`https://doi.org/${doc.doi}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-accent hover:underline"
                              >
                                {renderInlineTitle(doc.title)}
                              </a>
                            ) : (
                              renderInlineTitle(doc.title)
                            )}
                          </p>
                        )}
                        {year && (
                          <span className="font-ui text-xs text-ink-muted">
                            {year}
                          </span>
                        )}
                      </div>

                      {wf.workflow_objective && (
                        <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                          <span className="font-ui text-xs font-medium uppercase text-ink-muted">
                            Objective:{" "}
                          </span>
                          {renderInlineTitle(wf.workflow_objective)}
                        </p>
                      )}

                      {wf.why_workflow_works && (
                        <p className="mt-1 text-sm leading-relaxed text-ink-secondary">
                          <span className="font-ui text-xs font-medium uppercase text-ink-muted">
                            Why it works:{" "}
                          </span>
                          {renderInlineTitle(wf.why_workflow_works)}
                        </p>
                      )}

                      {(wf.target_mechanisms.length > 0 ||
                        wf.target_techniques.length > 0) && (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {wf.target_mechanisms.map((m) => (
                            <span
                              key={m}
                              className="rounded bg-violet-50 px-2 py-0.5 font-ui text-xs text-violet-800"
                            >
                              {m}
                            </span>
                          ))}
                          {wf.target_techniques.map((t) => (
                            <span
                              key={t}
                              className="rounded bg-emerald-50 px-2 py-0.5 font-ui text-xs text-emerald-800"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      )}

                      {wf.stages.length > 0 && (
                        <div className="mt-3">
                          <p className="mb-1.5 font-ui text-xs font-medium uppercase tracking-wide text-ink-muted">
                            Stages
                          </p>
                          <ol className="space-y-1.5 text-sm">
                            {wf.stages.map((stage, si) => (
                              <li key={si} className="flex gap-2">
                                <span className="shrink-0 font-data text-xs text-ink-faint">
                                  {stage.stage_order}.
                                </span>
                                <div>
                                  <span className="font-ui font-medium text-ink">
                                    {renderInlineTitle(stage.stage_name)}
                                  </span>
                                  <span className="ml-1 font-ui text-xs text-ink-muted">
                                    ({stage.stage_kind})
                                  </span>
                                  {stage.why_stage_exists && (
                                    <p className="mt-0.5 text-ink-secondary">
                                      {renderInlineTitle(stage.why_stage_exists)}
                                    </p>
                                  )}
                                  {stage.selection_basis && (
                                    <p className="mt-0.5 text-xs text-ink-muted">
                                      Selection: {renderInlineTitle(stage.selection_basis)}
                                    </p>
                                  )}
                                </div>
                              </li>
                            ))}
                          </ol>
                        </div>
                      )}

                      {wf.steps.length > 0 && (
                        <div className="mt-3">
                          <p className="mb-1.5 font-ui text-xs font-medium uppercase tracking-wide text-ink-muted">
                            Steps
                          </p>
                          <ol className="space-y-1.5 text-sm">
                            {wf.steps.map((step, si) => (
                              <li key={si} className="flex gap-2">
                                <span className="shrink-0 font-data text-xs text-ink-faint">
                                  {step.step_order}.
                                </span>
                                <div>
                                  <span className="font-ui font-medium text-ink">
                                    {renderInlineTitle(step.step_name)}
                                  </span>
                                  {step.item_role && (
                                    <span className="ml-1.5 rounded bg-blue-50 px-1.5 py-0.5 font-ui text-xs text-blue-800">
                                      {step.item_role}
                                    </span>
                                  )}
                                  {step.purpose && (
                                    <p className="mt-0.5 text-ink-secondary">
                                      {renderInlineTitle(step.purpose)}
                                    </p>
                                  )}
                                  {step.why_this_step_now && (
                                    <p className="mt-0.5 text-xs text-ink-muted">
                                      {renderInlineTitle(step.why_this_step_now)}
                                    </p>
                                  )}
                                </div>
                              </li>
                            ))}
                          </ol>
                        </div>
                      )}
                    </div>
                  );
                })}

                {extractedWorkflows.length === 0 &&
                  workflowRecommendations.length > 0 &&
                  workflowRecommendations.map((recommendation) => (
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

                {extractedWorkflows.length === 0 &&
                  workflowRecommendations.length === 0 &&
                  workflowLikelyFit.length > 0 && (
                    <div>
                      <p className="mb-2 text-xs uppercase tracking-wide text-ink-muted">
                        Likely fit
                      </p>
                      <ul className="space-y-2 text-sm leading-relaxed text-ink-secondary">
                        {workflowLikelyFit.map((note) => (
                          <li key={note} className="flex gap-2">
                            <span className="shrink-0 text-ink-faint">
                              &bull;
                            </span>
                            <span>{note}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                {extractedWorkflows.length === 0 &&
                  workflowMissingEvidence.length > 0 && (
                    <div>
                      <p className="mb-2 text-xs uppercase tracking-wide text-ink-muted">
                        Missing evidence
                      </p>
                      <ul className="space-y-2 text-sm leading-relaxed text-ink-muted">
                        {workflowMissingEvidence.map((note) => (
                          <li key={note} className="flex gap-2">
                            <span className="shrink-0 text-ink-faint">
                              &bull;
                            </span>
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
                    {renderInlineTitle(explainerByKind.get("implementation_constraints")!.body)}
                  </p>
                )}
                {explainerByKind.get("limitations") && (
                  <p className="text-sm leading-relaxed text-ink-secondary">
                    {renderInlineTitle(explainerByKind.get("limitations")!.body)}
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

          {sourceDocuments.length > 0 && (
            <Section title="Supporting Sources">
              <div className="space-y-3">
                {sourceDocuments.map((document) => {
                  const relatedClaims = claimsBySourceId.get(document.id) ?? [];
                  const relatedCitations = citationsBySourceId.get(document.id) ?? [];
                  const sourceNumber = sourceIndexById.get(document.id) ?? "?";
                  return (
                    <article
                      key={document.id}
                      id={`source-${document.id}`}
                      className="rounded border border-edge px-4 py-4"
                    >
                      <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-2 font-ui text-xs text-ink-muted">
                        <span className="rounded bg-surface-alt px-2 py-1 font-semibold text-ink-secondary">
                          Source {sourceNumber}
                        </span>
                        <span>{document.source_type.replace(/_/g, " ")}</span>
                        {document.publication_year ? <span>{document.publication_year}</span> : null}
                        {document.journal_or_source ? (
                          <span>{document.journal_or_source}</span>
                        ) : null}
                      </div>
                      <div className="mb-2 text-sm text-ink">
                        <PaperLink
                          document={document}
                          className="text-left text-ink no-underline hover:text-accent hover:underline"
                        >
                          {renderInlineTitle(document.title)}
                        </PaperLink>
                      </div>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 font-ui text-xs text-ink-muted">
                        <a href="#ranked-citations" className="text-accent hover:underline">
                          {relatedCitations.length} ranked citation
                          {relatedCitations.length === 1 ? "" : "s"}
                        </a>
                        <a href="#ranked-claims" className="text-accent hover:underline">
                          {relatedClaims.length} ranked claim
                          {relatedClaims.length === 1 ? "" : "s"}
                        </a>
                        {relatedCitations.slice(0, 3).map((citation) => (
                          <a
                            key={citation.id}
                            href={citationAnchor(citation.id)}
                            className="text-accent hover:underline"
                          >
                            Citation {citationNumberById.get(citation.id) ?? "?"}
                          </a>
                        ))}
                        {relatedClaims.slice(0, 3).map((claim) => (
                          <a
                            key={claim.id}
                            href={claimAnchor(claim.id)}
                            className="text-accent hover:underline"
                          >
                            Claim {claimNumberById.get(claim.id) ?? "?"}
                          </a>
                        ))}
                      </div>
                    </article>
                  );
                })}
              </div>
            </Section>
          )}

          {claims.length > 0 && (
            <Section title="Ranked Claims">
              <div className="space-y-4">
                {claims.map((claim, index) => {
                  const sourceNumber = sourceIndexById.get(claim.source_document.id) ?? "?";
                  const locatorRows = getLocatorRows(claim.source_locator);
                  return (
                  <article
                    key={claim.id}
                    id={`claim-${claim.id}`}
                    className="rounded border border-edge px-4 py-4"
                  >
                    <div className="mb-2 flex flex-wrap items-center gap-x-2 gap-y-1 font-ui text-xs text-ink-muted">
                      <span className="rounded bg-surface-alt px-2 py-1 font-semibold text-ink-secondary">
                        Claim {index + 1}
                      </span>
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
                      {claim.source_document.publication_year && (
                        <span>{claim.source_document.publication_year}</span>
                      )}
                      <a
                        href={sourceAnchor(claim.source_document.id)}
                        className="text-accent hover:underline"
                      >
                        Source {sourceNumber}
                      </a>
                      <PaperLink
                        document={claim.source_document}
                        className="font-medium text-ink-secondary"
                      >
                        {renderInlineTitle(claim.source_document.title)}
                      </PaperLink>
                      {claim.needs_review && (
                        <span className="text-caution">needs review</span>
                      )}
                    </div>
                    <p className="text-sm leading-relaxed text-ink">
                      {renderInlineTitle(claim.claim_text_normalized)}
                    </p>
                    {typeof claim.source_locator?.quoted_text === "string" &&
                      claim.source_locator.quoted_text && (
                        <blockquote className="mt-3 border-l-2 border-edge pl-4 text-sm italic text-ink-secondary">
                          {renderInlineTitle(claim.source_locator.quoted_text)}
                        </blockquote>
                      )}
                    {locatorRows.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 font-ui text-xs text-ink-muted">
                        {locatorRows.map((row) => (
                          <span key={`${claim.id}-${row.label}`}>
                            {row.label}: {row.value}
                          </span>
                        ))}
                      </div>
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
                  </article>
                  );
                })}
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
                          {renderInlineTitle(snippet.text)}
                        </blockquote>
                        <p className="mt-3 font-ui text-xs text-ink-muted">
                          Source:{" "}
                          <PaperLink
                            document={snippet.source_document}
                            className="font-medium text-ink-secondary"
                          >
                            {renderInlineTitle(snippet.source_document.title)}
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
                          {renderInlineTitle(claim.claim_text_normalized)}
                        </p>
                        {typeof claim.source_locator?.quoted_text === "string" &&
                          claim.source_locator.quoted_text && (
                            <blockquote className="mt-3 border-l-2 border-edge pl-4 text-sm italic text-ink-secondary">
                              {renderInlineTitle(claim.source_locator.quoted_text)}
                            </blockquote>
                          )}
                        <p className="mt-3 font-ui text-xs text-ink-muted">
                          Source:{" "}
                          <PaperLink
                            document={claim.source_document}
                            className="font-medium text-ink-secondary"
                          >
                            {renderInlineTitle(claim.source_document.title)}
                          </PaperLink>
                        </p>
                      </article>
                    ))}
                  </div>
                )}
              </Section>
            )}

          <Section title="Comparisons">
            <div className="space-y-5">
              {explainerByKind.get("alternatives") && (
                <div>
                  <p className="mb-1 text-xs uppercase tracking-wide text-ink-muted">
                    Source-stated alternatives
                  </p>
                  <p className="text-sm leading-relaxed text-ink-secondary">
                    {renderInlineTitle(explainerByKind.get("alternatives")!.body)}
                  </p>
                  <EvidenceSources
                    payload={explainerByKind.get("alternatives")?.evidence_payload}
                  />
                </div>
              )}
              {explainerByKind.get("strengths") && (
                <div>
                  <p className="mb-1 text-xs uppercase tracking-wide text-ink-muted">
                    Source-backed strengths
                  </p>
                  <p className="text-sm leading-relaxed text-ink-secondary">
                    {renderInlineTitle(explainerByKind.get("strengths")!.body)}
                  </p>
                  <EvidenceSources
                    payload={explainerByKind.get("strengths")?.evidence_payload}
                  />
                </div>
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
                    {renderInlineTitle(comparison.summary)}
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
                  <EvidenceSources payload={comparison.evidence_payload} />
                </div>
              ))}
              {!explainerByKind.get("alternatives") &&
                !explainerByKind.get("strengths") &&
                comparisons.length === 0 && (
                  <p className="font-ui text-sm italic text-ink-muted">
                    No literature-backed comparison notes have been materialized
                    for this record yet.
                  </p>
                )}
            </div>
          </Section>

          {/* Citations */}
          <Section title="Ranked Citations">
            {sortedCitations.length > 0 ? (
              <ol id="ranked-citations" className="space-y-6">
                {sortedCitations.map((citation, index) => {
                  const sourceNumber = sourceIndexById.get(citation.document.id) ?? "?";
                  const relatedClaims = claimsBySourceId.get(citation.document.id) ?? [];
                  return (
                    <li
                      key={citation.id}
                      id={`citation-${citation.id}`}
                      className="flex gap-4"
                    >
                      <span className="mt-1 font-data text-sm font-bold text-ink-muted">
                        {index + 1}.
                      </span>
                      <div className="flex-1">
                        <PaperLink
                          document={citation.document}
                          citationRole={citation.citation_role}
                          whyThisMatters={citation.why_this_matters}
                          className="font-body text-[15px] font-medium leading-snug text-ink"
                        >
                          {renderInlineTitle(citation.document.title)}
                        </PaperLink>
                        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 font-ui text-xs">
                          <span className="font-semibold text-accent">
                            {CITATION_ROLE_LABELS[citation.citation_role]}
                          </span>
                          <a
                            href={sourceAnchor(citation.document.id)}
                            className="text-accent hover:underline"
                          >
                            Source {sourceNumber}
                          </a>
                          {citation.document.journal_or_source &&
                            !citation.document.journal_or_source.startsWith("http") && (
                              <span className="italic text-ink-muted">
                                {citation.document.journal_or_source}
                              </span>
                            )}
                          {citation.document.publication_year && (
                            <span className="font-data text-ink-muted">
                              {citation.document.publication_year}
                            </span>
                          )}
                          {relatedClaims.slice(0, 3).map((claim) => (
                            <a
                              key={`${citation.id}-${claim.id}`}
                              href={claimAnchor(claim.id)}
                              className="text-accent hover:underline"
                            >
                              Claim {claimNumberById.get(claim.id) ?? "?"}
                            </a>
                          ))}
                          {citation.document.is_retracted && (
                            <span className="font-bold text-danger">RETRACTED</span>
                          )}
                        </div>
                        <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">
                          {renderInlineTitle(citation.why_this_matters)}
                        </p>
                      </div>
                    </li>
                  );
                })}
              </ol>
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
                Scores are unavailable because the citation and validation inputs
                needed for evidence-weighted scoring have not yet been fully
                materialized for this record.
              </p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
