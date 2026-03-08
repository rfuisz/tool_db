import { NextRequest, NextResponse } from "next/server";

import { parseItemSearchFilters } from "@/lib/api-route-utils";
import { getItems } from "@/lib/backend-data";
import { searchItems } from "@/lib/api-search";

export async function GET(request: NextRequest) {
  const filters = parseItemSearchFilters(request.nextUrl.searchParams);
  const items = await getItems();
  const result = searchItems(items, filters);

  return NextResponse.json({
    filters,
    total: result.total,
    limit: result.limit,
    offset: result.offset,
    items: result.results,
  });
}
