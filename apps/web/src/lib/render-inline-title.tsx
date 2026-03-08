import type { ReactNode } from "react";

const ENCODED_EMPHASIS_TAG_PATTERN = /&lt;(\/?)(i|em)&gt;/gi;
const EMPHASIS_TAG_PATTERN = /<\/?(?:i|em)>/i;
// Avoid the dotAll flag so Render's current TypeScript target can compile this file.
const EMPHASIS_SEGMENT_PATTERN = /<(i|em)>([\s\S]*?)<\/\1>/gi;

export function renderInlineTitle(title: string): ReactNode {
  const normalized = title.replace(ENCODED_EMPHASIS_TAG_PATTERN, "<$1$2>");

  if (!EMPHASIS_TAG_PATTERN.test(normalized)) {
    return normalized;
  }

  const parts: ReactNode[] = [];
  let cursor = 0;
  let matchIndex = 0;

  for (const match of normalized.matchAll(EMPHASIS_SEGMENT_PATTERN)) {
    const [fullMatch, tagName, content] = match;
    const start = match.index ?? 0;

    if (start > cursor) {
      parts.push(normalized.slice(cursor, start));
    }

    const TagName = tagName as "i" | "em";
    parts.push(<TagName key={`emphasis-${matchIndex}`}>{content}</TagName>);

    cursor = start + fullMatch.length;
    matchIndex += 1;
  }

  if (parts.length === 0) {
    return normalized.replace(/<\/?(?:i|em)>/gi, "");
  }

  if (cursor < normalized.length) {
    parts.push(normalized.slice(cursor));
  }

  return parts;
}
