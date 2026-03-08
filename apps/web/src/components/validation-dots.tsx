import type { ValidationRollup } from "@/lib/types";

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
        return (
          <span
            key={key}
            title={`${label}: ${active ? "Yes" : "No"}`}
            className={`inline-flex h-5 items-center rounded px-1.5 text-[10px] font-medium leading-none ${
              active
                ? "bg-valid-light text-valid"
                : "text-ink-faint"
            }`}
          >
            {short}
          </span>
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
        return (
          <div
            key={key}
            className={`rounded-lg p-3 text-center ${
              active ? "bg-valid-light" : "bg-surface-alt"
            }`}
          >
            <div
              className={`mx-auto mb-1.5 h-2.5 w-2.5 rounded-full ${
                active ? "bg-valid" : "bg-ink-faint"
              }`}
            />
            <p className={`text-xs font-medium ${active ? "text-valid" : "text-ink-muted"}`}>
              {label}
            </p>
          </div>
        );
      })}
    </div>
  );
}
