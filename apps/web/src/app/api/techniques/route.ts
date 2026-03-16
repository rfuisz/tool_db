import { NextResponse } from "next/server";

import { getItemAggregates } from "@/lib/backend-data";
import { TECHNIQUE_LABELS } from "@/lib/vocabularies";
import { TECHNIQUE_DESCRIPTIONS } from "@/lib/explanations";

export async function GET() {
  const aggregates = await getItemAggregates();

  const techniques = aggregates.by_technique
    .map((b) => ({
      key: b.value,
      label: TECHNIQUE_LABELS[b.value] ?? b.value.replace(/_/g, " "),
      description:
        TECHNIQUE_DESCRIPTIONS[b.value] ??
        "A technique-level grouping derived from the current toolkit evidence.",
      total_count: b.count,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return NextResponse.json({
    total: techniques.length,
    techniques,
  });
}
