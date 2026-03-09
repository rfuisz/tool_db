import { ITEM_TYPE_LABELS, MECHANISM_LABELS } from "@/lib/vocabularies";
import type { ToolkitItem } from "@/lib/types";

function humanizeToken(value: string): string {
  return value.replace(/_/g, " ");
}

function stripSimpleMarkdown(value: string): string {
  return value
    .replace(/^---[\s\S]*?---\s*/m, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .trim();
}

function formatList(values: string[]): string {
  const filtered = values.map((value) => value.trim()).filter(Boolean);
  if (filtered.length === 0) {
    return "";
  }
  if (filtered.length === 1) {
    return filtered[0];
  }
  if (filtered.length === 2) {
    return `${filtered[0]} and ${filtered[1]}`;
  }
  return `${filtered.slice(0, -1).join(", ")}, and ${filtered.at(-1)}`;
}

function extractMarkdownSection(markdown: string | null | undefined, heading: string): string {
  if (!markdown) {
    return "";
  }

  const escapedHeading = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = markdown.match(
    new RegExp(`^## ${escapedHeading}\\s*\\n([\\s\\S]*?)(?=^##\\s|\\Z)`, "m"),
  );

  return stripSimpleMarkdown(match?.[1] ?? "");
}

function extractMarkdownBullets(markdown: string | null | undefined, heading: string): string[] {
  const section = extractMarkdownSection(markdown, heading);
  if (!section) {
    return [];
  }

  return section
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => /^(-|\d+\.)\s+/.test(line))
    .map((line) => stripSimpleMarkdown(line.replace(/^(-|\d+\.)\s+/, "")));
}

function buildUsefulnessText(
  item: ToolkitItem,
  layerTitle: string,
  workflowLikelyFit: string[],
): string {
  const mechanismText = formatList(
    item.mechanisms.map((mechanism) => MECHANISM_LABELS[mechanism] ?? humanizeToken(mechanism)),
  );
  const processText = formatList(item.target_processes.map(humanizeToken));
  const inputText = item.primary_input_modality
    ? `${humanizeToken(item.primary_input_modality)}-controlled`
    : null;
  const outputText = item.primary_output_modality
    ? humanizeToken(item.primary_output_modality)
    : null;

  const leading =
    inputText && processText
      ? `${item.canonical_name} is most useful when you need ${inputText} control over ${processText}.`
      : inputText && outputText
        ? `${item.canonical_name} is most useful when you need ${inputText} ${outputText} control.`
        : processText
          ? `${item.canonical_name} is most useful when you need a concrete way to control ${processText}.`
          : `${item.canonical_name} is most useful as a ${ITEM_TYPE_LABELS[item.item_type].toLowerCase()} record in the toolkit.`;

  const layerNote =
    layerTitle === "Component"
      ? "Because this is a component, it should be read as a part that plugs into a larger architecture rather than as a complete switch on its own."
      : layerTitle === "Architecture"
        ? "Because this is an architecture, the main question is how well its arrangement of parts solves the control problem in practice."
        : "Because this sits high in the taxonomy, it is best read as a reusable strategy rather than a one-off implementation.";

  const mechanismNote = mechanismText
    ? `Its currently tagged mechanism is ${mechanismText}.`
    : "";
  const workflowNote = workflowLikelyFit.length > 0
    ? `Current workflow-fit notes point to ${formatList(workflowLikelyFit)}.`
    : "";

  return [leading, layerNote, mechanismNote, workflowNote].filter(Boolean).join(" ");
}

function buildProblemSolvedText(item: ToolkitItem, layerTitle: string): string {
  const processText = formatList(item.target_processes.map(humanizeToken));
  const outputText = item.primary_output_modality
    ? humanizeToken(item.primary_output_modality)
    : null;

  if (layerTitle === "Component") {
    return `${item.canonical_name} helps by supplying a specific functional part inside a larger design${processText ? ` for ${processText}` : ""}${outputText ? `, with the intended downstream effect landing on ${outputText}` : ""}.`;
  }

  return `${item.canonical_name} helps by bundling a reusable control pattern${processText ? ` for ${processText}` : ""}${outputText ? ` that produces ${outputText}` : ""}.`;
}

function buildComparisonGuidance(
  item: ToolkitItem,
  axisTitle: string,
  layerTitle: string,
): string {
  const compareWithin = [
    item.family ? `${item.family} family records` : "",
    item.mechanisms.length > 0
      ? `${formatList(
          item.mechanisms.map((mechanism) =>
            (MECHANISM_LABELS[mechanism] ?? humanizeToken(mechanism)).toLowerCase(),
          ),
        )} items`
      : "",
    `${ITEM_TYPE_LABELS[item.item_type].toLowerCase()} records`,
  ].filter(Boolean);

  const sameLayer = `Compare ${item.canonical_name} first against ${formatList(compareWithin)} that address similar control goals.`;
  const crossLayer =
    layerTitle === "Component"
      ? `Because it is a ${layerTitle.toLowerCase()} in the ${axisTitle.toLowerCase()}, the key comparison is what role it fills inside a larger construct, not whether it already behaves like a complete switch or workflow.`
      : `Because it sits at the ${layerTitle.toLowerCase()} layer, cross-layer comparisons to components, methods, or workflows answer a different question than apples-to-apples comparison within the same layer.`;
  const evidenceBoundary =
    item.citations.length === 0 && item.comparisons?.length === 0
      ? "This record still lacks ranked benchmark citations, so the page can frame how to compare it even when it cannot yet make a source-backed winner/loser claim."
      : "";

  return [sameLayer, crossLayer, evidenceBoundary].filter(Boolean).join(" ");
}

function buildScoreStatus(item: ToolkitItem): string {
  const missingInputs = [
    item.citations.length === 0 ? "ranked citations are still missing" : "",
    item.validations.length === 0 && !item.validation_rollup
      ? "canonical validation observations have not been stored yet"
      : "",
  ].filter(Boolean);

  const whyMissing = missingInputs.length > 0
    ? `Scores are intentionally blank because ${formatList(missingInputs)}.`
    : "Scores are intentionally blank because the evidence inputs needed for scoring are incomplete.";

  return `${whyMissing} For now, use the page as a structural guide to mechanism, modality, taxonomy, and likely workflow role rather than as an evidence-weighted ranking.`;
}

export function buildItemDetailFallbacks(
  item: ToolkitItem,
  taxonomy: { axisTitle: string; layerTitle: string },
): {
  usefulness: string;
  problemSolved: string;
  comparisonGuidance: string;
  workflowLikelyFit: string[];
  workflowMissingEvidence: string[];
  scoreStatus: string;
} {
  const workflowLikelyFit = extractMarkdownBullets(item.workflow_fit_markdown, "Likely Fit");
  const workflowMissingEvidence = extractMarkdownBullets(
    item.workflow_fit_markdown,
    "Missing Evidence",
  );

  return {
    usefulness: buildUsefulnessText(item, taxonomy.layerTitle, workflowLikelyFit),
    problemSolved: buildProblemSolvedText(item, taxonomy.layerTitle),
    comparisonGuidance: buildComparisonGuidance(
      item,
      taxonomy.axisTitle,
      taxonomy.layerTitle,
    ),
    workflowLikelyFit,
    workflowMissingEvidence,
    scoreStatus: buildScoreStatus(item),
  };
}
