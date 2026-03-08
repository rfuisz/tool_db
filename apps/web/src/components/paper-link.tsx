"use client";

import type { SourceDocument, CitationRole } from "@/lib/types";
import { usePaperModal } from "./paper-modal";
import type { ReactNode } from "react";

interface PaperLinkProps {
  document: SourceDocument;
  citationRole?: CitationRole;
  whyThisMatters?: string;
  children: ReactNode;
  className?: string;
}

export function PaperLink({
  document,
  citationRole,
  whyThisMatters,
  children,
  className = "",
}: PaperLinkProps) {
  const { openPaper } = usePaperModal();

  return (
    <button
      type="button"
      onClick={() => openPaper({ document, citationRole, whyThisMatters })}
      className={`cursor-pointer text-left underline decoration-edge decoration-1 underline-offset-2 transition-colors hover:text-accent hover:decoration-accent ${className}`}
    >
      {children}
    </button>
  );
}
