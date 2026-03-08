/**
 * Design-system consistency tests.
 *
 * Run:  node --test tests/design-system.test.mjs
 *
 * Verifies that:
 *   1. globals.css defines every color token from design-tokens.ts
 *   2. globals.css defines every font stack
 *   3. Component and page files do not use banned color classes (raw slate/gray)
 *   4. Component and page files use font-display / font-body / font-ui / font-data
 *      rather than font-sans / font-serif
 *   5. Heading elements use the display font (via CSS rule)
 *   6. Key spacing and margin patterns are respected
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, extname } from "node:path";

const ROOT = new URL("..", import.meta.url).pathname.replace(/\/$/, "");

function read(rel) {
  return readFileSync(join(ROOT, rel), "utf-8");
}

function collectFiles(dir, ext) {
  const results = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectFiles(full, ext));
    } else if (extname(entry.name) === ext) {
      results.push(full);
    }
  }
  return results;
}

// ── Canonical token lists ──────────────────────────────

const COLOR_TOKENS = [
  "ink", "ink-secondary", "ink-muted", "ink-faint",
  "parchment", "surface", "surface-alt",
  "edge", "edge-strong",
  "brand", "brand-hover", "brand-light",
  "accent", "accent-hover", "accent-light",
  "valid", "valid-light",
  "caution", "caution-light",
  "danger", "danger-light",
];

const FONT_TOKENS = ["display", "body", "ui", "data"];

const BANNED_CLASS_PATTERNS = [
  /\btext-slate-\d/,
  /\bbg-slate-\d/,
  /\bborder-slate-\d/,
  /\btext-gray-\d/,
  /\bbg-gray-\d/,
  /\bborder-gray-\d/,
];

const BANNED_FONT_CLASSES = [/\bfont-sans\b/, /\bfont-serif\b/];

// ── Tests ──────────────────────────────────────────────

const css = read("src/app/globals.css");

describe("Color tokens in globals.css", () => {
  for (const token of COLOR_TOKENS) {
    it(`defines --color-${token}`, () => {
      const re = new RegExp(`--color-${token}\\s*:`);
      assert.match(css, re, `Missing --color-${token} in globals.css`);
    });
  }
});

describe("Font tokens in globals.css", () => {
  for (const token of FONT_TOKENS) {
    it(`defines --font-${token} in @theme`, () => {
      const re = new RegExp(`--font-${token}\\s*:`);
      assert.match(css, re, `Missing --font-${token} in globals.css`);
    });
  }
});

describe("Typography base rules", () => {
  it("body sets font-family to var(--font-body)", () => {
    assert.match(css, /body\s*\{[^}]*font-family:\s*var\(--font-body\)/s);
  });

  it("headings set font-family to var(--font-display)", () => {
    assert.match(css, /h1.*\{[^}]*font-family:\s*var\(--font-display\)/s);
  });

  it("nav/button/input set font-family to var(--font-ui)", () => {
    assert.match(css, /nav.*\{[^}]*font-family:\s*var\(--font-ui\)/s);
  });

  it("body sets background to var(--color-parchment)", () => {
    assert.match(css, /body\s*\{[^}]*background-color:\s*var\(--color-parchment\)/s);
  });

  it("body sets color to var(--color-ink)", () => {
    assert.match(css, /body\s*\{[^}]*color:\s*var\(--color-ink\)/s);
  });
});

describe("Font stacks defined in :root (not only @theme inline)", () => {
  for (const token of FONT_TOKENS) {
    it(`:root defines --font-${token}`, () => {
      const rootBlock = css.match(/:root\s*\{([^}]+)\}/s)?.[1] ?? "";
      const re = new RegExp(`--font-${token}\\s*:`);
      assert.match(rootBlock, re, `Font stack --font-${token} must be in :root so CSS rules can reference it`);
    });
  }
});

describe("Component files: no banned color classes", () => {
  const componentDir = join(ROOT, "src/components");
  const pageDir = join(ROOT, "src/app");
  const files = [
    ...collectFiles(componentDir, ".tsx"),
    ...collectFiles(pageDir, ".tsx"),
  ];

  for (const file of files) {
    const content = readFileSync(file, "utf-8");
    const rel = file.replace(ROOT + "/", "");

    for (const pattern of BANNED_CLASS_PATTERNS) {
      it(`${rel} has no ${pattern.source}`, () => {
        const match = content.match(pattern);
        assert.equal(
          match,
          null,
          `Found banned class "${match?.[0]}" in ${rel}. Use design-token equivalents (text-ink, bg-surface, border-edge, etc.) instead.`
        );
      });
    }
  }
});

describe("Component files: no raw font-sans / font-serif", () => {
  const componentDir = join(ROOT, "src/components");
  const pageDir = join(ROOT, "src/app");
  const files = [
    ...collectFiles(componentDir, ".tsx"),
    ...collectFiles(pageDir, ".tsx"),
  ];

  for (const file of files) {
    const content = readFileSync(file, "utf-8");
    const rel = file.replace(ROOT + "/", "");

    for (const pattern of BANNED_FONT_CLASSES) {
      it(`${rel} has no ${pattern.source}`, () => {
        const match = content.match(pattern);
        assert.equal(
          match,
          null,
          `Found "${match?.[0]}" in ${rel}. Use font-display, font-body, font-ui, or font-data instead.`
        );
      });
    }
  }
});

describe("Key spacing patterns", () => {
  it("layout.tsx uses pt-24 (page top padding)", () => {
    const layout = read("src/app/layout.tsx");
    assert.match(layout, /pt-24/, "Root layout should use pt-24 for header offset");
  });

  it("layout.tsx uses max-w-5xl", () => {
    const layout = read("src/app/layout.tsx");
    assert.match(layout, /max-w-5xl/, "Root layout should constrain content width");
  });
});

describe("design-tokens.ts is in sync with globals.css", () => {
  const tokens = read("src/lib/design-tokens.ts");

  for (const token of COLOR_TOKENS) {
    it(`design-tokens.ts lists color "${token}"`, () => {
      const quoted = tokens.includes(`"${token}"`);
      const unquoted = new RegExp(`\\b${token.replace(/-/g, "\\-")}\\s*:`).test(tokens);
      assert.ok(
        quoted || unquoted,
        `design-tokens.ts is missing color token "${token}"`
      );
    });
  }

  for (const font of FONT_TOKENS) {
    it(`design-tokens.ts lists font "${font}"`, () => {
      const re = new RegExp(`\\b${font}\\s*:`);
      assert.ok(
        re.test(tokens),
        `design-tokens.ts is missing font token "${font}"`
      );
    });
  }
});
