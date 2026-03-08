"use client";

import Link from "next/link";
import { Tooltip } from "./tooltip";
import {
  MATURITY_EXPLANATIONS,
  STATUS_EXPLANATIONS,
  MODALITY_EXPLANATIONS,
  MECHANISM_EXPLANATIONS,
} from "@/lib/explanations";
import {
  ITEM_TYPE_LABELS,
  MATURITY_LABELS,
  MODALITY_LABELS,
  MECHANISM_LABELS,
  TECHNIQUE_LABELS,
} from "@/lib/vocabularies";
import type { ItemType, MaturityStage, Modality, ItemStatus } from "@/lib/types";

export function DetailTooltips() {
  return null;
}

export function TypeBadge({ type }: { type: ItemType }) {
  return (
    <Tooltip content={`Filter all items of type: ${ITEM_TYPE_LABELS[type]}`} position="bottom">
      <Link
        href={`/items?type=${type}`}
        className="transition-colors hover:text-accent"
      >
        {ITEM_TYPE_LABELS[type]}
      </Link>
    </Tooltip>
  );
}

export function MaturityBadge({ stage }: { stage: MaturityStage }) {
  const explanation = MATURITY_EXPLANATIONS[MATURITY_LABELS[stage]];
  return (
    <Tooltip content={explanation ?? MATURITY_LABELS[stage]} position="bottom">
      <span className="cursor-help border-b border-dotted border-ink-faint">
        {MATURITY_LABELS[stage]}
      </span>
    </Tooltip>
  );
}

export function StatusBadge({ status }: { status: ItemStatus }) {
  const explanation = STATUS_EXPLANATIONS[status];
  if (status !== "seed") return null;
  return (
    <Tooltip content={explanation} position="bottom">
      <span className="ml-2 cursor-help border-b border-dotted border-caution text-caution">
        Seed — needs curation
      </span>
    </Tooltip>
  );
}

export function ModalityLabel({ modality, direction }: { modality: Modality; direction: "Input" | "Output" }) {
  const explanation = MODALITY_EXPLANATIONS[modality];
  return (
    <p className="text-ink-secondary">
      <span className="text-xs text-ink-muted">{direction}: </span>
      {explanation ? (
        <Tooltip content={explanation} position="bottom">
          <span className="cursor-help border-b border-dotted border-ink-faint">
            {MODALITY_LABELS[modality]}
          </span>
        </Tooltip>
      ) : (
        MODALITY_LABELS[modality]
      )}
    </p>
  );
}

export function MechanismTag({ mechanism }: { mechanism: string }) {
  const explanation = MECHANISM_EXPLANATIONS[mechanism];
  const label = MECHANISM_LABELS[mechanism] ?? mechanism.replace(/_/g, " ");
  return (
    <Tooltip content={explanation ?? `Filter by mechanism: ${label}`} position="bottom">
      <Link
        href={`/items?mechanism=${mechanism}`}
        className="mr-2 cursor-help border-b border-dotted border-ink-faint text-ink-secondary transition-colors hover:text-accent hover:border-accent"
      >
        {label}
      </Link>
    </Tooltip>
  );
}

export function TechniqueTag({ technique }: { technique: string }) {
  const label = TECHNIQUE_LABELS[technique] ?? technique.replace(/_/g, " ");
  return (
    <Tooltip content={`Filter by technique: ${label}`} position="bottom">
      <Link
        href={`/items?technique=${technique}`}
        className="mr-2 text-ink-secondary transition-colors hover:text-accent"
      >
        {label}
      </Link>
    </Tooltip>
  );
}
