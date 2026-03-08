import Link from "next/link";
import { notFound } from "next/navigation";

import { PaperLink } from "@/components/paper-link";
import { Tooltip } from "@/components/tooltip";
import { getFirstPassItemBySlug } from "@/lib/backend-data";
import { isFirstPassEnabled } from "@/lib/first-pass-access";
import { renderInlineTitle } from "@/lib/render-inline-title";
import type {
  FirstPassClaim,
  FirstPassEvidenceSnippet,
  FirstPassSourceDocument,
  SourceDocument,
} from "@/lib/types";

function sourceAnchor(documentId: string) {
  return `#source-${documentId}`;
}

function claimAnchor(claimId: string) {
  return `#claim-${claimId}`;
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
  return typeof quotedText === "string" && quotedText.trim() ? quotedText.trim() : null;
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

export default async function FirstPassItemPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  if (!(await isFirstPassEnabled())) {
    notFound();
  }

  const { slug } = await params;
  const item = await getFirstPassItemBySlug(slug);

  if (!item) {
    notFound();
  }

  const sourceIndexById = new Map(
    item.source_documents.map((doc, index) => [doc.id, index + 1]),
  );
  const claimsBySourceId = new Map<string, FirstPassClaim[]>();
  const evidenceBySourceId = new Map<string, FirstPassEvidenceSnippet[]>();

  for (const claim of item.claims) {
    const existing = claimsBySourceId.get(claim.source_document.id) ?? [];
    existing.push(claim);
    claimsBySourceId.set(claim.source_document.id, existing);
  }

  for (const snippet of item.evidence_snippets) {
    const sourceDocumentId = snippet.source_document?.id;
    if (!sourceDocumentId) {
      continue;
    }
    const existing = evidenceBySourceId.get(sourceDocumentId) ?? [];
    existing.push(snippet);
    evidenceBySourceId.set(sourceDocumentId, existing);
  }

  return (
    <div>
      <div className="mb-8">
        <Link href="/first-pass" className="font-ui text-sm text-accent hover:text-accent-hover">
          Back to first-pass browser
        </Link>
      </div>

      <header className="mb-10">
        <p className="small-caps mb-3">First-pass extracted item</p>
        <h1 className="mb-3">{item.canonical_name}</h1>
        <div className="flex flex-wrap gap-4 font-ui text-sm text-ink-secondary">
          {item.item_type ? <span>Type: {item.item_type.replace(/_/g, " ")}</span> : null}
          <span>{item.source_document_count} source documents</span>
          <span>{item.claim_count} linked claims</span>
          {item.matched_slug ? <span>Canonical suggestion: {item.matched_slug}</span> : null}
        </div>
        <div className="mt-4 flex flex-wrap gap-3 font-ui text-sm">
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
      </header>

      {item.aliases.length > 0 ? (
        <section className="mb-10 border border-edge bg-surface p-5">
          <p className="small-caps mb-3">Aliases</p>
          <p className="text-sm leading-relaxed text-ink-secondary">
            {item.aliases.join(", ")}
          </p>
        </section>
      ) : null}

      <section id="evidence-snippets" className="mb-10 border border-edge bg-surface p-5">
        <p className="small-caps mb-3">Evidence Snippets</p>
        <div className="space-y-3">
          {item.evidence_snippets.length > 0 ? (
            item.evidence_snippets.map((snippet, index) => {
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
                      content="This snippet comes from the extracted item candidate row. Some backend payloads do not yet include the linked source document."
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
          {item.source_documents.length > 0 ? (
            item.source_documents.map((doc) => {
              const relatedClaims = claimsBySourceId.get(doc.id) ?? [];
              const relatedEvidence = evidenceBySourceId.get(doc.id) ?? [];
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
                      content="Document linked to this first-pass item or one of its linked claims."
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
          {item.claims.length > 0 ? (
            item.claims.map((claim, index) => {
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
