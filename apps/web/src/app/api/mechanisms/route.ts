import { NextResponse } from "next/server";

import { getItemAggregates } from "@/lib/backend-data";
import { MECHANISM_LABELS } from "@/lib/vocabularies";
import { MECHANISM_DESCRIPTIONS } from "@/lib/explanations";

export async function GET() {
  const aggregates = await getItemAggregates();

  const mechanisms = aggregates.by_mechanism
    .map((b) => ({
      key: b.value,
      label: MECHANISM_LABELS[b.value] ?? b.value.replace(/_/g, " "),
      description:
        MECHANISM_DESCRIPTIONS[b.value] ??
        "A mechanism-level grouping derived from the current toolkit evidence.",
      total_count: b.count,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return NextResponse.json({
    total: mechanisms.length,
    mechanisms,
  });
}
