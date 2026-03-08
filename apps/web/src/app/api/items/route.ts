import { NextRequest, NextResponse } from "next/server";

import { parseItemSearchFilters } from "@/lib/api-route-utils";
import { searchItems } from "@/lib/api-search";

export async function GET(request: NextRequest) {
  const filters = parseItemSearchFilters(request.nextUrl.searchParams);
  const result = searchItems(filters);

  return NextResponse.json({
    filters,
    total: result.total,
    limit: result.limit,
    offset: result.offset,
    items: result.results,
  });
}
