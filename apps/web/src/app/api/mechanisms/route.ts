import { NextRequest, NextResponse } from "next/server";

import { parseMechanismConceptSearchFilters } from "@/lib/api-route-utils";
import { getItems } from "@/lib/backend-data";
import { searchMechanismConcepts } from "@/lib/api-search";

export async function GET(request: NextRequest) {
  const filters = parseMechanismConceptSearchFilters(request.nextUrl.searchParams);
  const items = await getItems();
  const result = searchMechanismConcepts(items, filters);

  return NextResponse.json({
    filters,
    total: result.total,
    limit: result.limit,
    offset: result.offset,
    mechanisms: result.results.map((c) => ({
      key: c.key,
      label: c.label,
      description: c.description,
      summary: c.summary,
      total_count: c.totalCount,
      architecture_count: c.architectureCount,
      component_count: c.componentCount,
      capabilities: c.capabilities,
      component_names: c.componentNames,
    })),
  });
}
