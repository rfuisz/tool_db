import type { ItemCitation } from "@/lib/types";
import { CITATION_ROLE_LABELS } from "@/lib/vocabularies";

export function CitationList({ citations }: { citations: ItemCitation[] }) {
  if (citations.length === 0) {
    return (
      <p className="font-ui text-sm italic text-ink-muted">
        No citations yet — backfill required.
      </p>
    );
  }

  const sorted = [...citations].sort((a, b) => a.importance_rank - b.importance_rank);

  return (
    <ol className="space-y-6">
      {sorted.map((cit, idx) => (
        <li key={cit.id} className="flex gap-4">
          <span className="mt-1 font-data text-sm font-bold text-ink-muted">
            {idx + 1}.
          </span>
          <div className="flex-1">
            <p className="font-body text-[15px] font-medium leading-snug text-ink">
              {cit.document.title}
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 font-ui text-xs">
              <span className="font-semibold text-accent">
                {CITATION_ROLE_LABELS[cit.citation_role]}
              </span>
              {cit.document.journal_or_source && (
                <span className="italic text-ink-muted">{cit.document.journal_or_source}</span>
              )}
              {cit.document.publication_year && (
                <span className="font-data text-ink-muted">{cit.document.publication_year}</span>
              )}
              {cit.document.doi && (
                <a
                  href={`https://doi.org/${cit.document.doi}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand hover:underline"
                >
                  DOI
                </a>
              )}
              {cit.document.is_retracted && (
                <span className="font-bold text-danger">RETRACTED</span>
              )}
            </div>
            <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">
              {cit.why_this_matters}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
