"use client";

import Link from "next/link";
import { Tooltip } from "./tooltip";
import {
  ITEM_TYPE_DESCRIPTIONS,
  MATURITY_DESCRIPTIONS,
  STATUS_DESCRIPTIONS,
  MODALITY_DESCRIPTIONS,
  MECHANISM_DESCRIPTIONS,
  TECHNIQUE_DESCRIPTIONS,
} from "@/lib/explanations";
import {
  ITEM_TYPE_LABELS,
  MATURITY_LABELS,
  MODALITY_LABELS,
  MECHANISM_LABELS,
  TECHNIQUE_LABELS,
} from "@/lib/vocabularies";
import type { ItemType, MaturityStage, Modality, ItemStatus } from "@/lib/types";

export function TypeBadge({ type }: { type: ItemType }) {
  const description = ITEM_TYPE_DESCRIPTIONS[type];
  return (
    <Tooltip content={description ?? `Filter all items of type: ${ITEM_TYPE_LABELS[type]}`} position="bottom">
      <Link
        href={`/items?type=${type}`}
        className="cursor-help transition-colors hover:text-accent"
      >
        {ITEM_TYPE_LABELS[type]}
      </Link>
    </Tooltip>
  );
}

export function MaturityBadge({ stage }: { stage: MaturityStage }) {
  const description = MATURITY_DESCRIPTIONS[stage];
  return (
    <Tooltip content={description ?? MATURITY_LABELS[stage]} position="bottom">
      <span className="cursor-help border-b border-dotted border-ink-faint">
        {MATURITY_LABELS[stage]}
      </span>
    </Tooltip>
  );
}

export function StatusBadge({ status }: { status: ItemStatus }) {
  const description = STATUS_DESCRIPTIONS[status];
  if (status !== "seed") return null;
  return (
    <Tooltip content={description} position="bottom">
      <span className="ml-2 cursor-help border-b border-dotted border-caution text-caution">
        Seed — needs curation
      </span>
    </Tooltip>
  );
}

export function ModalityLabel({ modality, direction }: { modality: Modality; direction: "Input" | "Output" }) {
  const description = MODALITY_DESCRIPTIONS[modality];
  return (
    <p className="text-ink-secondary">
      <span className="text-xs text-ink-muted">{direction}: </span>
      {description ? (
        <Tooltip content={description} position="bottom">
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
  const description = MECHANISM_DESCRIPTIONS[mechanism];
  const label = MECHANISM_LABELS[mechanism] ?? mechanism.replace(/_/g, " ");
  return (
    <Tooltip content={description ?? `View mechanism concept: ${label}`} position="bottom">
      <Link
        href={`/mechanisms/${mechanism}`}
        className="mr-2 cursor-help border-b border-dotted border-ink-faint text-ink-secondary transition-colors hover:text-accent hover:border-accent"
      >
        {label}
      </Link>
    </Tooltip>
  );
}

export function TechniqueTag({ technique }: { technique: string }) {
  const description = TECHNIQUE_DESCRIPTIONS[technique];
  const label = TECHNIQUE_LABELS[technique] ?? technique.replace(/_/g, " ");
  return (
    <Tooltip content={description ?? `View technique concept: ${label}`} position="bottom">
      <Link
        href={`/techniques/${technique}`}
        className="mr-2 cursor-help border-b border-dotted border-ink-faint text-ink-secondary transition-colors hover:text-accent hover:border-accent"
      >
        {label}
      </Link>
    </Tooltip>
  );
}
