import { NextRequest, NextResponse } from "next/server";

import { parseItemSearchFilters } from "@/lib/api-route-utils";
import { getItemsBrowse, type ItemBrowseParams } from "@/lib/backend-data";

export async function GET(request: NextRequest) {
  const filters = parseItemSearchFilters(request.nextUrl.searchParams);

  const params: ItemBrowseParams = {
    q: filters.q,
    type: filters.type,
    mechanism: filters.mechanism,
    technique: filters.technique,
    family: filters.family,
    maturity_stage: filters.maturity_stage,
    status: filters.status,
    has_independent_replication: filters.has_independent_replication,
    has_mouse_in_vivo_validation: filters.has_mouse_in_vivo_validation,
    has_therapeutic_use: filters.has_therapeutic_use,
    sort: filters.sort,
    limit: filters.limit ?? 20,
    offset: filters.offset ?? 0,
  };

  const result = await getItemsBrowse(params);

  return NextResponse.json({
    filters,
    total: result.total,
    limit: result.limit,
    offset: result.offset,
    items: result.items,
  });
}
