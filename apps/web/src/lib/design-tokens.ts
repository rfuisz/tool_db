/**
 * Canonical design token definitions.
 *
 * This is the single source of truth for the design system.
 * Any change here must be reflected in globals.css and docs/design-system.md.
 * The test suite at tests/design-system.test.mjs verifies consistency.
 */

export const COLORS = {
  ink:              "#1c1917",
  "ink-secondary":  "#44403c",
  "ink-muted":      "#a8a29e",
  "ink-faint":      "#d6d3d1",
  parchment:        "#f4efe6",
  surface:          "#fffdf7",
  "surface-alt":    "#f0ebe2",
  edge:             "#d8cfc4",
  "edge-strong":    "#c4b8a9",

  brand:            "#1e3a5f",
  "brand-hover":    "#162d4a",
  "brand-light":    "#e8edf4",

  accent:           "#b45309",
  "accent-hover":   "#92400e",
  "accent-light":   "#fef3e2",

  valid:            "#166534",
  "valid-light":    "#dcfce7",
  caution:          "#92400e",
  "caution-light":  "#fef3c7",
  danger:           "#991b1b",
  "danger-light":   "#fee2e2",
} as const;

export const FONTS = {
  display:  "Jost",
  body:     "EB Garamond",
  ui:       "Inter",
  data:     "JetBrains Mono",
} as const;

export const FONT_STACKS = {
  display: `var(--font-jost), "Century Gothic", "Avant Garde", "Futura", sans-serif`,
  body:    `var(--font-eb-garamond), "Palatino Linotype", Palatino, Georgia, serif`,
  ui:      `var(--font-inter), system-ui, -apple-system, sans-serif`,
  data:    `var(--font-jetbrains), "Courier New", monospace`,
} as const;

export const SPACING = {
  "page-x":    "1.5rem",
  "page-top":  "6rem",
  section:     "3rem",
  card:        "1.5rem",
} as const;

/** Tailwind utility class names that should NOT appear in components. */
export const BANNED_CLASSES = [
  "text-slate-",
  "bg-slate-",
  "border-slate-",
  "text-gray-",
  "bg-gray-",
  "border-gray-",
] as const;

/** Tailwind utility class names that replace the banned ones. */
export const REQUIRED_TOKEN_CLASSES = [
  "text-ink",
  "text-ink-secondary",
  "text-ink-muted",
  "bg-surface",
  "bg-parchment",
  "border-edge",
] as const;
