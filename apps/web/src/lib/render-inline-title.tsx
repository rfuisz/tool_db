import type { ReactNode } from "react";

const SUPPORTED_TAGS = "i|em|b|strong|sup|sub";

const ENCODED_TAG_PATTERN = new RegExp(
  `&lt;(\\/?)(${SUPPORTED_TAGS})&gt;`,
  "gi",
);
const TAG_DETECT_PATTERN = new RegExp(`<\\/?(?:${SUPPORTED_TAGS})>`, "i");
const TAG_SEGMENT_PATTERN = new RegExp(
  `<(${SUPPORTED_TAGS})>([\\s\\S]*?)<\\/\\1>`,
  "gi",
);

function normalizeInlineMarkup(text: string): string {
  return text.replace(ENCODED_TAG_PATTERN, "<$1$2>");
}

export function stripInlineTitleMarkup(title: string): string {
  return normalizeInlineMarkup(title).replace(
    new RegExp(`<\\/?(?:${SUPPORTED_TAGS})>`, "gi"),
    "",
  );
}

type InlineTag = "i" | "em" | "b" | "strong" | "sup" | "sub";

export function renderInlineTitle(title: string): ReactNode {
  const normalized = normalizeInlineMarkup(title);

  if (!TAG_DETECT_PATTERN.test(normalized)) {
    return normalized;
  }

  const parts: ReactNode[] = [];
  let cursor = 0;
  let matchIndex = 0;

  for (const match of normalized.matchAll(TAG_SEGMENT_PATTERN)) {
    const [fullMatch, tagName, content] = match;
    const start = match.index ?? 0;

    if (start > cursor) {
      parts.push(normalized.slice(cursor, start));
    }

    const TagName = tagName.toLowerCase() as InlineTag;
    parts.push(<TagName key={`inline-${matchIndex}`}>{content}</TagName>);

    cursor = start + fullMatch.length;
    matchIndex += 1;
  }

  if (parts.length === 0) {
    return stripInlineTitleMarkup(normalized);
  }

  if (cursor < normalized.length) {
    parts.push(normalized.slice(cursor));
  }

  return parts;
}
