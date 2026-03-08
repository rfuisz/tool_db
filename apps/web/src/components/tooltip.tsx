"use client";

import { useState, useRef, useCallback, type ReactNode } from "react";

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  position?: "top" | "bottom";
  maxWidth?: string;
}

export function Tooltip({ content, children, position = "top", maxWidth = "280px" }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = useCallback(() => {
    if (timeout.current) {
      clearTimeout(timeout.current);
    }
    timeout.current = setTimeout(() => setVisible(true), 200);
  }, []);

  const hide = useCallback(() => {
    if (timeout.current) {
      clearTimeout(timeout.current);
    }
    timeout.current = setTimeout(() => setVisible(false), 100);
  }, []);

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {visible && (
        <span
          role="tooltip"
          className={`
            pointer-events-none absolute z-50
            ${position === "top" ? "bottom-full left-1/2 mb-2 -translate-x-1/2" : "top-full left-1/2 mt-2 -translate-x-1/2"}
            rounded border border-edge bg-surface px-3 py-2
            font-ui text-xs leading-relaxed text-ink-secondary
            shadow-lg shadow-ink/8 animate-in
          `}
          style={{ maxWidth, width: "max-content" }}
        >
          {content}
          <span
            className={`absolute left-1/2 -translate-x-1/2 border-[5px] border-transparent ${
              position === "top"
                ? "top-full border-t-surface"
                : "bottom-full border-b-surface"
            }`}
          />
        </span>
      )}
    </span>
  );
}
