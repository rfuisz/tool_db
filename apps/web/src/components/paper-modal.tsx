"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { SourceDocument, CitationRole } from "@/lib/types";
import { CITATION_ROLE_LABELS } from "@/lib/vocabularies";
import { renderInlineTitle } from "@/lib/render-inline-title";

interface PaperModalPayload {
  document: SourceDocument;
  citationRole?: CitationRole;
  whyThisMatters?: string;
}

interface PaperModalContextValue {
  openPaper: (payload: PaperModalPayload) => void;
}

const PaperModalContext = createContext<PaperModalContextValue>({
  openPaper: () => {},
});

export function usePaperModal() {
  return useContext(PaperModalContext);
}

// ── Provider ────────────────────────────────────────

export function PaperModalProvider({ children }: { children: ReactNode }) {
  const [payload, setPayload] = useState<PaperModalPayload | null>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  const openPaper = useCallback((p: PaperModalPayload) => setPayload(p), []);
  const close = useCallback(() => setPayload(null), []);

  useEffect(() => {
    if (!payload) return;
    function onEsc(e: KeyboardEvent) {
      if (e.key === "Escape") close();
    }
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, [payload, close]);

  return (
    <PaperModalContext.Provider value={{ openPaper }}>
      {children}

      {payload && (
        <div
          ref={overlayRef}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-ink/30 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === overlayRef.current) close();
          }}
        >
          <PaperCard payload={payload} onClose={close} />
        </div>
      )}
    </PaperModalContext.Provider>
  );
}

// ── Modal Card ──────────────────────────────────────

function PaperCard({
  payload,
  onClose,
}: {
  payload: PaperModalPayload;
  onClose: () => void;
}) {
  const { document: doc, citationRole, whyThisMatters } = payload;

  const doiUrl = doc.doi ? `https://doi.org/${doc.doi}` : null;
  const pmidUrl = doc.pmid ? `https://pubmed.ncbi.nlm.nih.gov/${doc.pmid}/` : null;
  const externalUrl = doiUrl ?? pmidUrl ?? (doc.journal_or_source?.startsWith("http") ? doc.journal_or_source : null);

  return (
    <div className="mx-4 w-full max-w-lg animate-in rounded-lg border border-edge bg-surface shadow-xl shadow-ink/10">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 border-b border-edge px-6 pb-4 pt-5">
        <div className="min-w-0 flex-1">
          {citationRole && (
            <p className="small-caps mb-2 text-accent">
              {CITATION_ROLE_LABELS[citationRole]}
            </p>
          )}
          <h3 className="font-body text-lg font-semibold leading-snug text-ink">
            {renderInlineTitle(doc.title)}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="shrink-0 rounded p-1 text-ink-muted transition-colors hover:bg-surface-alt hover:text-ink"
          aria-label="Close"
        >
          <svg className="h-4 w-4" viewBox="0 0 16 16" fill="none">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {/* Meta */}
      <div className="space-y-3 px-6 py-5">
        {/* Journal + Year */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-ui text-sm">
          {doc.journal_or_source && !doc.journal_or_source.startsWith("http") && (
            <span className="italic text-ink-secondary">{doc.journal_or_source}</span>
          )}
          {doc.publication_year && (
            <span className="font-data text-ink-muted">{doc.publication_year}</span>
          )}
          {doc.source_type && (
            <span className="text-ink-muted">{doc.source_type.replace(/_/g, " ")}</span>
          )}
        </div>

        {/* IDs */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 font-ui text-xs">
          {doc.doi && (
            <span className="text-ink-muted">
              DOI: <span className="font-data text-ink-secondary">{doc.doi}</span>
            </span>
          )}
          {doc.pmid && (
            <span className="text-ink-muted">
              PMID: <span className="font-data text-ink-secondary">{doc.pmid}</span>
            </span>
          )}
        </div>

        {/* Why this matters */}
        {whyThisMatters && (
          <div className="rounded bg-surface-alt px-4 py-3">
            <p className="small-caps mb-1.5">Why this matters</p>
            <p className="text-sm leading-relaxed text-ink-secondary">
              {whyThisMatters}
            </p>
          </div>
        )}

        {doc.is_retracted && (
          <div className="rounded bg-danger-light px-4 py-3 font-ui text-sm font-bold text-danger">
            This paper has been retracted.
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 border-t border-edge px-6 py-4">
        {doiUrl && (
          <a
            href={doiUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded bg-brand px-3.5 py-2 font-ui text-xs font-medium text-white transition-colors hover:bg-brand-hover"
          >
            View via DOI
            <ExternalIcon />
          </a>
        )}
        {pmidUrl && (
          <a
            href={pmidUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded border border-edge px-3.5 py-2 font-ui text-xs font-medium text-ink-secondary transition-colors hover:border-edge-strong hover:text-ink"
          >
            PubMed
            <ExternalIcon />
          </a>
        )}
        {!doiUrl && !pmidUrl && externalUrl && (
          <a
            href={externalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded bg-brand px-3.5 py-2 font-ui text-xs font-medium text-white transition-colors hover:bg-brand-hover"
          >
            View Source
            <ExternalIcon />
          </a>
        )}
        <button
          onClick={onClose}
          className="ml-auto font-ui text-xs text-ink-muted transition-colors hover:text-ink"
        >
          Close
        </button>
      </div>
    </div>
  );
}

function ExternalIcon() {
  return (
    <svg className="h-3 w-3" viewBox="0 0 12 12" fill="none">
      <path d="M5 1H2a1 1 0 00-1 1v8a1 1 0 001 1h8a1 1 0 001-1V7M7 1h4m0 0v4m0-4L6 6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
