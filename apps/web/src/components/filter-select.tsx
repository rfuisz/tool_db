"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface FilterSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder: string;
}

export function FilterSelect({ value, onChange, options, placeholder }: FilterSelectProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const selected = options.find((o) => o.value === value);
  const label = selected?.label ?? placeholder;
  const isPlaceholder = !selected;

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) close();
    }
    function onEsc(e: KeyboardEvent) {
      if (e.key === "Escape") close();
    }
    document.addEventListener("mousedown", onClickOutside);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onClickOutside);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open, close]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`
          flex h-9 items-center gap-1.5 border-b bg-transparent
          pr-5 text-left text-sm outline-none transition-colors
          ${open ? "border-accent text-ink" : "border-edge text-ink-secondary hover:border-edge-strong hover:text-ink"}
          ${isPlaceholder ? "text-ink-muted" : ""}
        `}
      >
        <span className="truncate">{label}</span>
        <svg
          className={`pointer-events-none absolute right-0 top-1/2 h-2 w-3 -translate-y-1/2 transition-transform ${open ? "rotate-180" : ""}`}
          viewBox="0 0 12 8"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M1 1.5L6 6.5L11 1.5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-ink-muted"
          />
        </svg>
      </button>

      {open && (
        <div className="absolute left-0 top-full z-50 mt-1.5 min-w-[180px] overflow-hidden rounded border border-edge bg-surface shadow-lg shadow-ink/5">
          {options.map((opt) => {
            const active = opt.value === value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  onChange(opt.value);
                  close();
                }}
                className={`
                  flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors
                  ${active
                    ? "bg-accent-light font-medium text-accent"
                    : "text-ink-secondary hover:bg-surface-alt hover:text-ink"
                  }
                `}
              >
                {active && (
                  <svg className="h-3 w-3 shrink-0 text-accent" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
                {!active && <span className="w-3 shrink-0" />}
                <span>{opt.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
