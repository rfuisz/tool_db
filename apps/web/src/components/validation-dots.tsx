"use client";

import type { ValidationRollup } from "@/lib/types";
import { Tooltip } from "./tooltip";
import { BIO_SYSTEM_EXPLANATIONS } from "@/lib/explanations";

const LEVELS: { key: keyof ValidationRollup; label: string; short: string }[] = [
  { key: "has_cell_free_validation", label: "Cell-free", short: "CF" },
  { key: "has_bacterial_validation", label: "Bacteria", short: "Bac" },
  { key: "has_mammalian_cell_validation", label: "Mammalian", short: "Mam" },
  { key: "has_mouse_in_vivo_validation", label: "Mouse", short: "Mus" },
  { key: "has_human_clinical_validation", label: "Human", short: "Hum" },
  { key: "has_therapeutic_use", label: "Therapeutic", short: "Tx" },
  { key: "has_independent_replication", label: "Indep. Replication", short: "Rep" },
];

export function ValidationDots({ rollup }: { rollup: ValidationRollup }) {
  return (
    <div className="flex gap-1 font-ui">
      {LEVELS.map(({ key, label, short }) => {
        const active = rollup[key];
        const explanation = BIO_SYSTEM_EXPLANATIONS[label];
        return (
          <Tooltip
            key={key}
            content={
              <span>
                <strong className={active ? "text-valid" : "text-ink-muted"}>
                  {label}: {active ? "Yes" : "No"}
                </strong>
                {explanation && <span className="mt-1 block text-ink-muted">{explanation}</span>}
              </span>
            }
            position="bottom"
          >
            <span
              className={`inline-flex h-5 cursor-help items-center rounded px-1.5 text-[10px] font-medium leading-none ${
                active
                  ? "bg-valid-light text-valid"
                  : "text-ink-faint"
              }`}
            >
              {short}
            </span>
          </Tooltip>
        );
      })}
    </div>
  );
}

export function ValidationMatrix({ rollup }: { rollup: ValidationRollup }) {
  return (
    <div className="grid grid-cols-2 gap-3 font-ui sm:grid-cols-4">
      {LEVELS.map(({ key, label }) => {
        const active = rollup[key];
        const explanation = BIO_SYSTEM_EXPLANATIONS[label];
        return (
          <Tooltip key={key} content={explanation ?? label} position="bottom">
            <span
              className={`block cursor-help rounded-lg p-3 text-center ${
                active ? "bg-valid-light" : "bg-surface-alt"
              }`}
            >
              <span
                className={`mx-auto mb-1.5 block h-2.5 w-2.5 rounded-full ${
                  active ? "bg-valid" : "bg-ink-faint"
                }`}
              />
              <span className={`block text-xs font-medium ${active ? "text-valid" : "text-ink-muted"}`}>
                {label}
              </span>
            </span>
          </Tooltip>
        );
      })}
    </div>
  );
}
