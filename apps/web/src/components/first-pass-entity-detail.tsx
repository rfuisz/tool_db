"use client";

import Link from "next/link";

import { FirstPassLiveRefresh } from "@/components/first-pass-live-refresh";
import { PaperLink } from "@/components/paper-link";
import { Tooltip } from "@/components/tooltip";
import { renderInlineTitle } from "@/lib/render-inline-title";
import type {
  FirstPassClaim,
  FirstPassEntityDetail,
  FirstPassExplainer,
  FirstPassEvidenceSnippet,
  FirstPassSourceDocument,
  FirstPassWorkflowObservation,
  FirstPassWorkflowStageObservation,
  FirstPassWorkflowStepObservation,
  SourceDocument,
} from "@/lib/types";

const FIRST_PASS_EXPLAINER_LABELS: Record<string, string> = {
  what_it_does: "What the tool is doing",
  resources_required: "Resources required",
  problem_it_solves: "What problem it solves",
  problem_it_does_not_solve: "What it does not solve",
  alternatives: "Alternatives",
};

const FIRST_PASS_EXPLAINER_ORDER = [
  "what_it_does",
  "resources_required",
  "problem_it_solves",
  "problem_it_does_not_solve",
  "alternatives",
] as const;

function sourceAnchor(documentId: string) {
  return `#source-${documentId}`;
}

function claimAnchor(claimId: string) {
  return `#claim-${claimId}`;
}

function stageAnchor(localId: string) {
  return `#stage-${localId}`;
}

function formatLabel(value: string) {
  return value.replace(/_/g, " ");
}

function toPaperDocument(doc: FirstPassSourceDocument): SourceDocument {
  return {
    id: doc.id,
    title: doc.title,
    source_type: doc.source_type,
    publication_year: doc.publication_year,
    journal_or_source: doc.journal_or_source,
    doi: doc.doi,
    pmid: doc.pmid,
    is_retracted: false,
  };
}

function getQuotedText(claim: FirstPassClaim) {
  const quotedText = claim.source_locator.quoted_text;
  return typeof quotedText === "string" && quotedText.trim()
    ? quotedText.trim()
    : null;
}

function getLocatorRows(locator: Record<string, unknown>) {
  const entries: Array<{ label: string; value: string }> = [];
  const chunkIndex = locator.chunk_index;
  const sectionLabel = locator.section_label;
  const pageOrLocator = locator.page_or_locator;

  if (typeof sectionLabel === "string" && sectionLabel.trim()) {
    entries.push({ label: "Section", value: sectionLabel });
  }
  if (typeof pageOrLocator === "string" && pageOrLocator.trim()) {
    entries.push({ label: "Page / locator", value: pageOrLocator });
  }
  if (typeof chunkIndex === "number") {
    entries.push({ label: "Chunk", value: String(chunkIndex) });
  }

  return entries;
}

function isMethodLikeItemType(itemType: string | null) {
  return Boolean(itemType && /(_method|_technique)$/.test(itemType));
}

function getBackHref(entity: FirstPassEntityDetail) {
  if (entity.candidate_type === "workflow_template") {
    return "/first-pass/workflows";
  }
  if (isMethodLikeItemType(entity.item_type)) {
    return "/first-pass/methods";
  }
  return "/first-pass";
}

function getBackLabel(entity: FirstPassEntityDetail) {
  if (entity.candidate_type === "workflow_template") {
    return "Back to workflow browser";
  }
  if (isMethodLikeItemType(entity.item_type)) {
    return "Back to methods browser";
  }
  return "Back to first-pass browser";
}

function SourceExternalLinks({ doc }: { doc: FirstPassSourceDocument }) {
  return (
    <>
      {doc.doi ? (
        <a
          href={`https://doi.org/${doc.doi}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand hover:underline"
        >
          DOI
        </a>
      ) : null}
      {doc.pmid ? (
        <a
          href={`https://pubmed.ncbi.nlm.nih.gov/${doc.pmid}/`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand hover:underline"
        >
          PubMed
        </a>
      ) : null}
    </>
  );
}

function FreeformExplainerGroup({
  explainers,
  sourceIndexById,
}: {
  explainers: FirstPassExplainer[];
  sourceIndexById: Map<string, number>;
}) {
  const first = explainers[0];
  const label = FIRST_PASS_EXPLAINER_LABELS[first.explainer_kind] ?? formatLabel(first.explainer_kind);

  return (
    <div>
      <h3 className="mb-3 text-base text-ink">{label}</h3>
      <div className="space-y-3">
        {explainers.map((explainer, index) => {
          const sourceDocument = explainer.source_document;
          const sourceNumber = sourceIndexById.get(sourceDocument.id) ?? "?";
          return (
            <article
              key={`${explainer.explainer_kind}-${sourceDocument.id}-${index}`}
              className="rounded border border-edge bg-surface-alt px-4 py-3"
            >
              <p className="mb-3 text-sm leading-relaxed text-ink-secondary">
                {explainer.body}
              </p>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-2 font-ui text-xs text-ink-muted">
                <a
                  href={sourceAnchor(sourceDocument.id)}
                  className="text-brand hover:underline"
                >
                  Source {sourceNumber}
                </a>
                <PaperLink
                  document={toPaperDocument(sourceDocument)}
                  className="text-left text-brand no-underline hover:underline"
                >
                  {renderInlineTitle(sourceDocument.title)}
                </PaperLink>
                <SourceExternalLinks doc={sourceDocument} />
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function StageObservationCard({
  observation,
  index,
  sourceNumber,
}: {
  observation: FirstPassWorkflowStageObservation;
  index: number;
  sourceNumber: number | string;
}) {
  const locatorRows = getLocatorRows(observation.source_locator);
  const listRows = [
    {
      label: "Enriches for",
      values: observation.enriches_for_axes,
    },
    {
      label: "Guards against",
      values: observation.guards_against_axes,
    },
    {
      label: "Preserves downstream axes",
      values: observation.preserves_downstream_property_axes,
    },
  ].filter((row) => row.values.length > 0);

  return (
    <article
      id={`stage-${observation.local_id}`}
      className="scroll-mt-28 border-b border-edge pb-4 last:border-b-0 last:pb-0"
    >
      <div className="mb-2 flex flex-wrap items-center gap-2 font-ui text-xs text-ink-muted">
        <span className="rounded bg-surface-alt px-2 py-1 font-semibold text-ink-secondary">
          Stage {index + 1}
        </span>
        <span>{formatLabel(observation.stage_kind)}</span>
        {observation.search_modality ? (
          <span>{formatLabel(observation.search_modality)}</span>
        ) : null}
        <a
          href={sourceAnchor(observation.source_document.id)}
          className="text-brand hover:underline"
        >
          Source {sourceNumber}
        </a>
        <PaperLink
          document={toPaperDocument(observation.source_document)}
          className="text-left text-brand no-underline hover:underline"
        >
          {renderInlineTitle(observation.source_document.title)}
        </PaperLink>
        <SourceExternalLinks doc={observation.source_document} />
        {locatorRows.length > 0 ? (
          <Tooltip
            position="bottom"
            maxWidth="360px"
            content={
              <div className="space-y-1">
                {locatorRows.map((row) => (
                  <div key={row.label}>
                    <span className="font-semibold text-ink">{row.label}:</span>{" "}
                    <span>{row.value}</span>
                  </div>
                ))}
              </div>
            }
          >
            <span className="cursor-help border-b border-dotted border-edge text-ink-muted">
              locator
            </span>
          </Tooltip>
        ) : null}
      </div>
      <h3 className="mb-2 text-base text-ink">{renderInlineTitle(observation.stage_name)}</h3>
      <div className="space-y-2 text-sm leading-relaxed text-ink-secondary">
        {observation.why_stage_exists ? (
          <p>
            <span className="font-semibold text-ink">Why this stage exists:</span>{" "}
            {renderInlineTitle(observation.why_stage_exists)}
          </p>
        ) : null}
        {observation.selection_basis ? (
          <p>
            <span className="font-semibold text-ink">Selection basis:</span>{" "}
            {renderInlineTitle(observation.selection_basis)}
          </p>
        ) : null}
        {observation.counterselection_basis ? (
          <p>
            <span className="font-semibold text-ink">Counterselection:</span>{" "}
            {renderInlineTitle(observation.counterselection_basis)}
          </p>
        ) : null}
        {observation.advance_criteria ? (
          <p>
            <span className="font-semibold text-ink">Advance criteria:</span>{" "}
            {renderInlineTitle(observation.advance_criteria)}
          </p>
        ) : null}
        {observation.decision_gate_reason ? (
          <p>
            <span className="font-semibold text-ink">Decision gate:</span>{" "}
            {renderInlineTitle(observation.decision_gate_reason)}
          </p>
        ) : null}
        {observation.bottleneck_risk ? (
          <p>
            <span className="font-semibold text-ink">Bottleneck risk:</span>{" "}
            {renderInlineTitle(observation.bottleneck_risk)}
          </p>
        ) : null}
        {observation.higher_fidelity_than_previous !== null ? (
          <p>
            <span className="font-semibold text-ink">Higher fidelity:</span>{" "}
            {observation.higher_fidelity_than_previous ? "yes" : "no"}
          </p>
        ) : null}
        {listRows.map((row) => (
          <p key={row.label}>
            <span className="font-semibold text-ink">{row.label}:</span>{" "}
            {row.values.join(", ")}
          </p>
        ))}
      </div>
    </article>
  );
}

function WorkflowObservationCard({
  observation,
  sourceNumber,
}: {
  observation: FirstPassWorkflowObservation;
  sourceNumber: number | string;
}) {
  return (
    <article className="border-b border-edge pb-4 last:border-b-0 last:pb-0">
      <div className="mb-2 flex flex-wrap items-center gap-2 font-ui text-xs text-ink-muted">
        <span className="rounded bg-surface-alt px-2 py-1 font-semibold text-ink-secondary">
          Workflow evidence
        </span>
        <a
          href={sourceAnchor(observation.source_document.id)}
          className="text-brand hover:underline"
        >
          Source {sourceNumber}
        </a>
      </div>
      <div className="space-y-2 text-sm leading-relaxed text-ink-secondary">
        {observation.workflow_objective ? (
          <p>
            <span className="font-semibold text-ink">Objective:</span>{" "}
            {renderInlineTitle(observation.workflow_objective)}
          </p>
        ) : null}
        {observation.why_workflow_works ? (
          <p>
            <span className="font-semibold text-ink">Why it works:</span>{" "}
            {renderInlineTitle(observation.why_workflow_works)}
          </p>
        ) : null}
        {observation.workflow_priority_logic ? (
          <p>
            <span className="font-semibold text-ink">Priority logic:</span>{" "}
            {renderInlineTitle(observation.workflow_priority_logic)}
          </p>
        ) : null}
        {observation.validation_strategy ? (
          <p>
            <span className="font-semibold text-ink">Validation strategy:</span>{" "}
            {renderInlineTitle(observation.validation_strategy)}
          </p>
        ) : null}
        {observation.target_property_axes.length > 0 ? (
          <p>
            <span className="font-semibold text-ink">Target properties:</span>{" "}
            {observation.target_property_axes.join(", ")}
          </p>
        ) : null}
        {observation.target_mechanisms.length > 0 ? (
          <p>
            <span className="font-semibold text-ink">Target mechanisms:</span>{" "}
            {observation.target_mechanisms.join(", ")}
          </p>
        ) : null}
        {observation.target_techniques.length > 0 ? (
          <p>
            <span className="font-semibold text-ink">Target techniques:</span>{" "}
            {observation.target_techniques.join(", ")}
          </p>
        ) : null}
      </div>
    </article>
  );
}

function StepObservationCard({
  observation,
  sourceNumber,
}: {
  observation: FirstPassWorkflowStepObservation;
  sourceNumber: number | string;
}) {
  return (
    <article className="border-b border-edge pb-4 last:border-b-0 last:pb-0">
      <div className="mb-2 flex flex-wrap items-center gap-2 font-ui text-xs text-ink-muted">
        <span className="rounded bg-surface-alt px-2 py-1 font-semibold text-ink-secondary">
          Step {observation.step_order}
        </span>
        {observation.step_type ? <span>{formatLabel(observation.step_type)}</span> : null}
        <a
          href={sourceAnchor(observation.source_document.id)}
          className="text-brand hover:underline"
        >
          Source {sourceNumber}
        </a>
      </div>
      <h3 className="mb-2 text-base text-ink">{renderInlineTitle(observation.step_name)}</h3>
      <div className="space-y-2 text-sm leading-relaxed text-ink-secondary">
        {observation.purpose ? (
          <p>
            <span className="font-semibold text-ink">Purpose:</span>{" "}
            {renderInlineTitle(observation.purpose)}
          </p>
        ) : null}
        {observation.why_this_step_now ? (
          <p>
            <span className="font-semibold text-ink">Why now:</span>{" "}
            {renderInlineTitle(observation.why_this_step_now)}
          </p>
        ) : null}
        {observation.validation_focus ? (
          <p>
            <span className="font-semibold text-ink">Validation focus:</span>{" "}
            {renderInlineTitle(observation.validation_focus)}
          </p>
        ) : null}
        {observation.decision_gate_reason ? (
          <p>
            <span className="font-semibold text-ink">Decision gate:</span>{" "}
            {renderInlineTitle(observation.decision_gate_reason)}
          </p>
        ) : null}
        {observation.target_property_axes.length > 0 ? (
          <p>
            <span className="font-semibold text-ink">Targets properties:</span>{" "}
            {observation.target_property_axes.join(", ")}
          </p>
        ) : null}
      </div>
    </article>
  );
}

export function FirstPassEntityDetailView({
  entity,
}: {
  entity: FirstPassEntityDetail;
}) {
  const sourceIndexById = new Map(
    entity.source_documents.map((doc, index) => [doc.id, index + 1]),
  );
  const claimsBySourceId = new Map<string, FirstPassClaim[]>();
  const evidenceBySourceId = new Map<string, FirstPassEvidenceSnippet[]>();
  const workflowsBySourceId = new Map<string, FirstPassWorkflowObservation[]>();
  const stagesBySourceId = new Map<string, FirstPassWorkflowStageObservation[]>();
  const stepsBySourceId = new Map<string, FirstPassWorkflowStepObservation[]>();
  const explainersByKind = new Map<string, FirstPassExplainer[]>();

  for (const claim of entity.claims) {
    const existing = claimsBySourceId.get(claim.source_document.id) ?? [];
    existing.push(claim);
    claimsBySourceId.set(claim.source_document.id, existing);
  }

  for (const snippet of entity.evidence_snippets) {
    const sourceDocumentId = snippet.source_document?.id;
    if (!sourceDocumentId) {
      continue;
    }
    const existing = evidenceBySourceId.get(sourceDocumentId) ?? [];
    existing.push(snippet);
    evidenceBySourceId.set(sourceDocumentId, existing);
  }

  for (const observation of entity.workflow_observations) {
    const existing = workflowsBySourceId.get(observation.source_document.id) ?? [];
    existing.push(observation);
    workflowsBySourceId.set(observation.source_document.id, existing);
  }

  for (const observation of entity.workflow_stage_observations) {
    const existing = stagesBySourceId.get(observation.source_document.id) ?? [];
    existing.push(observation);
    stagesBySourceId.set(observation.source_document.id, existing);
  }

  for (const observation of entity.workflow_step_observations) {
    const existing = stepsBySourceId.get(observation.source_document.id) ?? [];
    existing.push(observation);
    stepsBySourceId.set(observation.source_document.id, existing);
  }

  for (const explainer of entity.freeform_explainers) {
    const existing = explainersByKind.get(explainer.explainer_kind) ?? [];
    existing.push(explainer);
    explainersByKind.set(explainer.explainer_kind, existing);
  }

  return (
    <div>
      <div className="mb-8">
        <Link
          href={getBackHref(entity)}
          className="font-ui text-sm text-accent hover:text-accent-hover"
        >
          {getBackLabel(entity)}
        </Link>
      </div>

      <header className="mb-10">
        <p className="small-caps mb-3">First-pass extracted concept</p>
        <h1 className="mb-3">{renderInlineTitle(entity.canonical_name)}</h1>
        <div className="flex flex-wrap gap-4 font-ui text-sm text-ink-secondary">
          <span>Candidate: {formatLabel(entity.candidate_type)}</span>
          {entity.item_type ? <span>Type: {formatLabel(entity.item_type)}</span> : null}
          <span>{entity.source_document_count} source documents</span>
          <span>{entity.claim_count} linked claims</span>
          {entity.workflow_observations.length > 0 ? (
            <span>{entity.workflow_observations.length} workflow observations</span>
          ) : null}
          {entity.workflow_stage_observations.length > 0 ? (
            <span>{entity.workflow_stage_observations.length} stage observations</span>
          ) : null}
          {entity.workflow_step_observations.length > 0 ? (
            <span>{entity.workflow_step_observations.length} step observations</span>
          ) : null}
          {entity.matched_slug ? (
            <span>Canonical suggestion: {entity.matched_slug}</span>
          ) : null}
        </div>
        <div className="mt-4 flex flex-wrap gap-3 font-ui text-sm">
          {entity.freeform_explainers.length > 0 ? (
            <a href="#extracted-explainers" className="text-brand hover:text-accent">
              Jump to explainers
            </a>
          ) : null}
          {entity.workflow_stage_observations.length > 0 ? (
            <a
              href="#workflow-stage-observations"
              className="text-brand hover:text-accent"
            >
              Jump to workflow stages
            </a>
          ) : null}
          {entity.workflow_observations.length > 0 ? (
            <a
              href="#workflow-observations"
              className="text-brand hover:text-accent"
            >
              Jump to workflow logic
            </a>
          ) : null}
          {entity.workflow_step_observations.length > 0 ? (
            <a href="#workflow-step-observations" className="text-brand hover:text-accent">
              Jump to workflow steps
            </a>
          ) : null}
          <a href="#evidence-snippets" className="text-brand hover:text-accent">
            Jump to evidence
          </a>
          <a href="#supporting-sources" className="text-brand hover:text-accent">
            Jump to sources
          </a>
          <a href="#linked-claims" className="text-brand hover:text-accent">
            Jump to claims
          </a>
        </div>
        <div className="mt-4">
          <FirstPassLiveRefresh />
        </div>
      </header>

      {entity.aliases.length > 0 ? (
        <section className="mb-10 border border-edge bg-surface p-5">
          <p className="small-caps mb-3">Aliases</p>
          <p className="text-sm leading-relaxed text-ink-secondary">
            {entity.aliases.join(", ")}
          </p>
        </section>
      ) : null}

      {entity.freeform_explainers.length > 0 ? (
        <section id="extracted-explainers" className="mb-10 border border-edge bg-surface p-5">
          <p className="small-caps mb-3">Extracted Explainers</p>
          <div className="space-y-6">
            {FIRST_PASS_EXPLAINER_ORDER.map((kind) => {
              const explainers = explainersByKind.get(kind) ?? [];
              if (explainers.length === 0) {
                return null;
              }
              return (
                <FreeformExplainerGroup
                  key={kind}
                  explainers={explainers}
                  sourceIndexById={sourceIndexById}
                />
              );
            })}
          </div>
        </section>
      ) : null}

      {entity.workflow_stage_observations.length > 0 ? (
        <section
          id="workflow-stage-observations"
          className="mb-10 border border-edge bg-surface p-5"
        >
          <p className="small-caps mb-3">Workflow Stage Observations</p>
          <div className="space-y-4">
            {entity.workflow_stage_observations.map((observation, index) => (
              <StageObservationCard
                key={`${observation.local_id}-${index}`}
                observation={observation}
                index={index}
                sourceNumber={
                  sourceIndexById.get(observation.source_document.id) ?? "?"
                }
              />
            ))}
          </div>
        </section>
      ) : null}

      {entity.workflow_observations.length > 0 ? (
        <section
          id="workflow-observations"
          className="mb-10 border border-edge bg-surface p-5"
        >
          <p className="small-caps mb-3">Workflow Logic</p>
          <div className="space-y-4">
            {entity.workflow_observations.map((observation, index) => (
              <WorkflowObservationCard
                key={`${observation.local_id}-${index}`}
                observation={observation}
                sourceNumber={
                  sourceIndexById.get(observation.source_document.id) ?? "?"
                }
              />
            ))}
          </div>
        </section>
      ) : null}

      {entity.workflow_step_observations.length > 0 ? (
        <section
          id="workflow-step-observations"
          className="mb-10 border border-edge bg-surface p-5"
        >
          <p className="small-caps mb-3">Workflow Step Observations</p>
          <div className="space-y-4">
            {entity.workflow_step_observations.map((observation, index) => (
              <StepObservationCard
                key={`${observation.local_id}-${index}`}
                observation={observation}
                sourceNumber={
                  sourceIndexById.get(observation.source_document.id) ?? "?"
                }
              />
            ))}
          </div>
        </section>
      ) : null}

      <section id="evidence-snippets" className="mb-10 border border-edge bg-surface p-5">
        <p className="small-caps mb-3">Evidence Snippets</p>
        <div className="space-y-3">
          {entity.evidence_snippets.length > 0 ? (
            entity.evidence_snippets.map((snippet, index) => {
              const sourceDocument = snippet.source_document;

              return (
                <article
                  key={`${sourceDocument?.id ?? "unlinked"}-${snippet.text}-${index}`}
                  className="border-b border-edge pb-4 last:border-b-0 last:pb-0"
                >
                  <blockquote className="mb-3 border-l-2 border-accent/30 pl-4 text-sm leading-relaxed text-ink-secondary">
                    {snippet.text}
                  </blockquote>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-2 font-ui text-xs text-ink-muted">
                    <span className="font-semibold text-ink-secondary">
                      Evidence {index + 1}
                    </span>
                    {sourceDocument ? (
                      <>
                        <a
                          href={sourceAnchor(sourceDocument.id)}
                          className="text-brand hover:underline"
                        >
                          Source {sourceIndexById.get(sourceDocument.id) ?? "?"}
                        </a>
                        <PaperLink
                          document={toPaperDocument(sourceDocument)}
                          className="text-left text-brand no-underline hover:underline"
                        >
                          {renderInlineTitle(sourceDocument.title)}
                        </PaperLink>
                        <SourceExternalLinks doc={sourceDocument} />
                      </>
                    ) : (
                      <span>Source unavailable</span>
                    )}
                    <Tooltip
                      content="This snippet comes from the extracted candidate row. Some backend payloads do not yet include a richer source link."
                      position="bottom"
                    >
                      <span className="cursor-help border-b border-dotted border-edge text-ink-muted">
                        provenance
                      </span>
                    </Tooltip>
                  </div>
                </article>
              );
            })
          ) : (
            <p className="text-sm text-ink-muted">No evidence snippets captured.</p>
          )}
        </div>
      </section>

      <section id="supporting-sources" className="mb-10 border border-edge bg-surface p-5">
        <p className="small-caps mb-3">Supporting Sources</p>
        <div className="space-y-3">
          {entity.source_documents.length > 0 ? (
            entity.source_documents.map((doc) => {
              const relatedClaims = claimsBySourceId.get(doc.id) ?? [];
              const relatedEvidence = evidenceBySourceId.get(doc.id) ?? [];
              const relatedWorkflows = workflowsBySourceId.get(doc.id) ?? [];
              const relatedStages = stagesBySourceId.get(doc.id) ?? [];
              const relatedSteps = stepsBySourceId.get(doc.id) ?? [];
              const sourceNumber = sourceIndexById.get(doc.id) ?? "?";

              return (
                <article
                  key={doc.id}
                  id={`source-${doc.id}`}
                  className="scroll-mt-28 border-b border-edge pb-4 last:border-b-0 last:pb-0"
                >
                  <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-2 font-ui text-xs text-ink-muted">
                    <span className="rounded bg-surface-alt px-2 py-1 font-semibold text-ink-secondary">
                      Source {sourceNumber}
                    </span>
                    <Tooltip
                      content="Document linked to this first-pass entity or one of its linked claims/stage observations."
                      position="bottom"
                    >
                      <span className="cursor-help border-b border-dotted border-edge">
                        {formatLabel(doc.source_type)}
                      </span>
                    </Tooltip>
                    {doc.publication_year ? <span>{doc.publication_year}</span> : <span>year unknown</span>}
                    {doc.journal_or_source ? <span>{doc.journal_or_source}</span> : null}
                    <SourceExternalLinks doc={doc} />
                  </div>
                  <div className="mb-2 text-sm text-ink">
                    <PaperLink
                      document={toPaperDocument(doc)}
                      className="text-left text-ink no-underline hover:text-accent hover:underline"
                    >
                      {renderInlineTitle(doc.title)}
                    </PaperLink>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-2 font-ui text-xs text-ink-muted">
                    <a href="#evidence-snippets" className="text-brand hover:underline">
                      {relatedEvidence.length} evidence snippet{relatedEvidence.length === 1 ? "" : "s"}
                    </a>
                    {relatedWorkflows.length > 0 ? (
                      <a
                        href="#workflow-observations"
                        className="text-brand hover:underline"
                      >
                        {relatedWorkflows.length} workflow logic note
                        {relatedWorkflows.length === 1 ? "" : "s"}
                      </a>
                    ) : null}
                    {relatedStages.length > 0 ? (
                      <a
                        href="#workflow-stage-observations"
                        className="text-brand hover:underline"
                      >
                        {relatedStages.length} workflow stage
                        {relatedStages.length === 1 ? "" : "s"}
                      </a>
                    ) : null}
                    {relatedSteps.length > 0 ? (
                      <a
                        href="#workflow-step-observations"
                        className="text-brand hover:underline"
                      >
                        {relatedSteps.length} workflow step
                        {relatedSteps.length === 1 ? "" : "s"}
                      </a>
                    ) : null}
                    <a href="#linked-claims" className="text-brand hover:underline">
                      {relatedClaims.length} linked claim{relatedClaims.length === 1 ? "" : "s"}
                    </a>
                    {relatedClaims.slice(0, 3).map((claim, index) => (
                      <a
                        key={claim.id}
                        href={claimAnchor(claim.id)}
                        className="text-brand hover:underline"
                      >
                        Claim {index + 1}
                      </a>
                    ))}
                    {relatedStages.slice(0, 2).map((observation) => (
                      <a
                        key={observation.local_id}
                        href={stageAnchor(observation.local_id)}
                        className="text-brand hover:underline"
                      >
                        {observation.stage_name}
                      </a>
                    ))}
                  </div>
                </article>
              );
            })
          ) : (
            <p className="text-sm text-ink-muted">No source documents captured.</p>
          )}
        </div>
      </section>

      <section id="linked-claims" className="border border-edge bg-surface p-5">
        <p className="small-caps mb-3">Linked Claims</p>
        <div className="space-y-4">
          {entity.claims.length > 0 ? (
            entity.claims.map((claim, index) => {
              const locatorRows = getLocatorRows(claim.source_locator);
              const quotedText = getQuotedText(claim);
              const sourceNumber = sourceIndexById.get(claim.source_document.id) ?? "?";

              return (
                <article
                  key={claim.id}
                  id={`claim-${claim.id}`}
                  className="scroll-mt-28 border-b border-edge pb-4 last:border-b-0 last:pb-0"
                >
                  <div className="mb-2 flex flex-wrap items-center gap-2 font-ui text-xs text-ink-muted">
                    <span className="rounded bg-surface-alt px-2 py-1 font-semibold text-ink-secondary">
                      Claim {index + 1}
                    </span>
                    <span>{formatLabel(claim.claim_type)}</span>
                    <span>{claim.polarity}</span>
                    <span>{claim.source_document.publication_year ?? "year unknown"}</span>
                    <a
                      href={sourceAnchor(claim.source_document.id)}
                      className="text-brand hover:underline"
                    >
                      Source {sourceNumber}
                    </a>
                    <PaperLink
                      document={toPaperDocument(claim.source_document)}
                      className="text-left text-brand no-underline hover:underline"
                    >
                      {renderInlineTitle(claim.source_document.title)}
                    </PaperLink>
                    {locatorRows.length > 0 ? (
                      <Tooltip
                        position="bottom"
                        maxWidth="360px"
                        content={
                          <div className="space-y-1">
                            {locatorRows.map((row) => (
                              <div key={row.label}>
                                <span className="font-semibold text-ink">{row.label}:</span>{" "}
                                <span>{row.value}</span>
                              </div>
                            ))}
                          </div>
                        }
                      >
                        <span className="cursor-help border-b border-dotted border-edge text-ink-muted">
                          locator
                        </span>
                      </Tooltip>
                    ) : null}
                    <SourceExternalLinks doc={claim.source_document} />
                  </div>
                  <p className="mb-3 text-sm leading-relaxed text-ink-secondary">
                    {claim.claim_text_normalized}
                  </p>
                  {quotedText ? (
                    <div className="rounded border border-edge bg-surface-alt px-4 py-3">
                      <div className="mb-1 flex flex-wrap items-center gap-2 font-ui text-xs text-ink-muted">
                        <span className="font-semibold text-ink-secondary">Quoted text</span>
                        <Tooltip
                          content="Direct quote captured in the source locator for this extracted claim."
                          position="bottom"
                        >
                          <span className="cursor-help border-b border-dotted border-edge">
                            source-backed
                          </span>
                        </Tooltip>
                      </div>
                      <blockquote className="text-sm leading-relaxed text-ink-secondary">
                        {quotedText}
                      </blockquote>
                    </div>
                  ) : null}
                </article>
              );
            })
          ) : (
            <p className="text-sm text-ink-muted">No linked claims captured.</p>
          )}
        </div>
      </section>
    </div>
  );
}
