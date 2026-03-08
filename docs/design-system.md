# Design System — Scientific Parchment

Canonical reference for the BioControl Toolkit DB visual identity. All values
are defined in `apps/web/src/lib/design-tokens.ts` and applied via
`apps/web/src/app/globals.css`. Consistency is verified by the test suite at
`apps/web/tests/design-system.test.mjs`.

---

## Color Palette

### Core

| Token           | Hex       | Usage                               |
| --------------- | --------- | ----------------------------------- |
| `ink`           | `#1c1917` | Primary text, headings              |
| `ink-secondary` | `#44403c` | Body text, descriptions             |
| `ink-muted`     | `#a8a29e` | Labels, metadata, placeholders      |
| `ink-faint`     | `#d6d3d1` | Disabled states, empty indicators   |
| `parchment`     | `#f4efe6` | Page background (warm cream)        |
| `surface`       | `#fffdf7` | Card and panel backgrounds          |
| `surface-alt`   | `#f0ebe2` | Hover states, alternate backgrounds |
| `edge`          | `#d8cfc4` | Default borders, horizontal rules   |
| `edge-strong`   | `#c4b8a9` | Emphasized borders, hover borders   |

### Brand

| Token         | Hex       | Usage                             |
| ------------- | --------- | --------------------------------- |
| `brand`       | `#1e3a5f` | Primary brand, links, nav accents |
| `brand-hover` | `#162d4a` | Brand hover state                 |
| `brand-light` | `#e8edf4` | Light brand backgrounds           |

### Accent

| Token          | Hex       | Usage                               |
| -------------- | --------- | ----------------------------------- |
| `accent`       | `#b45309` | Warm copper accent, card hover text |
| `accent-hover` | `#92400e` | Accent hover state                  |
| `accent-light` | `#fef3e2` | Light accent backgrounds            |

### Semantic

| Token           | Hex       | Usage                      |
| --------------- | --------- | -------------------------- |
| `valid`         | `#166534` | Validation passed, success |
| `valid-light`   | `#dcfce7` | Success backgrounds        |
| `caution`       | `#92400e` | Warnings, penalties        |
| `caution-light` | `#fef3c7` | Warning backgrounds        |
| `danger`        | `#991b1b` | Errors, retractions        |
| `danger-light`  | `#fee2e2` | Error backgrounds          |

### Tag Colors (per item type)

Item-type badges use Tailwind's built-in palette at the `-50`/`-800` range for
subtle, refined contrast:

| Item Type              | Background   | Text          |
| ---------------------- | ------------ | ------------- |
| Protein Domain         | `blue-50`    | `blue-800`    |
| Multi-Component Switch | `violet-50`  | `violet-800`  |
| RNA Element            | `emerald-50` | `emerald-800` |
| Construct Pattern      | `amber-50`   | `amber-800`   |
| Engineering Method     | `rose-50`    | `rose-800`    |
| Assay Method           | `cyan-50`    | `cyan-800`    |
| Computation Method     | `orange-50`  | `orange-800`  |
| Delivery Harness       | `teal-50`    | `teal-800`    |

---

## Typography

### Font Stacks

| Token     | Font Family      | Fallback Stack                       | Usage                         |
| --------- | ---------------- | ------------------------------------ | ----------------------------- |
| `display` | Playfair Display | Georgia, Times New Roman, serif      | Page titles, h1-h3            |
| `body`    | Source Serif 4   | Georgia, Times New Roman, serif      | Body text, summaries, prose   |
| `ui`      | Inter            | system-ui, -apple-system, sans-serif | Nav, badges, labels, controls |
| `data`    | JetBrains Mono   | Courier New, monospace               | Metrics, scores, tabular data |

### Assignment Rules

Fonts are assigned in `globals.css` via element selectors:

- **`body`** → `font-body` (serif for prose)
- **`h1, h2, h3, h4`** → `font-display` (display serif for headings)
- **`nav, button, input, select, label`** → `font-ui` (sans for chrome)

Components use `font-ui`, `font-body`, `font-display`, or `font-data` Tailwind
utilities to override the inherited family where needed.

### Heading Styles

| Level | Weight | Line Height | Letter Spacing |
| ----- | ------ | ----------- | -------------- |
| h1    | 700    | 1.15        | -0.015em       |
| h2    | 600    | 1.25        | -0.015em       |
| h3    | 600    | 1.35        | -0.015em       |
| h4    | 600    | 1.4         | -0.015em       |

### Body Text

- Line height: 1.7
- Font smoothing: antialiased on both WebKit and Firefox

---

## Spacing

| Context           | Value    | Usage                              |
| ----------------- | -------- | ---------------------------------- |
| Page horizontal   | `1.5rem` | `px-6` on the main container       |
| Page top offset   | `6rem`   | `pt-24` to clear the fixed nav     |
| Section gap       | `3-4rem` | `mb-12` / `mb-16` between sections |
| Card padding      | `1.5rem` | `p-6` on card interiors            |
| Max content width | `64rem`  | `max-w-5xl` (editorial narrow)     |

---

## Banned Patterns

The following Tailwind classes are banned in component and page files. The test
suite enforces this automatically.

| Banned Class Pattern | Replacement                                        |
| -------------------- | -------------------------------------------------- |
| `text-slate-*`       | `text-ink`, `text-ink-secondary`, `text-ink-muted` |
| `bg-slate-*`         | `bg-surface`, `bg-surface-alt`, `bg-parchment`     |
| `border-slate-*`     | `border-edge`, `border-edge-strong`                |
| `text-gray-*`        | Same as above                                      |
| `bg-gray-*`          | Same as above                                      |
| `border-gray-*`      | Same as above                                      |
| `font-sans`          | `font-ui`                                          |
| `font-serif`         | `font-body` or `font-display`                      |

---

## Running the Tests

```bash
cd apps/web
node --test tests/design-system.test.mjs
```

If you are using a coding agent, note that repo-level `tests/` is hidden from
Cursor-style search by default. Reveal the suite intentionally first if needed:

```bash
python scripts/agent_test_visibility.py show
```

Re-hide it afterward with:

```bash
python scripts/agent_test_visibility.py hide
```

The test suite checks:

1. Every design token is defined in both `design-tokens.ts` and `globals.css`
2. CSS base rules set the correct font families and colors
3. No component or page file uses banned color or font classes
4. Key spacing values are present in the layout
