import { NextRequest, NextResponse } from "next/server";

import { parseWorkflowSearchFilters } from "@/lib/api-route-utils";
import { getWorkflows } from "@/lib/backend-data";
import { searchWorkflows } from "@/lib/api-search";

export async function GET(request: NextRequest) {
  const filters = parseWorkflowSearchFilters(request.nextUrl.searchParams);
  const workflows = await getWorkflows();
  const result = searchWorkflows(workflows, filters);

  return NextResponse.json({
    filters,
    total: result.total,
    limit: result.limit,
    offset: result.offset,
    workflows: result.results,
  });
}
