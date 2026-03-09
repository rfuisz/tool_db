import { NextRequest, NextResponse } from "next/server";

import { parseTechniqueConceptSearchFilters } from "@/lib/api-route-utils";
import { getItems } from "@/lib/backend-data";
import { searchTechniqueConcepts } from "@/lib/api-search";

export async function GET(request: NextRequest) {
  const filters = parseTechniqueConceptSearchFilters(request.nextUrl.searchParams);
  const items = await getItems();
  const result = searchTechniqueConcepts(items, filters);

  return NextResponse.json({
    filters,
    total: result.total,
    limit: result.limit,
    offset: result.offset,
    techniques: result.results.map((c) => ({
      key: c.key,
      label: c.label,
      description: c.description,
      summary: c.summary,
      total_count: c.totalCount,
      method_count: c.methodCount,
      capabilities: c.capabilities,
    })),
  });
}
