import { NextRequest, NextResponse } from "next/server";

import { parseExtractedWorkflowSearchFilters } from "@/lib/api-route-utils";
import { getExtractedWorkflows } from "@/lib/backend-data";
import { searchExtractedWorkflows } from "@/lib/api-search";

export async function GET(request: NextRequest) {
  const filters = parseExtractedWorkflowSearchFilters(
    request.nextUrl.searchParams,
  );
  const workflows = await getExtractedWorkflows();
  const result = searchExtractedWorkflows(workflows, filters);

  return NextResponse.json({
    total: result.total,
    limit: result.limit,
    offset: result.offset,
    workflows: result.results,
  });
}
